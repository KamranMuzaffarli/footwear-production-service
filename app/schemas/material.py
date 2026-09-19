from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MaterialCategorySummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_category_id: int
    material_category_code: str
    material_category_name: str


class MaterialAttributeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_attribute_id: int
    material_attribute_code: str
    material_attribute_name: str
    value_type: str
    unit_of_measure: str | None
    description: str | None
    is_active: bool


class MaterialAttributeValueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_attribute_value_id: int
    material_id: int
    material_attribute_id: int

    value_text: str | None
    value_numeric: Decimal | None
    value_boolean: bool | None

    description: str | None
    created_at: datetime
    updated_at: datetime

    attribute: MaterialAttributeRead


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_id: int
    material_category_id: int
    material_code: str
    material_name: str
    unit_of_measure: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MaterialDetailRead(MaterialRead):
    category: MaterialCategorySummaryRead
    attribute_values: list[MaterialAttributeValueRead]
