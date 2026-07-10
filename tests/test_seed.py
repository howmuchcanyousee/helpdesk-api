from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.user import User
from app.scripts.seed import seed_demo_data


def test_seed_creates_demo_data_once() -> None:
    passwords = {
        "admin@example.com": "admin-password",
        "support@example.com": "support-password",
        "user@example.com": "user-password",
    }

    with SessionLocal() as session:
        first_result = seed_demo_data(session, passwords)
        session.commit()

        assert first_result.users_created == 3
        assert first_result.tickets_created == 2
        assert first_result.comments_created == 2
        assert session.scalar(select(func.count()).select_from(User)) == 3
        assert session.scalar(select(func.count()).select_from(Ticket)) == 2
        assert session.scalar(select(func.count()).select_from(Comment)) == 2

        second_result = seed_demo_data(session, passwords)
        session.commit()

        assert second_result.users_created == 0
        assert second_result.tickets_created == 0
        assert second_result.comments_created == 0
