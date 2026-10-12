from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

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
    naming_strategies : set[BenchlingNamingStrategy] = {BenchlingNamingStrategy.NEW_IDS, BenchlingNamingStrategy.IDS_FROM_NAMES, BenchlingNamingStrategy.REPLACE_NAME_WITH_ID}
        The naming strategies of the schema. If left empty, the default is set to Benchling's default initial naming strategies.
    mixture_schema_config : MixtureSchemaConfig | None = None
        The mixture schema config of the schema.
    use_registry_id_as_label : bool | None = False
        Flag for configuring the chip label for entities. Determines if the chip will use the Registry ID as the main label for items.
    include_registry_id_in_chips : bool | None = False
        Flag for configuring the chip label for entities. Determines if the chip will include the Registry ID in the chip label.
    constraint_fields : set[str] = set()
        Set of constraints for field values for the schema. Must be a set of warehouse column names. This specifies that their entity field values must be a unique combination within an entity.
        The following sequence constraints are also supported:
        - bases: only supported for nucleotide sequence entity types. hasUniqueResidues=True
        - amino_acids_ignore_case: only supported for amino acid sequence entity types. hasUniqueResidues=True
        - amino_acids_exact_match: only supported for amino acid sequence entity types. hasUniqueResidues=True, areUniqueResiduesCaseSensitive=True
    show_bases_in_expanded_view : bool | None = None
        Whether the bases should be shown in the expanded view of the entity.
    _archived : bool = False
        Whether the schema is archived in Benchling.
    """

    name: str
    warehouse_name: str
    prefix: str
    entity_type: BenchlingEntityType
    naming_strategies: set[BenchlingNamingStrategy] = {
        BenchlingNamingStrategy.NEW_IDS,
        BenchlingNamingStrategy.IDS_FROM_NAMES,
        BenchlingNamingStrategy.REPLACE_NAME_WITH_ID,
    }
    use_registry_id_as_label: bool | None = False
    include_registry_id_in_chips: bool | None = False
    mixture_schema_config: MixtureSchemaConfig | None = None
    constraint_fields: set[str] = Field(default_factory=set)
    show_bases_in_expanded_view: bool | None = False
    _archived: bool = False

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._archived = data.get("_archived", False)

    @staticmethod
    def unsupported_schema_properties(entity_type: BenchlingEntityType) -> set[str]:
        """Returns the fields that Benchling does not support for the given entity type."""
        if entity_type == BenchlingEntityType.ENTRY:
            return {
                "naming_strategies",
                "use_registry_id_as_label",
                "include_registry_id_in_chips",
                "constraint_fields",
                "show_bases_in_expanded_view",
            }
        if not entity_type.is_sequence():
            return {"show_bases_in_expanded_view"}
        return set()

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
        is_valid_wh_name(self.warehouse_name)
        is_valid_prefix(self.prefix)
        return self

    @model_validator(mode="after")
    def validate_supported_properties(self) -> SchemaProperties:
        unsupported_properties = self.unsupported_schema_properties(self.entity_type)
        explicitly_set = {
            f
            for f in unsupported_properties.intersection(self.model_fields_set)
            if getattr(self, f) is not None
        }
        if explicitly_set:
            raise ValueError(
                f"{', '.join(sorted(explicitly_set))} cannot be set for {self.entity_type} schemas."
            )
        return self

    def set_archived(self, value: bool) -> SchemaProperties:
        self._archived = value
        return self
