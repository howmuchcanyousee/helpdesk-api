import pytest
from pydantic import ValidationError

from app.core.config import Settings
from tests.conftest import _validate_test_database_url


def test_settings_rejects_short_secret_key() -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            database_url="sqlite+pysqlite://",
            secret_key="too-short",
        )


def test_settings_rejects_placeholder_secret_key() -> None:
    with pytest.raises(ValidationError, match="must be replaced"):
        Settings(
            database_url="sqlite+pysqlite://",
            secret_key="replace_with_a_long_random_value",
        )


def test_settings_hide_invalid_input_values() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(
            APP_DEBUG="not-a-boolean",
            database_url="postgresql://user:private-password@localhost/database",
            secret_key="test-secret-key-with-at-least-thirty-two-bytes",
        )

    assert "not-a-boolean" not in str(error.value)
    assert "private-password" not in str(error.value)


def test_external_test_database_requires_test_suffix() -> None:
    with pytest.raises(pytest.UsageError, match="must end with '_test'"):
        _validate_test_database_url(
            "postgresql+psycopg://user:password@localhost/helpdesk",
            None,
        )
