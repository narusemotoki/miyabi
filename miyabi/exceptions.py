class MiyabiError(Exception):
    pass


class ValidationError(MiyabiError):
    pass


class ResponseValidationError(ValidationError):
    pass


class DefinitionError(MiyabiError):
    pass
