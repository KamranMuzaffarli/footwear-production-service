from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ShoeLastRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_last_id: int
    last_code: str
    last_name: str
    last_type: str
    gender_category: str | None
    size_system: str
    base_size: Decimal
    toe_shape: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShoeLastSizeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_last_size_id: int
    shoe_last_id: int
    size_value: Decimal
    heel_height_mm: Decimal | None
    instep_height_mm: Decimal | None
    ball_girth_mm: Decimal | None
    waist_girth_mm: Decimal | None
    last_length_mm: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShoeLastDetailRead(ShoeLastRead):
    sizes: list[ShoeLastSizeRead]
