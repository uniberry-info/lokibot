import sqlalchemy as s
import sqlalchemy.orm as o
import secrets
import logging
import flask

log = logging.getLogger(__name__)


Base = o.declarative_base()
"""
The declarative base of all the SQL tables.
"""


class Account(Base):
    """
    A logged-in OpenID Connect account.
    """

    __tablename__ = "accounts"

    email = s.Column(s.String, primary_key=True)
    """
    The verified email of the account.
    """

    first_name = s.Column(s.String)
    """
    The first name of the account owner.
    """

    last_name = s.Column(s.String)
    """
    The last name of the account owner.
    """

    matrix_users = o.relationship("MatrixUser", back_populates="account")
    """
    The Matrix users linked to this account.
    """

    def __repr__(self):
        return f"{self.__qualname__}(id={self.id!r}, email={self.email!r}, first_name={self.first_name!r}, last_name={self.last_name!r}, private={self.private!r})"


class MatrixUser(Base):
    """
    A Matrix user, which may or may not be linked to an account.

    Has an associated token, which allows it to authenticate with Loki.
    """

    __tablename__ = "matrix_users"

    id = s.Column(s.String, primary_key=True)
    """
    The Matrix id of the user, such as ``@steffo:ryg.one``.
    """

    token = s.Column(s.String, nullable=False, default=secrets.token_urlsafe)
    """
    A secure token that the user can use to access their account.
    """

    account_email = s.Column(s.String, s.ForeignKey("accounts.email"))
    """
    If the user linked a OpenID Connect account, its email.
    """

    joined_private_space = s.Column(s.Boolean, nullable=False, default=False)
    """
    Whether this specific Matrix user has joined the private Matrix space monitored by Loki.
    """

    account = o.relationship("Account", back_populates="matrix_users")
    """
    The account linked with this Matrix user.
    """

    def __repr__(self):
        return f"{self.__class__.__qualname__}(id={self.id!r}, token={self.token!r}, account_email={self.account_email!r})"

    @classmethod
    def create(cls, session: o.Session, id: str) -> "MatrixUser":
        """
        Create a `.MatrixUser` in the database for the given Matrix user ID.

        :param session: The `sqlalchemy.orm.Session` to use.
        :param id: The user ID to create an account for.
        :return: The created `.MatrixUser`.
        """

        log.debug("Creating MatrixUser for %s", id)
        matrix_user = MatrixUser(id=id)
        matrix_user = session.merge(matrix_user)
        log.debug("Created MatrixUser for %s", id)
        return matrix_user

    def destroy(self, session: o.Session) -> None:
        """
        Destroy a `.MatrixUser` in the database.

        :param session: The `sqlalchemy.orm.Session` to use.
        """

        id = self.id
        log.debug("Deleting MatrixUser for %s", id)
        if self.account is not None and len(self.account.matrix_users) == 1:
            session.delete(self.account)
        session.delete(self)
        log.debug("Deleted MatrixUser for %s", id)

    # noinspection PyUnusedLocal
    def link(self, session: o.Session, account: Account) -> None:
        """
        Link a `.MatrixUser` to an `.Account`.

        :param session: The `sqlalchemy.orm.Session` to use. (Currently unused.)
        :param account: The `.Account` to link to.
        """
        log.debug("Linking MatrixUser %s to Account %s", self.id, account.email)
        self.account = account
        log.debug("Linked MatrixUser %s to Account %s", self.id, account.email)

    def unlink(self, session: o.Session) -> None:
        """
        Unlink a `.MatrixUser` from an `.Account`, deleting the `.Account` if it has no other connected `.MatrixUser`\\ s.

        :param session: The `sqlalchemy.orm.Session` to use.
        """

        log.debug("Unlinking Account for %s", self.id)
        if len(self.account.matrix_users) == 1:
            session.delete(self.account)
        self.account = None
        self.joined_private_space = False
        log.debug("Unlinked Account for %s", self.id)

    def profile_url(self) -> str:
        """
        Uses the `.token` to get the `~flask.url_for` this `.MatrixUser`'s profile.

        .. warning::
            Must be called inside a `~flask.Flask.app_context`!

        :return: The URL to this `.MatrixUser`'s profile.
        """

        return flask.url_for("page_matrix_profile", token=self.token)


class MatrixProcessedEvent(Base):
    """
    A Matrix event that has been processed by the bot and that should not be processed again.
    """

    __tablename__ = "matrix_processed_events"

    id = s.Column(s.String, primary_key=True)
    """
    The id of the processed event, such as ``$IhC83CM3TRkPG7UbNRsH_t_O2J5DASqzkUYVkPxYR-o``.
    """


__all__ = (
    "Base",
    "Account",
    "MatrixUser",
    "MatrixProcessedEvent",
)
