from unittest.mock import ANY

TEST_CASE_REQUEST_1 = {
    "title": "TC-1",
    "description": "desc",
    "nl_text": "Given ... When ... Then ...",
    "comment": "initial",
    "created_by": "tester"
}

TEST_CASE_ITEM_RESPONSE_1 = {
    "id": ANY,
    "title": "TC-1",
    "description": "desc",
    "created_at": ANY,
    "updated_at": ANY,
    "revisions_count": ANY,
    "last_revision": {
        "id": ANY,
        "created_by": "tester",
        "test_case_id": ANY,
        "nl_text": "Given ... When ... Then ...",
        "created_at": ANY,
        "comment": "initial",
    },
}

TEST_CASE_REQUEST_2 = {
    "title": "TC-2",
    "description": "desc 2",
    "nl_text": "Given ... When ... Then ... Second",
    "comment": "initial 2",
    "created_by": "tester"
}

TEST_CASE_ITEM_RESPONSE_2 = {
    "id": ANY,
    "title": "TC-2",
    "description": "desc 2",
    "created_at": ANY,
    "updated_at": ANY,
    "revisions_count": ANY,
    "last_revision": {
        "id": ANY,
        "created_by": "tester",
        "test_case_id": ANY,
        "nl_text": "Given ... When ... Then ... Second",
        "created_at": ANY,
        "comment": "initial 2"
    },
}

TEST_CASE_UPDATE_REQUEST_1 = {
    "title": "TC-UPDATE",
    "description": "desc update",
}

TEST_CASE_REVISION_REQUEST_1 = {
  "nl_text": "New NL instructions",
  "comment": "new revision comment",
  "created_by": "tester"
}

TEST_CASE_REVISION_REQUEST_2 = {
  "nl_text": "Another New NL instructions",
  "comment": "another new revision comment",
  "created_by": "tester"
}

TEST_CASE_REQUEST_TITLE_PARAM_1 = {
    "title": "login test",
    "description": "desc",
    "nl_text": "Given ... When ... Then ...",
    "comment": "initial",
    "created_by": "tester"
}

TEST_CASE_REQUEST_TITLE_PARAM_2 = {
    "title": "login flow",
    "description": "desc",
    "nl_text": "Given ... When ... Then ...",
    "comment": "initial",
    "created_by": "tester"
}

TEST_CASE_REQUEST_TITLE_PARAM_3 = {
    "title": "Payment",
    "description": "desc",
    "nl_text": "Given ... When ... Then ...",
    "comment": "initial",
    "created_by": "tester"
}

TEST_CASE_REQUEST_DESCR_PARAM_1 = {
    "title": "login test",
    "description": "smoke: test",
    "nl_text": "Given ... When ... Then ...",
    "comment": "initial",
    "created_by": "tester"
}

TEST_CASE_REQUEST_DESCR_PARAM_2 = {
    "title": "login flow",
    "description": "this is SMOKE params",
    "nl_text": "Given ... When ... Then ...",
    "comment": "initial",
    "created_by": "tester"
}

TEST_CASE_REQUEST_DESCR_PARAM_3 = {
    "title": "Payment",
    "description": "Fake descr",
    "nl_text": "Given ... When ... Then ...",
    "comment": "initial",
    "created_by": "tester"
}

TEST_CASE_REVISION_NL_TEXT_1 = {
  "nl_text": "login",
  "comment": "descr",
  "created_by": "tester"
}

TEST_CASE_REVISION_NL_TEXT_2 = {
  "nl_text": "any LOGIN where",
  "comment": "descr",
  "created_by": "tester"
}

TEST_CASE_REVISION_NL_TEXT_3 = {
  "nl_text": "stuFF",
  "comment": "descr",
  "created_by": "tester"
}

TEST_CASE_REVISION_COMMENT_1 = {
  "nl_text": "text",
  "comment": "review",
  "created_by": "tester"
}

TEST_CASE_REVISION_COMMENT_2 = {
  "nl_text": "text",
  "comment": "some REVIEW here",
  "created_by": "tester"
}

TEST_CASE_REVISION_COMMENT_3 = {
  "nl_text": "text",
  "comment": "no descr",
  "created_by": "tester"
}