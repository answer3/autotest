from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from starlette import status

from app.dependencies import (
    get_plan_proposal_repo,
    get_redis_publisher,
    get_test_case_rev_repo,
    get_uow,
)
from app.models.enums import PlanProposalStatus
from app.models.models import PlanProposal
from app.query.filters import PlanProposalListQuery, get_plan_proposal_list_query
from app.queue.redis_queue import RedisPublisher
from app.repositories.repositories import PlanProposalRepository, TestCaseRevisionRepository
from app.schemas.schemas import PlanProposalResponse
from app.uow import UnitOfWork

router = APIRouter(prefix="", tags=["Plan proposals"])


@router.get("/plan-proposals/{proposal_id}", response_model=PlanProposalResponse)
def get_plan_proposal(
    proposal_id: int, plan_proposal_repo: PlanProposalRepository = Depends(get_plan_proposal_repo)
) -> PlanProposal:
    proposal = plan_proposal_repo.get_item(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="plan_proposal not found")
    return proposal


@router.get(
    "/test-case-revisions/{revision_id}/plan-proposals", response_model=list[PlanProposalResponse]
)
def list_revision_proposals(
    revision_id: int,
    plan_proposal_repo: PlanProposalRepository = Depends(get_plan_proposal_repo),
    test_case_rev_repo: TestCaseRevisionRepository = Depends(get_test_case_rev_repo),
    q: PlanProposalListQuery = Depends(get_plan_proposal_list_query),
    limit: int = Query(default=20, ge=1, le=200),
    page: int = Query(default=1, ge=1),
) -> list[PlanProposal]:
    rev = test_case_rev_repo.get_item(revision_id)
    if not rev:
        raise HTTPException(status_code=404, detail="test_case_revision not found")

    proposals = plan_proposal_repo.get_list(
        test_case_revision_id=revision_id, page=page, limit=limit, q=q
    )
    return proposals


@router.post(
    "/test-case-revisions/{revision_id}/plan-proposals",
    response_model=PlanProposalResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_plan_proposal(
    revision_id: int,
    uow: UnitOfWork = Depends(get_uow),
    publisher: RedisPublisher = Depends(get_redis_publisher),
) -> PlanProposal:
    if not uow.revisions_repo.get_item(revision_id):
        raise HTTPException(status_code=404, detail="test_case_revision not found")

    proposal = uow.plan_proposals_repo.create(revision_id)
    uow.commit()

    logger.info("Sending plan generation msg to queue")
    publisher.publish_plan_generation({"proposal_id": proposal.id})

    return proposal


@router.patch(
    "/plan-proposals/{plan_proposal_id}/ready",
    response_model=PlanProposalResponse,
)
def mark_plan_proposal_ready_for_test(
    plan_proposal_id: int,
    plan_proposal_repo: PlanProposalRepository = Depends(get_plan_proposal_repo),
) -> PlanProposal | None:
    proposal = plan_proposal_repo.get_item(plan_proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="plan_proposal not found")

    if proposal.status != PlanProposalStatus.succeeded:
        raise HTTPException(status_code=400, detail="plan_proposal is not succeeded")

    new_proposal = plan_proposal_repo.set_is_ready_for_test(proposal_id=plan_proposal_id)
    return new_proposal
