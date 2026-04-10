from fastapi import FastAPI
from api.v1.routers.health import router as health_router

from api.v1.routers.router import api_router # 공통 라우터

app = FastAPI(title="HR Copilot API")
app.include_router(health_router)
app.include_router(api_router)