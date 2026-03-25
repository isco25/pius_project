from __future__ import annotations

from fastapi import FastAPI

from app.routers.analytics import router as analytics_router

app = FastAPI(
    title="Сервис аналитики",
    description="Базовая статистика по опросам.",
    version="1.0.0",
)


@app.get("/health", summary="Проверка здоровья сервиса")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(analytics_router)
