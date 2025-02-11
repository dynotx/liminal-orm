from datetime import datetime
from functools import partial, wraps
from typing import TYPE_CHECKING, Any, Callable

from pydantic import BaseModel, ConfigDict

from liminal.utils import pascalize
from liminal.validation.validation_severity import ValidationSeverity

if TYPE_CHECKING:
    from liminal.orm.base_model import BaseModel as BenchlingBaseModel


class BenchlingValidatorReport(BaseModel):
    """
    Represents a report generated by a Benchling validator.

    Attributes
    ----------
    valid : bool
        Indicates whether the validation passed or failed.
    model : str
        The name of the model being validated. (eg: NGSSample)
    level : ValidationSeverity
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
    level: ValidationSeverity
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

    @classmethod
    def create_validation_report(
        cls,
        valid: bool,
        level: ValidationSeverity,
        entity: type["BenchlingBaseModel"],
        validator_name: str,
        message: str | None = None,
        **kwargs: Any,
    ) -> "BenchlingValidatorReport":
        """Creates a BenchlingValidatorReport with the given parameters.

        Parameters
        ----------
        valid: bool
            Indicates whether the validation passed or failed.
        level: ValidationSeverity
            The severity level of the validation report.
        entity: type[BenchlingBaseModel]
            The entity being validated.
        validator_name: str
            The name of the validator that generated this report.
        message: str | None
            A message describing the result of the validation.
        """
        return cls(
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
            **kwargs,
        )


def liminal_validator(
    func: Callable[["BenchlingBaseModel"], BenchlingValidatorReport | None]
    | None = None,
    *,
    validator_level: ValidationSeverity = ValidationSeverity.LOW,
    validator_name: str | None = None,
) -> Callable:
    """A decorator for a function that validates a Benchling entity, defined on a schema class.
    Can be used with or without parameters. Wraps around any exceptions raised by the validator function,
    and returns a BenchlingValidatorReport.

    Parameters
    ----------
    validator_level: ValidationSeverity
        The severity level of the validation report. Defaults to ValidationSeverity.LOW.
    validator_name: str | None
        The name of the validator. Defaults to the PascalCase version of the function name.
    """
    if func is None:
        return partial(
            liminal_validator,
            validator_level=validator_level,
            validator_name=validator_name,
        )

    @wraps(func)
    def wrapper(self: "BenchlingBaseModel") -> BenchlingValidatorReport:
        """Wrapper that runs the validator function and returns a BenchlingValidatorReport."""
        try:
            ret_val = func(self)
            if type(ret_val) is BenchlingValidatorReport:
                return ret_val
        except Exception as e:
            return BenchlingValidatorReport.create_validation_report(
                valid=False,
                level=validator_level,
                entity=self,
                validator_name=validator_name or pascalize(func.__name__),
                message=str(e),
            )
        return BenchlingValidatorReport.create_validation_report(
            valid=True,
            level=validator_level,
            entity=self,
            validator_name=validator_name or pascalize(func.__name__),
        )

    setattr(wrapper, "_is_liminal_validator", True)
    return wrapper
