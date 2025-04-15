from benchling_api_client.v2.stable.models.assay_result_schema import AssayResultSchema

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_id_name_map
from liminal.entity_schemas.utils import convert_tag_schema_field_to_field_properties
from liminal.orm.results_schema_properties import ResultsSchemaProperties
from liminal.results_schemas.models.results_schema_model import ResultsSchemaModel
from liminal.unit_dictionary.utils import get_unit_id_to_name_map


def get_converted_results_schemas(
    benchling_service: BenchlingService,
) -> list[tuple[ResultsSchemaProperties, dict[str, BaseFieldProperties]]]:
    results_schemas = ResultsSchemaModel.get_all(benchling_service)
    dropdowns_map = get_benchling_dropdown_id_name_map(benchling_service)
    unit_id_to_name_map = get_unit_id_to_name_map(benchling_service)
    results_schemas_list = []
    for schema in results_schemas:
        schema_properties = ResultsSchemaProperties(
            name=schema.name,
            warehouse_name=schema.sqlIdentifier,
        )
        field_properties_dict = {}
        for field in schema.fields:
            field_properties_dict[field.systemName] = (
                convert_tag_schema_field_to_field_properties(
                    field, dropdowns_map, unit_id_to_name_map
                )
            )
        results_schemas_list.append((schema_properties, field_properties_dict))
    return results_schemas_list


def get_results_schemas_dict(
    benchling_service: BenchlingService,
) -> dict[str, AssayResultSchema]:
    flattened_schemas = [
        s
        for schemas in list(benchling_service.schemas.list_assay_result_schemas())
        for s in schemas
    ]
    schemas_dict = {s.system_name: s for s in flattened_schemas}
    return schemas_dict
