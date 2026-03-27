from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers.answers import router as answers_router
from app.routers.surveys import router as surveys_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Сервис опросов",
    description="CRUD опросов и сохранение ответов.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", summary="Проверка здоровья сервиса")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(surveys_router)
app.include_router(answers_router)
