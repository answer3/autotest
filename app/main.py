from fastapi import FastAPI
from fastapi.requests import Request
from loguru import logger
from pydantic import ValidationError
from starlette.responses import JSONResponse

from app.core.logging import setup_logger
from app.routers.plan_proposals import router as PlanProposalsRouter
from app.routers.test_case_revisions import router as TestCasesRevisionsRouter
from app.routers.test_cases import router as TestCasesRouter
from app.routers.test_run_artifacts import router as TestRunArtifactsRouter
from app.routers.test_runs import router as TestRunsRouter

setup_logger()

app = FastAPI(title="Autotest MVP API")

logger.info("api_startup")


@app.exception_handler(ValidationError)
def handle_query_param_error(request: Request, exc: ValidationError) -> JSONResponse:
    details = []
    for e in exc.errors():
        loc = list(e.get("loc", ()))
        if loc and loc[0] != "query":
            loc = ["query", *loc]
        details.append(
            {
                "loc": loc,
                "msg": e.get("msg", "Invalid value"),
                "type": e.get("type", "value_error"),
            }
        )

    return JSONResponse(status_code=422, content={"detail": details})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(TestCasesRouter)
app.include_router(TestCasesRevisionsRouter)
app.include_router(PlanProposalsRouter)
app.include_router(TestRunsRouter)
app.include_router(TestRunArtifactsRouter)
