from functools import lru_cache

from benchling_api_client.v2.stable.models.assay_result_schema import AssayResultSchema

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_id_name_map
from liminal.entity_schemas.utils import (
    get_benchling_entity_schema_id_to_system_name_map,
)
from liminal.enums.benchling_field_definition_type import BenchlingFieldDefinitionType
from liminal.mappers import benchling_field_definition_type_to_field_type
from liminal.orm.results_schema_properties import ResultsSchemaProperties
from liminal.results_schemas.models.results_schema_model import (
    ResultsSchemaFieldModel,
    ResultsSchemaModel,
)
from liminal.unit_dictionary.utils import get_unit_id_to_name_map


def convert_result_schema_field_to_field_properties(
    field: ResultsSchemaFieldModel,
    entity_schema_id_to_system_name_map: dict[str, str],
    dropdowns_map: dict[str, str],
    unit_id_to_name_map: dict[str, str],
) -> BaseFieldProperties:
    field_type = benchling_field_definition_type_to_field_type(field.typename)

    link_definition_id = field.linkDefinition.id if field.linkDefinition else None
    unit_id = (
        field.unit.get("id")
        if isinstance(field.unit, dict)
        else getattr(field.unit, "id", None)
    )

    return BaseFieldProperties(
        name=field.name,
        type=field_type,
        required=field.isRequired,
        is_multi=field.isMulti,
        dropdown_link=dropdowns_map.get(link_definition_id)
        if BenchlingFieldDefinitionType.is_dropdown_link(field.typename)
        and link_definition_id
        else None,
        parent_link=field.isParent,
        entity_link=entity_schema_id_to_system_name_map.get(link_definition_id)
        if BenchlingFieldDefinitionType.is_entity_link(field.typename)
        and link_definition_id
        else None,
        tooltip=field.description,
        _archived=field.archived,
        unit_name=unit_id_to_name_map.get(unit_id) if unit_id else None,
        decimal_places=field.displayPrecision,
    )


def get_converted_results_schemas(
    benchling_service: BenchlingService, include_archived: bool = False
) -> list[tuple[ResultsSchemaProperties, dict[str, BaseFieldProperties]]]:
    """This functions gets all Results Schema schemas from Benchling and converts them to our internal representation of a schema and its fields.
    It parses the Results Schema and creates ResultsSchemaProperties and a list of FieldProperties for each field in the schema.
    """
    results_schemas = ResultsSchemaModel.get_all(benchling_service)
    dropdown_id_to_name_map = get_benchling_dropdown_id_name_map(benchling_service)
    unit_id_to_name_map = get_unit_id_to_name_map(benchling_service)
    entity_schema_id_to_system_name_map = (
        get_benchling_entity_schema_id_to_system_name_map(benchling_service)
    )
    results_schemas_list = []
    if not include_archived:
        results_schemas = [s for s in results_schemas if not s.archived]
    for schema in results_schemas:
        schema_properties = ResultsSchemaProperties(
            name=schema.name,
            warehouse_name=schema.systemName,
        )
        field_properties_dict = {}
        for field in schema.fields:
            field_properties_dict[field.systemName] = (
                convert_result_schema_field_to_field_properties(
                    field,
                    entity_schema_id_to_system_name_map,
                    dropdown_id_to_name_map,
                    unit_id_to_name_map,
                )
            )
        results_schemas_list.append((schema_properties, field_properties_dict))
    return results_schemas_list


@lru_cache
def get_benchling_results_schemas(
    benchling_service: BenchlingService,
) -> list[AssayResultSchema]:
    return [
        s for loe in benchling_service.schemas.list_assay_result_schemas() for s in loe
    ]
