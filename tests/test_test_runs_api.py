from datetime import datetime

import pytest

from app.models.enums import TestRunStatus
from tests.conftest import make_test_case_revision_proposal, make_test_run
from tests.data.data_proposals import (
    PROPOSAL_DATA_CREATE_1,
    PROPOSAL_DATA_SUCCESS_1,
    PROPOSAL_DATA_SUCCESS_READY_1,
)
from tests.data.data_test_case import TEST_CASE_REQUEST_1
from tests.data.data_test_run import TEST_RUN_DATA_CREATE_1, TEST_RUN_REQUEST_1


@pytest.mark.parametrize("domain, response_code", [
    ("example.com", 422),
    ("example", 422),
    ("ftp://example.com", 422),
    ("http://exapmple.com/", 422),
    ("http://exapmple.com", 404)
])
def test_create_test_run_site_domain_error(client, domain, response_code):
    r = client.post("/plan-proposals/999999/test-runs", json={
        "run_params": {},
        "placeholders": {},
        "site_domain": domain,
    })
    assert r.status_code == response_code
    if response_code == 422:
        data = r.json()
        assert "site_domain" in data["detail"][0]['loc']
        assert data["detail"] is not None


def test_create_test_run_404_if_plan_proposal_not_found(client):
    r = client.post("/plan-proposals/999999/test-runs", json={
        "run_params": {},
        "placeholders": {},
        "site_domain": "http://example.com",
    })
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


def test_create_test_run_400_if_plan_proposal_not_succeeded(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_CREATE_1)

    r = client.post(f"/plan-proposals/{proposal.id}/test-runs", json={
        "run_params": {},
        "placeholders": {},
        "site_domain": "http://example.com",
    })
    assert r.status_code == 400
    assert "incorrect status" in r.json()["detail"]


def test_create_test_run_400_if_plan_proposal_not_ready(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_1)

    r = client.post(f"/plan-proposals/{proposal.id}/test-runs", json={
        "run_params": {},
        "placeholders": {},
        "site_domain": "http://example.com",
    })
    assert r.status_code == 400
    assert "is not marked as ready" in r.json()["detail"]


def test_create_test_run_202_creates_and_publishes(client, db_session, publisher):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    r = client.post(f"/plan-proposals/{proposal.id}/test-runs", json=TEST_RUN_REQUEST_1)
    assert r.status_code == 202, r.text
    data = r.json()
    assert "id" in data
    assert data["plan_proposal_id"] == proposal.id
    assert data["result_payload"] is None
    assert data["run_params"] == TEST_RUN_REQUEST_1["run_params"]
    assert data["created_at"] is not None
    assert data["started_at"] is None
    assert data["finished_at"] is None
    assert data["error"] is None

    assert publisher.test_run_calls == [{"run_id": data["id"], "placeholders": TEST_RUN_REQUEST_1["placeholders"]}]


def test_get_test_run_404(client):
    r = client.get("/test-runs/999999")
    assert r.status_code == 404
    assert "test_run not found" in r.json().get("detail", "")


def test_get_test_run_ok(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    tr = make_test_run(db_session, plan_proposal_id=proposal.id, **TEST_RUN_DATA_CREATE_1)

    r = client.get(f"/test-runs/{tr.id}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == tr.id
    assert data["plan_proposal_id"] == proposal.id


def test_list_test_runs_ok_empty(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    r = client.get(f"/plan-proposals/{proposal.id}/test-runs")
    assert r.status_code == 200
    assert r.json() == []


def test_list_test_runs_ok_with_pagination(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    t1 = make_test_run(db_session, plan_proposal_id=proposal.id, **TEST_RUN_DATA_CREATE_1)
    t2 = make_test_run(db_session, plan_proposal_id=proposal.id, **TEST_RUN_DATA_CREATE_1)
    t3 = make_test_run(db_session, plan_proposal_id=proposal.id, **TEST_RUN_DATA_CREATE_1)

    r = client.get(f"/plan-proposals/{proposal.id}/test-runs?limit=2&page=1")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["id"] == t3.id
    assert data[1]["id"] == t2.id

    r2 = client.get(f"/plan-proposals/{proposal.id}/test-runs?limit=2&page=2")
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2) == 1
    assert data2[0]["id"] == t1.id


######
# FILTERS TEST
######

def test_test_runs_filter_status_list(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                  created_at=datetime(2026, 1, 1, 10, 0))
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.failed,
                  created_at=datetime(2026, 1, 2, 10, 0))
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                  created_at=datetime(2026, 1, 3, 10, 0))

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params=[("status", "passed"), ("status", "failed")],
    )
    assert r.status_code == 200
    data = r.json()

    assert {item["status"] for item in data} <= {"passed", "failed"}
    assert "running" not in {item["status"] for item in data}


def test_test_runs_filter_error_true(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.failed,
                  created_at=datetime(2026, 1, 1, 10, 0), error="boom")
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.failed,
                  created_at=datetime(2026, 1, 2, 10, 0), error=None)

    r = client.get(f"/plan-proposals/{proposal.id}/test-runs", params={"error": "true"})
    assert r.status_code == 200
    data = r.json()

    assert len(data) == 1
    assert data[0]["error"] == "boom"


def test_test_runs_filter_error_false(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.failed,
                  created_at=datetime(2026, 1, 1, 10, 0), error="boom")
    a = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.failed,
                      created_at=datetime(2026, 1, 2, 10, 0), error=None)

    r = client.get(f"/plan-proposals/{proposal.id}/test-runs", params={"error": "false"})
    assert r.status_code == 200
    data = r.json()

    ids = [item["id"] for item in data]
    assert set(ids) == {a.id}


def test_test_runs_filter_site_domain_contains(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    a = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                      created_at=datetime(2026, 1, 1, 10, 0), site_domain="example.com")
    b = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                      created_at=datetime(2026, 1, 2, 10, 0), site_domain="sub.EXAMPLE.com")
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                  created_at=datetime(2026, 1, 3, 10, 0), site_domain="other.com")

    r = client.get(f"/plan-proposals/{proposal.id}/test-runs", params={"site_domain": "  example  "})
    assert r.status_code == 200
    data = r.json()

    ids = {item["id"] for item in data}
    assert ids == {a.id, b.id}


def test_test_runs_filter_created_at_range(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                  created_at=datetime(2026, 1, 1, 10, 0))
    mid = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                        created_at=datetime(2026, 1, 2, 10, 0))
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                  created_at=datetime(2026, 1, 3, 10, 0))

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params={
            "created_at_from": "2026-01-02T00:00:00",
            "created_at_to": "2026-01-02T23:59:59",
        },
    )
    assert r.status_code == 200
    data = r.json()

    assert [item["id"] for item in data] == [mid.id]


def test_test_runs_filter_started_at_range(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                  created_at=datetime(2026, 1, 1, 10, 0), started_at=datetime(2026, 1, 10, 10, 0))
    mid = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                        created_at=datetime(2026, 1, 2, 10, 0), started_at=datetime(2026, 1, 20, 10, 0))
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                  created_at=datetime(2026, 1, 3, 10, 0), started_at=datetime(2026, 1, 30, 10, 0))

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params={"started_at_from": "2026-01-15T00:00:00", "started_at_to": "2026-01-25T23:59:59"},
    )
    assert r.status_code == 200
    data = r.json()
    assert [item["id"] for item in data] == [mid.id]


def test_test_runs_filter_finished_at_range(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                  created_at=datetime(2026, 1, 1, 10, 0), finished_at=datetime(2026, 2, 1, 12, 0))
    mid = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                        created_at=datetime(2026, 1, 2, 10, 0), finished_at=datetime(2026, 2, 5, 12, 0))
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                  created_at=datetime(2026, 1, 3, 10, 0), finished_at=datetime(2026, 2, 10, 12, 0))

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params={"finished_at_from": "2026-02-05T00:00:00", "finished_at_to": "2026-02-05T23:59:59"},
    )
    assert r.status_code == 200
    data = r.json()
    assert [item["id"] for item in data] == [mid.id]


def test_test_runs_sort_created_at_asc(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    a = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                      created_at=datetime(2026, 1, 1, 10, 0))
    b = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                      created_at=datetime(2026, 1, 2, 10, 0))
    c = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                      created_at=datetime(2026, 1, 3, 10, 0))

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params={"sort_by": "created_at", "sort_order": "asc"},
    )
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()]
    assert ids[:3] == [a.id, b.id, c.id]


def test_test_runs_sort_created_at_desc(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    a = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                      created_at=datetime(2026, 1, 1, 10, 0))
    b = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                      created_at=datetime(2026, 1, 2, 10, 0))
    c = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                      created_at=datetime(2026, 1, 3, 10, 0))

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params={"sort_by": "created_at", "sort_order": "desc"},
    )
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()]
    assert ids[:3] == [c.id, b.id, a.id]


def test_test_runs_sort_started_at_nulls_first(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    n1 = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.queued,
                       created_at=datetime(2026, 1, 1, 10, 0), started_at=None)
    d1 = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                       created_at=datetime(2026, 1, 2, 10, 0), started_at=datetime(2026, 1, 10, 10, 0))
    n2 = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.queued,
                       created_at=datetime(2026, 1, 3, 10, 0), started_at=None)
    d2 = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                       created_at=datetime(2026, 1, 4, 10, 0), started_at=datetime(2026, 1, 11, 10, 0))

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params={"sort_by": "started_at", "sort_order": "asc", "nulls": "first"},
    )
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()]

    assert set(ids[:2]) == {n1.id, n2.id}
    assert ids.index(d1.id) < ids.index(d2.id)


def test_test_runs_sort_finished_at_nulls_last(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    d1 = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                       created_at=datetime(2026, 1, 1, 10, 0), finished_at=datetime(2026, 2, 1, 10, 0))
    n1 = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                       created_at=datetime(2026, 1, 2, 10, 0), finished_at=None)
    d2 = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                       created_at=datetime(2026, 1, 3, 10, 0), finished_at=datetime(2026, 2, 2, 10, 0))
    n2 = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.running,
                       created_at=datetime(2026, 1, 4, 10, 0), finished_at=None)

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params={"sort_by": "finished_at", "sort_order": "asc", "nulls": "last"},
    )
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()]

    assert ids.index(d1.id) < ids.index(d2.id)
    assert set(ids[-2:]) == {n1.id, n2.id}


def test_test_runs_filter_and_sort_combined(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)

    a = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.failed,
                      created_at=datetime(2026, 1, 1, 10, 0), site_domain="example.com", error="x",
                      finished_at=datetime(2026, 2, 2, 10, 0))
    b = make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.failed,
                      created_at=datetime(2026, 1, 2, 10, 0), site_domain="sub.example.com", error="y",
                      finished_at=datetime(2026, 2, 1, 10, 0))
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.failed,
                  created_at=datetime(2026, 1, 3, 10, 0), site_domain="example.com", error=None)
    make_test_run(db_session, plan_proposal_id=proposal.id, status=TestRunStatus.passed,
                  created_at=datetime(2026, 1, 4, 10, 0), site_domain="example.com", error="boom")

    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params=[
            ("status", "failed"),
            ("error", "true"),
            ("site_domain", "example"),
            ("sort_by", "finished_at"),
            ("sort_order", "asc"),
        ],
    )
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()]

    assert ids[:2] == [b.id, a.id]


def test_test_runs_invalid_range_returns_422(db_session, client):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    r = client.get(
        f"/plan-proposals/{proposal.id}/test-runs",
        params={"created_at_from": "2026-02-01T00:00:00", "created_at_to": "2026-01-01T00:00:00"},
    )
    assert r.status_code == 422
