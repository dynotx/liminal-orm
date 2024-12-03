import inspect
from datetime import datetime
from functools import wraps
from typing import Callable

from pydantic import ConfigDict

from liminal.orm.base_model import BaseModel
from liminal.validation.validation_report_level import ValidationReportLevel


class BenchlingValidatorReport(BaseModel):
    """
    Represents a report generated by a Benchling validator.

    Attributes
    ----------
    valid : bool
        Indicates whether the validation passed or failed.
    model : str
        The name of the model being validated. (eg: NGSSample)
    level : BenchlingReportLevel
        The severity level of the validation report.
    validator_name : str | None
        The name of the validator that generated this report. (eg: BioContextValidator)
    entity_id : str | None
        The ID of the entity being validated.
    registry_id : str | None
        The ID of the registry associated with the entity.
    entity_name : str | None
        The name of the entity being validated.
    message : str | None
        A message describing the result of the validation.
    creator_name : str | None
        The name of the creator of the entity being validated.
    creator_email : str | None
        The email of the creator of the entity being validated.
    updated_date : datetime | None
        The date the entity was last updated.
    **kwargs: Any
        Additional metadata to include in the report.
    """

    valid: bool
    model: str
    level: ValidationReportLevel
    validator_name: str | None = None
    entity_id: str | None = None
    registry_id: str | None = None
    entity_name: str | None = None
    web_url: str | None = None
    message: str | None = None
    creator_name: str | None = None
    creator_email: str | None = None
    updated_date: datetime | None = None

    model_config = ConfigDict(extra="allow")


def _create_validation_report(
    valid: bool,
    level: ValidationReportLevel,
    entity: type[BaseModel],
    validator_name: str,
    message: str | None = None,
) -> BenchlingValidatorReport:
    """Creates a BenchlingValidatorReport with the given parameters."""
    return BenchlingValidatorReport(
        valid=valid,
        level=level,
        model=entity.__class__.__name__,
        validator_name=validator_name,
        entity_id=entity.id,
        registry_id=entity.file_registry_id,
        entity_name=entity.name,
        web_url=entity.url,
        creator_name=entity.creator.name if entity.creator else None,
        creator_email=entity.creator.email if entity.creator else None,
        updated_date=entity.modified_at,
        message=message,
    )


class LiminalValidationError(Exception):
    """An exception that is raised when a validation error occurs."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def liminal_validator(
    validator_name: str,
    validator_level: ValidationReportLevel,
) -> Callable:
    """A decorator that validates a function that takes a Benchling entity as an argument and returns None.

    Parameters:
        validator_name: The name of the validator.
        validator_level: The level of the validator.
    """

    def decorator(func: Callable[[type[BaseModel]], None]) -> Callable:
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        if not params or params[0].name != "self" or len(params) > 1:
            raise TypeError("The only argument to this validator must be 'self'.")

        if params[0].annotation is not type[BaseModel]:
            raise TypeError(
                "The only argument to this validator must be a Benchling entity."
            )

        if sig.return_annotation is not None:
            raise TypeError("The return type must be None.")

        @wraps(func)
        def wrapper(self: type[BaseModel]) -> BenchlingValidatorReport:
            try:
                func(self)
            except LiminalValidationError as e:
                return _create_validation_report(
                    valid=False,
                    level=validator_level,
                    entity=self,
                    validator_name=validator_name,
                    message=e.message,
                )
            return _create_validation_report(
                valid=True,
                level=validator_level,
                entity=self,
                validator_name=validator_name,
            )

        return wrapper

    return decorator
