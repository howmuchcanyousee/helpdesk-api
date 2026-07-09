from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbSession
from app.core.security import create_access_token
from app.schemas.auth import Token, UserLogin
from app.schemas.user import UserCreate, UserRead
from app.services.users import authenticate_user, create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user_data: UserCreate, db: DbSession) -> UserRead:
    """Register a new active user with the default role."""
    if get_user_by_email(db, str(user_data.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    try:
        return create_user(db, user_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from error


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: DbSession) -> Token:
    """Authenticate a user and return a JWT access token."""
    user = authenticate_user(db, str(user_data.email), user_data.password)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(user.email))
