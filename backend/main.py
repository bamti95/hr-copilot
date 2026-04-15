import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.routers.health import router as health_router
from api.v1.routers.router import api_router
from core.config import get_settings
from core.database import init_db

settings = get_settings()

origins = [
    "http://localhost:5173",
    "https://your-domain.com",
    "*",
]

if settings.DB_ECHO:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title="HR Copilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router)
