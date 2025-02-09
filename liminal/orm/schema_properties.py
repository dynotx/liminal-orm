from __future__ import annotations

from typing import Any

from pydantic import model_validator

from liminal.base.properties.base_schema_properties import (
    BaseSchemaProperties,
    MixtureSchemaConfig,
)
from liminal.enums import BenchlingEntityType, BenchlingNamingStrategy
from liminal.utils import is_valid_prefix, is_valid_wh_name


class SchemaProperties(BaseSchemaProperties):
    """
    This class is the validated class that is public facing and inherits from the BaseSchemaProperties class.
    It has the same fields as the BaseSchemaProperties class, but it is validated to ensure that the fields are valid.

    Parameters
    ----------
    name : str
        The name of the schema.
    warehouse_name : str
       The sql table name of the schema in the benchling warehouse.
    prefix : str
        The prefix to use for the schema.
    entity_type : BenchlingEntityType
        The entity type of the schema.
    naming_strategies : set[BenchlingNamingStrategy]
        The naming strategies of the schema.
    mixture_schema_config : MixtureSchemaConfig | None
        The mixture schema config of the schema.
    use_registry_id_as_label : bool | None = None
        Flag for configuring the chip label for entities. Determines if the chip will use the Registry ID as the main label for items.
    include_registry_id_in_chips : bool | None = None
        Flag for configuring the chip label for entities. Determines if the chip will include the Registry ID in the chip label.
    constraint_fields : set[str] | None
        Set of constraints for field values for the schema. Must be a set of column names that specify that their values must be a unique combination within an entity.
        If the entity type is a Sequence, "bases" can be a constraint field.
    _archived : bool | None
        Whether the schema is archived in Benchling.
    """

    name: str
    warehouse_name: str
    prefix: str
    entity_type: BenchlingEntityType
    naming_strategies: set[BenchlingNamingStrategy]
    use_registry_id_as_label: bool | None = False
    include_registry_id_in_chips: bool | None = False
    mixture_schema_config: MixtureSchemaConfig | None = None
    constraint_fields: set[str] | None = None
    _archived: bool = False

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._archived = data.get("_archived", False)

    @model_validator(mode="after")
    def validate_mixture_schema_config(self) -> SchemaProperties:
        if (
            self.entity_type == BenchlingEntityType.MIXTURE
            and self.mixture_schema_config is None
        ):
            raise ValueError(
                "Mixture schema config must be defined when entity type is Mixture."
            )
        if (
            self.mixture_schema_config
            and self.entity_type != BenchlingEntityType.MIXTURE
        ):
            raise ValueError(
                "The entity type is not a Mixture. Remove the mixture schema config."
            )

        if self.naming_strategies and len(self.naming_strategies) == 0:
            raise ValueError(
                "Schema must have at least 1 registry naming option enabled"
            )
        is_valid_wh_name(self.warehouse_name)
        is_valid_prefix(self.prefix)
        return self

    def set_archived(self, value: bool) -> SchemaProperties:
        self._archived = value
        return self
