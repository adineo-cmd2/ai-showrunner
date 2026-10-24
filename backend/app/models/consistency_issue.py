from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConsistencyIssue(Base):
    __tablename__ = "consistency_issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(Integer, ForeignKey("stories.id"), index=True)
    episode_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("episodes.id"), nullable=True, index=True
    )
    severity: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(60))
    detail: Mapped[str] = mapped_column(Text, default="")
    passage: Mapped[str] = mapped_column(Text, default="")
