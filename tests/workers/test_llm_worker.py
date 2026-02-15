from sqlalchemy import select

from app.models.enums import PlanProposalStatus
from app.models.models import PlanProposal
from app.workers.llm_worker import handle_message
from tests.conftest import (
    make_test_case_revision_proposal,
)
from tests.data.data_llm_worker import LLM_PAYLOAD_OK
from tests.data.data_proposals import PROPOSAL_DATA_CREATE_1, PROPOSAL_DATA_SUCCESS_1
from tests.data.data_test_case import TEST_CASE_REQUEST_1
from tests.workers.helper_llm_worker import OllamaBoom, OllamaOK, msg


def get_proposal(db, proposal_id: int) -> PlanProposal:
    return db.execute(select(PlanProposal).where(PlanProposal.id == proposal_id)).scalars().one()


def test_llm_worker_happy_path(db_session, llm_uow_factory):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_CREATE_1)
    proposal_id = proposal.id

    handle_message(
        msg(proposal.id),
        llm_uow_factory=llm_uow_factory,
        llm_client_factory=lambda: OllamaOK(),
    )

    updated = get_proposal(db_session, proposal_id)

    assert updated.status == PlanProposalStatus.succeeded
    assert updated.started_at is not None
    assert updated.finished_at is not None
    assert updated.error is None
    assert updated.result_payload == LLM_PAYLOAD_OK


def test_llm_worker_final_status_exits(db_session, llm_uow_factory):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_1)
    proposal_id = proposal.id

    handle_message(
        msg(proposal.id),
        llm_uow_factory=llm_uow_factory,
        llm_client_factory=lambda: OllamaBoom(),
    )

    updated = get_proposal(db_session, proposal_id)

    assert updated.status == PlanProposalStatus.succeeded
    assert updated.error is None
    assert updated.result_payload == PROPOSAL_DATA_SUCCESS_1["result_payload"]


def test_llm_worker_ollama_error_marks_failed(db_session, llm_uow_factory):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_CREATE_1)

    proposal_id = proposal.id

    handle_message(
        msg(proposal.id),
        llm_uow_factory=llm_uow_factory,
        llm_client_factory=lambda: OllamaBoom(),
    )

    updated = get_proposal(db_session, proposal_id)

    assert updated.status == PlanProposalStatus.failed
    assert updated.error is not None
    assert updated.started_at is not None
    assert updated.finished_at is not None
    assert updated.result_payload is None
