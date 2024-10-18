import copy
from unittest.mock import Mock, patch

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.entity_schemas.compare import compare_entity_schemas
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
from liminal.enums import BenchlingFieldType


class TestCompareEntitySchemas:
    def test_compare_benchling_schemas_create(  # type: ignore[no-untyped-def]
        self, mock_benchling_schema_one, mock_benchling_subclasses
    ) -> None:
        with (
            patch(
                "liminal.entity_schemas.compare.get_converted_tag_schemas"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.orm.base_model.BaseModel.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_all_subclasses.return_value = mock_benchling_subclasses

            # Test when there are two models defined but only one in Benchling
            mock_get_benchling_entity_schemas.return_value = mock_benchling_schema_one
            invalid_models = compare_entity_schemas(mock_benchling_sdk)

            mock_get_benchling_entity_schemas.assert_called_once()
            mock_get_all_subclasses.assert_called()
            assert len(invalid_models["mock_entity_two_wh"]) == 2
            assert isinstance(
                invalid_models["mock_entity_two_wh"][0].op, CreateEntitySchema
            )
            assert (
                invalid_models["mock_entity_two_wh"][0].op.schema_properties.name
                == "Mock Entity Two"
            )
            assert list(invalid_models["mock_entity_two_wh"][0].op.fields.keys()) == [
                "parent_link_field"
            ]
            assert isinstance(
                invalid_models["mock_entity_two_wh"][1].op, UpdateEntitySchema
            )
            assert (
                invalid_models["mock_entity_two_wh"][1].op.update_props.warehouse_name
                == "mock_entity_two_wh"
            )

    def test_compare_benchling_schemas_archive(  # type: ignore[no-untyped-def]
        self, mock_benchling_schema_one
    ) -> None:
        with (
            patch(
                "liminal.entity_schemas.compare.get_converted_tag_schemas"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.orm.base_model.BaseModel.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_all_subclasses.return_value = []

            # Test when there are two models defined but only one in Benchling
            mock_get_benchling_entity_schemas.return_value = mock_benchling_schema_one
            invalid_models = compare_entity_schemas(mock_benchling_sdk)

            mock_get_benchling_entity_schemas.assert_called_once()
            mock_get_all_subclasses.assert_called_once()
            assert len(invalid_models["Archive"]) == 1
            assert isinstance(invalid_models["Archive"][0].op, ArchiveEntitySchema)
            assert invalid_models["Archive"][0].op.wh_schema_name == "mock_entity_one"

    def test_compare_benchling_schemas_unarchive(  # type: ignore[no-untyped-def]
        self, mock_benchling_schema_archived, mock_benchling_subclass_small
    ) -> None:
        with (
            patch(
                "liminal.entity_schemas.compare.get_converted_tag_schemas"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.orm.base_model.BaseModel.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_benchling_entity_schemas.return_value = (
                mock_benchling_schema_archived
            )
            mock_get_all_subclasses.return_value = mock_benchling_subclass_small
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            mock_get_benchling_entity_schemas.assert_called_once()
            mock_get_all_subclasses.assert_called_once()
            assert len(invalid_models["mock_entity_small"]) == 2
            assert isinstance(
                invalid_models["mock_entity_small"][0].op, UnarchiveEntitySchema
            )
            assert (
                invalid_models["mock_entity_small"][0].op.wh_schema_name
                == "mock_entity_small"
            )
            assert isinstance(
                invalid_models["mock_entity_small"][1].op, ArchiveEntitySchemaField
            )
            assert (
                invalid_models["mock_entity_small"][1].op.wh_field_name
                == "string_field_req_2"
            )

    def test_compare_benchling_schema_fields(  # type: ignore[no-untyped-def]
        self,
        mock_benchling_schema,
        mock_benchling_subclass,
        mock_false_benchling_dropdown,
        mock_benchling_dropdown,
    ) -> None:
        with (
            patch(
                "liminal.entity_schemas.compare.get_converted_tag_schemas"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.orm.base_model.BaseModel.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_all_subclasses.return_value = mock_benchling_subclass

            # Test when the Benchling schema is the exact same as the model
            mock_get_benchling_entity_schemas.return_value = mock_benchling_schema
            invalid_models = compare_entity_schemas(mock_benchling_sdk)

            mock_get_benchling_entity_schemas.assert_called_once()
            mock_get_all_subclasses.assert_called_once()
            assert len(invalid_models["mock_entity"]) == 0

            # Test when the Benchling schema is missing a field compared to the table model
            missing_field = copy.deepcopy(mock_benchling_schema)
            missing_field[0][1].pop("string_field_req")
            mock_get_benchling_entity_schemas.return_value = missing_field
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, CreateEntitySchemaField
            )
            assert (
                invalid_models["mock_entity"][0].op.wh_field_name == "string_field_req"
            )

            # Test when the Benchling schema has an extra field compared to the table model
            extra_field = copy.deepcopy(mock_benchling_schema)
            extra_field[0][1]["extra_field"] = BaseFieldProperties(
                name="Extra Field",
                type=BenchlingFieldType.TEXT,
                required=False,
                is_multi=False,
                dropdown_link=None,
            ).set_archived(False)

            mock_get_benchling_entity_schemas.return_value = extra_field
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, ArchiveEntitySchemaField
            )
            assert invalid_models["mock_entity"][0].op.wh_field_name == "extra_field"

            # Test when the Benchling schema has a required field and the model field is nullable (not required)
            benchling_switched_required_field = copy.deepcopy(mock_benchling_schema)
            benchling_switched_required_field[0][1]["enum_field"].required = True
            mock_get_benchling_entity_schemas.return_value = (
                benchling_switched_required_field
            )
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, UpdateEntitySchemaField
            )
            update_props_dict = invalid_models["mock_entity"][
                0
            ].op.update_props.model_dump(exclude_unset=True)
            assert len(update_props_dict.keys()) == 1
            assert update_props_dict["required"] is False

            # Test when the Benchling schema has a non required field and the model field is not nullable (required)
            benchling_switched_required_field = copy.deepcopy(mock_benchling_schema)
            benchling_switched_required_field[0][1]["string_field_req"].required = False
            mock_get_benchling_entity_schemas.return_value = (
                benchling_switched_required_field
            )
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, UpdateEntitySchemaField
            )
            update_props_dict = invalid_models["mock_entity"][
                0
            ].op.update_props.model_dump(exclude_unset=True)
            assert len(update_props_dict.keys()) == 1
            assert update_props_dict["required"] is True

            # Test when the Benchling schema has a non multi field and the model field is a list
            benchling_switched_multi_field = copy.deepcopy(mock_benchling_schema)
            benchling_switched_multi_field[0][1]["list_dropdown_field"].is_multi = False
            mock_get_benchling_entity_schemas.return_value = (
                benchling_switched_multi_field
            )
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, UpdateEntitySchemaField
            )
            update_props_dict = invalid_models["mock_entity"][
                0
            ].op.update_props.model_dump(exclude_unset=True)
            assert len(update_props_dict.keys()) == 1
            assert update_props_dict["is_multi"] is True

            # Test when the Benchling schema has a multi field and the model field is not a list
            benchling_switched_multi_field = copy.deepcopy(mock_benchling_schema)
            benchling_switched_multi_field[0][1]["enum_field"].is_multi = True
            mock_get_benchling_entity_schemas.return_value = (
                benchling_switched_multi_field
            )
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, UpdateEntitySchemaField
            )
            update_props_dict = invalid_models["mock_entity"][
                0
            ].op.update_props.model_dump(exclude_unset=True)
            assert len(update_props_dict.keys()) == 1
            assert update_props_dict["is_multi"] is False

            # Test when the multi field in the Benchling schema has a different entity type than the model field
            benchling_false_entity_type = copy.deepcopy(mock_benchling_schema)
            benchling_false_entity_type[0][1][
                "list_dropdown_field"
            ].type = BenchlingFieldType.INTEGER
            mock_get_benchling_entity_schemas.return_value = benchling_false_entity_type
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, UpdateEntitySchemaField
            )
            update_props_dict = invalid_models["mock_entity"][
                0
            ].op.update_props.model_dump(exclude_unset=True)
            assert len(update_props_dict.keys()) == 1
            assert update_props_dict["type"] is BenchlingFieldType.DROPDOWN

            # Test when enum field in the Benchling schema has a different enum than the model field
            benchling_false_enum = copy.deepcopy(mock_benchling_schema)
            benchling_false_enum[0][1][
                "enum_field"
            ].dropdown_link = mock_false_benchling_dropdown.__benchling_name__
            mock_get_benchling_entity_schemas.return_value = benchling_false_enum
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, UpdateEntitySchemaField
            )
            update_props_dict = invalid_models["mock_entity"][
                0
            ].op.update_props.model_dump(exclude_unset=True)
            assert len(update_props_dict.keys()) == 1
            assert (
                update_props_dict["dropdown_link"]
                is mock_benchling_dropdown.__benchling_name__
            )

            # Test mismatching table/schema properties
            benchling_mismatch_schema = copy.deepcopy(mock_benchling_schema)
            benchling_mismatch_schema[0][0].name = "MismatchName"
            mock_get_benchling_entity_schemas.return_value = benchling_mismatch_schema
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(invalid_models["mock_entity"][0].op, UpdateEntitySchema)
            update_props_dict = invalid_models["mock_entity"][
                0
            ].op.update_props.model_dump(exclude_unset=True)
            assert len(update_props_dict.keys()) == 1
            assert update_props_dict["name"] == "Mock Entity"

            # Test when the Benchling schema has an archived field that is in the model
            create_existing_field_schema = copy.deepcopy(mock_benchling_schema)
            create_existing_field_schema[0][1]["string_field_req"].set_archived(True)
            mock_get_benchling_entity_schemas.return_value = (
                create_existing_field_schema
            )
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, UnarchiveEntitySchemaField
            )

            # Test when Benchling schema fields are out of order
            benchling_unordered_fields_schema = copy.deepcopy(mock_benchling_schema)
            fields = benchling_unordered_fields_schema[0][1]
            keys = list(fields.keys())
            idx1, idx2 = (
                keys.index("string_field_req"),
                keys.index("string_field_not_req"),
            )
            keys[idx1], keys[idx2] = keys[idx2], keys[idx1]
            new_fields = {k: fields[k] for k in keys}
            new_benchling_unordered_fields_schema = [
                (benchling_unordered_fields_schema[0][0], new_fields)
            ]
            mock_get_benchling_entity_schemas.return_value = (
                new_benchling_unordered_fields_schema
            )
            invalid_models = compare_entity_schemas(mock_benchling_sdk)
            assert len(invalid_models["mock_entity"]) == 1
            assert isinstance(
                invalid_models["mock_entity"][0].op, ReorderEntitySchemaFields
            )
