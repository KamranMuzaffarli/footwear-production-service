from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConstructionMethodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    construction_method_id: int
    construction_method_code: str
    construction_method_name: str
    difficulty_level: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MaterialCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_category_id: int
    material_category_code: str
    material_category_name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MaterialUsageRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_usage_role_id: int
    material_role_code: str
    material_role_name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
