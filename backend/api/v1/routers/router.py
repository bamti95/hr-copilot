"""v1 API 하위 라우터를 하나로 묶는다."""

from fastapi import APIRouter

from api.v1.routers.auth.auth_router import router as auth_router
from api.v1.routers.candidate_router import router as candidate_router
from api.v1.routers.llm_call_log_router import router as llm_call_log_router
from api.v1.routers.llm_usage_router import router as llm_usage_router
from api.v1.routers.manager_dashboard_router import router as manager_dashboard_router
from api.v1.routers.manager_router import router as manager_router
from api.v1.routers.job_posting_router import router as job_posting_router
from api.v1.routers.prompt_profile_router import router as prompt_profile_router
from api.v1.routers.sessions_router import router as session_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(manager_dashboard_router)
api_router.include_router(manager_router)
api_router.include_router(candidate_router)
api_router.include_router(session_router)
api_router.include_router(prompt_profile_router)
api_router.include_router(llm_usage_router)
api_router.include_router(llm_call_log_router)
api_router.include_router(job_posting_router)
