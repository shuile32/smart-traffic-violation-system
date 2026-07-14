from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class AnnouncementCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("title", "content", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class AnnouncementUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1, max_length=5000)

    @field_validator("title", "content", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_update(self) -> "AnnouncementUpdateIn":
        if self.title is None and self.content is None:
            raise ValueError("至少提供标题或正文中的一个字段")
        return self


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class AnnouncementListResponse(BaseModel):
    items: list[AnnouncementOut]
    total: int
    page: int
    page_size: int
