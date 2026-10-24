from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import bible, episodes, stories, suggest
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

import app.models.user  # noqa: F401 register tables
import app.models.story  # noqa: F401
import app.models.character  # noqa: F401
import app.models.location  # noqa: F401
import app.models.timeline_event  # noqa: F401
import app.models.plot_thread  # noqa: F401
import app.models.episode  # noqa: F401
import app.models.consistency_issue  # noqa: F401
import app.models.bible_change  # noqa: F401

Base.metadata.create_all(bind=engine)

settings = get_settings()

app = FastAPI(title="AI Showrunner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:4325"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"ok": True}


app.include_router(stories.router, prefix="/api/story", tags=["story"])
app.include_router(bible.router, prefix="/api/story", tags=["bible"])
app.include_router(episodes.router, prefix="/api/story", tags=["episodes"])
app.include_router(suggest.router, prefix="/api/story", tags=["suggest"])
