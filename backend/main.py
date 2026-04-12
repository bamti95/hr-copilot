from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 추가된 import
from api.v1.routers.health import router as health_router

from api.v1.routers.router import api_router # 공통 라우터

origins = [
    "http://localhost:5173",    # 로컬 프론트엔드 예시
    "https://your-domain.com",  # 운영 도메인 예시
    "*"                         # 모든 도메인 허용 (보안상 주의 필요)
]

app = FastAPI(title="HR Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 허용할 도메인 리스트
    allow_credentials=True,           # 쿠키 포함 여부
    allow_methods=["*"],              # 모든 HTTP Method 허용 (GET, POST 등)
    allow_headers=["*"],              # 모든 HTTP Header 허용
)

app.include_router(health_router)
app.include_router(api_router)