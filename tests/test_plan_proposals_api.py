from datetime import datetime

from app.models.enums import PlanProposalStatus
from tests.conftest import (
    make_plan_proposal,
    make_test_case_and_revision,
    make_test_case_revision_proposal,
)
from tests.data.data_proposals import (
    PROPOSAL_DATA_CREATE_1,
    PROPOSAL_DATA_FAILED_1,
    PROPOSAL_DATA_SUCCESS_1,
)
from tests.data.data_test_case import TEST_CASE_REQUEST_1


def test_get_plan_proposal_404(client):
    r = client.get("/plan-proposals/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "plan_proposal not found"


def test_get_plan_proposal_ok(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_CREATE_1)

    r = client.get(f"/plan-proposals/{proposal.id}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == proposal.id
    assert data["test_case_revision_id"] == tc.revisions[0].id
    assert data["status"] == PlanProposalStatus.pending
    assert data["created_at"] is not None
    assert data["started_at"] is None
    assert data["finished_at"] is None
    assert data["result_payload"] is None
    assert data["error"] is None
    assert data["is_ready_for_test"] is False
    assert data["ready_for_test_at"] is None


def test_list_plan_proposals_404_if_revision_not_found(client):
    r = client.get("/test-case-revisions/999999/plan-proposals")
    assert r.status_code == 404
    assert r.json()["detail"] == "test_case_revision not found"


def test_list_plan_proposals_ok_empty(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    r = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals")
    assert r.status_code == 200
    assert r.json() == []


def test_list_plan_proposals_ok_with_pagination(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    p1 = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_CREATE_1)
    p2 = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_CREATE_1)
    p3 = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_CREATE_1)

    r = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals?limit=2&page=1")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["id"] == p3.id
    assert data[1]["id"] == p2.id

    r2 = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals?limit=2&page=2")
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2) == 1
    assert data2[0]["id"] == p1.id


def test_create_plan_proposal_404_if_revision_not_found(client):
    r = client.post("/test-case-revisions/999999/plan-proposals")
    assert r.status_code == 404
    assert r.json()["detail"] == "test_case_revision not found"


def test_create_plan_proposal_202_creates_and_publishes(client, db_session, publisher):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    r = client.post(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals")
    assert r.status_code == 202, r.text
    data = r.json()
    assert "id" in data
    assert data["test_case_revision_id"] == tc.revisions[0].id
    assert data["status"] == PlanProposalStatus.pending
    assert data["created_at"] is not None
    assert data["started_at"] is None
    assert data["finished_at"] is None
    assert data["result_payload"] is None
    assert publisher.proposal_calls == [{"proposal_id": data["id"]}]


def test_mark_ready_404_if_proposal_not_found(client):
    r = client.patch("/plan-proposals/999999/ready")
    assert r.status_code == 404
    assert r.json()["detail"] == "plan_proposal not found"


def test_mark_ready_400_if_not_succeeded(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_CREATE_1)

    r = client.patch(f"/plan-proposals/{proposal.id}/ready")
    assert r.status_code == 400
    assert r.json()["detail"] == "plan_proposal is not succeeded"


def test_mark_ready_ok(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_1)

    r = client.patch(f"/plan-proposals/{proposal.id}/ready")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == proposal.id
    assert data["is_ready_for_test"] is True
    assert data["ready_for_test_at"] is not None


######
# FILTERS TEST
######


def test_plan_proposals_filter_status_list(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    a = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1)
    b = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_FAILED_1)
    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_CREATE_1)

    r = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals",
                   params=[("status", "succeeded"), ("status", "failed")])
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert ids == {a.id, b.id}


def test_plan_proposals_filter_is_ready_for_test(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    a = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           is_ready_for_test=True)
    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1, is_ready_for_test=False)

    r = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals", params={"is_ready_for_test": 1})
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert ids == [a.id]


def test_plan_proposals_filter_error_true(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    a = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1, error="AAAAA")
    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1, error=None)

    r = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals", params={"error": 1})
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert ids == {a.id}


def test_plan_proposals_filter_created_at_range(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                       created_at=datetime(2026, 1, 1, 10, 0))
    b = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           created_at=datetime(2026, 1, 2, 10, 0))
    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                       created_at=datetime(2026, 1, 3, 10, 0))

    r = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals",
                   params={"created_at_from": "2026-01-02T00:00:00", "created_at_to": "2026-01-02T23:59:59"},
                   )
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert ids == [b.id]


def test_plan_proposals_filter_started_at_range(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                       started_at=datetime(2026, 1, 10, 10, 0))
    b = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           started_at=datetime(2026, 1, 20, 10, 0))
    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                       started_at=datetime(2026, 1, 30, 10, 0))

    r = client.get(
        f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals",
        params={"started_at_from": "2026-01-15T00:00:00", "started_at_to": "2026-01-25T23:59:59"},
    )
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert ids == [b.id]


def test_plan_proposals_filter_finished_at_range(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                       finished_at=datetime(2026, 1, 1, 10, 0))
    b = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           finished_at=datetime(2026, 2, 3, 10, 0))
    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                       finished_at=datetime(2026, 1, 12, 10, 0))

    r = client.get(
        f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals",
        params={"finished_at_from": "2026-02-02T00:00:00", "finished_at_to": "2026-02-05T23:59:59"},
    )
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert ids == [b.id]


def test_plan_proposals_sort_created_at_asc(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    a = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           created_at=datetime(2026, 1, 1, 10, 0))
    b = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           created_at=datetime(2026, 1, 2, 10, 0))
    c = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           created_at=datetime(2026, 1, 3, 3, 0))

    r = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals",
                   params={"sort_by": "created_at", "sort_order": "asc"})
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert ids[:3] == [a.id, b.id, c.id]


def test_plan_proposals_sort_created_at_desc(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    a = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           created_at=datetime(2026, 1, 1, 10, 0))
    b = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           created_at=datetime(2026, 1, 2, 10, 0))
    c = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_SUCCESS_1,
                           created_at=datetime(2026, 1, 3, 3, 0))

    r = client.get(f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals",
                   params={"sort_by": "created_at", "sort_order": "desc"})
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert ids[:3] == [c.id, b.id, a.id]


def test_plan_proposals_filter_and_sort_combined(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    a = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_FAILED_1, error="x", created_at=datetime(2026,1,1,10,0), finished_at=datetime(2026,2,2,10,0))
    b = make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_FAILED_1, created_at=datetime(2026,1,2,10,0), error="y", finished_at=datetime(2026,2,1,10,0))
    make_plan_proposal(db_session, revision_id=tc.revisions[0].id, **PROPOSAL_DATA_FAILED_1, created_at=datetime(2026,1,3,10,0), error=None, finished_at=datetime(2026,2,3,10,0))

    r = client.get(
        f"/test-case-revisions/{tc.revisions[0].id}/plan-proposals",
        params=[("status", "failed"), ("error", "true"), ("sort_by", "finished_at"), ("sort_order", "asc")],
    )
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert ids[:2] == [b.id, a.id]
