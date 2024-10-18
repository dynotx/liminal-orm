from __future__ import annotations

from pydantic import PrivateAttr, model_validator

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
    """

    name: str
    warehouse_name: str
    prefix: str
    entity_type: BenchlingEntityType
    naming_strategies: set[BenchlingNamingStrategy]
    mixture_schema_config: MixtureSchemaConfig | None = None
    _archived: bool | None = PrivateAttr(default=None)

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
        # TODO:if naming_strategies contains SET_FROM_NAME_PARTS or REPLACE_NAMES_FROM_PARTS, name template for schema must be set
        return self

    def set_archived(self, value: bool) -> SchemaProperties:
        self._archived = value
        return self
