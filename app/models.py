from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    notion_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("pages.id"), nullable=True)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    synced_at: Mapped[datetime] = mapped_column(server_default=func.now())

    blocks: Mapped[list["Block"]] = relationship(
        back_populates="page", cascade="all, delete-orphan"
    )
    change_logs: Mapped[list["ChangeLogEntry"]] = relationship(back_populates="page")


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    page_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    block_type: Mapped[str] = mapped_column(Text, nullable=False)
    plain_text: Mapped[str | None] = mapped_column(Text)
    checked: Mapped[bool | None] = mapped_column(Boolean)
    indent_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    synced_at: Mapped[datetime] = mapped_column(server_default=func.now())

    page: Mapped["Page"] = relationship(back_populates="blocks")


class ChangeLogEntry(Base):
    __tablename__ = "change_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_time: Mapped[datetime] = mapped_column(server_default=func.now())
    page_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pages.id"), nullable=False)
    change_type: Mapped[str] = mapped_column(Text, nullable=False)
    old_hash: Mapped[str | None] = mapped_column(Text)
    new_hash: Mapped[str | None] = mapped_column(Text)
    detail: Mapped[str | None] = mapped_column(Text)

    page: Mapped["Page"] = relationship(back_populates="change_logs")
