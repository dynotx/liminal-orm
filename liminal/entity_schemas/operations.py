from typing import Any, ClassVar

from liminal.base.base_operation import BaseOperation
from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.base.properties.base_schema_properties import BaseSchemaProperties
from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_id_name_map
from liminal.entity_schemas.api import (
    archive_tag_schemas,
    create_entity_schema,
    unarchive_tag_schemas,
    update_tag_schema,
)
from liminal.entity_schemas.entity_schema_models import CreateEntitySchemaModel
from liminal.entity_schemas.tag_schema_models import (
    CreateTagSchemaFieldModel,
    TagSchemaModel,
    UpdateTagSchemaModel,
)
from liminal.entity_schemas.utils import (
    convert_tag_schema_field_to_field_properties,
    convert_tag_schema_to_internal_schema,
)
from liminal.enums.benchling_naming_strategy import BenchlingNamingStrategy
from liminal.orm.schema_properties import SchemaProperties


class CreateEntitySchema(BaseOperation):
    order: ClassVar[int] = 80

    def __init__(
        self,
        schema_properties: BaseSchemaProperties,
        fields: dict[str, BaseFieldProperties],
    ) -> None:
        self.schema_properties = schema_properties
        self.fields = fields
        self._validated_schema_properties = SchemaProperties(
            **schema_properties.model_dump()
        )

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        try:
            schema = TagSchemaModel.get_one(
                benchling_service, self._validated_schema_properties.warehouse_name
            )
        except ValueError:
            schema = None
        if schema is None:
            self._validate_create(benchling_service)
            return self._execute_create(benchling_service)
        else:
            self._validate_unarchive(benchling_service, schema)
            return UnarchiveEntitySchema(
                self._validated_schema_properties.warehouse_name
            ).execute(benchling_service)

    def _execute_create(self, benchling_service: BenchlingService) -> dict[str, Any]:
        create_model = CreateEntitySchemaModel.from_benchling_props(
            self._validated_schema_properties, self.fields, benchling_service
        )
        return create_entity_schema(
            benchling_service, create_model.model_dump(exclude_none=True)
        )

    def describe_operation(self) -> str:
        return f"{self._validated_schema_properties.name}: Creating new entity schema with fields: {','.join(self.fields.keys())}."

    def describe(self) -> str:
        return f"{self._validated_schema_properties.name}: Schema is defined in code but not in Benchling."

    def _validate_create(self, benchling_service: BenchlingService) -> None:
        all_schemas = TagSchemaModel.get_all_json(benchling_service)
        if self._validated_schema_properties.name in [
            schema["name"] for schema in all_schemas
        ]:
            raise ValueError(
                f"Entity schema name {self._validated_schema_properties.name} already exists in Benchling."
            )
        if self._validated_schema_properties.warehouse_name in [
            schema["sqlIdentifier"] for schema in all_schemas
        ]:
            raise ValueError(
                f"Entity schema name {self._validated_schema_properties.name} already exists in Benchling."
            )
        if self._validated_schema_properties.warehouse_name in [
            schema["sqlIdentifier"] for schema in all_schemas
        ]:
            raise ValueError(
                f"Entity schema warehouse name {self._validated_schema_properties.warehouse_name} already exists in Benchling."
            )
        if self._validated_schema_properties.prefix in [
            schema["prefix"] for schema in all_schemas
        ]:
            raise ValueError(
                f"Entity schema prefix {self._validated_schema_properties.prefix} already exists in Benchling."
            )
        if any(
            BenchlingNamingStrategy.is_template_based(strategy)
            for strategy in self._validated_schema_properties.naming_strategies
        ):
            raise ValueError(
                "Invalid naming strategies for schema. Cannot create entity schema using template-based naming strategies."
            )
        return None

    def _validate_unarchive(
        self, benchling_service: BenchlingService, schema: TagSchemaModel
    ) -> None:
        if schema.archiveRecord is None:
            raise ValueError(
                f"Entity schema {self._validated_schema_properties.warehouse_name} is already active in Benchling."
            )
        dropdowns_map = get_benchling_dropdown_id_name_map(benchling_service)
        benchling_schema_props, benchling_fields_props = (
            convert_tag_schema_to_internal_schema(schema, dropdowns_map)
        )
        if (
            self._validated_schema_properties != benchling_schema_props
            or self.fields != benchling_fields_props
        ):
            raise ValueError(
                f"Entity schema {self._validated_schema_properties.warehouse_name} is different in code versus Benchling. Cannot unarchive."
            )
        return None


class ArchiveEntitySchema(BaseOperation):
    order: ClassVar[int] = 180

    def __init__(self, wh_schema_name: str) -> None:
        self.wh_schema_name = wh_schema_name

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = self._validate(benchling_service)
        return archive_tag_schemas(benchling_service, [tag_schema.id])

    def describe_operation(self) -> str:
        return f"{self.wh_schema_name}: Archiving entity schema."

    def describe(self) -> str:
        return f"{self.wh_schema_name}: Schema is defined in Benchling but not in code anymore."

    def _validate(self, benchling_service: BenchlingService) -> TagSchemaModel:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        if tag_schema.archiveRecord is not None:
            raise ValueError(
                f"Entity schema {self.wh_schema_name} is already archived in Benchling."
            )
        return tag_schema


class UnarchiveEntitySchema(BaseOperation):
    order: ClassVar[int] = 110

    def __init__(self, wh_schema_name: str) -> None:
        self.wh_schema_name = wh_schema_name

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = self._validate(benchling_service)
        return unarchive_tag_schemas(benchling_service, [tag_schema.id])

    def describe_operation(self) -> str:
        return f"{self.wh_schema_name}: Unarchiving entity schema."

    def describe(self) -> str:
        return f"{self.wh_schema_name}: Schema is archived in Benchling but is defined in code again."

    def _validate(self, benchling_service: BenchlingService) -> TagSchemaModel:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        if tag_schema.archiveRecord is None:
            raise ValueError(
                f"Entity schema {self.wh_schema_name} is already unarchived in Benchling."
            )
        return tag_schema


class UpdateEntitySchema(BaseOperation):
    order: ClassVar[int] = 90

    def __init__(
        self,
        wh_schema_name: str,
        update_props: BaseSchemaProperties,
    ) -> None:
        self.wh_schema_name = wh_schema_name
        self.update_props = update_props

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = self._validate(benchling_service)
        updated_tag_schema = tag_schema.update_schema_props(
            self.update_props.model_dump(exclude_unset=True)
        )
        update = UpdateTagSchemaModel(**updated_tag_schema.model_dump())
        return update_tag_schema(benchling_service, tag_schema.id, update.model_dump())

    def describe_operation(self) -> str:
        return f"Updating properties for entity schema {self.wh_schema_name}: {str(self.update_props)}."

    def describe(self) -> str:
        return f"Schema properties for {self.wh_schema_name} are different in code versus Benchling: {str(self.update_props)}."

    def _validate(self, benchling_service: BenchlingService) -> TagSchemaModel:
        all_schemas = TagSchemaModel.get_all_json(benchling_service)
        tag_schema = TagSchemaModel.get_one(
            benchling_service, self.wh_schema_name, all_schemas
        )
        if self.update_props.name and self.update_props.name in [
            schema["name"] for schema in all_schemas
        ]:
            raise ValueError(
                f"Entity schema name {self.update_props.name} already exists in Benchling."
            )
        if self.update_props.warehouse_name and self.update_props.warehouse_name in [
            schema["sqlIdentifier"] for schema in all_schemas
        ]:
            raise ValueError(
                f"Entity schema warehouse name {self.update_props.warehouse_name} already exists in Benchling."
            )
        if self.update_props.prefix and self.update_props.prefix in [
            schema["prefix"] for schema in all_schemas
        ]:
            raise ValueError(
                f"Entity schema prefix {self.update_props.prefix} already exists in Benchling."
            )
        if (
            self.update_props.naming_strategies
            and not BenchlingNamingStrategy.is_valid_set(
                self.update_props.naming_strategies, bool(tag_schema.nameTemplateParts)
            )
        ):
            raise ValueError(
                "Invalid naming strategies for schema. The name template must be set on the schema through the UI when using template-based naming strategies."
            )
        return tag_schema


class UpdateEntitySchemaName(BaseOperation):
    order: ClassVar[int] = 100

    def __init__(
        self,
        old_wh_schema_name: str,
        new_wh_schema_name: str,
    ) -> None:
        self.old_wh_schema_name = old_wh_schema_name
        self.new_wh_schema_name = new_wh_schema_name

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = self._validate(benchling_service)
        update = UpdateTagSchemaModel(sqlIdentifier=self.new_wh_schema_name)
        return update_tag_schema(
            benchling_service, tag_schema.id, update.model_dump(exclude_unset=True)
        )

    def _validate(self, benchling_service: BenchlingService) -> TagSchemaModel:
        all_schemas = TagSchemaModel.get_all(benchling_service)
        tag_schema = next(
            (s for s in all_schemas if s.sqlIdentifier == self.old_wh_schema_name), None
        )
        if tag_schema is None:
            raise ValueError(
                f"Entity schema {self.old_wh_schema_name} does not exist in Benchling."
            )
        new_tag_schema = next(
            (s for s in all_schemas if s.sqlIdentifier == self.new_wh_schema_name), None
        )
        if new_tag_schema is not None:
            raise ValueError(
                f"Entity schema warehouse name {self.new_wh_schema_name} already exists in Benchling."
            )
        return tag_schema

    def describe_operation(self) -> str:
        return f"{self.old_wh_schema_name}: Renaming entity schema warehouse name to {self.new_wh_schema_name}."

    def describe(self) -> str:
        return f"{self.old_wh_schema_name}: Entity schema in Benchling has a different warehouse name than in code."


class CreateEntitySchemaField(BaseOperation):
    order: ClassVar[int] = 120

    def __init__(
        self,
        wh_schema_name: str,
        wh_field_name: str,
        field_props: BaseFieldProperties,
        index: int,
    ) -> None:
        self.wh_schema_name = wh_schema_name
        self.wh_field_name = wh_field_name
        self.field_props = field_props
        self.index = index

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        try:
            field = TagSchemaModel.get_one(
                benchling_service, self.wh_schema_name
            ).get_field(self.wh_field_name)
        except ValueError:
            field = None
        if field is None:
            return self._execute_create(benchling_service)
        else:
            if field.archiveRecord is None:
                raise ValueError(
                    f"Field {self.wh_field_name} is already active on entity schema {self.wh_schema_name}."
                )
            dropdowns_map = get_benchling_dropdown_id_name_map(benchling_service)
            if self.field_props == convert_tag_schema_field_to_field_properties(
                field, dropdowns_map
            ):
                return UnarchiveEntitySchemaField(
                    self.wh_schema_name, self.wh_field_name, self.index
                ).execute(benchling_service)
            else:
                raise ValueError(
                    f"Field {self.wh_field_name} on entity schema {self.wh_schema_name} is different in code versus Benchling."
                )

    def _execute_create(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        existing_new_field = next(
            (f for f in tag_schema.allFields if f.systemName == self.wh_field_name),
            None,
        )
        if existing_new_field:
            raise ValueError(
                f"Field {self.wh_field_name} already exists on entity schema {self.wh_schema_name} and is {'archived' if existing_new_field.archiveRecord is not None else 'active'} in Benchling."
            )
        index_to_insert = (
            self.index if self.index is not None else len(tag_schema.allFields)
        )
        new_field = CreateTagSchemaFieldModel.from_props(
            self.wh_field_name, self.field_props, benchling_service
        )
        fields_for_update = tag_schema.allFields
        fields_for_update.insert(index_to_insert, new_field)  # type: ignore
        return update_tag_schema(
            benchling_service,
            tag_schema.id,
            {"fields": [f.model_dump() for f in fields_for_update]},
        )

    def describe_operation(self) -> str:
        return f"{self.wh_schema_name}: Creating entity schema field '{self.wh_field_name}' at index {self.index}."

    def describe(self) -> str:
        return f"{self.wh_schema_name}: Entity schema field '{self.wh_field_name}' is not defined in Benchling but is defined in code."


class ArchiveEntitySchemaField(BaseOperation):
    order: ClassVar[int] = 160

    def __init__(
        self, wh_schema_name: str, wh_field_name: str, index: int | None = None
    ) -> None:
        self.wh_schema_name = wh_schema_name
        self.wh_field_name = wh_field_name
        self.index = index

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        existing_field = next(
            (f for f in tag_schema.allFields if f.systemName == self.wh_field_name),
            None,
        )
        if existing_field is None:
            raise ValueError(
                f"Field {self.wh_field_name} does not exist on entity schema {self.wh_schema_name} in Benchling."
            )
        if existing_field.archiveRecord:
            raise ValueError(
                f"Field {self.wh_field_name} is already archived on entity schema {self.wh_schema_name}."
            )
        # The query will fail if the field is used in calculated fields or name template or constraints. Not covered atm. TODO
        updated_tag_schema = tag_schema.archive_field(self.wh_field_name)
        return update_tag_schema(
            benchling_service,
            tag_schema.id,
            {"fields": [f.model_dump() for f in updated_tag_schema.allFields]},
        )

    def describe_operation(self) -> str:
        return f"{self.wh_schema_name}: Archiving entity schema field '{self.wh_field_name}'."

    def describe(self) -> str:
        return f"{self.wh_schema_name}: Entity schema field '{self.wh_field_name}' is defined in Benchling but not in code."

    def _validate(self, benchling_service: BenchlingService) -> TagSchemaModel:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        field = tag_schema.get_field(self.wh_field_name)
        if (
            tag_schema.nameTemplateFields
            and field.name in tag_schema.nameTemplateFields
        ):
            raise ValueError(
                f"Cannot archive field {self.wh_field_name} on entity schema {self.wh_schema_name}. Field is used in name template."
            )
        return tag_schema


class UnarchiveEntitySchemaField(BaseOperation):
    order: ClassVar[int] = 130

    def __init__(
        self, wh_schema_name: str, wh_field_name: str, index: int | None = None
    ) -> None:
        self.wh_schema_name = wh_schema_name
        self.wh_field_name = wh_field_name
        self.index = index

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        existing_field = next(
            (f for f in tag_schema.allFields if f.systemName == self.wh_field_name),
            None,
        )
        if existing_field is None:
            raise ValueError(
                f"Field {self.wh_field_name} does not exist on entity schema {self.wh_schema_name} in Benchling."
            )
        if existing_field.archiveRecord is None:
            raise ValueError(
                f"Field {self.wh_field_name} is already active on entity schema {self.wh_schema_name}."
            )
        updated_tag_schema = tag_schema.unarchive_field(self.wh_field_name)
        index_to_insert = (
            self.index if self.index is not None else len(updated_tag_schema.allFields)
        )
        fields_for_update = updated_tag_schema.allFields
        archived_field = next(
            f for f in fields_for_update if f.systemName == self.wh_field_name
        )
        fields_for_update.remove(archived_field)
        fields_for_update.insert(index_to_insert, archived_field)
        return update_tag_schema(
            benchling_service,
            updated_tag_schema.id,
            {"fields": [f.model_dump() for f in fields_for_update]},
        )

    def describe_operation(self) -> str:
        return f"{self.wh_schema_name}: Unarchiving entity schema field '{self.wh_field_name}'."

    def describe(self) -> str:
        return f"{self.wh_schema_name}: Entity schema field '{self.wh_field_name}' is archived in Benchling but is defined in code again."


class UpdateEntitySchemaField(BaseOperation):
    order: ClassVar[int] = 14

    def __init__(
        self,
        wh_schema_name: str,
        wh_field_name: str,
        update_props: BaseFieldProperties,
    ) -> None:
        self.wh_schema_name = wh_schema_name
        self.wh_field_name = wh_field_name
        self.update_props = update_props

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = self._validate(benchling_service)
        updated_tag_schema = tag_schema.update_field(
            benchling_service,
            self.wh_field_name,
            self.update_props.model_dump(exclude_unset=True),
        )
        return update_tag_schema(
            benchling_service,
            tag_schema.id,
            {"fields": [f.model_dump() for f in updated_tag_schema.allFields]},
        )

    def describe_operation(self) -> str:
        return f"{self.wh_schema_name}: Updating entity schema field '{self.wh_field_name}': {str(self.update_props)}."

    def describe(self) -> str:
        return f"{self.wh_schema_name}: Entity schema field '{self.wh_field_name}' in Benchling is different than in code: {str(self.update_props)}."

    def _validate(self, benchling_service: BenchlingService) -> TagSchemaModel:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        # Only if changing name of field
        if self.update_props.name:
            existing_new_field = next(
                (f for f in tag_schema.allFields if f.name == self.update_props.name),
                None,
            )
            if existing_new_field:
                raise ValueError(
                    f"New field name {self.update_props.name} already exists on entity schema {self.wh_schema_name} and is {'archived' if existing_new_field.archiveRecord is not None else 'active'} in Benchling."
                )
        return tag_schema


class UpdateEntitySchemaFieldName(BaseOperation):
    order: ClassVar[int] = 150

    def __init__(
        self,
        wh_schema_name: str,
        old_wh_field_name: str,
        new_wh_field_name: str,
    ) -> None:
        self.wh_schema_name = wh_schema_name
        self.old_wh_field_name = old_wh_field_name
        self.new_wh_field_name = new_wh_field_name

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        existing_new_field = next(
            (f for f in tag_schema.allFields if f.systemName == self.new_wh_field_name),
            None,
        )
        if existing_new_field is not None:
            raise ValueError(
                f"Field {self.new_wh_field_name} already exists on entity schema {self.wh_schema_name}."
            )
        updated_tag_schema = tag_schema.update_field_wh_name(
            self.old_wh_field_name, self.new_wh_field_name
        )
        return update_tag_schema(
            benchling_service,
            tag_schema.id,
            {"fields": [f.model_dump() for f in updated_tag_schema.allFields]},
        )

    def describe_operation(self) -> str:
        return f"{self.wh_schema_name}: Renaming entity schema field from '{self.old_wh_field_name}' to '{self.new_wh_field_name}'."

    def describe(self) -> str:
        return f"{self.wh_schema_name}: Entity schema field '{self.old_wh_field_name}' in Benchling has wh_name '{self.new_wh_field_name}' in code."


class ReorderEntitySchemaFields(BaseOperation):
    order: ClassVar[int] = 170

    def __init__(self, wh_schema_name: str, new_order: list[str]) -> None:
        self.wh_schema_name = wh_schema_name
        self.new_order = new_order

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        tag_schema = TagSchemaModel.get_one(benchling_service, self.wh_schema_name)
        updated_tag_schema = tag_schema.reorder_fields(self.new_order)
        return update_tag_schema(
            benchling_service,
            tag_schema.id,
            {"fields": [f.model_dump() for f in updated_tag_schema.allFields]},
        )

    def describe_operation(self) -> str:
        return f"{self.wh_schema_name}: Reordering fields."

    def describe(self) -> str:
        return f"{self.wh_schema_name}: Order of fields is different in code versus Benchling."
