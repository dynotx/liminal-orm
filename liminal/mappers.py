from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.sql.type_api import TypeEngine

from liminal.enums import (
    BenchlingAPIFieldType,
    BenchlingEntityType,
    BenchlingFieldType,
    BenchlingFolderItemType,
    BenchlingSequenceType,
)


def convert_benchling_type_to_python_type(benchling_type: BenchlingFieldType) -> type:
    benchling_to_python_type_map = {
        BenchlingFieldType.DATE: datetime,
        BenchlingFieldType.DECIMAL: float,
        BenchlingFieldType.INTEGER: int,
        BenchlingFieldType.BLOB_LINK: dict[str, Any],
        BenchlingFieldType.CUSTOM_ENTITY_LINK: str,
        BenchlingFieldType.DNA_SEQUENCE_LINK: str,
        BenchlingFieldType.DROPDOWN: str,
        BenchlingFieldType.ENTITY_LINK: str,
        BenchlingFieldType.ENTRY_LINK: str,
        BenchlingFieldType.MIXTURE_LINK: str,
        BenchlingFieldType.LONG_TEXT: str,
        BenchlingFieldType.STORAGE_LINK: str,
        BenchlingFieldType.TEXT: str,
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
        BenchlingFieldType.DECIMAL: Float,
        BenchlingFieldType.INTEGER: Integer,
        BenchlingFieldType.BLOB_LINK: JSON,
        BenchlingFieldType.CUSTOM_ENTITY_LINK: String,
        BenchlingFieldType.DNA_SEQUENCE_LINK: String,
        BenchlingFieldType.DROPDOWN: String,
        BenchlingFieldType.ENTITY_LINK: String,
        BenchlingFieldType.ENTRY_LINK: String,
        BenchlingFieldType.LONG_TEXT: String,
        BenchlingFieldType.STORAGE_LINK: String,
        BenchlingFieldType.MIXTURE_LINK: String,
        BenchlingFieldType.AA_SEQUENCE_LINK: String,
        BenchlingFieldType.TEXT: String,
    }
    if benchling_type in benchling_to_sql_alchemy_type_map:
        return benchling_to_sql_alchemy_type_map[benchling_type]  # type: ignore
    else:
        raise ValueError(f"Benchling field type '{benchling_type}' is not supported.")


def convert_field_type_to_api_field_type(
    field_type: BenchlingFieldType,
) -> tuple[BenchlingAPIFieldType, BenchlingFolderItemType | None]:
    conversion_map = {
        BenchlingFieldType.BLOB_LINK: (BenchlingAPIFieldType.BLOB_LINK, None),
        BenchlingFieldType.DATE: (BenchlingAPIFieldType.DATE, None),
        BenchlingFieldType.ENTRY_LINK: (BenchlingAPIFieldType.ENTRY_LINK, None),
        BenchlingFieldType.AA_SEQUENCE_LINK: (
            BenchlingAPIFieldType.FILE_LINK,
            BenchlingFolderItemType.PROTEIN,
        ),
        BenchlingFieldType.MIXTURE_LINK: (
            BenchlingAPIFieldType.FILE_LINK,
            BenchlingFolderItemType.MIXTURE,
        ),
        BenchlingFieldType.CUSTOM_ENTITY_LINK: (
            BenchlingAPIFieldType.FILE_LINK,
            BenchlingFolderItemType.BASIC_FOLDER_ITEM,
        ),
        BenchlingFieldType.DNA_SEQUENCE_LINK: (
            BenchlingAPIFieldType.FILE_LINK,
            BenchlingFolderItemType.SEQUENCE,
        ),
        BenchlingFieldType.ENTITY_LINK: (BenchlingAPIFieldType.FILE_LINK, None),
        BenchlingFieldType.DECIMAL: (BenchlingAPIFieldType.FLOAT, None),
        BenchlingFieldType.INTEGER: (BenchlingAPIFieldType.INTEGER, None),
        BenchlingFieldType.LONG_TEXT: (BenchlingAPIFieldType.LONG_TEXT, None),
        BenchlingFieldType.DROPDOWN: (BenchlingAPIFieldType.SELECTOR, None),
        BenchlingFieldType.STORAGE_LINK: (BenchlingAPIFieldType.STORABLE_LINK, None),
        BenchlingFieldType.TEXT: (BenchlingAPIFieldType.STRING, None),
    }
    if field_type in conversion_map:
        return conversion_map[field_type]
    else:
        raise ValueError(f"Field type '{field_type}' is not supported.")


def convert_api_field_type_to_field_type(
    field_type: BenchlingAPIFieldType,
    folder_item_type: BenchlingFolderItemType | None = None,
) -> BenchlingFieldType:
    conversion_map = {
        (BenchlingAPIFieldType.BLOB_LINK, None): BenchlingFieldType.BLOB_LINK,
        (BenchlingAPIFieldType.DATE, None): BenchlingFieldType.DATE,
        (BenchlingAPIFieldType.ENTRY_LINK, None): BenchlingFieldType.ENTRY_LINK,
        (
            BenchlingAPIFieldType.FILE_LINK,
            BenchlingFolderItemType.BASIC_FOLDER_ITEM,
        ): BenchlingFieldType.CUSTOM_ENTITY_LINK,
        (
            BenchlingAPIFieldType.FILE_LINK,
            BenchlingFolderItemType.SEQUENCE,
        ): BenchlingFieldType.DNA_SEQUENCE_LINK,
        (
            BenchlingAPIFieldType.FILE_LINK,
            BenchlingFolderItemType.MIXTURE,
        ): BenchlingFieldType.MIXTURE_LINK,
        (
            BenchlingAPIFieldType.FILE_LINK,
            BenchlingFolderItemType.PROTEIN,
        ): BenchlingFieldType.AA_SEQUENCE_LINK,
        (BenchlingAPIFieldType.FILE_LINK, None): BenchlingFieldType.ENTITY_LINK,
        (BenchlingAPIFieldType.FLOAT, None): BenchlingFieldType.DECIMAL,
        (BenchlingAPIFieldType.INTEGER, None): BenchlingFieldType.INTEGER,
        (BenchlingAPIFieldType.LONG_TEXT, None): BenchlingFieldType.LONG_TEXT,
        (BenchlingAPIFieldType.SELECTOR, None): BenchlingFieldType.DROPDOWN,
        (BenchlingAPIFieldType.STORABLE_LINK, None): BenchlingFieldType.STORAGE_LINK,
        (BenchlingAPIFieldType.STRING, None): BenchlingFieldType.TEXT,
    }
    if (field_type, folder_item_type) in conversion_map:
        return conversion_map[(field_type, folder_item_type)]
    else:
        raise ValueError(f"Field type '{field_type}' is not supported.")


def convert_api_entity_type_to_entity_type(
    folder_item_type: BenchlingFolderItemType,
    sequence_type: BenchlingSequenceType | None,
) -> BenchlingEntityType:
    conversion_map = {
        (
            BenchlingFolderItemType.BASIC_FOLDER_ITEM,
            None,
        ): BenchlingEntityType.CUSTOM_ENTITY,
        (BenchlingFolderItemType.ENTRY, None): BenchlingEntityType.ENTRY,
        (BenchlingFolderItemType.MIXTURE, None): BenchlingEntityType.MIXTURE,
        (BenchlingFolderItemType.PROTEIN, None): BenchlingEntityType.AA_SEQUENCE,
        (
            BenchlingFolderItemType.SEQUENCE,
            BenchlingSequenceType.DNA_SEQUENCE,
        ): BenchlingEntityType.DNA_SEQUENCE,
        (
            BenchlingFolderItemType.SEQUENCE,
            BenchlingSequenceType.RNA_SEQUENCE,
        ): BenchlingEntityType.RNA_SEQUENCE,
        (
            BenchlingFolderItemType.SEQUENCE,
            BenchlingSequenceType.DNA_OLIGO,
        ): BenchlingEntityType.DNA_OLIGO,
        (
            BenchlingFolderItemType.SEQUENCE,
            BenchlingSequenceType.RNA_OLIGO,
        ): BenchlingEntityType.RNA_OLIGO,
    }
    if (folder_item_type, sequence_type) in conversion_map:
        return conversion_map[(folder_item_type, sequence_type)]
    else:
        raise ValueError(
            f"Folder item type '{folder_item_type}' and sequence type '{sequence_type}' do not map to a valid Benchling entity type."
        )


def convert_entity_type_to_api_entity_type(
    entity_type: BenchlingEntityType,
) -> tuple[BenchlingFolderItemType, BenchlingSequenceType | None]:
    conversion_map = {
        BenchlingEntityType.CUSTOM_ENTITY: (
            BenchlingFolderItemType.BASIC_FOLDER_ITEM,
            None,
        ),
        BenchlingEntityType.ENTRY: (BenchlingFolderItemType.ENTRY, None),
        BenchlingEntityType.MIXTURE: (BenchlingFolderItemType.MIXTURE, None),
        BenchlingEntityType.AA_SEQUENCE: (BenchlingFolderItemType.PROTEIN, None),
        BenchlingEntityType.DNA_SEQUENCE: (
            BenchlingFolderItemType.SEQUENCE,
            BenchlingSequenceType.DNA_SEQUENCE,
        ),
        BenchlingEntityType.RNA_SEQUENCE: (
            BenchlingFolderItemType.SEQUENCE,
            BenchlingSequenceType.RNA_SEQUENCE,
        ),
        BenchlingEntityType.DNA_OLIGO: (
            BenchlingFolderItemType.SEQUENCE,
            BenchlingSequenceType.DNA_OLIGO,
        ),
        BenchlingEntityType.RNA_OLIGO: (
            BenchlingFolderItemType.SEQUENCE,
            BenchlingSequenceType.RNA_OLIGO,
        ),
    }
    if entity_type in conversion_map:
        return conversion_map[entity_type]
    else:
        raise ValueError(f"Entity type '{entity_type}' is not supported.")
