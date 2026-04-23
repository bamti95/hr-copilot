import json
import logging

from schemas.session_generation import (
    CandidateInterviewPrepInput,
    build_candidate_interview_prep_log_payload,
)

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    async def request_candidate_interview_prep(
        self,
        payload: CandidateInterviewPrepInput,
    ) -> None:
        logger.info(
            "Question Generation Stub Request Payload\n%s",
            json.dumps(
                build_candidate_interview_prep_log_payload(payload),
                ensure_ascii=False,
                indent=2,
            ),
        )
        # TODO: Connect async queue / LangGraph entrypoint with this payload.
        _ = payload
        pass
