import sqlalchemy as s
import sqlalchemy.orm as o
import secrets


Base = o.declarative_base()
"""
The declarative base of all the SQL tables.
"""


class Account(Base):
    """
    A logged-in OAuth2 account.
    """

    __tablename__ = "accounts"

    id = s.Column(s.Integer, primary_key=True, autoincrement=True)
    """
    Surrogate SQL id of the account.
    """

    email = s.Column(s.String, nullable=False, unique=True)
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

    private = s.Column(s.Boolean, nullable=False, default=True)
    """
    Whether the details of this account should be kept hidden, or shown on the public listing.
    """

    matrix_users = o.relationship("MatrixUser", back_populates="user")
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

    token = s.Column(s.String, nullable=False, default=lambda: secrets.token_urlsafe())
    """
    A secure token that the user can use to access their account.
    """

    account_id = s.Column(s.Integer, s.ForeignKey("accounts.id"))
    """
    If the user linked a OAuth2 account, its id.
    """

    account = o.relationship("Account", back_populates="matrix_users")
    """
    The account linked with this Matrix user.
    """

    def __repr__(self):
        return f"{self.__qualname__}(id={self.id!r}, token={self.token}, account_id={self.account_id})"


__all__ = (
    "Base",
    "Account",
    "MatrixUser",
)
