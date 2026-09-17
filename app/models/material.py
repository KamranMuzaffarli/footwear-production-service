from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from app.models.shoe_model import ShoeModelClass


class MaterialCategory(Base):
    __tablename__ = "material_categories"
    __table_args__ = (
        UniqueConstraint(
            "material_category_code",
            name="material_categories_material_category_code_key",
        ),
        {"schema": "public"},
    )

    material_category_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    material_category_code: Mapped[str] = mapped_column(String(40), nullable=False)
    material_category_name: Mapped[str] = mapped_column(String(80), nullable=False)
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

    materials: Mapped[list["Material"]] = relationship(
        back_populates="category",
    )


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (
        UniqueConstraint("material_code", name="materials_material_code_key"),
        {"schema": "public"},
    )

    material_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    material_category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.material_categories.material_category_id",
            name="fk_materials_material_category",
        ),
        nullable=False,
    )
    material_code: Mapped[str] = mapped_column(String(80), nullable=False)
    material_name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
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

    category: Mapped[MaterialCategory] = relationship(
        back_populates="materials",
    )
    attribute_values: Mapped[list["MaterialAttributeValue"]] = relationship(
        back_populates="material",
    )
    compositions: Mapped[list["ShoeModelClassMaterial"]] = relationship(
        back_populates="material",
    )


class MaterialAttribute(Base):
    __tablename__ = "material_attributes"
    __table_args__ = (
        UniqueConstraint(
            "material_attribute_code",
            name="material_attributes_material_attribute_code_key",
        ),
        CheckConstraint(
            "value_type IN ('text', 'numeric', 'boolean')",
            name="chk_material_attributes_value_type",
        ),
        {"schema": "public"},
    )

    material_attribute_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    material_attribute_code: Mapped[str] = mapped_column(String(40), nullable=False)
    material_attribute_name: Mapped[str] = mapped_column(String(80), nullable=False)
    value_type: Mapped[str] = mapped_column(String(30), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
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

    values: Mapped[list["MaterialAttributeValue"]] = relationship(
        back_populates="attribute",
    )


class MaterialAttributeValue(Base):
    __tablename__ = "material_attribute_values"
    __table_args__ = (
        UniqueConstraint(
            "material_id",
            "material_attribute_id",
            name="uq_material_attribute_values_material_attribute",
        ),
        CheckConstraint(
            "((value_text IS NOT NULL)::integer "
            "+ (value_numeric IS NOT NULL)::integer "
            "+ (value_boolean IS NOT NULL)::integer) = 1",
            name="chk_material_attribute_values_single_value",
        ),
        {"schema": "public"},
    )

    material_attribute_value_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    material_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.materials.material_id",
            name="fk_material_attribute_values_material",
        ),
        nullable=False,
    )
    material_attribute_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.material_attributes.material_attribute_id",
            name="fk_material_attribute_values_attribute",
        ),
        nullable=False,
    )
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_numeric: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    material: Mapped[Material] = relationship(
        back_populates="attribute_values",
    )
    attribute: Mapped[MaterialAttribute] = relationship(
        back_populates="values",
    )


class MaterialUsageRole(Base):
    __tablename__ = "material_usage_roles"
    __table_args__ = (
        UniqueConstraint(
            "material_role_code",
            name="material_usage_roles_material_role_code_key",
        ),
        {"schema": "public"},
    )

    material_usage_role_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    material_role_code: Mapped[str] = mapped_column(String(40), nullable=False)
    material_role_name: Mapped[str] = mapped_column(String(80), nullable=False)
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

    compositions: Mapped[list["ShoeModelClassMaterial"]] = relationship(
        back_populates="usage_role",
    )


class ShoeModelClassMaterial(Base):
    __tablename__ = "shoe_model_class_materials"
    __table_args__ = (
        UniqueConstraint(
            "shoe_model_class_id",
            "material_id",
            "material_usage_role_id",
            name="uq_shoe_model_class_materials_class_material_role",
        ),
        {"schema": "public"},
    )

    shoe_model_class_material_id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=False),
        primary_key=True,
    )
    shoe_model_class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.shoe_model_classes.shoe_model_class_id",
            name="fk_shoe_model_class_materials_model_class",
        ),
        nullable=False,
    )
    material_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.materials.material_id",
            name="fk_shoe_model_class_materials_material",
        ),
        nullable=False,
    )
    material_usage_role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "public.material_usage_roles.material_usage_role_id",
            name="fk_shoe_model_class_materials_usage_role",
        ),
        nullable=False,
    )
    consumption_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    consumption_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
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

    shoe_model_class: Mapped[ShoeModelClass] = relationship()
    material: Mapped[Material] = relationship(
        back_populates="compositions",
    )
    usage_role: Mapped[MaterialUsageRole] = relationship(
        back_populates="compositions",
    )
