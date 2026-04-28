import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionGenerationMeta(BaseModel):
    session_id: int
    candidate_id: int
    target_job: str
    difficulty_level: str | None = None
    prompt_profile_id: int | None = None
    created_at: datetime | None = None


class CandidatePayload(BaseModel):
    candidate_id: int
    name: str
    email: str | None = None
    phone: str | None = None
    birth_date: date | None = None
    job_position: str | None = None
    apply_status: str | None = None


class CandidateDocumentPayload(BaseModel):
    document_id: int
    document_type: str
    title: str
    original_file_name: str
    file_ext: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    extract_status: str
    extracted_text: str | None = None
    extracted_summary: str | None = None
    structured_data: dict[str, Any] = Field(default_factory=dict)


class PromptProfilePayload(BaseModel):
    id: int
    profile_key: str
    target_job: str | None = None
    system_prompt: str
    output_schema: dict[str, Any] | list[Any] | str | None = None

    @staticmethod
    def parse_output_schema(raw_value: str | None) -> dict[str, Any] | list[Any] | str | None:
        if raw_value is None:
            return None
        stripped = raw_value.strip()
        if not stripped:
            return None
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return stripped


class CandidateInterviewPrepInput(BaseModel):
    session: SessionGenerationMeta
    candidate: CandidatePayload
    prompt_profile: PromptProfilePayload | None = None
    candidate_documents: list[CandidateDocumentPayload] = Field(default_factory=list)
    additional_instruction: str | None = None
    human_action: str | None = None
    target_question_ids: list[str] = Field(default_factory=list)
    existing_questions: list[dict[str, Any]] = Field(default_factory=list)


def _truncate_text(value: str | None, max_length: int = 500) -> str | None:
    if value is None:
        return None
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}... (truncated)"


def build_candidate_interview_prep_log_payload(
    payload: CandidateInterviewPrepInput,
) -> dict[str, Any]:
    document_items: list[dict[str, Any]] = []
    total_extracted_text_length = 0

    for document in payload.candidate_documents:
        extracted_text_length = len(document.extracted_text or "")
        total_extracted_text_length += extracted_text_length
        document_items.append(
            {
                "document_id": document.document_id,
                "document_type": document.document_type,
                "title": document.title,
                "extract_status": document.extract_status,
                "extracted_text_length": extracted_text_length,
                "extracted_text_preview": _truncate_text(document.extracted_text, max_length=500),
            }
        )

    return {
        "session": payload.session.model_dump(mode="json"),
        "candidate": payload.candidate.model_dump(mode="json"),
        "prompt_profile": (
            payload.prompt_profile.model_dump(mode="json")
            if payload.prompt_profile is not None
            else None
        ),
        "candidate_documents_summary": {
            "count": len(payload.candidate_documents),
            "total_extracted_text_length": total_extracted_text_length,
            "items": document_items,
        },
    }
