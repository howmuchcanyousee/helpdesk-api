import os
from collections.abc import Generator

import pytest

# The health endpoint does not require a real database connection, but settings
# require a database URL when the application is imported.
os.environ["DATABASE_URL"] = "sqlite+pysqlite://"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-thirty-two-bytes"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    """Create an empty database for every test."""
    from app.core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
