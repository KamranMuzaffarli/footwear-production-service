from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class ShoeModelCreate(BaseModel):
    shoe_last_id: int
    model_code: str = Field(max_length=60)
    model_name: str = Field(max_length=100)
    footwear_category: str = Field(max_length=80)
    footwear_type: str | None = Field(default=None, max_length=80)
    target_group: str = Field(max_length=40)
    description: str | None = None
    is_active: bool = True


class ShoeModelUpdate(BaseModel):
    shoe_last_id: int | None = None
    model_code: str | None = Field(default=None, max_length=60)
    model_name: str | None = Field(default=None, max_length=100)
    footwear_category: str | None = Field(default=None, max_length=80)
    footwear_type: str | None = Field(default=None, max_length=80)
    target_group: str | None = Field(default=None, max_length=40)
    description: str | None = None
    is_active: bool | None = None

    @field_validator(
        "shoe_last_id",
        "model_code",
        "model_name",
        "footwear_category",
        "target_group",
        "is_active",
    )
    @classmethod
    def reject_null_for_non_nullable_fields(cls, value):
        if value is None:
            raise ValueError("Field may not be null")
        return value


class ShoeModelClassCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_code: str = Field(max_length=40)
    class_name: str = Field(max_length=80)
    construction_method_id: int
    quality_level: str | None = Field(default=None, max_length=40)
    warranty_months: int | None = None
    description: str | None = None
    is_active: bool = True


class ShoeModelClassClone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_code: str = Field(max_length=40)
    class_name: str = Field(max_length=80)


class ShoeModelClassUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    construction_method_id: int | None = None
    quality_level: str | None = Field(default=None, max_length=40)
    warranty_months: int | None = None
    is_active: bool | None = None

    @field_validator(
        "construction_method_id",
        "is_active",
    )
    @classmethod
    def reject_null_for_non_nullable_fields(cls, value):
        if value is None:
            raise ValueError("Field may not be null")
        return value
