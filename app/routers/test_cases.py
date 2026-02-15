from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_test_case_repo
from app.query.filters import TestCaseListQuery, get_test_case_list_query
from app.repositories.repositories import TestCaseRepository
from app.schemas.schemas import (
    TestCaseCreate,
    TestCaseItemResponse,
    TestCaseListItemResponse,
    TestCaseUpdate,
)

router = APIRouter(prefix="/test-cases", tags=["Test cases"])


@router.post("", response_model=TestCaseItemResponse, status_code=status.HTTP_201_CREATED)
def create_test_case(
    payload: TestCaseCreate, test_case_repo: TestCaseRepository = Depends(get_test_case_repo)
) -> TestCaseItemResponse:
    tc = test_case_repo.create_test_case(payload)
    if tc is None:
        raise HTTPException(status_code=400, detail="Test case not created")
    return TestCaseItemResponse(**tc)


@router.get("", response_model=list[TestCaseListItemResponse])
def list_test_cases(
    test_case_repo: TestCaseRepository = Depends(get_test_case_repo),
    q: TestCaseListQuery = Depends(get_test_case_list_query),
    limit: int = Query(default=20, ge=1, le=200),
    page: int = Query(default=1, ge=1),
) -> list[TestCaseListItemResponse]:
    tc_list = test_case_repo.get_test_case_list(page, limit, q)
    return [TestCaseListItemResponse(**tc) for tc in tc_list]


@router.get("/{test_case_id}", response_model=TestCaseItemResponse)
def get_test_case(
    test_case_id: int, test_case_repo: TestCaseRepository = Depends(get_test_case_repo)
) -> TestCaseItemResponse:
    tc = test_case_repo.get_item(test_case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="test_case not found")
    return TestCaseItemResponse(**tc)


@router.patch("/{test_case_id}", response_model=TestCaseItemResponse)
def update_test_case(
    test_case_id: int,
    payload: TestCaseUpdate,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repo),
) -> TestCaseItemResponse:
    tc = test_case_repo.get_test_case(test_case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="test_case not found")
    updated = test_case_repo.update_test_case(tc, payload)
    if not updated:
        raise HTTPException(status_code=400, detail="test_case not updated")

    return TestCaseItemResponse(**updated)
