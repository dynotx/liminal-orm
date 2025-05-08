from benchling_sdk.models import EntitySchema

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_id_name_map
from liminal.entity_schemas.tag_schema_models import TagSchemaFieldModel, TagSchemaModel
from liminal.enums import BenchlingAPIFieldType, BenchlingNamingStrategy
from liminal.enums.benchling_entity_type import BenchlingEntityType
from liminal.enums.sequence_constraint import SequenceConstraint
from liminal.mappers import (
    convert_api_entity_type_to_entity_type,
    convert_api_field_type_to_field_type,
)
from liminal.orm.name_template import NameTemplate
from liminal.orm.schema_properties import MixtureSchemaConfig, SchemaProperties
from liminal.unit_dictionary.utils import get_unit_id_to_name_map


def get_converted_tag_schemas(
    benchling_service: BenchlingService,
    include_archived: bool = False,
    wh_schema_names: set[str] | None = None,
) -> list[tuple[SchemaProperties, NameTemplate, dict[str, BaseFieldProperties]]]:
    """This functions gets all Tag schemas from Benchling and converts them to our internal representation of a schema and its fields.
    It parses the Tag Schema and creates SchemaProperties and a list of FieldProperties for each field in the schema.
    If include_archived is True, it will include archived schemas and archived fields.
    """
    all_schemas = TagSchemaModel.get_all(benchling_service, wh_schema_names)
    dropdowns_map = get_benchling_dropdown_id_name_map(benchling_service)
    unit_id_to_name_map = get_unit_id_to_name_map(benchling_service)
    all_schemas = (
        all_schemas
        if include_archived
        else [s for s in all_schemas if not s.archiveRecord]
    )
    all_schemas = [s for s in all_schemas if s.sqlIdentifier != "_liminal_remote"]
    return [
        convert_tag_schema_to_internal_schema(
            tag_schema, dropdowns_map, unit_id_to_name_map, include_archived
        )
        for tag_schema in all_schemas
    ]


def convert_tag_schema_to_internal_schema(
    tag_schema: TagSchemaModel,
    dropdowns_map: dict[str, str],
    unit_id_to_name_map: dict[str, str],
    include_archived_fields: bool = False,
) -> tuple[SchemaProperties, NameTemplate, dict[str, BaseFieldProperties]]:
    all_fields = tag_schema.allFields
    if not include_archived_fields:
        all_fields = [f for f in all_fields if not f.archiveRecord]
    constraint_fields: set[str] = set()
    entity_type = convert_api_entity_type_to_entity_type(
        tag_schema.folderItemType, tag_schema.sequenceType
    )
    if tag_schema.constraint:
        constraint_fields = constraint_fields.union(
            [f.systemName for f in tag_schema.constraint.fields]
        )
        if tag_schema.constraint.uniqueResidues:
            if entity_type.is_nt_sequence():
                constraint_fields.add(SequenceConstraint.BASES.value)
            elif entity_type == BenchlingEntityType.AA_SEQUENCE:
                if tag_schema.constraint.areUniqueResiduesCaseSensitive:
                    constraint_fields.add(
                        SequenceConstraint.AMINO_ACIDS_EXACT_MATCH.value
                    )
                else:
                    constraint_fields.add(
                        SequenceConstraint.AMINO_ACIDS_IGNORE_CASE.value
                    )
    return (
        SchemaProperties(
            name=tag_schema.name,
            prefix=tag_schema.prefix,
            warehouse_name=tag_schema.sqlIdentifier,
            schema_id=tag_schema.id,
            entity_type=entity_type,
            mixture_schema_config=MixtureSchemaConfig(
                allowMeasuredIngredients=tag_schema.mixtureSchemaConfig.allowMeasuredIngredients,
                componentLotStorageEnabled=tag_schema.mixtureSchemaConfig.componentLotStorageEnabled,
                componentLotTextEnabled=tag_schema.mixtureSchemaConfig.componentLotTextEnabled,
            )
            if tag_schema.mixtureSchemaConfig
            else None,
            naming_strategies=set(
                BenchlingNamingStrategy(strategy)
                for strategy in tag_schema.labelingStrategies
            ),
            constraint_fields=constraint_fields,
            _archived=tag_schema.archiveRecord is not None,
            use_registry_id_as_label=tag_schema.useOrganizationCollectionAliasForDisplayLabel,
            include_registry_id_in_chips=tag_schema.includeRegistryIdInChips,
            show_bases_in_expanded_view=tag_schema.showResidues,
        ),
        NameTemplate(
            parts=tag_schema.get_internal_name_template_parts(),
            order_name_parts_by_sequence=tag_schema.shouldOrderNamePartsBySequence,
        ),
        {
            f.systemName: convert_tag_schema_field_to_field_properties(
                f, dropdowns_map, unit_id_to_name_map
            )
            for f in all_fields
        },
    )


def convert_tag_schema_field_to_field_properties(
    field: TagSchemaFieldModel,
    dropdowns_map: dict[str, str],
    unit_id_to_name_map: dict[str, str],
) -> BaseFieldProperties:
    return BaseFieldProperties(
        name=field.name,
        type=convert_api_field_type_to_field_type(
            BenchlingAPIFieldType(field.fieldType),
            field.requiredLink.folderItemType if field.requiredLink else None,
        ),
        required=field.isRequired,
        is_multi=field.isMulti,
        dropdown_link=dropdowns_map.get(field.schemaFieldSelectorId)
        if field.schemaFieldSelectorId
        else None,
        parent_link=field.isParentLink,
        entity_link=field.requiredLink.tagSchema["sqlIdentifier"]
        if field.requiredLink and field.requiredLink.tagSchema
        else None,
        tooltip=field.tooltipText,
        _archived=field.archiveRecord is not None,
        unit_name=unit_id_to_name_map.get(field.unitApiIdentifier)
        if field.unitApiIdentifier
        else None,
        decimal_places=field.decimalPrecision,
    )


def get_benchling_entity_schemas(
    benchling_service: BenchlingService,
) -> list[EntitySchema]:
    return [
        s
        for schemas in benchling_service.schemas.list_entity_schemas()
        for s in schemas
    ]
