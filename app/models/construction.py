from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Identity, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ShoeConstructionMethod(Base):
    __tablename__ = "shoe_construction_methods"
    __table_args__ = (
        UniqueConstraint(
            "construction_method_code",
            name="shoe_construction_methods_construction_method_code_key",
        ),
        {"schema": "public"},
    )

    construction_method_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    construction_method_code: Mapped[str] = mapped_column(String(40), nullable=False)
    construction_method_name: Mapped[str] = mapped_column(String(80), nullable=False)
    difficulty_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    model_classes: Mapped[list["ShoeModelClass"]] = relationship(
        back_populates="construction_method",
    )
