from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SpecificationValidationIssue(BaseModel):
    code: str
    message: str


class SpecificationShoeLast(BaseModel):
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


class SpecificationShoeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_model_id: int
    model_code: str
    model_name: str
    footwear_category: str
    footwear_type: str | None
    target_group: str
    description: str | None
    is_active: bool

    shoe_last: SpecificationShoeLast


class SpecificationConstructionMethod(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    construction_method_id: int
    construction_method_code: str
    construction_method_name: str
    difficulty_level: str | None
    description: str | None
    is_active: bool


class SpecificationModelClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_model_class_id: int
    class_code: str
    class_name: str
    quality_level: str | None
    warranty_months: int | None
    description: str | None
    is_active: bool


class SpecificationMaterialCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_category_id: int
    material_category_code: str
    material_category_name: str
    description: str | None
    is_active: bool


class SpecificationMaterialAttributeDefinition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_attribute_id: int
    material_attribute_code: str
    material_attribute_name: str
    value_type: str
    unit_of_measure: str | None
    description: str | None
    is_active: bool


class SpecificationMaterialAttributeValue(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_attribute_value_id: int
    value_text: str | None
    value_numeric: Decimal | None
    value_boolean: bool | None
    description: str | None

    attribute: SpecificationMaterialAttributeDefinition


class SpecificationMaterial(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_id: int
    material_code: str
    material_name: str
    unit_of_measure: str
    description: str | None
    is_active: bool

    category: SpecificationMaterialCategory
    attribute_values: list[SpecificationMaterialAttributeValue]


class SpecificationUsageRole(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_usage_role_id: int
    material_role_code: str
    material_role_name: str
    description: str | None
    is_active: bool


class SpecificationCompositionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shoe_model_class_material_id: int
    consumption_quantity: Decimal | None
    consumption_unit: str | None
    is_required: bool
    description: str | None

    material: SpecificationMaterial
    usage_role: SpecificationUsageRole


class ProductionSpecificationRead(BaseModel):
    shoe_model: SpecificationShoeModel
    model_class: SpecificationModelClass
    construction_method: SpecificationConstructionMethod
    composition: list[SpecificationCompositionItem]

    is_production_ready: bool
    validation_issues: list[SpecificationValidationIssue]
