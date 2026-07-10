from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Callable, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.ticket import Ticket, TicketPriority, TicketStatus
    from app.models.user import User, UserRole


def pytest_configure() -> None:
    """Configure isolated application settings before test modules are imported."""
    test_database_url = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite://")
    _validate_test_database_url(test_database_url, os.getenv("DATABASE_URL"))
    os.environ["DATABASE_URL"] = test_database_url
    os.environ["APP_DEBUG"] = "false"
    os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-thirty-two-bytes"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"


def _validate_test_database_url(
    test_database_url: str,
    application_database_url: str | None,
) -> None:
    """Prevent destructive fixtures from targeting a non-test database."""
    test_url = make_url(test_database_url)
    if test_url.drivername.startswith("sqlite"):
        return

    if not test_url.database or not test_url.database.endswith("_test"):
        raise pytest.UsageError(
            "Non-SQLite TEST_DATABASE_URL database name must end with '_test'"
        )

    if application_database_url and test_url == make_url(application_database_url):
        raise pytest.UsageError("TEST_DATABASE_URL must differ from DATABASE_URL")


@dataclass(frozen=True)
class AuthenticatedClient:
    """HTTP client and credentials for a test user."""

    client: AsyncClient
    user: User
    access_token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    """Create a fresh isolated schema for every test."""
    import app.models  # noqa: F401
    from app.core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client bound to the FastAPI application."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def user_factory() -> Callable[[str, UserRole], User]:
    """Create a persisted user with a requested role."""
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models.user import User, UserRole

    def create_user(email: str, role: UserRole = UserRole.USER) -> User:
        with SessionLocal() as session:
            user = User(
                email=email,
                full_name=email.split("@")[0],
                hashed_password=hash_password("secure-password"),
                role=role,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            session.expunge(user)
            return user

    return create_user


@pytest.fixture
def user(user_factory: Callable[[str, UserRole], User]) -> User:
    from app.models.user import UserRole

    return user_factory("user@example.com", UserRole.USER)


@pytest.fixture
def support_user(user_factory: Callable[[str, UserRole], User]) -> User:
    from app.models.user import UserRole

    return user_factory("support@example.com", UserRole.SUPPORT)


@pytest.fixture
def admin_user(user_factory: Callable[[str, UserRole], User]) -> User:
    from app.models.user import UserRole

    return user_factory("admin@example.com", UserRole.ADMIN)


@pytest.fixture
def ticket_factory() -> Callable[..., Ticket]:
    """Create tickets directly when tests need setup data."""
    from app.core.database import SessionLocal
    from app.models.ticket import Ticket, TicketPriority, TicketStatus

    def create_ticket(
        author: User,
        *,
        title: str = "Test ticket",
        description: str = "Test ticket description",
        status: TicketStatus = TicketStatus.OPEN,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assigned_to: User | None = None,
    ) -> Ticket:
        with SessionLocal() as session:
            ticket = Ticket(
                title=title,
                description=description,
                status=status,
                priority=priority,
                author_id=author.id,
                assigned_to_id=assigned_to.id if assigned_to else None,
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            session.expunge(ticket)
            return ticket

    return create_ticket


@pytest.fixture
def comment_factory() -> Callable[[Ticket, User, str], Comment]:
    """Create comments directly when tests need setup data."""
    from app.core.database import SessionLocal
    from app.models.comment import Comment

    def create_comment(
        ticket: Ticket, author: User, text: str = "Test comment"
    ) -> Comment:
        with SessionLocal() as session:
            comment = Comment(ticket_id=ticket.id, author_id=author.id, text=text)
            session.add(comment)
            session.commit()
            session.refresh(comment)
            session.expunge(comment)
            return comment

    return create_comment


@pytest.fixture
async def user_client(api_client: AsyncClient, user: User) -> AuthenticatedClient:
    from app.core.security import create_access_token

    return AuthenticatedClient(api_client, user, create_access_token(user.email))


@pytest.fixture
async def support_client(
    api_client: AsyncClient,
    support_user: User,
) -> AuthenticatedClient:
    from app.core.security import create_access_token

    return AuthenticatedClient(
        api_client,
        support_user,
        create_access_token(support_user.email),
    )


@pytest.fixture
async def admin_client(
    api_client: AsyncClient, admin_user: User
) -> AuthenticatedClient:
    from app.core.security import create_access_token

    return AuthenticatedClient(
        api_client, admin_user, create_access_token(admin_user.email)
    )
