import uuid

from liminal.base.base_operation import BaseOperation
from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.base.properties.base_schema_properties import BaseSchemaProperties
from liminal.connection.benchling_service import BenchlingService
from liminal.entity_schemas.operations import (
    ArchiveEntitySchema,
    ArchiveEntitySchemaField,
    CreateEntitySchema,
    CreateEntitySchemaField,
    ReorderEntitySchemaFields,
    UnarchiveEntitySchema,
    UnarchiveEntitySchemaField,
    UpdateEntitySchema,
    UpdateEntitySchemaField,
    UpdateEntitySchemaFieldName,
)
from liminal.enums import (
    BenchlingEntityType,
    BenchlingFieldType,
    BenchlingNamingStrategy,
)
from liminal.migrate.components import execute_operations, execute_operations_dry_run
from liminal.orm.schema_properties import SchemaProperties


def mock_entity_schema_full_migration(
    benchling_service: BenchlingService, test_model_wh_name: str, dry_run: bool = True
) -> None:
    """This test is a full migration of an entity schema, including renaming, creating, updating, archiving, and unarchiving options.
    This is meant to test the connection of all entity schema operations and can be run multiple times if successful.
    If this test fails at any point, ensure that the entity schema in benchling is archived and renamed to an arbitrary value.
    If dry_run is set to False, the operations will be executed.
    If dry_run is set to True, the operations will be executed in dry run mode and only the description of the operations will be printed.
    """
    random_id = f"{str(uuid.uuid4())[0:8]}_arch"
    if len(test_model_wh_name) + len(random_id) > 32:
        raise ValueError(
            f"Test model warehouse name is too long. Must be less than {32 - len(random_id)} characters."
        )

    schema_properties = SchemaProperties(
        warehouse_name=test_model_wh_name,
        name=test_model_wh_name,
        prefix=test_model_wh_name,
        entity_type=BenchlingEntityType.CUSTOM_ENTITY,
        naming_strategies=[BenchlingNamingStrategy.IDS_FROM_NAMES],
    )
    create_entity_schema_op = CreateEntitySchema(
        schema_properties=schema_properties,
        fields={
            "test_column_1": BaseFieldProperties(
                name="Test Column 1",
                type=BenchlingFieldType.TEXT,
                required=False,
                is_multi=False,
                parent_link=False,
            ),
            "test_column_2": BaseFieldProperties(
                name="Test Column 2",
                type=BenchlingFieldType.INTEGER,
                required=False,
                is_multi=False,
                parent_link=False,
            ),
            "test_column_4": BaseFieldProperties(
                name="Test Column 4",
                type=BenchlingFieldType.ENTITY_LINK,
                entity_link="ngs_sample",
                required=False,
                is_multi=False,
                parent_link=True,
            ),
        },
    )

    test_model_wh_name = f"{test_model_wh_name}_{random_id}"
    update_schema_properties = BaseSchemaProperties(
        warehouse_name=test_model_wh_name,
        name=test_model_wh_name,
        prefix=test_model_wh_name,
        entity_type=BenchlingEntityType.AA_SEQUENCE,
        naming_strategies=[
            BenchlingNamingStrategy.IDS_FROM_NAMES,
            BenchlingNamingStrategy.NEW_IDS,
        ],
    )
    update_entity_schema_op = UpdateEntitySchema(
        schema_properties.warehouse_name, update_schema_properties
    )

    test_column_3_field_properties = BaseFieldProperties(
        name="Test Column 3 New",
        type=BenchlingFieldType.TEXT,
        required=False,
        is_multi=False,
        parent_link=False,
    )
    create_entity_schema_field_op = CreateEntitySchemaField(
        test_model_wh_name, "test_column_3_new", test_column_3_field_properties, 2
    )

    update_test_column_3_field_properties = BaseFieldProperties(
        type=BenchlingFieldType.CUSTOM_ENTITY_LINK, is_multi=True
    )
    update_entity_schema_field_op = UpdateEntitySchemaField(
        test_model_wh_name, "test_column_3_new", update_test_column_3_field_properties
    )

    update_entity_schema_field_name_op = UpdateEntitySchemaFieldName(
        test_model_wh_name, "test_column_3_new", "test_column_3"
    )

    archive_entity_schema_field_op = ArchiveEntitySchemaField(
        test_model_wh_name, "test_column_3"
    )

    unarchive_entity_schema_field_op = UnarchiveEntitySchemaField(
        test_model_wh_name, "test_column_3", 1
    )

    reorder_entity_schema_field_op = ReorderEntitySchemaFields(
        test_model_wh_name,
        ["test_column_1", "test_column_2", "test_column_3", "test_column_4"],
    )

    archive_entity_schema_op = ArchiveEntitySchema(test_model_wh_name)
    unarchive_entity_schema_op = UnarchiveEntitySchema(test_model_wh_name)
    rearchive_entity_schema_op = ArchiveEntitySchema(test_model_wh_name)

    ops: list[BaseOperation] = [
        create_entity_schema_op,
        update_entity_schema_op,
        create_entity_schema_field_op,
        update_entity_schema_field_op,
        update_entity_schema_field_name_op,
        archive_entity_schema_field_op,
        unarchive_entity_schema_field_op,
        reorder_entity_schema_field_op,
        archive_entity_schema_op,
        unarchive_entity_schema_op,
        rearchive_entity_schema_op,
    ]
    execute_operations_dry_run(ops) if dry_run else execute_operations(
        benchling_service, ops
    )
    print("Dry run migration complete!") if dry_run else print("Migration complete!")