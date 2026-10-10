from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String, Boolean
from sqlalchemy.sql.type_api import TypeEngine

from liminal.enums import (
    BenchlingEntitySchemaEndpointType,
    BenchlingEntityTypeName,
    BenchlingEntityType,
    BenchlingFieldDefinitionInputType,
    BenchlingFieldDefinitionType,
    BenchlingFieldType,
)


def convert_field_definition_type_to_field_type(
    field_definition_type: BenchlingFieldDefinitionType, has_entity_link: bool = False
) -> BenchlingFieldType:
    conversion_map = {
        BenchlingFieldDefinitionType.TEXT_FIELD_DEFINITION: BenchlingFieldType.TEXT,
        BenchlingFieldDefinitionType.LONG_TEXT_FIELD_DEFINITION: BenchlingFieldType.LONG_TEXT,
        BenchlingFieldDefinitionType.INTEGER_FIELD_DEFINITION: BenchlingFieldType.INTEGER,
        BenchlingFieldDefinitionType.FLOAT_FIELD_DEFINITION: BenchlingFieldType.DECIMAL,
        BenchlingFieldDefinitionType.DECIMAL_FIELD_DEFINITION: BenchlingFieldType.DECIMAL,
        BenchlingFieldDefinitionType.BOOLEAN_FIELD_DEFINITION: BenchlingFieldType.BOOLEAN,
        BenchlingFieldDefinitionType.DATE_FIELD_DEFINITION: BenchlingFieldType.DATE,
        BenchlingFieldDefinitionType.DATETIME_FIELD_DEFINITION: BenchlingFieldType.DATETIME,
        BenchlingFieldDefinitionType.JSON_FIELD_DEFINITION: BenchlingFieldType.JSON,
        BenchlingFieldDefinitionType.AA_SEQUENCE_LINK_FIELD_DEFINITION: BenchlingFieldType.AA_SEQUENCE_LINK,
        BenchlingFieldDefinitionType.ANTIBODY_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.ASSAY_REQUEST_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.ASSAY_RESULT_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.ASSAY_RUN_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.BLOB_LINK_FIELD_DEFINITION: BenchlingFieldType.BLOB_LINK,
        BenchlingFieldDefinitionType.ATTACHMENT_LINK_FIELD_DEFINITION: BenchlingFieldType.BLOB_LINK,
        BenchlingFieldDefinitionType.CUSTOM_ENTITY_LINK_FIELD_DEFINITION: BenchlingFieldType.CUSTOM_ENTITY_LINK,
        BenchlingFieldDefinitionType.DNA_OLIGO_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.DNA_SEQUENCE_LINK_FIELD_DEFINITION: BenchlingFieldType.DNA_SEQUENCE_LINK,
        BenchlingFieldDefinitionType.DROPDOWN_LINK_FIELD_DEFINITION: BenchlingFieldType.DROPDOWN,
        BenchlingFieldDefinitionType.ANY_ENTITY_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.ENTRY_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTRY_LINK,
        BenchlingFieldDefinitionType.EQUIPMENT_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.FIELDSET_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.MIXTURE_LINK_FIELD_DEFINITION: BenchlingFieldType.MIXTURE_LINK,
        BenchlingFieldDefinitionType.MOLECULE_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.OLIGO_CONJUGATE_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.OLIGO_DUPLEX_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.RNA_SEQUENCE_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.RNA_OLIGO_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.STORABLE_LINK_FIELD_DEFINITION: BenchlingFieldType.STORAGE_LINK,
        BenchlingFieldDefinitionType.SYSTEM_CATEGORY_LINK_FIELD_DEFINITION: BenchlingFieldType.ENTITY_LINK,
        BenchlingFieldDefinitionType.DNA_PART_LINK_FIELD_DEFINITION: BenchlingFieldType.PART_LINK,
        BenchlingFieldDefinitionType.RNA_PART_LINK_FIELD_DEFINITION: BenchlingFieldType.PART_LINK,
        BenchlingFieldDefinitionType.TRANSCRIPTION_LINK_FIELD_DEFINITION: BenchlingFieldType.TRANSCRIPTION_LINK,
        BenchlingFieldDefinitionType.TRANSLATION_LINK_FIELD_DEFINITION: BenchlingFieldType.TRANSLATION_LINK,
    }

    if field_definition_type not in conversion_map:
        raise ValueError(
            f"Field definition type '{field_definition_type}' is not supported."
        )
    field_type = conversion_map[field_definition_type]
    # Links to a specific entity schema are represented as ENTITY_LINK with entity_link set.
    if has_entity_link and field_type in BenchlingFieldType.get_entity_types():
        return BenchlingFieldType.ENTITY_LINK
    return field_type


def convert_field_type_to_field_definition_type(
    field_type: BenchlingFieldType,
    linked_schema_type: BenchlingEntityTypeName | None = None,
) -> BenchlingFieldDefinitionType:
    if field_type == BenchlingFieldType.ENTITY_LINK and linked_schema_type is not None:
        linked_schema_conversion_map = {
            BenchlingEntityTypeName.AA_SEQUENCE: BenchlingFieldDefinitionType.AA_SEQUENCE_LINK_FIELD_DEFINITION,
            BenchlingEntityTypeName.CUSTOM_ENTITY: BenchlingFieldDefinitionType.CUSTOM_ENTITY_LINK_FIELD_DEFINITION,
            BenchlingEntityTypeName.DNA_OLIGO: BenchlingFieldDefinitionType.DNA_OLIGO_LINK_FIELD_DEFINITION,
            BenchlingEntityTypeName.DNA_SEQUENCE: BenchlingFieldDefinitionType.DNA_SEQUENCE_LINK_FIELD_DEFINITION,
            BenchlingEntityTypeName.ENTRY: BenchlingFieldDefinitionType.ENTRY_LINK_FIELD_DEFINITION,
            BenchlingEntityTypeName.MIXTURE: BenchlingFieldDefinitionType.MIXTURE_LINK_FIELD_DEFINITION,
            BenchlingEntityTypeName.MOLECULE: BenchlingFieldDefinitionType.MOLECULE_LINK_FIELD_DEFINITION,
            BenchlingEntityTypeName.RNA_OLIGO: BenchlingFieldDefinitionType.RNA_OLIGO_LINK_FIELD_DEFINITION,
            BenchlingEntityTypeName.RNA_SEQUENCE: BenchlingFieldDefinitionType.RNA_SEQUENCE_LINK_FIELD_DEFINITION,
        }
        return linked_schema_conversion_map[linked_schema_type]
    if (
        field_type == BenchlingFieldType.PART_LINK
        and linked_schema_type == BenchlingEntityTypeName.RNA_SEQUENCE
    ):
        return BenchlingFieldDefinitionType.RNA_PART_LINK_FIELD_DEFINITION
    conversion_map = {
        BenchlingFieldType.TEXT: BenchlingFieldDefinitionType.TEXT_FIELD_DEFINITION,
        BenchlingFieldType.LONG_TEXT: BenchlingFieldDefinitionType.LONG_TEXT_FIELD_DEFINITION,
        BenchlingFieldType.INTEGER: BenchlingFieldDefinitionType.INTEGER_FIELD_DEFINITION,
        BenchlingFieldType.DECIMAL: BenchlingFieldDefinitionType.FLOAT_FIELD_DEFINITION,
        BenchlingFieldType.BOOLEAN: BenchlingFieldDefinitionType.BOOLEAN_FIELD_DEFINITION,
        BenchlingFieldType.DATE: BenchlingFieldDefinitionType.DATE_FIELD_DEFINITION,
        BenchlingFieldType.DATETIME: BenchlingFieldDefinitionType.DATETIME_FIELD_DEFINITION,
        BenchlingFieldType.JSON: BenchlingFieldDefinitionType.JSON_FIELD_DEFINITION,
        BenchlingFieldType.DROPDOWN: BenchlingFieldDefinitionType.DROPDOWN_LINK_FIELD_DEFINITION,
        BenchlingFieldType.BLOB_LINK: BenchlingFieldDefinitionType.BLOB_LINK_FIELD_DEFINITION,
        BenchlingFieldType.ENTRY_LINK: BenchlingFieldDefinitionType.ENTRY_LINK_FIELD_DEFINITION,
        BenchlingFieldType.STORAGE_LINK: BenchlingFieldDefinitionType.STORABLE_LINK_FIELD_DEFINITION,
        BenchlingFieldType.ENTITY_LINK: BenchlingFieldDefinitionType.ANY_ENTITY_LINK_FIELD_DEFINITION,
        BenchlingFieldType.AA_SEQUENCE_LINK: BenchlingFieldDefinitionType.AA_SEQUENCE_LINK_FIELD_DEFINITION,
        BenchlingFieldType.CUSTOM_ENTITY_LINK: BenchlingFieldDefinitionType.CUSTOM_ENTITY_LINK_FIELD_DEFINITION,
        BenchlingFieldType.DNA_SEQUENCE_LINK: BenchlingFieldDefinitionType.DNA_SEQUENCE_LINK_FIELD_DEFINITION,
        BenchlingFieldType.MIXTURE_LINK: BenchlingFieldDefinitionType.MIXTURE_LINK_FIELD_DEFINITION,
        BenchlingFieldType.PART_LINK: BenchlingFieldDefinitionType.DNA_PART_LINK_FIELD_DEFINITION,
        BenchlingFieldType.TRANSLATION_LINK: BenchlingFieldDefinitionType.TRANSLATION_LINK_FIELD_DEFINITION,
        BenchlingFieldType.TRANSCRIPTION_LINK: BenchlingFieldDefinitionType.TRANSCRIPTION_LINK_FIELD_DEFINITION,
    }
    if field_type not in conversion_map:
        raise ValueError(f"Field type '{field_type}' is not supported.")
    return conversion_map[field_type]


def convert_field_type_to_field_definition_input_type(
    field_type: BenchlingFieldType,
    linked_schema_type: BenchlingEntityTypeName | None = None,
) -> BenchlingFieldDefinitionInputType:
    if field_type == BenchlingFieldType.ENTITY_LINK and linked_schema_type is not None:
        linked_schema_conversion_map = {
            BenchlingEntityTypeName.AA_SEQUENCE: BenchlingFieldDefinitionInputType.AA_SEQUENCE_LINK,
            BenchlingEntityTypeName.CUSTOM_ENTITY: BenchlingFieldDefinitionInputType.CUSTOM_ENTITY_LINK,
            BenchlingEntityTypeName.DNA_OLIGO: BenchlingFieldDefinitionInputType.DNA_OLIGO_LINK,
            BenchlingEntityTypeName.DNA_SEQUENCE: BenchlingFieldDefinitionInputType.DNA_SEQUENCE_LINK,
            BenchlingEntityTypeName.MIXTURE: BenchlingFieldDefinitionInputType.MIXTURE_LINK,
            BenchlingEntityTypeName.MOLECULE: BenchlingFieldDefinitionInputType.MOLECULE_LINK,
            BenchlingEntityTypeName.RNA_OLIGO: BenchlingFieldDefinitionInputType.RNA_OLIGO_LINK,
            BenchlingEntityTypeName.RNA_SEQUENCE: BenchlingFieldDefinitionInputType.RNA_SEQUENCE_LINK,
        }
        if linked_schema_type not in linked_schema_conversion_map:
            raise ValueError(
                f"Entity links to '{linked_schema_type}' schemas are not supported."
            )
        return linked_schema_conversion_map[linked_schema_type]
    if (
        field_type == BenchlingFieldType.PART_LINK
        and linked_schema_type == BenchlingEntityTypeName.RNA_SEQUENCE
    ):
        return BenchlingFieldDefinitionInputType.RNA_PART_LINK
    conversion_map = {
        BenchlingFieldType.TEXT: BenchlingFieldDefinitionInputType.TEXT,
        BenchlingFieldType.LONG_TEXT: BenchlingFieldDefinitionInputType.LONG_TEXT,
        BenchlingFieldType.INTEGER: BenchlingFieldDefinitionInputType.INTEGER,
        BenchlingFieldType.DECIMAL: BenchlingFieldDefinitionInputType.FLOAT,
        BenchlingFieldType.BOOLEAN: BenchlingFieldDefinitionInputType.BOOLEAN,
        BenchlingFieldType.DATE: BenchlingFieldDefinitionInputType.DATE,
        BenchlingFieldType.DATETIME: BenchlingFieldDefinitionInputType.DATE_TIME,
        BenchlingFieldType.DROPDOWN: BenchlingFieldDefinitionInputType.DROPDOWN,
        BenchlingFieldType.BLOB_LINK: BenchlingFieldDefinitionInputType.BLOB_LINK,
        BenchlingFieldType.ENTRY_LINK: BenchlingFieldDefinitionInputType.ENTRY_LINK,
        BenchlingFieldType.STORAGE_LINK: BenchlingFieldDefinitionInputType.STORAGE_LINK,
        BenchlingFieldType.ENTITY_LINK: BenchlingFieldDefinitionInputType.ENTITY_LINK,
        BenchlingFieldType.AA_SEQUENCE_LINK: BenchlingFieldDefinitionInputType.AA_SEQUENCE_LINK,
        BenchlingFieldType.CUSTOM_ENTITY_LINK: BenchlingFieldDefinitionInputType.CUSTOM_ENTITY_LINK,
        BenchlingFieldType.DNA_SEQUENCE_LINK: BenchlingFieldDefinitionInputType.DNA_SEQUENCE_LINK,
        BenchlingFieldType.MIXTURE_LINK: BenchlingFieldDefinitionInputType.MIXTURE_LINK,
        BenchlingFieldType.PART_LINK: BenchlingFieldDefinitionInputType.DNA_PART_LINK,
        BenchlingFieldType.TRANSLATION_LINK: BenchlingFieldDefinitionInputType.TRANSLATION_LINK,
        BenchlingFieldType.TRANSCRIPTION_LINK: BenchlingFieldDefinitionInputType.TRANSCRIPTION_LINK,
    }
    if field_type not in conversion_map:
        raise ValueError(
            f"Field type '{field_type}' cannot be created through the v3 API."
        )
    return conversion_map[field_type]


def convert_field_definition_type_to_field_definition_input_type(
    field_definition_type: BenchlingFieldDefinitionType,
) -> BenchlingFieldDefinitionInputType:
    conversion_map = {
        BenchlingFieldDefinitionType.TEXT_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.TEXT,
        BenchlingFieldDefinitionType.LONG_TEXT_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.LONG_TEXT,
        BenchlingFieldDefinitionType.INTEGER_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.INTEGER,
        BenchlingFieldDefinitionType.FLOAT_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.FLOAT,
        BenchlingFieldDefinitionType.DECIMAL_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.DECIMAL,
        BenchlingFieldDefinitionType.BOOLEAN_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.BOOLEAN,
        BenchlingFieldDefinitionType.DATE_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.DATE,
        BenchlingFieldDefinitionType.DATETIME_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.DATE_TIME,
        BenchlingFieldDefinitionType.DROPDOWN_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.DROPDOWN,
        BenchlingFieldDefinitionType.BLOB_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.BLOB_LINK,
        BenchlingFieldDefinitionType.ATTACHMENT_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.ATTACHMENT_LINK,
        BenchlingFieldDefinitionType.ENTRY_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.ENTRY_LINK,
        BenchlingFieldDefinitionType.STORABLE_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.STORAGE_LINK,
        BenchlingFieldDefinitionType.ANY_ENTITY_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.ENTITY_LINK,
        BenchlingFieldDefinitionType.AA_SEQUENCE_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.AA_SEQUENCE_LINK,
        BenchlingFieldDefinitionType.CUSTOM_ENTITY_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.CUSTOM_ENTITY_LINK,
        BenchlingFieldDefinitionType.DNA_OLIGO_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.DNA_OLIGO_LINK,
        BenchlingFieldDefinitionType.DNA_SEQUENCE_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.DNA_SEQUENCE_LINK,
        BenchlingFieldDefinitionType.MIXTURE_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.MIXTURE_LINK,
        BenchlingFieldDefinitionType.MOLECULE_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.MOLECULE_LINK,
        BenchlingFieldDefinitionType.RNA_OLIGO_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.RNA_OLIGO_LINK,
        BenchlingFieldDefinitionType.RNA_SEQUENCE_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.RNA_SEQUENCE_LINK,
        BenchlingFieldDefinitionType.DNA_PART_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.DNA_PART_LINK,
        BenchlingFieldDefinitionType.RNA_PART_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.RNA_PART_LINK,
        BenchlingFieldDefinitionType.TRANSCRIPTION_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.TRANSCRIPTION_LINK,
        BenchlingFieldDefinitionType.TRANSLATION_LINK_FIELD_DEFINITION: BenchlingFieldDefinitionInputType.TRANSLATION_LINK,
    }
    if field_definition_type not in conversion_map:
        raise ValueError(
            f"Field definition type '{field_definition_type}' cannot be set through the v3 API."
        )
    return conversion_map[field_definition_type]


def convert_entity_schema_type_to_entity_type(
    entity_schema_type: BenchlingEntityTypeName,
) -> BenchlingEntityType:
    conversion_map = {
        BenchlingEntityTypeName.AA_SEQUENCE: BenchlingEntityType.AA_SEQUENCE,
        BenchlingEntityTypeName.CUSTOM_ENTITY: BenchlingEntityType.CUSTOM_ENTITY,
        BenchlingEntityTypeName.DNA_OLIGO: BenchlingEntityType.DNA_OLIGO,
        BenchlingEntityTypeName.DNA_SEQUENCE: BenchlingEntityType.DNA_SEQUENCE,
        BenchlingEntityTypeName.ENTRY: BenchlingEntityType.ENTRY,
        BenchlingEntityTypeName.MIXTURE: BenchlingEntityType.MIXTURE,
        BenchlingEntityTypeName.MOLECULE: BenchlingEntityType.MOLECULE,
        BenchlingEntityTypeName.RNA_OLIGO: BenchlingEntityType.RNA_OLIGO,
        BenchlingEntityTypeName.RNA_SEQUENCE: BenchlingEntityType.RNA_SEQUENCE,
    }
    if entity_schema_type in conversion_map:
        return conversion_map[entity_schema_type]
    raise ValueError(f"Entity schema type '{entity_schema_type}' is not supported.")


def convert_benchling_type_to_python_type(benchling_type: BenchlingFieldType) -> type:
    benchling_to_python_type_map = {
        BenchlingFieldType.DATE: datetime,
        BenchlingFieldType.DATETIME: datetime,
        BenchlingFieldType.DECIMAL: float,
        BenchlingFieldType.INTEGER: int,
        BenchlingFieldType.BLOB_LINK: dict[str, Any],
        BenchlingFieldType.CUSTOM_ENTITY_LINK: str,
        BenchlingFieldType.DNA_SEQUENCE_LINK: str,
        BenchlingFieldType.AA_SEQUENCE_LINK: str,
        BenchlingFieldType.TRANSLATION_LINK: str,
        BenchlingFieldType.TRANSCRIPTION_LINK: str,
        BenchlingFieldType.DROPDOWN: str,
        BenchlingFieldType.ENTITY_LINK: str,
        BenchlingFieldType.ENTRY_LINK: str,
        BenchlingFieldType.MIXTURE_LINK: str,
        BenchlingFieldType.LONG_TEXT: str,
        BenchlingFieldType.STORAGE_LINK: str,
        BenchlingFieldType.PART_LINK: str,
        BenchlingFieldType.TEXT: str,
        BenchlingFieldType.JSON: dict[str, Any],
        BenchlingFieldType.BOOLEAN: bool,
    }
    if benchling_type in benchling_to_python_type_map:
        return benchling_to_python_type_map[benchling_type]
    else:
        raise ValueError(f"Benchling field type '{benchling_type}' is not supported.")


def convert_benchling_type_to_sql_alchemy_type(
    benchling_type: BenchlingFieldType,
) -> TypeEngine:
    benchling_to_sql_alchemy_type_map = {
        BenchlingFieldType.DATE: DateTime,
        BenchlingFieldType.DATETIME: DateTime,
        BenchlingFieldType.DECIMAL: Float,
        BenchlingFieldType.INTEGER: Integer,
        BenchlingFieldType.BLOB_LINK: JSON,
        BenchlingFieldType.CUSTOM_ENTITY_LINK: String,
        BenchlingFieldType.DNA_SEQUENCE_LINK: String,
        BenchlingFieldType.AA_SEQUENCE_LINK: String,
        BenchlingFieldType.TRANSLATION_LINK: String,
        BenchlingFieldType.TRANSCRIPTION_LINK: String,
        BenchlingFieldType.DROPDOWN: String,
        BenchlingFieldType.ENTITY_LINK: String,
        BenchlingFieldType.ENTRY_LINK: String,
        BenchlingFieldType.LONG_TEXT: String,
        BenchlingFieldType.STORAGE_LINK: String,
        BenchlingFieldType.PART_LINK: String,
        BenchlingFieldType.MIXTURE_LINK: String,
        BenchlingFieldType.TEXT: String,
        BenchlingFieldType.JSON: JSON,
        BenchlingFieldType.BOOLEAN: Boolean,
    }
    if benchling_type in benchling_to_sql_alchemy_type_map:
        return benchling_to_sql_alchemy_type_map[benchling_type]
    else:
        raise ValueError(f"Benchling field type '{benchling_type}' is not supported.")


def convert_entity_type_to_entity_schema_endpoint(
    entity_type: BenchlingEntityType,
) -> BenchlingEntitySchemaEndpointType:
    conversion_map = {
        BenchlingEntityType.CUSTOM_ENTITY: BenchlingEntitySchemaEndpointType.CUSTOM_ENTITY,
        BenchlingEntityType.DNA_SEQUENCE: BenchlingEntitySchemaEndpointType.DNA_SEQUENCE,
        BenchlingEntityType.DNA_OLIGO: BenchlingEntitySchemaEndpointType.DNA_OLIGO,
        BenchlingEntityType.RNA_OLIGO: BenchlingEntitySchemaEndpointType.RNA_OLIGO,
        BenchlingEntityType.RNA_SEQUENCE: BenchlingEntitySchemaEndpointType.RNA_SEQUENCE,
        BenchlingEntityType.AA_SEQUENCE: BenchlingEntitySchemaEndpointType.AA_SEQUENCE,
        BenchlingEntityType.ENTRY: BenchlingEntitySchemaEndpointType.ENTRY,
        BenchlingEntityType.MIXTURE: BenchlingEntitySchemaEndpointType.MIXTURE,
        BenchlingEntityType.MOLECULE: BenchlingEntitySchemaEndpointType.MOLECULE,
    }
    if entity_type in conversion_map:
        return conversion_map[entity_type]
    else:
        raise ValueError(f"Entity type '{entity_type}' is not supported.")


def entity_type_to_valid_field_types(
    entity_type: BenchlingEntityType,
) -> list[BenchlingFieldType]:
    entity_type_to_valid_field_types_map: dict[
        BenchlingEntityType, list[BenchlingFieldType]
    ] = {
        BenchlingEntityType.CUSTOM_ENTITY: [],
        BenchlingEntityType.DNA_SEQUENCE: [
            BenchlingFieldType.PART_LINK,
            BenchlingFieldType.TRANSLATION_LINK,
            BenchlingFieldType.TRANSCRIPTION_LINK,
        ],
        BenchlingEntityType.DNA_OLIGO: [],
        BenchlingEntityType.RNA_OLIGO: [],
        BenchlingEntityType.RNA_SEQUENCE: [
            BenchlingFieldType.PART_LINK,
            BenchlingFieldType.TRANSLATION_LINK,
        ],
        BenchlingEntityType.AA_SEQUENCE: [],
        BenchlingEntityType.ENTRY: [],
        BenchlingEntityType.MIXTURE: [],
        BenchlingEntityType.MOLECULE: [],
    }
    for valid_field_types in entity_type_to_valid_field_types_map.values():
        valid_field_types.extend(BenchlingFieldType.get_default_field_types())
    return entity_type_to_valid_field_types_map[entity_type]
