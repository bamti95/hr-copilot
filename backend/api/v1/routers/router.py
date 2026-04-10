from fastapi import APIRouter

from api.v1.routers.admin.admin_router import router as admin_router
from api.v1.routers.auth.auth_router import router as auth_router
from api.v1.routers.admin.admin_group_router import router as admin_group_router


# 공통 라우터 묶기
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(admin_group_router)
