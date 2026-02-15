from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_test_case_repo, get_test_case_rev_repo
from app.query.filters import TestCaseRevisionListQuery, get_revision_list_query
from app.repositories.repositories import TestCaseRepository, TestCaseRevisionRepository
from app.schemas.schemas import TestCaseRevisionCreate, TestCaseRevisionResponse

router = APIRouter(prefix="/test-cases", tags=["Test case revisions"])


@router.post(
    "/{test_case_id}/revisions",
    response_model=TestCaseRevisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_revision(
    test_case_id: int,
    payload: TestCaseRevisionCreate,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repo),
    test_case_rev_repo: TestCaseRevisionRepository = Depends(get_test_case_rev_repo),
) -> TestCaseRevisionResponse:
    tc = test_case_repo.get_test_case(test_case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="test_case not found")
    rev = test_case_rev_repo.create_test_case_revision(test_case_id, payload)

    return TestCaseRevisionResponse.model_validate(rev)


@router.get("/{test_case_id}/revisions", response_model=list[TestCaseRevisionResponse])
def list_revisions(
    test_case_id: int,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repo),
    test_case_rev_repo: TestCaseRevisionRepository = Depends(get_test_case_rev_repo),
    q: TestCaseRevisionListQuery = Depends(get_revision_list_query),
    limit: int = Query(default=20, ge=1, le=200),
    page: int = Query(default=1, ge=1),
) -> list[TestCaseRevisionResponse]:
    tc = test_case_repo.get_test_case(test_case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="test_case not found")

    revs = test_case_rev_repo.get_list(test_case_id, page, limit, q)
    return [TestCaseRevisionResponse.model_validate(item) for item in revs]


@router.get("/{test_case_id}/revisions/{revision_id}", response_model=TestCaseRevisionResponse)
def get_revision(
    test_case_id: int,
    revision_id: int,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repo),
    test_case_rev_repo: TestCaseRevisionRepository = Depends(get_test_case_rev_repo),
) -> TestCaseRevisionResponse:
    tc = test_case_repo.get_test_case(test_case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="test_case not found")

    rev = test_case_rev_repo.get_item(revision_id)
    if not rev:
        raise HTTPException(status_code=404, detail="revision not found")
    return TestCaseRevisionResponse.model_validate(rev)
