from http import HTTPStatus


class ApplicationError(Exception):
    status_code: int
    code: str

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BusinessRuleError(ApplicationError):
    status_code = HTTPStatus.BAD_REQUEST
    code = "business_rule_violation"


class EntityNotFoundError(ApplicationError):
    status_code = HTTPStatus.NOT_FOUND
    code = "entity_not_found"


class ConflictError(ApplicationError):
    status_code = HTTPStatus.CONFLICT
    code = "conflict"
