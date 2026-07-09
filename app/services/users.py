from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    """Return a user by email, if one exists."""
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create and persist a regular active user."""
    user = User(
        email=str(user_data.email),
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user when their credentials are valid."""
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
