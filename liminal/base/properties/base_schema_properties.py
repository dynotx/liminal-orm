from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from liminal.enums import BenchlingEntityType, BenchlingNamingStrategy


class MixtureSchemaConfig(BaseModel):
    """
    This class is used to define the properties of a mixture schema within our code and when retrieving data from the benchling api.
    It is only used when the entity schema type is Mixture.
    It can either be storage, text, or both if allowMeasuredIngredients is True. Otherwise, both must be false.

    Parameters
    ----------
    allowMeasuredIngredients : bool | None
        Whether the mixture schema allows measured ingredients.
    componentLotStorageEnabled : bool | None
        Whether the mixture schema allows component lot storage.
    componentLotTextEnabled : bool | None
        Whether the mixture schema allows component lot text.
    """

    allowMeasuredIngredients: bool = False
    componentLotStorageEnabled: bool | None = None
    componentLotTextEnabled: bool | None = None

    @model_validator(mode="after")
    def validate_mixture_schema_config(self) -> MixtureSchemaConfig:
        if self.allowMeasuredIngredients:
            if not (self.componentLotStorageEnabled or self.componentLotTextEnabled):
                raise ValueError(
                    "If allowMeasuredIngredients is True, either componentLotStorageEnabled or componentLotTextEnabled must be True."
                )
        elif self.allowMeasuredIngredients is False:
            if self.componentLotStorageEnabled or self.componentLotTextEnabled:
                raise ValueError(
                    "If allowMeasuredIngredients is False, both componentLotStorageEnabled and componentLotTextEnabled must be False."
                )
        return self


class BaseSchemaProperties(BaseModel):
    """
    This class is the generic class for defining the Benchling entity schema properties, where all fields are optional.
    It is used to create a diff between the old and new schema properties.

    Parameters
    ----------
    name : str | None
        The name of the schema.
    warehouse_name : str | None
       The sql table name of the schema in the benchling warehouse.
    prefix : str | None
        The prefix to use for the schema.
    entity_type : BenchlingEntityType | None
        The entity type of the schema.
    mixture_schema_config : MixtureSchemaConfig | None
        The mixture schema config of the schema.
    _archived : bool | None
        Whether the schema is archived in Benchling.
    """

    name: str | None = None
    warehouse_name: str | None = None
    prefix: str | None = None
    entity_type: BenchlingEntityType | None = None
    naming_strategies: set[BenchlingNamingStrategy] | None = None
    mixture_schema_config: MixtureSchemaConfig | None = None
    _archived: bool | None = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._archived = data.get("_archived", None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def merge(self, new_props: BaseSchemaProperties) -> dict[str, Any]:
        """Creates a diff between the current schema properties and the new schema properties.
        Sets value to None if the values are equal, otherwise sets the value to the new value.

        Parameters
        ----------
        new_props : Benchling BaseSchemaProperties
            The new schema properties.

        Returns
        -------
        dict[str, Any]
            A dictionary of the differences between the old and new schema properties.
        """
        diff = {}
        for new_field_name, new_val in new_props.model_dump().items():
            if getattr(self, new_field_name) != new_val:
                diff[new_field_name] = new_val
        return diff

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseSchemaProperties):
            return False
        return self.model_dump() == other.model_dump()

    def __str__(self) -> str:
        return ", ".join(
            [f"{k}={v}" for k, v in self.model_dump(exclude_unset=True).items()]
        )

    def __repr__(self) -> str:
        """Generates a string representation of the class so that it can be executed."""
        return f"{self.__class__.__name__}({', '.join([f'{k}={v.__repr__()}' for k, v in self.model_dump(exclude_defaults=True).items()])})"
