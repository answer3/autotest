from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from app.dependencies import get_redis_publisher, get_test_run_repo, get_uow
from app.models.enums import PlanProposalStatus
from app.models.models import TestRun
from app.query.filters import TestRunListQuery, get_test_run_list_query
from app.queue.redis_queue import RedisPublisher
from app.repositories.repositories import TestRunRepository
from app.schemas.schemas import TestRunCreateRequest, TestRunResponse
from app.uow import UnitOfWork

router = APIRouter(prefix="", tags=["Test runs"])


@router.post(
    "/plan-proposals/{plan_proposal_id}/test-runs",
    response_model=TestRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_test_run(
    plan_proposal_id: int,
    payload: TestRunCreateRequest,
    uow: UnitOfWork = Depends(get_uow),
    publisher: RedisPublisher = Depends(get_redis_publisher),
) -> TestRun:
    plan_prop = uow.plan_proposals_repo.get_item(plan_proposal_id)
    if not plan_prop:
        raise HTTPException(status_code=404, detail=f"plan_proposal {plan_proposal_id} not found")

    if plan_prop.status != PlanProposalStatus.succeeded:
        raise HTTPException(
            status_code=400,
            detail=f"plan_proposal {plan_proposal_id} incorrect status {plan_prop.status}",
        )

    if not plan_prop.is_ready_for_test:
        raise HTTPException(
            status_code=400, detail=f"plan_proposal {plan_proposal_id} is not marked as ready"
        )

    ts = uow.test_runs_repo.create(
        plan_proposal_id=plan_proposal_id,
        run_params=payload.run_params,
        created_by=payload.created_by,
        site_domain=payload.site_domain,
    )
    uow.commit()

    logger.info("Sending run test msg to queue")
    publisher.publish_test_run({"run_id": ts.id, "placeholders": payload.placeholders})
    return ts


@router.get("/test-runs/{test_run_id}", response_model=TestRunResponse)
def get_test_run(
    test_run_id: int,
    test_run_repo: TestRunRepository = Depends(get_test_run_repo),
) -> TestRun:
    ts = test_run_repo.get_item(test_run_id)
    if not ts:
        raise HTTPException(404, "test_run not found")
    return ts


@router.get("/plan-proposals/{plan_proposal_id}/test-runs", response_model=list[TestRunResponse])
def list_test_runs(
    plan_proposal_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    page: int = Query(default=1, ge=1),
    uow: UnitOfWork = Depends(get_uow),
    q: TestRunListQuery = Depends(get_test_run_list_query),
) -> list[TestRun]:
    plan_prop = uow.plan_proposals_repo.get_item(plan_proposal_id)
    if not plan_prop:
        raise HTTPException(status_code=404, detail=f"plan_proposal {plan_proposal_id} not found")

    items = uow.test_runs_repo.list(plan_proposal_id=plan_proposal_id, limit=limit, page=page, q=q)
    return items
