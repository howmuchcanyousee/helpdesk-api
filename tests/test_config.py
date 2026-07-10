import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_rejects_short_secret_key() -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            database_url="sqlite+pysqlite://",
            secret_key="too-short",
        )
