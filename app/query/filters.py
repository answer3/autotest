from datetime import datetime
from typing import Literal

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import PlanProposalStatus, TestRunStatus


class QueryParamError(ValueError):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message)


class SortOrderMixin(BaseModel):
    sort_order: Literal["asc", "desc"] = "desc"


class NullsMixin(BaseModel):
    nulls: Literal["first", "last"] = "last"


class CreatedRangeMixin(BaseModel):
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None


class CreatedUpdatedRangeMixin(CreatedRangeMixin):
    updated_at_from: datetime | None = None
    updated_at_to: datetime | None = None


class CreatedStartedFinishedMixin(CreatedRangeMixin):
    started_at_from: datetime | None = None
    started_at_to: datetime | None = None

    finished_at_from: datetime | None = None
    finished_at_to: datetime | None = None

    sort_by: Literal["created_at", "started_at", "finished_at"] = "created_at"

    @model_validator(mode="after")
    def validate_ranges(self) -> "CreatedStartedFinishedMixin":
        def _check(a: datetime | None, b: datetime | None, name: str) -> None:
            if a and b and a > b:
                raise QueryParamError(
                    field=f"{name}_from", message=f"{name}_from must be <= {name}_to"
                )

        _check(self.created_at_from, self.created_at_to, "created_at")
        _check(self.started_at_from, self.started_at_to, "started_at")
        _check(self.finished_at_from, self.finished_at_to, "finished_at")
        return self


class TestCaseListQuery(SortOrderMixin, CreatedUpdatedRangeMixin):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=200)

    sort_by: Literal["created_at", "updated_at"] = "created_at"

    @model_validator(mode="after")
    def validate_ranges(self) -> "TestCaseListQuery":
        if (
            self.created_at_from
            and self.created_at_to
            and self.created_at_from > self.created_at_to
        ):
            raise QueryParamError(
                field="created_at_from", message="created_at_from must be <= created_at_to"
            )
        if (
            self.updated_at_from
            and self.updated_at_to
            and self.updated_at_from > self.updated_at_to
        ):
            raise QueryParamError(
                field="updated_at_from", message="updated_at_from must be <= updated_at_to"
            )
        return self


def get_test_case_list_query(
    title: str | None = Query(default=None, max_length=200),
    description: str | None = Query(default=None, max_length=200),
    created_at_from: datetime | None = Query(default=None),
    created_at_to: datetime | None = Query(default=None),
    updated_at_from: datetime | None = Query(default=None),
    updated_at_to: datetime | None = Query(default=None),
    sort_by: Literal["created_at", "updated_at"] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
) -> TestCaseListQuery:
    return TestCaseListQuery(
        title=title,
        description=description,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        updated_at_from=updated_at_from,
        updated_at_to=updated_at_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


class TestCaseRevisionListQuery(SortOrderMixin, CreatedRangeMixin):
    model_config = ConfigDict(extra="forbid")

    nl_text: str | None = Field(default=None, max_length=10_000)
    comment: str | None = Field(default=None, max_length=10_000)

    sort_by: Literal["created_at"] = "created_at"

    @model_validator(mode="after")
    def validate_ranges(self) -> "TestCaseRevisionListQuery":
        if (
            self.created_at_from
            and self.created_at_to
            and self.created_at_from > self.created_at_to
        ):
            raise QueryParamError(
                field="created_at_from", message="created_at_from must be <= created_at_to"
            )
        return self


def get_revision_list_query(
    nl_text: str | None = Query(default=None),
    comment: str | None = Query(default=None),
    created_at_from: datetime | None = Query(default=None),
    created_at_to: datetime | None = Query(default=None),
    sort_by: Literal["created_at"] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
) -> TestCaseRevisionListQuery:
    return TestCaseRevisionListQuery(
        nl_text=nl_text,
        comment=comment,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


class PlanProposalListQuery(SortOrderMixin, NullsMixin, CreatedStartedFinishedMixin):
    model_config = ConfigDict(extra="forbid")

    statuses: list[PlanProposalStatus] = Field(default_factory=list)

    is_ready_for_test: bool | None = None
    error: bool | None = None  # True => error IS NOT NULL, False => error IS NULL

    @model_validator(mode="after")
    def validate_ranges(self) -> "PlanProposalListQuery":
        def _check(a: datetime | None, b: datetime | None, name: str) -> None:
            if a and b and a > b:
                raise QueryParamError(
                    field=f"{name}_from", message=f"{name}_from must be <= {name}_to"
                )

        _check(self.created_at_from, self.created_at_to, "created_at")
        _check(self.started_at_from, self.started_at_to, "started_at")
        _check(self.finished_at_from, self.finished_at_to, "finished_at")
        return self


def get_plan_proposal_list_query(
    status: list[PlanProposalStatus] = Query(default=[]),
    is_ready_for_test: bool | None = Query(default=None),
    error: bool | None = Query(default=None),
    created_at_from: datetime | None = Query(default=None),
    created_at_to: datetime | None = Query(default=None),
    started_at_from: datetime | None = Query(default=None),
    started_at_to: datetime | None = Query(default=None),
    finished_at_from: datetime | None = Query(default=None),
    finished_at_to: datetime | None = Query(default=None),
    sort_by: Literal["created_at", "started_at", "finished_at"] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    nulls: Literal["first", "last"] = Query(default="last"),
) -> PlanProposalListQuery:
    return PlanProposalListQuery(
        statuses=status,
        is_ready_for_test=is_ready_for_test,
        error=error,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        started_at_from=started_at_from,
        started_at_to=started_at_to,
        finished_at_from=finished_at_from,
        finished_at_to=finished_at_to,
        sort_by=sort_by,
        sort_order=sort_order,
        nulls=nulls,
    )


class TestRunListQuery(SortOrderMixin, NullsMixin, CreatedStartedFinishedMixin):
    model_config = ConfigDict(extra="forbid")

    statuses: list[TestRunStatus] = Field(default_factory=list)
    site_domain: str | None = Field(default=None, max_length=255)

    error: bool | None = None  # True => error IS NOT NULL, False => error IS NULL


def get_test_run_list_query(
    status: list[TestRunStatus] = Query(default=[]),
    site_domain: str | None = Query(default=None),
    error: bool | None = Query(default=None),
    created_at_from: datetime | None = Query(default=None),
    created_at_to: datetime | None = Query(default=None),
    started_at_from: datetime | None = Query(default=None),
    started_at_to: datetime | None = Query(default=None),
    finished_at_from: datetime | None = Query(default=None),
    finished_at_to: datetime | None = Query(default=None),
    sort_by: Literal["created_at", "started_at", "finished_at"] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    nulls: Literal["first", "last"] = Query(default="last"),
) -> TestRunListQuery:
    return TestRunListQuery(
        statuses=status,
        site_domain=site_domain,
        error=error,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        started_at_from=started_at_from,
        started_at_to=started_at_to,
        finished_at_from=finished_at_from,
        finished_at_to=finished_at_to,
        sort_by=sort_by,
        sort_order=sort_order,
        nulls=nulls,
    )
