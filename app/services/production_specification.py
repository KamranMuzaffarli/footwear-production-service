from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.repositories.production_specification import (
    get_model_class_specification,
)
from app.schemas.production_specification import (
    ProductionSpecificationRead,
    SpecificationCompositionItem,
    SpecificationConstructionMethod,
    SpecificationModelClass,
    SpecificationShoeModel,
    SpecificationValidationIssue,
)


async def get_production_specification(
    session: AsyncSession,
    shoe_model_class_id: int,
) -> ProductionSpecificationRead:
    model_class = await get_model_class_specification(
        session,
        shoe_model_class_id,
    )

    if model_class is None:
        raise EntityNotFoundError("Model Class not found")

    shoe_model = model_class.shoe_model
    shoe_last = shoe_model.shoe_last
    construction_method = model_class.construction_method
    compositions = model_class.compositions

    validation_issues: list[SpecificationValidationIssue] = []

    if not shoe_model.is_active:
        validation_issues.append(
            SpecificationValidationIssue(
                code="inactive_shoe_model",
                message="Shoe Model is not active",
            )
        )

    if not model_class.is_active:
        validation_issues.append(
            SpecificationValidationIssue(
                code="inactive_model_class",
                message="Model Class is not active",
            )
        )

    if not shoe_last.is_active:
        validation_issues.append(
            SpecificationValidationIssue(
                code="inactive_shoe_last",
                message="Shoe Last is not active",
            )
        )

    if not construction_method.is_active:
        validation_issues.append(
            SpecificationValidationIssue(
                code="inactive_construction_method",
                message="Construction Method is not active",
            )
        )

    if not compositions:
        validation_issues.append(
            SpecificationValidationIssue(
                code="no_active_composition",
                message="Model Class has no active Production Composition",
            )
        )

    for composition in compositions:
        composition_id = (
            composition.shoe_model_class_material_id
        )

        if not composition.material.is_active:
            validation_issues.append(
                SpecificationValidationIssue(
                    code="inactive_material",
                    message=(
                        f"Composition {composition_id} uses "
                        "an inactive Material"
                    ),
                )
            )

        if not composition.usage_role.is_active:
            validation_issues.append(
                SpecificationValidationIssue(
                    code="inactive_usage_role",
                    message=(
                        f"Composition {composition_id} uses "
                        "an inactive Usage Role"
                    ),
                )
            )

        if composition.consumption_quantity is None:
            validation_issues.append(
                SpecificationValidationIssue(
                    code="missing_consumption_quantity",
                    message=(
                        f"Composition {composition_id} is missing "
                        "consumption quantity"
                    ),
                )
            )

        elif composition.consumption_quantity <= 0:
            validation_issues.append(
                SpecificationValidationIssue(
                    code="invalid_consumption_quantity",
                    message=(
                        f"Composition {composition_id} has "
                        "a non-positive consumption quantity"
                    ),
                )
            )

        if (
            composition.consumption_unit is None
            or not composition.consumption_unit.strip()
        ):
            validation_issues.append(
                SpecificationValidationIssue(
                    code="missing_consumption_unit",
                    message=(
                        f"Composition {composition_id} is missing "
                        "consumption unit"
                    ),
                )
            )

    return ProductionSpecificationRead(
        shoe_model=SpecificationShoeModel.model_validate(
            shoe_model
        ),
        model_class=SpecificationModelClass.model_validate(
            model_class
        ),
        construction_method=(
            SpecificationConstructionMethod.model_validate(
                construction_method
            )
        ),
        composition=[
            SpecificationCompositionItem.model_validate(
                composition
            )
            for composition in compositions
        ],
        is_production_ready=not validation_issues,
        validation_issues=validation_issues,
    )
