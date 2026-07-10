"""Create idempotent demo data for local development."""

import os
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.comment import Comment
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole


@dataclass(frozen=True)
class DemoUser:
    """Description of a user created by the seed command."""

    email: str
    full_name: str
    role: UserRole
    password_environment_variable: str


@dataclass
class SeedResult:
    """Count of records created during one seed run."""

    users_created: int = 0
    tickets_created: int = 0
    comments_created: int = 0


DEMO_USERS = (
    DemoUser(
        email="admin@example.com",
        full_name="Demo Administrator",
        role=UserRole.ADMIN,
        password_environment_variable="SEED_ADMIN_PASSWORD",
    ),
    DemoUser(
        email="support@example.com",
        full_name="Demo Support",
        role=UserRole.SUPPORT,
        password_environment_variable="SEED_SUPPORT_PASSWORD",
    ),
    DemoUser(
        email="user@example.com",
        full_name="Demo User",
        role=UserRole.USER,
        password_environment_variable="SEED_USER_PASSWORD",
    ),
)


def get_seed_passwords() -> dict[str, str]:
    """Read required demo passwords without putting them in application code."""
    passwords = {
        user.email: os.getenv(user.password_environment_variable, "")
        for user in DEMO_USERS
    }
    missing_variables = [
        user.password_environment_variable
        for user in DEMO_USERS
        if not passwords[user.email]
    ]
    if missing_variables:
        variables = ", ".join(missing_variables)
        raise RuntimeError(
            f"Set seed password variables before running the command: {variables}"
        )
    return passwords


def get_or_create_user(
    session: Session,
    demo_user: DemoUser,
    password: str,
) -> tuple[User, bool]:
    """Create a demo account when an account with its email does not exist."""
    user = session.scalar(select(User).where(User.email == demo_user.email))
    if user is not None:
        return user, False

    user = User(
        email=demo_user.email,
        full_name=demo_user.full_name,
        role=demo_user.role,
        hashed_password=hash_password(password),
    )
    session.add(user)
    session.flush()
    return user, True


def get_or_create_ticket(
    session: Session,
    *,
    title: str,
    description: str,
    status: TicketStatus,
    priority: TicketPriority,
    author: User,
    assigned_to: User | None,
) -> tuple[Ticket, bool]:
    """Create a demo ticket identified by its title and author."""
    ticket = session.scalar(
        select(Ticket).where(Ticket.title == title, Ticket.author_id == author.id)
    )
    if ticket is not None:
        return ticket, False

    ticket = Ticket(
        title=title,
        description=description,
        status=status,
        priority=priority,
        author_id=author.id,
        assigned_to_id=assigned_to.id if assigned_to else None,
    )
    session.add(ticket)
    session.flush()
    return ticket, True


def get_or_create_comment(
    session: Session,
    *,
    ticket: Ticket,
    author: User,
    text: str,
) -> bool:
    """Create a demo comment once for a ticket and author."""
    comment = session.scalar(
        select(Comment).where(
            Comment.ticket_id == ticket.id,
            Comment.author_id == author.id,
            Comment.text == text,
        )
    )
    if comment is not None:
        return False

    session.add(Comment(ticket_id=ticket.id, author_id=author.id, text=text))
    session.flush()
    return True


def seed_demo_data(session: Session, passwords: dict[str, str]) -> SeedResult:
    """Create demo users, tickets and comments without duplicating existing data."""
    result = SeedResult()
    users: dict[str, User] = {}
    for demo_user in DEMO_USERS:
        user, created = get_or_create_user(
            session,
            demo_user,
            passwords[demo_user.email],
        )
        users[demo_user.email] = user
        result.users_created += created

    first_ticket, created = get_or_create_ticket(
        session,
        title="Не удаётся войти в личный кабинет",
        description="После ввода пароля отображается сообщение об ошибке.",
        status=TicketStatus.IN_PROGRESS,
        priority=TicketPriority.HIGH,
        author=users["user@example.com"],
        assigned_to=users["support@example.com"],
    )
    result.tickets_created += created

    second_ticket, created = get_or_create_ticket(
        session,
        title="Как изменить данные профиля?",
        description="Нужна помощь с обновлением контактного телефона.",
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        author=users["user@example.com"],
        assigned_to=None,
    )
    result.tickets_created += created

    result.comments_created += get_or_create_comment(
        session,
        ticket=first_ticket,
        author=users["support@example.com"],
        text="Проверяю проблему. Вернусь с результатом в ближайшее время.",
    )
    result.comments_created += get_or_create_comment(
        session,
        ticket=second_ticket,
        author=users["user@example.com"],
        text="Телефон нужно заменить на новый рабочий номер.",
    )
    return result


def ensure_development_environment() -> None:
    """Prevent accidental demo data creation outside local development or tests."""
    allowed_environments = {"development", "test"}
    if settings.app_env.lower() not in allowed_environments:
        raise RuntimeError("Demo seed is allowed only for APP_ENV=development or test")


def main() -> None:
    """Run the local demo data seed command."""
    ensure_development_environment()
    passwords = get_seed_passwords()

    with SessionLocal() as session:
        try:
            result = seed_demo_data(session, passwords)
            session.commit()
        except Exception:
            session.rollback()
            raise

    print(
        "Demo data is ready: "
        f"{result.users_created} users, "
        f"{result.tickets_created} tickets, "
        f"{result.comments_created} comments created."
    )


if __name__ == "__main__":
    main()
