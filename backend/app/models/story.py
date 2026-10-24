from sqlalchemy import String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    genre: Mapped[str] = mapped_column(String(100), default="")
    setting: Mapped[str] = mapped_column(Text, default="")
    setting_rules: Mapped[list] = mapped_column(JSON, default=list)
