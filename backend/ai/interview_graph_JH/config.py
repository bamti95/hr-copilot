"""Shared configuration values for the JH interview graph."""

MAX_DOCUMENT_CHARS = 18000
PREDICTOR_DOCUMENT_CHARS = 7000

DEFAULT_CANDIDATE_QUESTION_COUNT = 10
DEFAULT_SELECTED_QUESTION_COUNT = 5
MORE_QUESTION_COUNT = 3
ADD_QUESTION_COUNT = 2

MAX_QUESTION_TEXT_CHARS = 180
MAX_FOLLOW_UP_CHARS = 160
MAX_PREDICTED_ANSWER_CHARS = 170

QUESTION_QUALITY_KEYS = [
    "job_relevance",
    "document_grounding",
    "validation_power",
    "specificity",
    "distinctiveness",
    "interview_usability",
    "core_resume_coverage",
]

EVALUATION_GUIDE_KEYS = [
    "guide_alignment",
    "signal_clarity",
    "good_bad_answer_separation",
    "practical_usability",
    "verification_specificity",
]
