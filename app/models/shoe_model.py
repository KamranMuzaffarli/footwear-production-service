from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.shoe_last import ShoeLast
from app.models.construction import ShoeConstructionMethod


class ShoeModel(Base):
    __tablename__ = "shoe_models"
    __table_args__ = (
        UniqueConstraint("model_code", name="shoe_models_model_code_key"),
        {"schema": "public"},
    )

    shoe_model_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    shoe_last_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.shoe_lasts.shoe_last_id",
            name="fk_shoe_models_shoe_last",
        ),
        nullable=False,
    )
    model_code: Mapped[str] = mapped_column(String(60), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
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
    footwear_category: Mapped[str] = mapped_column(String(80), nullable=False)
    footwear_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_group: Mapped[str] = mapped_column(String(40), nullable=False)

    shoe_last: Mapped[ShoeLast] = relationship(
        back_populates="shoe_models",
    )
    model_classes: Mapped[list[ShoeModelClass]] = relationship(
        back_populates="shoe_model",
    )


class ShoeModelClass(Base):
    __tablename__ = "shoe_model_classes"
    __table_args__ = (
        UniqueConstraint(
            "shoe_model_id",
            "class_code",
            name="uq_shoe_model_classes_model_class",
        ),
        {"schema": "public"},
    )

    shoe_model_class_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    shoe_model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.shoe_models.shoe_model_id",
            name="fk_shoe_model_classes_shoe_model",
        ),
        nullable=False,
    )
    construction_method_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.shoe_construction_methods.construction_method_id",
            name="fk_shoe_model_classes_construction_method",
        ),
        nullable=False,
    )
    class_code: Mapped[str] = mapped_column(String(40), nullable=False)
    class_name: Mapped[str] = mapped_column(String(80), nullable=False)
    quality_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    warranty_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
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

    shoe_model: Mapped[ShoeModel] = relationship(
        back_populates="model_classes",
    )

    construction_method: Mapped[ShoeConstructionMethod] = relationship(
        back_populates="model_classes",
    )

    compositions: Mapped[list["ShoeModelClassMaterial"]] = relationship(
        "ShoeModelClassMaterial",
        back_populates="shoe_model_class",
    )
