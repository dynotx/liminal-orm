from liminal.base.compare_operation import CompareOperation
from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.base.properties.base_schema_properties import BaseSchemaProperties
from liminal.connection import BenchlingService
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
)
from liminal.entity_schemas.utils import get_converted_tag_schemas
from liminal.orm.base_model import BaseModel
from liminal.orm.column import Column
from liminal.utils import to_snake_case


def compare_entity_schemas(
    benchling_service: BenchlingService, schema_names: set[str] | None = None
) -> dict[str, list[CompareOperation]]:
    """Gets the Benchling schemas retrieved from the Benchling API and compares them to the associated models.
    Checks for missing fields, extra fields, incorrect field types, and whether they are required or not.

    Parameters
    ----------
    benchling_session : Session
        the sqlalchemy session to connect the the benchling postgres database

    Returns
    -------
    dict[str, list[str]]
        Returns a dictionary with the model name as the key and a list of error messages as the value.
    """
    model_operations: dict[str, list[CompareOperation]] = {}
    benchling_schemas = get_converted_tag_schemas(
        benchling_service, include_archived=True, wh_schema_names=schema_names
    )
    # If models are provided, filter the schemas from benchling so that only the models passed in are compared.
    # If you don't filter, it will compare to all the schemas in benchling and think that they are missing from code and should be archived.
    models = BaseModel.get_all_subclasses(schema_names)
    archived_benchling_schema_wh_names = [
        s[0].warehouse_name for s in benchling_schemas if s[0]._archived is True
    ]
    # Running list of schema names from benchling. As each model is checked, remove the schema name from this list.
    # This is used at the end to check if there are any schemas left (schemas that exist in benchling but not in code) and archive them if they are.
    running_benchling_schema_names = list(
        [s.warehouse_name for s, _ in benchling_schemas]
    )
    # Iterate through each benchling model defined in code.
    for model in models:
        ops: list[CompareOperation] = []
        model_columns: dict[str, Column] = model.get_columns_dict(
            exclude_base_columns=True
        )
        # Validate the entity_link and dropdown_link reference an entity_schema or dropdown that exists in code.
        model.validate_model()
        # if the model table_name is found in the benchling schemas, check for changes...
        if (model_wh_name := model.__schema_properties__.warehouse_name) in [
            s.warehouse_name for s, _ in benchling_schemas
        ]:
            benchling_schema_props, benchling_schema_fields = next(
                t for t in benchling_schemas if t[0].warehouse_name == model_wh_name
            )
            archived_benchling_schema_fields = {
                k: v for k, v in benchling_schema_fields.items() if v._archived is True
            }
            active_benchling_schema_fields = {
                k: v for k, v in benchling_schema_fields.items() if v._archived is False
            }
            if model_wh_name in archived_benchling_schema_wh_names:
                ops.append(
                    CompareOperation(
                        op=UnarchiveEntitySchema(model_wh_name),
                        reverse_op=ArchiveEntitySchema(model_wh_name),
                    )
                )
            # For each active field in the benchling schema...
            for (
                benchling_wh_field_name,
                benchling_field_props,
            ) in active_benchling_schema_fields.items():
                # If the benchling field is not found in the model columns, Archive.
                if benchling_wh_field_name not in model_columns.keys():
                    ops.append(
                        CompareOperation(
                            op=ArchiveEntitySchemaField(
                                model_wh_name,
                                benchling_wh_field_name,
                            ),
                            reverse_op=UnarchiveEntitySchemaField(
                                model_wh_name,
                                benchling_wh_field_name,
                            ),
                        )
                    )

                # If the field is found in the model columns, compare benchling to model properties.
                else:
                    model_column_props: BaseFieldProperties = model_columns[
                        benchling_wh_field_name
                    ].properties
                    # If the properties are not the same, Update.
                    if model_column_props != benchling_field_props:
                        ops.append(
                            CompareOperation(
                                op=UpdateEntitySchemaField(
                                    model_wh_name,
                                    benchling_wh_field_name,
                                    BaseFieldProperties(
                                        **benchling_field_props.merge(
                                            model_column_props
                                        )
                                    ),
                                ),
                                reverse_op=UpdateEntitySchemaField(
                                    model_wh_name,
                                    benchling_wh_field_name,
                                    BaseFieldProperties(
                                        **model_column_props.merge(
                                            benchling_field_props
                                        )
                                    ),
                                ),
                            )
                        )
            recreated_benchling_fields = [
                f for f in benchling_schema_fields.keys() if f in model_columns.keys()
            ]
            recreated_model_fields = [
                f for f in model_columns.keys() if f in recreated_benchling_fields
            ]
            if recreated_model_fields != recreated_benchling_fields:
                ops.append(
                    CompareOperation(
                        op=ReorderEntitySchemaFields(
                            model_wh_name, list(model_columns.keys())
                        ),
                        reverse_op=ReorderEntitySchemaFields(
                            model_wh_name, recreated_benchling_fields
                        ),
                    )
                )
            columns_missing_from_benchling_schema = (
                model_columns.keys() - active_benchling_schema_fields.keys()
            )
            # If the model column is not found in the benchling schema, Add.
            for column_name in columns_missing_from_benchling_schema:
                if column_name in archived_benchling_schema_fields.keys():
                    ops.append(
                        CompareOperation(
                            op=UnarchiveEntitySchemaField(
                                model_wh_name,
                                column_name,
                                index=list(model_columns.keys()).index(column_name),
                            ),
                            reverse_op=ArchiveEntitySchemaField(
                                model_wh_name,
                                column_name,
                                index=list(model_columns.keys()).index(column_name),
                            ),
                        )
                    )
                    if (
                        archived_benchling_schema_fields[column_name]
                        != model_columns[column_name].properties
                    ):
                        ops.append(
                            CompareOperation(
                                op=UpdateEntitySchemaField(
                                    model_wh_name,
                                    column_name,
                                    BaseFieldProperties(
                                        **archived_benchling_schema_fields[
                                            column_name
                                        ].merge(model_columns[column_name].properties)
                                    ),
                                ),
                                reverse_op=UpdateEntitySchemaField(
                                    model_wh_name,
                                    column_name,
                                    BaseFieldProperties(
                                        **model_columns[column_name].properties.merge(
                                            archived_benchling_schema_fields[
                                                column_name
                                            ]
                                        )
                                    ),
                                ),
                            )
                        )
                else:
                    ops.append(
                        CompareOperation(
                            op=CreateEntitySchemaField(
                                model_wh_name,
                                column_name,
                                field_props=model_columns[column_name].properties,
                                index=list(model_columns.keys()).index(column_name),
                            ),
                            reverse_op=ArchiveEntitySchemaField(
                                model_wh_name,
                                column_name,
                                index=list(model_columns.keys()).index(column_name),
                            ),
                        )
                    )
            if benchling_schema_props != model.__schema_properties__:
                ops.append(
                    CompareOperation(
                        op=UpdateEntitySchema(
                            model.__schema_properties__.warehouse_name,
                            BaseSchemaProperties(
                                **benchling_schema_props.merge(
                                    model.__schema_properties__
                                )
                            ),
                        ),
                        reverse_op=UpdateEntitySchema(
                            model.__schema_properties__.warehouse_name,
                            BaseSchemaProperties(
                                **model.__schema_properties__.merge(
                                    benchling_schema_props
                                )
                            ),
                        ),
                    ),
                )
        # If the model is not found as the benchling schema, Create.
        # Benchling api does not allow for setting a custom warehouse_name,
        # so we need to run another UpdateEntitySchema to set the warehouse_name if it is different from the snakecase version of the model name.
        else:
            model_props = {name: col.properties for name, col in model_columns.items()}

            ops.append(
                CompareOperation(
                    op=CreateEntitySchema(
                        BaseSchemaProperties(
                            **model.__schema_properties__.model_dump()
                        ),
                        fields=model_props,
                    ),
                    reverse_op=ArchiveEntitySchema(
                        model.__schema_properties__.warehouse_name
                    ),
                )
            )
            benchling_given_wh_name = to_snake_case(model.__schema_properties__.name)
            if model.__schema_properties__.warehouse_name != benchling_given_wh_name:
                ops.append(
                    CompareOperation(
                        op=UpdateEntitySchema(
                            benchling_given_wh_name,
                            BaseSchemaProperties(
                                warehouse_name=model.__schema_properties__.warehouse_name
                            ),
                        ),
                        reverse_op=UpdateEntitySchema(
                            model.__schema_properties__.warehouse_name,
                            BaseSchemaProperties(
                                warehouse_name=benchling_given_wh_name
                            ),
                        ),
                    )
                )

        model_operations[model.__schema_properties__.warehouse_name] = ops
        running_benchling_schema_names = [
            schema_name
            for schema_name in running_benchling_schema_names
            if schema_name != model.__schema_properties__.warehouse_name
        ]
    # Benchling schemas that exist that aren't found as a model, Archive.
    archive_schema_ops: list[CompareOperation] = []
    for schema_name in running_benchling_schema_names:
        if schema_name not in archived_benchling_schema_wh_names:
            archive_schema_ops.append(
                CompareOperation(
                    op=ArchiveEntitySchema(schema_name),
                    reverse_op=UnarchiveEntitySchema(schema_name),
                )
            )
    model_operations["Archive"] = archive_schema_ops
    return {k: sorted(v) for k, v in model_operations.items()}
