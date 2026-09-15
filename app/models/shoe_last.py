from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ShoeLast(Base):
    __tablename__ = "shoe_lasts"
    __table_args__ = (
        UniqueConstraint("last_code", name="shoe_lasts_last_code_key"),
        {"schema": "public"},
    )

    shoe_last_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    last_code: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(40), nullable=False)
    last_type: Mapped[str] = mapped_column(String(40), nullable=False)
    gender_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    size_system: Mapped[str] = mapped_column(String(20), nullable=False)
    base_size: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    toe_shape: Mapped[str | None] = mapped_column(String(40), nullable=True)
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

    sizes: Mapped[list[ShoeLastSize]] = relationship(
        back_populates="shoe_last",
    )


class ShoeLastSize(Base):
    __tablename__ = "shoe_last_sizes"
    __table_args__ = (
        UniqueConstraint(
            "shoe_last_id",
            "size_value",
            name="uq_shoe_last_sizes_shoe_last_size",
        ),
        {"schema": "public"},
    )

    shoe_last_size_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    shoe_last_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.shoe_lasts.shoe_last_id",
            name="fk_shoe_last_sizes_shoe_last",
        ),
        nullable=False,
    )
    size_value: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    heel_height_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 1),
        nullable=True,
    )
    instep_height_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 1),
        nullable=True,
    )
    ball_girth_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 1),
        nullable=True,
    )
    waist_girth_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 1),
        nullable=True,
    )
    last_length_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 1),
        nullable=True,
    )
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

    shoe_last: Mapped[ShoeLast] = relationship(
        back_populates="sizes",
    )
    