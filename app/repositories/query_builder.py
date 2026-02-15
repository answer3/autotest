from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import ColumnElement, Select


def apply_pagination(stmt: Select[Any], *, page: int, limit: int) -> Select[Any]:
    return stmt.limit(limit).offset((page - 1) * limit)


def apply_range(
    stmt: Select[Any],
    *,
    col: ColumnElement[Any] | InstrumentedAttribute[Any],
    from_: datetime | None = None,
    to: datetime | None = None,
) -> Select[Any]:
    if from_ is not None:
        stmt = stmt.where(col >= from_)
    if to is not None:
        stmt = stmt.where(col <= to)
    return stmt


def apply_ilike_contains(
    stmt: Select[Any], *, col: ColumnElement[Any] | InstrumentedAttribute[Any], value: str | None
) -> Select[Any]:
    if value is None:
        return stmt
    v = value.strip()
    if not v:
        return stmt
    return stmt.where(col.ilike(f"%{v}%"))


def apply_sort(
    stmt: Select[Any],
    *,
    sort_map: Mapping[str, ColumnElement[Any] | InstrumentedAttribute[Any]],
    sort_by: str,
    sort_order: str,
    tie_breaker: ColumnElement[Any] | None = None,
    nulls: str | None = None,
    nulls_allowed_fields: set[str] | None = None,
) -> Select[Any]:
    sort_col = sort_map[sort_by]
    order_expr = sort_col.asc() if sort_order == "asc" else sort_col.desc()

    if nulls and nulls_allowed_fields and sort_by in nulls_allowed_fields:
        order_expr = order_expr.nulls_first() if nulls == "first" else order_expr.nulls_last()

    if tie_breaker is not None:
        return stmt.order_by(order_expr, tie_breaker)
    return stmt.order_by(order_expr)


def apply_run_timestamps_filters(
    stmt: Select[Any],
    *,
    created_at: ColumnElement[Any] | InstrumentedAttribute[Any],
    started_at: ColumnElement[Any] | InstrumentedAttribute[Any],
    finished_at: ColumnElement[Any] | InstrumentedAttribute[Any],
    q: Any,
) -> Select[Any]:
    stmt = apply_range(stmt, col=created_at, from_=q.created_at_from, to=q.created_at_to)
    stmt = apply_range(stmt, col=started_at, from_=q.started_at_from, to=q.started_at_to)
    stmt = apply_range(stmt, col=finished_at, from_=q.finished_at_from, to=q.finished_at_to)
    return stmt
