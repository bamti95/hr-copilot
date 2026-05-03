import json
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate import Candidate
from models.document import Document
from models.interview_session import InterviewSession
from models.prompt_profile import PromptProfile
from repositories.candidate_repository import CandidateRepository
from repositories.prompt_profile_repository import PromptProfileRepository
from repositories.session_repo import SessionRepository
from schemas.session_generation import (
    CandidateDocumentPayload,
    CandidateInterviewPrepInput,
    CandidatePayload,
    PromptProfilePayload,
    SessionGenerationMeta,
    build_candidate_interview_prep_log_payload,
)

logger = logging.getLogger(__name__)


class SessionGenerationPayloadAssembler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.candidate_repo = CandidateRepository(db)
        self.prompt_profile_repo = PromptProfileRepository(db)

    async def build_candidate_interview_prep_input(
        self,
        session_id: int,
        manager_id: int | None = None,
    ) -> CandidateInterviewPrepInput:
        session = await self._get_session_or_raise(session_id)
        candidate = await self._get_candidate_or_raise(session.candidate_id)
        documents = await self.candidate_repo.find_active_documents_by_candidate_id(candidate.id)
        prompt_profile = await self._get_prompt_profile_or_raise(session.prompt_profile_id)

        payload = CandidateInterviewPrepInput(
            session=SessionGenerationMeta(
                session_id=session.id,
                manager_id=manager_id,
                candidate_id=session.candidate_id,
                target_job=session.target_job,
                difficulty_level=session.difficulty_level,
                prompt_profile_id=session.prompt_profile_id,
                created_at=session.created_at,
            ),
            candidate=self._to_candidate_payload(candidate),
            prompt_profile=self._to_prompt_profile_payload(prompt_profile),
            candidate_documents=[self._to_document_payload(document) for document in documents],
        )

        logger.info(
            "CandidateInterviewPrepInput Assembled\n%s",
            json.dumps(
                build_candidate_interview_prep_log_payload(payload),
                ensure_ascii=False,
                indent=2,
            ),
        )
        return payload

    async def _get_session_or_raise(self, session_id: int) -> InterviewSession:
        session = await self.session_repo.find_by_id_not_deleted(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="면접 세션을 찾을 수 없습니다.",
            )
        return session

    async def _get_candidate_or_raise(self, candidate_id: int) -> Candidate:
        candidate = await self.candidate_repo.find_by_id_not_deleted(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="지원자를 찾을 수 없습니다.",
            )
        return candidate

    async def _get_prompt_profile_or_raise(
        self,
        prompt_profile_id: int | None,
    ) -> PromptProfile | None:
        if prompt_profile_id is None:
            return None
        prompt_profile = await self.prompt_profile_repo.find_by_id_active(prompt_profile_id)
        if not prompt_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프롬프트 프로필을 찾을 수 없습니다.",
            )
        return prompt_profile

    @staticmethod
    def _to_candidate_payload(candidate: Candidate) -> CandidatePayload:
        return CandidatePayload(
            candidate_id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            birth_date=candidate.birth_date,
            job_position=candidate.job_position,
            apply_status=candidate.apply_status,
        )

    @staticmethod
    def _to_document_payload(document: Document) -> CandidateDocumentPayload:
        return CandidateDocumentPayload(
            document_id=document.id,
            document_type=document.document_type,
            title=document.title,
            original_file_name=document.original_file_name,
            file_ext=document.file_ext,
            mime_type=document.mime_type,
            file_size=document.file_size,
            extract_status=document.extract_status,
            extracted_text=document.extracted_text,
            extracted_summary=None,
            structured_data={},
        )

    @staticmethod
    def _to_prompt_profile_payload(
        prompt_profile: PromptProfile | None,
    ) -> PromptProfilePayload | None:
        if prompt_profile is None:
            return None
        return PromptProfilePayload(
            id=prompt_profile.id,
            profile_key=prompt_profile.profile_key,
            target_job=prompt_profile.target_job,
            system_prompt=prompt_profile.system_prompt,
            output_schema=PromptProfilePayload.parse_output_schema(prompt_profile.output_schema),
        )
