from __future__ import annotations

from fastapi import FastAPI

from app.routers.answers import router as answers_router
from app.routers.surveys import router as surveys_router

app = FastAPI(
    title="РЎРµСЂРІРёСЃ РѕРїСЂРѕСЃРѕРІ",
    description="CRUD РѕРїСЂРѕСЃРѕРІ Рё СЃРѕС…СЂР°РЅРµРЅРёРµ РѕС‚РІРµС‚РѕРІ.",
    version="1.0.0",
)


@app.get("/health", summary="РџСЂРѕРІРµСЂРєР° Р·РґРѕСЂРѕРІСЊСЏ СЃРµСЂРІРёСЃР°")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(surveys_router)
app.include_router(answers_router)
