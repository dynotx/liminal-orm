from functools import lru_cache
from typing import Any

from benchling_sdk.models import EntitySchema

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_id_name_map
from liminal.entity_schemas.entity_schema_models_v3 import (
    EntitySchemaFieldModel,
    EntitySchemaModel,
)
from liminal.entity_schemas.api_v3 import list_entity_schemas_v3
from liminal.enums import BenchlingNamingStrategy
from liminal.enums import (
    BenchlingLinkDefinitionType,
    SequenceConstraint,
    BenchlingEntityTypeName,
)
from liminal.mappers import (
    convert_entity_schema_type_to_entity_type,
    convert_field_definition_type_to_field_type,
)
from liminal.orm.name_template import NameTemplate
from liminal.orm.schema_properties import MixtureSchemaConfig, SchemaProperties
from liminal.unit_dictionary.utils import get_unit_id_to_name_map


def get_converted_entity_schemas(
    benchling_service: BenchlingService,
    include_archived: bool = False,
    wh_schema_names: set[str] | None = None,
    wh_schema_names_for_fields: set[str] | None = None,
) -> list[tuple[SchemaProperties, NameTemplate, dict[str, BaseFieldProperties]]]:
    """This functions gets all Entity schemas from Benchling and converts them to our internal representation of a schema and its fields.
    It parses the Entity Schema and creates SchemaProperties and a list of FieldProperties for each field in the schema.
    If include_archived is True, it will include archived schemas and archived fields.
    If wh_schema_names_for_fields is given, only those schemas have their fields fetched.
    If it is None, all schemas are fetched with their fields.
    """
    schemas_data = list_entity_schemas_v3(benchling_service, include_archived)
    entity_schema_id_to_name_map = {s["id"]: s["systemName"] for s in schemas_data}
    all_schemas = EntitySchemaModel.get_all(
        benchling_service,
        wh_schema_names,
        include_archived,
        wh_schema_names_for_fields=wh_schema_names_for_fields,
        schemas_data=schemas_data,
    )
    dropdown_id_to_name_map = get_benchling_dropdown_id_name_map(benchling_service)
    unit_id_to_name_map = get_unit_id_to_name_map(benchling_service)
    all_schemas = [s for s in all_schemas if s.systemName != "liminal_remote"]
    return [
        convert_entity_schema_to_internal_schema(
            entity_schema,
            entity_schema_id_to_name_map,
            dropdown_id_to_name_map,
            unit_id_to_name_map,
            include_archived,
            fields_fetched=wh_schema_names_for_fields is None
            or entity_schema.systemName in wh_schema_names_for_fields,
        )
        for entity_schema in all_schemas
    ]


def convert_entity_schema_to_internal_schema(
    entity_schema: EntitySchemaModel,
    entity_schema_id_to_name_map: dict[str, str],
    dropdown_id_to_name_map: dict[str, str],
    unit_id_to_name_map: dict[str, str],
    include_archived_fields: bool = False,
    fields_fetched: bool = True,
) -> tuple[SchemaProperties, NameTemplate, dict[str, BaseFieldProperties]]:
    all_fields = entity_schema.fields
    if not include_archived_fields:
        all_fields = [f for f in all_fields if not f.archived]
    constraint_fields: set[str] = set()
    entity_type = convert_entity_schema_type_to_entity_type(entity_schema.typename)
    if entity_schema.constraint:
        constraint_fields = constraint_fields.union(
            [n for n in entity_schema.constraint.fieldDefinitionNames]
        )
        if entity_schema.constraint.hasUniqueResidues:
            if entity_type.is_nt_sequence():
                constraint_fields.add(SequenceConstraint.BASES.value)
            # elif entity_type == BenchlingEntityType.AA_SEQUENCE:
            #     if entity_schema.constraint.hasUniqueResiduesCaseSensitive:
            #         constraint_fields.add(
            #             SequenceConstraint.AMINO_ACIDS_EXACT_MATCH.value
            #         )
            #     else:
            #         constraint_fields.add(
            #             SequenceConstraint.AMINO_ACIDS_IGNORE_CASE.value
            #         )
    schema_props: dict[str, Any] = dict(
        name=entity_schema.name,
        prefix=entity_schema.itemIdPrefix,
        warehouse_name=entity_schema.systemName,
        entity_type=entity_type,
        mixture_schema_config=MixtureSchemaConfig(
            allowMeasuredIngredients=entity_schema.allowMeasuredIngredients,
            componentLotStorageEnabled=entity_schema.componentLotStorageEnabled,
            componentLotTextEnabled=entity_schema.componentLotTextEnabled,
        )
        if entity_schema.typename == BenchlingEntityTypeName.MIXTURE
        else None,
        naming_strategies=set(
            BenchlingNamingStrategy(strategy)
            for strategy in entity_schema.availableRegistrationNamingOptions or []
        ),
        constraint_fields=constraint_fields,
        _archived=entity_schema.archived,
        use_registry_id_as_label=entity_schema.useRegistryIdForItemDisplayLabel
        or False,
        include_registry_id_in_chips=entity_schema.includeRegistryIdInChips or False,
        show_bases_in_expanded_view=entity_schema.showResidues or False,
    )
    for f in SchemaProperties.unsupported_schema_properties(entity_type):
        schema_props.pop(f, None)
    return (
        SchemaProperties(**schema_props),
        NameTemplate(
            parts=entity_schema.get_internal_name_template_parts(),
            order_name_parts_by_sequence=entity_schema.nameTemplate.shouldOrderPartsBySequence,
        )
        if entity_schema.nameTemplate and fields_fetched
        else NameTemplate(),
        {
            f.systemName: convert_entity_schema_field_to_field_properties(
                f,
                entity_schema_id_to_name_map,
                dropdown_id_to_name_map,
                unit_id_to_name_map,
            )
            for f in all_fields
        },
    )


def convert_entity_schema_field_to_field_properties(
    field: EntitySchemaFieldModel,
    entity_schema_id_to_name_map: dict[str, str],
    dropdown_id_to_name_map: dict[str, str],
    unit_id_to_name_map: dict[str, str],
) -> BaseFieldProperties:
    links_to_entity_schema = (
        field.linkDefinition is not None
        and field.linkDefinition.typename.is_entity_schema_type()
    )
    field_type = convert_field_definition_type_to_field_type(
        field.typename, links_to_entity_schema
    )
    field_props: dict[str, Any] = dict(
        name=field.name,
        type=field_type,
        required=field.isRequired,
        is_multi=field.isMulti,
        dropdown_link=dropdown_id_to_name_map.get(field.linkDefinition.id)
        if field.linkDefinition
        and field.linkDefinition.typename == BenchlingLinkDefinitionType.DROPDOWN
        else None,
        parent_link=field.isParent,
        entity_link=entity_schema_id_to_name_map.get(field.linkDefinition.id)
        if links_to_entity_schema
        else None,
        tooltip=field.description,
        _archived=field.archived,
        unit_name=unit_id_to_name_map.get(field.unit.id) if field.unit else None,
        decimal_places=field.displayPrecision,
    )
    for f in BaseFieldProperties.unsupported_field_properties(
        field_type, links_to_entity_schema
    ):
        field_props.pop(f, None)
    return BaseFieldProperties(**field_props)


@lru_cache
def get_benchling_entity_schemas(
    benchling_service: BenchlingService,
) -> list[EntitySchema]:
    return [
        s
        for schemas in benchling_service.schemas.list_entity_schemas()
        for s in schemas
    ]


def get_benchling_entity_schema_id_to_system_name_map(
    benchling_service: BenchlingService,
) -> dict[str, str]:
    return {s["id"]: s["systemName"] for s in list_entity_schemas_v3(benchling_service)}
