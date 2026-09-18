from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShoeLastSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_last_id: int
    last_code: str
    last_name: str
    last_type: str
    gender_category: str | None
    size_system: str


class ShoeModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_model_id: int
    shoe_last_id: int
    model_code: str
    model_name: str
    footwear_category: str
    footwear_type: str | None
    target_group: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShoeModelDetailRead(ShoeModelRead):
    shoe_last: ShoeLastSummaryRead


class ShoeModelClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_model_class_id: int
    shoe_model_id: int
    construction_method_id: int
    class_code: str
    class_name: str
    quality_level: str | None
    warranty_months: int | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
