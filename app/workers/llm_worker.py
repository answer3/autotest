import json
from collections.abc import Callable

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging import setup_logger
from app.llm.ollama_client import LLMClient, OllamaClient
from app.models.enums import PlanProposalStatus
from app.queue.redis_consumer import RedisConsumer
from app.utils import utcnow
from app.workers.db import LlmDbUnitOfWork


def handle_message(
    body: bytes,
    llm_uow_factory: Callable[[], LlmDbUnitOfWork],
    llm_client_factory: Callable[[], LLMClient] = OllamaClient,
) -> None:
    setup_logger()
    payload = json.loads(body.decode("utf-8"))
    proposal_id = int(payload["proposal_id"])

    logger.info(f"LLM Worker: message for proposal id={proposal_id} received")
    with llm_uow_factory() as llm_uow:
        try:
            ollama = llm_client_factory()
            proposal = llm_uow.plan_proposals_repo.get_item(proposal_id)
            if not proposal:
                logger.warning(f"LLM Worker: Can't find proposal id={proposal_id}, exit")
                return

            if proposal.status in (PlanProposalStatus.succeeded, PlanProposalStatus.failed):
                logger.warning(
                    f"LLM Worker: Status of proposal id={proposal_id} is {proposal.status}, exit"
                )
                return

            ok = llm_uow.plan_proposals_repo.mark_running(proposal_id, started_at=utcnow())
            if not ok:
                logger.warning(
                    f"LLM Worker: Can't set status of id={proposal_id} to {PlanProposalStatus.running}, exit"
                )
                return

            rev = llm_uow.test_case_revisions_repo.get_item(proposal.test_case_revision_id)
            if not rev:
                logger.warning(
                    f"LLM Worker: Can't set find test_case_revision id={proposal.test_case_revision_id}, exit"
                )
                llm_uow.plan_proposals_repo.mark_failed(
                    proposal_id, error="test_case_revision not found", finished_at=utcnow()
                )
                return

            try:
                logger.info(f"LLM Worker: proposal id={proposal_id}, generating plan...")
                plan_json = ollama.generate_plan_json(rev.nl_text)
                logger.info(f"LLM Worker: proposal id={proposal_id}, plan_json = {plan_json}")
            except Exception as e:
                logger.error(f"LLM Worker: Can't get json for proposal id={proposal_id}, error {e}")
                llm_uow.plan_proposals_repo.mark_failed(
                    proposal_id, error=f"ollama_error: {e}", finished_at=utcnow()
                )
                return

            llm_uow.plan_proposals_repo.mark_ready(
                proposal_id, result_payload=plan_json, finished_at=utcnow()
            )
            logger.info(f"LLM Worker: proposal id={proposal_id} is ready")

        except Exception as e:
            logger.error(f"LLM Worker: Unexpected error for proposal id={proposal_id}, error {e}")
            raise


def main() -> None:
    consumer = RedisConsumer("llm")
    engine = create_engine(settings.database_url, future=True)
    db_sessionmaker = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    consumer.consume(
        lambda msg: handle_message(
            msg, lambda: LlmDbUnitOfWork(db_sessionmaker()), lambda: OllamaClient()
        )
    )


if __name__ == "__main__":
    main()
