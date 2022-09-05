import sqlalchemy as s
import sqlalchemy.orm as o


Base = o.declarative_base()


class User(Base):
    """
    A Matrix user.
    """

    __tablename__ = "users"

    id = s.Column(s.String, primary_key=True)

    tokens = o.relationship("User", back_populates="user")
    authorizations = o.relationship("Authorization", back_populates="user")


class Token(Base):
    """
    A token issued to an user who joined the parent Matrix space.
    """

    __tablename__ = "tokens"

    user_id = s.Column(s.String, s.ForeignKey("users.id"), nullable=False)
    token = s.Column(s.String, primary_key=True)

    user = o.relationship("User", back_populates="tokens")


class Authorization(Base):
    """
    A successful authorization through the bot, which allows the user to join the child Matrix space.
    """

    __tablename__ = "authorizations"

    user_id = s.Column(s.String, s.ForeignKey("users.id"), primary_key=True)
    first_name = s.Column(s.String, nullable=False)
    last_name = s.Column(s.String, nullable=False)
    email = s.Column(s.String, nullable=False)
    published = s.Column(s.Boolean, nullable=False)

    user = o.relationship("User", back_populates="authorizations")


__all__ = (
    "Base",
    "User",
    "Token",
    "Authorization",
)
