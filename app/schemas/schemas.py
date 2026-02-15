from datetime import datetime
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import TestRunStatus


class TestCaseRevisionCreate(BaseModel):
    nl_text: str = Field(min_length=1)
    comment: str | None = Field(default=None, max_length=500)
    created_by: str | None = Field(default=None, max_length=200)


class TestCaseRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_case_id: int
    nl_text: str
    comment: str | None
    created_by: str | None
    created_at: datetime


class TestCaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    nl_text: str = Field(min_length=1)
    comment: str | None = Field(default=None, max_length=500)
    created_by: str | None = Field(default=None, max_length=200)


class TestCaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class TestCaseResponseBase(BaseModel):
    id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class TestCaseItemResponse(TestCaseResponseBase):
    revisions_count: int
    last_revision: TestCaseRevisionResponse


class TestCaseListItemResponse(TestCaseResponseBase):
    revisions_count: int
    last_revision_created_at: datetime


class PlanProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_case_revision_id: int
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result_payload: dict[str, Any] | None = None
    error: str | None = None
    is_ready_for_test: bool
    ready_for_test_at: datetime | None = None


class RunParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    playwright_headless: bool = True
    playwright_timeout_ms: int = Field(default=30_000, ge=1_000, le=300_000)
    playwright_browser: Literal["chromium", "firefox", "webkit"] = "chromium"


class TestRunCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_params: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = Field(default=None, max_length=200)
    placeholders: dict[str, str] = Field(default_factory=dict)
    site_domain: str | None = Field(default=None, max_length=200)

    @field_validator("site_domain")
    def validate_site_domain(cls, v: str | None) -> str | None:
        if v is None:
            return v

        parsed = urlparse(v)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("site_domain must start with http:// or https://")
        if not parsed.netloc:
            raise ValueError("site_domain must be a valid URL with host")
        if parsed.path not in ("", "/"):
            raise ValueError("site_domain must not contain a path")
        if v.endswith("/"):
            raise ValueError("site_domain must not end with '/'")
        return v

    @model_validator(mode="after")
    def validate_and_fill_run_params(self) -> "TestRunCreateRequest":
        parsed = RunParams.model_validate(self.run_params)
        self.run_params = parsed.model_dump()
        return self


class TestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_proposal_id: int
    status: TestRunStatus

    run_params: dict[str, Any]
    result_payload: dict[str, Any] | None
    error: str | None

    screenshot_name: str | None
    video_name: str | None

    video_object_key: str | None
    screenshot_object_key: str | None

    created_by: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
