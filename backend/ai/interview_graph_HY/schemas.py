from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class GraphBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


QuestionStatus = Literal["pending", "approved", "rejected", "human_rejected"]


class QuestionSet(GraphBaseModel):
    id: str
    generation_basis: str
    question_text: str
    evaluation_guide: str

    predicted_answer: str = ""
    follow_up_question: str = ""

    status: QuestionStatus = "pending"
    reject_reason: str = ""

    regen_targets: list[str] = Field(default_factory=list)


class AgentStateModel(GraphBaseModel):
    candidate_text: str
    recruitment_criteria: str
    questions: list[QuestionSet] = Field(default_factory=list)

    retry_count: int = 0
    max_retry_count: int = 3
    is_all_approved: bool = False

    human_action: str | None = None
    additional_instruction: str | None = None

    regen_question_ids: list[str] | None = None

    # for service layer consumption
    meta: dict[str, Any] = Field(default_factory=dict)
