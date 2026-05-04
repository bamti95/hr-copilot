"""JY 그래프 전용 스키마 진입점.

현재 JY 파이프라인은 서비스/DB 저장 로직과 동일한 응답 계약을 사용해야 하므로
공용 면접 질문 스키마를 재노출한다. 이후 JY만의 출력 필드가 필요해지면 이 파일에서
확장하거나 validator를 추가하면 된다.
"""

from ai.interview_graph.schemas import (
    DocumentAnalysisOutput,
    DocumentEvidence,
    DrillerOutput,
    FollowUpQuestion,
    GraphBaseModel,
    InterviewQuestionItem,
    PredictedAnswer,
    PredictorOutput,
    QuestionCandidate,
    QuestionGenerationResponse,
    QuestionInteractionRequest,
    QuestionerOutput,
    ReviewResult,
    ReviewerOutput,
    ScoreResult,
    ScorerOutput,
)

__all__ = [
    "DocumentAnalysisOutput",
    "DocumentEvidence",
    "DrillerOutput",
    "FollowUpQuestion",
    "GraphBaseModel",
    "InterviewQuestionItem",
    "PredictedAnswer",
    "PredictorOutput",
    "QuestionCandidate",
    "QuestionGenerationResponse",
    "QuestionInteractionRequest",
    "QuestionerOutput",
    "ReviewResult",
    "ReviewerOutput",
    "ScoreResult",
    "ScorerOutput",
]
