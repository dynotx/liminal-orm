from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.connection.benchling_service import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_summary_by_name
from liminal.entity_schemas.api_v3 import list_entity_schemas_with_fields_v3
from liminal.enums import BenchlingEntitySchemaType
from liminal.enums import BenchlingFieldDefinitionType
from liminal.enums import BenchlingLinkDefinitionType
from liminal.enums import BenchlingNamingStrategy
from liminal.enums import NameTemplatePartType
from liminal.enums.sequence_constraint import SequenceConstraint
from liminal.mappers import (
    convert_entity_type_to_entity_schema_type,
    convert_field_type_to_field_definition_type,
)
from liminal.orm.name_template_parts import NameTemplatePart
from liminal.orm.schema_properties import SchemaProperties
from liminal.unit_dictionary.utils import get_unit_id_from_name


class UnitModel(BaseModel):
    """A pydantic model for the unit on a numeric field definition, as returned by the v3 API."""

    id: str


class FieldLinkDefinitionModel(BaseModel):
    """A pydantic model for the object a link field points to (a schema, dropdown, or fieldset), as returned by the v3 API."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    typename: BenchlingLinkDefinitionType = Field(alias="__typename")


class EntitySchemaFieldModel(BaseModel):
    """A pydantic model for an entity schema field definition, as returned by the v3 field-definitions endpoint.
    The field type is given by `typename` (e.g. "TextFieldDefinition"); type-specific properties are optional."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    systemName: str
    archived: bool
    archiveReason: str | None
    createdAt: str
    modifiedAt: str
    isRequired: bool
    derivationType: str
    description: str | None
    typename: BenchlingFieldDefinitionType = Field(alias="__typename")
    isMulti: bool | None = None
    isParent: bool | None = None
    linkDefinition: FieldLinkDefinitionModel | None = None
    numericMin: float | None = None
    numericMax: float | None = None
    displayPrecision: int | None = None
    unit: UnitModel | None = None


class EntitySchemaOrganizationModel(BaseModel):
    """A pydantic model for the organization an entity schema belongs to, as returned by the v3 API."""

    id: str


class EntitySchemaConstraintModel(BaseModel):
    """A pydantic model for the uniqueness constraint on an entity schema, as returned by the v3 API."""

    fieldDefinitionNames: list[str] = []
    hasUniqueResidues: bool | None = None


class NameTemplateFieldReferenceModel(BaseModel):
    """A pydantic model for the field a name template part refers to, as returned by the v3 API."""

    id: str


class NameTemplatePartConfigurationModel(BaseModel):
    """A pydantic model for the configuration of a single part of an entity schema's name template, as returned by the v3 API."""

    field: NameTemplateFieldReferenceModel | None = None
    text: str | None = None


class NameTemplatePartModel(BaseModel):
    """A pydantic model for a single part of an entity schema's name template, as returned by the v3 API."""

    type: NameTemplatePartType
    configuration: NameTemplatePartConfigurationModel | None = None

    def to_name_template_part(
        self, fields: list[EntitySchemaFieldModel]
    ) -> NameTemplatePart:
        part_cls = NameTemplatePart.resolve_type(self.type)
        wh_field_name = None
        value = None
        if self.configuration:
            if self.configuration.field:
                field_id = self.configuration.field.id
                field = next((f for f in fields if f.id == field_id), None)
                if field is None:
                    raise ValueError(f"Field {field_id} not found in fields")
                wh_field_name = field.systemName
            value = self.configuration.text
        return part_cls(
            wh_field_name=wh_field_name, value=value
        )  # TODO: Might have to return class with only necessary properties set.


class NameTemplateModel(BaseModel):
    """A pydantic model for an entity schema's name template, as returned by the v3 API."""

    parts: list[NameTemplatePartModel] = []
    shouldOrderPartsBySequence: bool


class EntitySchemaModel(BaseModel):
    """A pydantic model for an entity schema, as returned by the v3 schema list endpoints.
    Entry schemas omit most registry-related fields, so those are optional."""

    id: str
    name: str
    systemName: str
    description: str
    archived: bool
    archiveReason: str | None
    createdAt: str
    modifiedAt: str
    itemIdPrefix: str
    iconId: str
    organization: EntitySchemaOrganizationModel
    fieldDefinitions: str
    fields: list[EntitySchemaFieldModel] = []
    containableType: str | None = None
    fieldsets: str | None = None
    systemCategories: list[str] | None = None
    includeRegistryIdInChips: bool | None = None
    useRegistryIdForItemDisplayLabel: bool | None = None
    availableRegistrationNamingOptions: list[BenchlingNamingStrategy] | None = None
    constraint: EntitySchemaConstraintModel | None = None
    nameTemplate: NameTemplateModel | None = None
    containerNameTemplate: NameTemplateModel | None = None
    showResidues: bool | None = None
    typedIconId: str | None = None
    allowMeasuredIngredients: bool | None = None
    componentLotTextEnabled: bool | None = None
    componentLotStorageEnabled: bool | None = None
    typename: BenchlingEntitySchemaType = Field(alias="__typename")

    @classmethod
    def get_all_json(
        cls,
        benchling_service: BenchlingService,
    ) -> list[dict[str, Any]]:
        return list_entity_schemas_with_fields_v3(benchling_service)

    @classmethod
    def get_all(
        cls,
        benchling_service: BenchlingService,
        wh_schema_names: set[str] | None = None,
    ) -> list[EntitySchemaModel]:
        schemas_data = cls.get_all_json(benchling_service)
        filtered_schemas: list[EntitySchemaModel] = []
        if wh_schema_names:
            for schema in schemas_data:
                if schema["systemName"] in wh_schema_names:
                    filtered_schemas.append(cls.model_validate(schema))
                if len(filtered_schemas) == len(wh_schema_names):
                    break
        else:
            for schema in schemas_data:
                try:
                    filtered_schemas.append(cls.model_validate(schema))
                except Exception as e:
                    print(f"Error validating schema {schema['systemName']}: {e}")
        return filtered_schemas

    @classmethod
    def get_one(
        cls,
        benchling_service: BenchlingService,
        wh_schema_name: str,
        schemas_data: list[dict[str, Any]] | None = None,
    ) -> EntitySchemaModel:
        if schemas_data is None:
            schemas_data = cls.get_all_json(benchling_service)
        schema = next(
            (
                schema
                for schema in schemas_data
                if schema["systemName"] == wh_schema_name
            ),
            None,
        )
        if schema is None:
            raise ValueError(
                f"Schema {wh_schema_name} not found in Benchling {benchling_service.benchling_tenant}."
            )
        return cls.model_validate(schema)

    @classmethod
    @lru_cache(maxsize=100)
    def get_one_cached(
        cls,
        benchling_service: BenchlingService,
        wh_schema_name: str,
    ) -> EntitySchemaModel:
        return cls.get_one(benchling_service, wh_schema_name)

    def get_field(self, wh_field_name: str) -> EntitySchemaFieldModel:
        """Returns a field from the entity schema by its warehouse field name."""
        for field in self.fields:
            if field.systemName == wh_field_name:
                return field
        raise ValueError(f"Field '{wh_field_name}' not found in schema")

    def get_internal_name_template_parts(self) -> list[NameTemplatePart]:
        if self.nameTemplate is None:
            return []
        return [
            part.to_name_template_part(self.fields) for part in self.nameTemplate.parts
        ]
