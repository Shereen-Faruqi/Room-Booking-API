"""Request and response shapes."""
import re
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BookingCreate(BaseModel):
    room: str = Field(min_length=1, max_length=50)
    starts_at: datetime
    ends_at: datetime
    customer_email: str = Field(max_length=254)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def to_utc(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone, for example 2026-11-02T09:00:00Z")
        return value.astimezone(timezone.utc).replace(microsecond=0)

    @field_validator("customer_email")
    @classmethod
    def looks_like_email(cls, value: str) -> str:
        if not EMAIL_PATTERN.match(value):
            raise ValueError("customer_email must look like an email address")
        return value

    @model_validator(mode="after")
    def ends_after_start(self) -> "BookingCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class BookingOut(BaseModel):
    id: int
    room: str
    starts_at: str
    ends_at: str
    customer_email: str
    owner: str
