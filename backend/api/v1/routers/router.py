from fastapi import APIRouter

from api.v1.routers.auth.auth_router import router as auth_router
from api.v1.routers.candidate_router import router as candidate_router
from api.v1.routers.manager_router import router as manager_router
from api.v1.routers.sessions import router as session_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(manager_router)
api_router.include_router(candidate_router)
api_router.include_router(session_router)
