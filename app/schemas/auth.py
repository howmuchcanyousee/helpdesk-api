from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def validate_bcrypt_password(value: str) -> str:
    """Reject values that bcrypt cannot process without truncation."""
    if "\x00" in value:
        raise ValueError("Password must not contain NUL characters")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")
    return value


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_bcrypt_password(value)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
