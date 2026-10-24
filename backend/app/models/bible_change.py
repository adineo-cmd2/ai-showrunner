from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BibleChange(Base):
    __tablename__ = "bible_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(Integer, ForeignKey("stories.id"), index=True)
    episode_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("episodes.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
