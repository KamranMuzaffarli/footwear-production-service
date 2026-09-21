from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.material import MaterialRead
from app.schemas.reference import MaterialUsageRoleRead


class ProductionCompositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_model_class_material_id: int
    shoe_model_class_id: int
    material_id: int
    material_usage_role_id: int
    consumption_quantity: Decimal | None
    consumption_unit: str | None
    is_required: bool
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    material: MaterialRead
    usage_role: MaterialUsageRoleRead


class ProductionCompositionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: int
    material_usage_role_id: int
    consumption_quantity: Decimal | None = Field(default=None, gt=0)
    consumption_unit: str | None = Field(default=None, max_length=20)
    is_required: bool = True
    description: str | None = None


class ProductionCompositionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consumption_quantity: Decimal | None = Field(default=None, gt=0)
    consumption_unit: str | None = Field(default=None, max_length=20)
    is_required: bool | None = None
    description: str | None = None

    @field_validator("is_required")
    @classmethod
    def reject_null_for_is_required(cls, value):
        if value is None:
            raise ValueError("Field may not be null")
        return value
