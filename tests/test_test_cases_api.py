from datetime import datetime

from tests.conftest import make_revision, make_test_case, make_test_case_and_revision
from tests.data.data_test_case import (
    TEST_CASE_REQUEST_1,
    TEST_CASE_REQUEST_2,
    TEST_CASE_REQUEST_DESCR_PARAM_1,
    TEST_CASE_REQUEST_DESCR_PARAM_2,
    TEST_CASE_REQUEST_DESCR_PARAM_3,
    TEST_CASE_REQUEST_TITLE_PARAM_1,
    TEST_CASE_REQUEST_TITLE_PARAM_2,
    TEST_CASE_REQUEST_TITLE_PARAM_3,
    TEST_CASE_REVISION_COMMENT_1,
    TEST_CASE_REVISION_COMMENT_2,
    TEST_CASE_REVISION_COMMENT_3,
    TEST_CASE_REVISION_NL_TEXT_1,
    TEST_CASE_REVISION_NL_TEXT_2,
    TEST_CASE_REVISION_NL_TEXT_3,
    TEST_CASE_REVISION_REQUEST_1,
    TEST_CASE_REVISION_REQUEST_2,
    TEST_CASE_UPDATE_REQUEST_1,
)


def test_create_test_case_returns_item_shape(client):
    r = client.post("/test-cases", json=TEST_CASE_REQUEST_1)
    assert r.status_code == 201, r.text
    data = r.json()

    assert isinstance(data["id"], int)
    assert data["title"] == TEST_CASE_REQUEST_1["title"]
    assert data["description"] == TEST_CASE_REQUEST_1["description"]
    assert "created_at" in data
    assert data["created_at"] is not None
    assert "updated_at" in data
    assert data["updated_at"] is not None
    assert data["revisions_count"] == 1
    assert data["last_revision"] is not None
    assert isinstance(data["last_revision"]["id"], int)
    assert data["last_revision"]["test_case_id"] == data["id"]
    assert data["last_revision"]["nl_text"] == TEST_CASE_REQUEST_1["nl_text"]
    assert data["last_revision"]["comment"] == TEST_CASE_REQUEST_1["comment"]


def test_get_by_id_test_case(client, db_session):
    created = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    r = client.get(f"/test-cases/{created.id}")
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["id"] == created.id
    assert "revisions_count" in data
    assert "last_revision" in data
    assert data["revisions_count"] == 1
    assert data["last_revision"]["nl_text"] == TEST_CASE_REQUEST_1["nl_text"]


def test_update_test_case(client, db_session):
    created = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    r = client.patch(
        f"/test-cases/{created.id}",
        json=TEST_CASE_UPDATE_REQUEST_1,
    )
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["revisions_count"] == 1
    assert data["title"] == TEST_CASE_UPDATE_REQUEST_1["title"]
    assert data["description"] == TEST_CASE_UPDATE_REQUEST_1["description"]


def test_update_wrong_test_case(client, db_session):
    make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    r = client.patch(
        f"/test-cases/{1111}",
        json=TEST_CASE_UPDATE_REQUEST_1,
    )
    assert r.status_code == 404


def test_get_list_test_case(client, db_session):
    make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)
    make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_2)

    r = client.get("/test-cases")
    data = r.json()

    assert r.status_code == 200
    assert len(data) == 2
    assert data[0]["title"] == TEST_CASE_REQUEST_2["title"]
    assert data[1]["title"] == TEST_CASE_REQUEST_1["title"]


def test_create_revision_test_case(client, db_session):
    created = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)
    r = client.post(f"/test-cases/{created.id}/revisions", json=TEST_CASE_REVISION_REQUEST_1)
    assert r.status_code == 201, r.text
    data = r.json()

    assert "created_at" in data
    assert "id" in data
    assert data["test_case_id"] == created.id
    assert data["nl_text"] == TEST_CASE_REVISION_REQUEST_1["nl_text"]
    assert data["comment"] == TEST_CASE_REVISION_REQUEST_1["comment"]


def test_get_by_id_revision(client, db_session):
    created = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    r = client.get(f"/test-cases/{created.id}/revisions/{created.revisions[0].id}")
    assert r.status_code == 200, r.text
    data = r.json()

    assert "id" in data
    assert "created_at" in data
    assert data["nl_text"] == TEST_CASE_REQUEST_1["nl_text"]
    assert data["comment"] == TEST_CASE_REQUEST_1["comment"]
    assert data["created_by"] == TEST_CASE_REQUEST_1["created_by"]


def test_get_list_revision_test_case(client, db_session):
    created = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)
    make_revision(db_session, created.id, **TEST_CASE_REVISION_REQUEST_1)
    make_revision(db_session, created.id, **TEST_CASE_REVISION_REQUEST_2)

    r = client.get(f"/test-cases/{created.id}/revisions")
    data = r.json()

    assert r.status_code == 200
    assert len(data) == 3
    assert data[0]["nl_text"] == TEST_CASE_REVISION_REQUEST_2["nl_text"]
    assert data[1]["nl_text"] == TEST_CASE_REVISION_REQUEST_1["nl_text"]
    assert data[0]["id"] > data[1]["id"]

######
# FILTERS TEST
######


def test_test_cases_filter_title_contains(client, db_session):
    a = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_TITLE_PARAM_1)
    b = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_TITLE_PARAM_2)
    make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_TITLE_PARAM_3)

    r = client.get("/test-cases", params={"title": "  login "})
    assert r.status_code == 200
    data = r.json()

    ids = {row["id"] for row in data}
    assert ids == {a.id, b.id}


def test_test_cases_filter_description_contains(client, db_session):
    a = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_DESCR_PARAM_1)
    b = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_DESCR_PARAM_2)
    make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_DESCR_PARAM_3)

    r = client.get("/test-cases", params={"description": "SMOKE"})
    assert r.status_code == 200
    ids = {row["id"] for row in r.json()}
    assert ids == {a.id, b.id}


def test_test_cases_filter_created_at_range(client, db_session):
    first = make_test_case(db_session, title="A", description="x", created_at=datetime(2026,1,1,10,0), updated_at=datetime(2026,1,10,10,0))
    make_revision(db_session, first.id, **TEST_CASE_REVISION_REQUEST_1)

    mid = make_test_case(db_session, title="B", description="x", created_at=datetime(2026,1,2,10,0), updated_at=datetime(2026,1,11,10,0))
    make_revision(db_session, mid.id, **TEST_CASE_REVISION_REQUEST_2)

    last = make_test_case(db_session, title="C", description="x", created_at=datetime(2026,1,3,10,0), updated_at=datetime(2026,1,12,10,0))
    make_revision(db_session, last.id, **TEST_CASE_REVISION_REQUEST_2)

    r = client.get(
        "/test-cases",
        params={
            "created_at_from": "2026-01-02T00:00:00",
            "created_at_to": "2026-01-02T23:59:59",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert [row["id"] for row in data] == [mid.id]


def test_test_cases_filter_updated_at_range(client, db_session):
    first = make_test_case(db_session, title="A", description="x", created_at=datetime(2026,1,1,10,0), updated_at=datetime(2026,1,10,10,0))
    make_revision(db_session, first.id, **TEST_CASE_REVISION_REQUEST_1)

    mid = make_test_case(db_session, title="B", description="x", created_at=datetime(2026,1,2,10,0), updated_at=datetime(2026,1,11,10,0))
    make_revision(db_session, mid.id, **TEST_CASE_REVISION_REQUEST_2)

    last = make_test_case(db_session, title="C", description="x", created_at=datetime(2026,1,3,10,0), updated_at=datetime(2026,1,12,10,0))
    make_revision(db_session, last.id, **TEST_CASE_REVISION_REQUEST_2)

    r = client.get(
        "/test-cases",
        params={
            "updated_at_from": "2026-01-11T00:00:00",
            "updated_at_to": "2026-01-11T23:59:59",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert [row["id"] for row in data] == [mid.id]


def test_test_cases_sort_created_at_asc(client, db_session):
    a = make_test_case(db_session, title="A", description="x", created_at=datetime(2026,1,1,10,0), updated_at=datetime(2026,1,5,10,0))
    make_revision(db_session, a.id, **TEST_CASE_REVISION_REQUEST_1)

    b = make_test_case(db_session, title="B", description="x", created_at=datetime(2026,1,2,10,0), updated_at=datetime(2026,1,4,10,0))
    make_revision(db_session, b.id, **TEST_CASE_REVISION_REQUEST_2)

    c = make_test_case(db_session, title="C", description="x", created_at=datetime(2026,1,3,10,0), updated_at=datetime(2026,1,3,10,0))
    make_revision(db_session, c.id, **TEST_CASE_REVISION_REQUEST_1)

    r = client.get("/test-cases", params={"sort_by": "created_at", "sort_order": "asc"})
    assert r.status_code == 200
    ids = [row["id"] for row in r.json()]
    assert ids[:3] == [a.id, b.id, c.id]


def test_test_cases_sort_updated_at_desc(client, db_session):
    a = make_test_case(db_session, title="A", description="x", created_at=datetime(2026,1,1,10,0), updated_at=datetime(2026,1,5,10,0))
    make_revision(db_session, a.id, **TEST_CASE_REVISION_REQUEST_1)

    b = make_test_case(db_session, title="B", description="x", created_at=datetime(2026,1,2,10,0), updated_at=datetime(2026,1,4,10,0))
    make_revision(db_session, b.id, **TEST_CASE_REVISION_REQUEST_1)

    c = make_test_case(db_session, title="C", description="x", created_at=datetime(2026,1,3,10,0), updated_at=datetime(2026,1,3,10,0))
    make_revision(db_session, c.id, **TEST_CASE_REVISION_REQUEST_1)

    r = client.get("/test-cases", params={"sort_by": "updated_at", "sort_order": "desc"})
    assert r.status_code == 200
    ids = [row["id"] for row in r.json()]
    assert ids[:3] == [a.id, b.id, c.id]


def test_test_cases_pagination(client, db_session):
    for i in range(1, 6):
        tc = make_test_case(
            db_session,
            title=f"T{i}",
            description="x",
            created_at=datetime(2026, 1, i, 10, 0),
            updated_at=datetime(2026, 1, i, 10, 0),
        )
        make_revision(db_session, tc.id, **TEST_CASE_REVISION_REQUEST_1)

    r1 = client.get("/test-cases", params={"limit": 2, "page": 1, "sort_by": "created_at", "sort_order": "asc"})
    r2 = client.get("/test-cases", params={"limit": 2, "page": 2, "sort_by": "created_at", "sort_order": "asc"})
    assert r1.status_code == 200 and r2.status_code == 200

    ids1 = [x["id"] for x in r1.json()]
    ids2 = [x["id"] for x in r2.json()]
    assert len(ids1) == 2 and len(ids2) == 2
    assert set(ids1).isdisjoint(set(ids2))


def test_test_cases_invalid_range_returns_422(client):
    r = client.get(
        "/test-cases",
        params={"created_at_from": "2026-02-01T00:00:00", "created_at_to": "2026-01-01T00:00:00"},
    )
    assert r.status_code == 422


def test_revisions_filter_nl_text_contains(client, db_session):
    tc = make_test_case(db_session, title="A", description="x")

    a = make_revision(db_session, test_case_id=tc.id, **TEST_CASE_REVISION_NL_TEXT_1)
    b = make_revision(db_session, test_case_id=tc.id, **TEST_CASE_REVISION_NL_TEXT_2)
    make_revision(db_session, test_case_id=tc.id, **TEST_CASE_REVISION_NL_TEXT_3)
    db_session.commit()

    r = client.get(f"/test-cases/{tc.id}/revisions", params={"nl_text": "  login  "})
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert ids == {a.id, b.id}


def test_revisions_filter_comment_contains(client, db_session):
    tc = make_test_case(db_session, title="A", description="x")

    a = make_revision(db_session, test_case_id=tc.id, **TEST_CASE_REVISION_COMMENT_1)
    b = make_revision(db_session, test_case_id=tc.id, **TEST_CASE_REVISION_COMMENT_2)
    make_revision(db_session, test_case_id=tc.id, **TEST_CASE_REVISION_COMMENT_3)
    db_session.commit()

    url = f"/test-cases/{tc.id}/revisions"
    r = client.get(url, params={"comment": "review"})
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert ids == {a.id, b.id}


def test_revisions_filter_created_at_range(client, db_session):
    tc = make_test_case(db_session, title="A", description="x")

    make_revision(db_session, test_case_id=tc.id, created_at=datetime(2026,1,4,10,0), nl_text="a", comment="a")
    mid = make_revision(db_session, test_case_id=tc.id, created_at=datetime(2026,1,5,10,0), nl_text="b", comment="b")
    make_revision(db_session, test_case_id=tc.id, created_at=datetime(2026,1,6,10,0), nl_text="c", comment="c")

    url = f"/test-cases/{tc.id}/revisions"
    r = client.get(
        url,
        params={
            "created_at_from": "2026-01-05T00:00:00",
            "created_at_to": "2026-01-05T23:59:59",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert [x["id"] for x in data] == [mid.id]


def test_revisions_sort_created_at_asc(client, db_session):
    tc = make_test_case(db_session, title="A", description="x")
    a = make_revision(db_session, test_case_id=tc.id, created_at=datetime(2026,1,1,10,0), nl_text="a", comment="a")
    b = make_revision(db_session, test_case_id=tc.id, created_at=datetime(2026,1,2,10,0), nl_text="b", comment="b")
    c = make_revision(db_session, test_case_id=tc.id, created_at=datetime(2026,1,3,10,0), nl_text="c", comment="c")
    db_session.commit()

    url = f"/test-cases/{tc.id}/revisions"
    r = client.get(url, params={"sort_by": "created_at", "sort_order": "asc"})
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert ids == [a.id, b.id, c.id]


def test_revisions_pagination(client, db_session):
    tc = make_test_case(db_session, title="A", description="x")

    for i in range(1, 6):
        make_revision(
            db_session,
            test_case_id=tc.id,
            created_at=datetime(2026, 1, i, 10, 0),
            nl_text=f"t{i}",
        )

    url = f"/test-cases/{tc.id}/revisions"
    r1 = client.get(url, params={"limit": 2, "page": 1, "sort_by": "created_at", "sort_order": "asc"})
    r2 = client.get(url, params={"limit": 2, "page": 2, "sort_by": "created_at", "sort_order": "asc"})
    assert r1.status_code == 200 and r2.status_code == 200

    ids1 = [x["id"] for x in r1.json()]
    ids2 = [x["id"] for x in r2.json()]
    assert len(ids1) == 2 and len(ids2) == 2
    assert set(ids1).isdisjoint(set(ids2))


def test_revisions_invalid_range_returns_422(client, db_session):
    tc = make_test_case_and_revision(db_session, **TEST_CASE_REQUEST_1)

    url = f"/test-cases/{tc.id}/revisions"
    r = client.get(
        url,
        params={"created_at_from": "2026-02-01T00:00:00", "created_at_to": "2026-01-01T00:00:00"},
    )
    assert r.status_code == 422
