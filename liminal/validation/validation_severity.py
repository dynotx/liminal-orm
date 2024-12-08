from liminal.base.str_enum import StrEnum


class ValidationSeverity(StrEnum):
    """This enum represents the different levels of validation that can be returned by Liminal."""

    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"
    UNEXPECTED = "UNEXPECTED"
