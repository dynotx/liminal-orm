from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
)

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.base.properties.base_name_template import BaseNameTemplate
from liminal.base.properties.base_schema_properties import BaseSchemaProperties
from liminal.connection.benchling_service import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_summary_by_name
from liminal.entity_schemas.api_v3 import (
    attach_entity_schema_field_definitions_v3,
    list_entity_schemas_v3,
    list_entity_schemas_with_fields_v3,
)
from liminal.enums import BenchlingEntitySchemaType
from liminal.enums import BenchlingEntityType
from liminal.enums import BenchlingFieldDefinitionInputType
from liminal.enums import BenchlingFieldDefinitionType
from liminal.enums import BenchlingLinkDefinitionType
from liminal.enums import BenchlingNamingStrategy
from liminal.enums import NameTemplatePartType
from liminal.enums import SequenceConstraint
from liminal.mappers import (
    convert_entity_schema_type_to_entity_type,
    convert_field_definition_type_to_field_definition_input_type,
    convert_field_type_to_field_definition_input_type,
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

    def update_from_props(
        self,
        update_diff: dict[str, Any],
        benchling_service: BenchlingService | None = None,
    ) -> EntitySchemaFieldModel:
        """Updates the entity schema field given the field properties defined in code.

        Parameters
        ----------
        update_diff : dict[str, Any]
            A dictionary of the field properties diff to update the entity schema field with.
            Only the fields that are in the dictionary are updated in the entity schema field model.
        benchling_service : BenchlingService | None
            The benchling service to use to look up linked schemas, dropdowns, and units if needed.

        Returns
        -------
        EntitySchemaFieldModel
            The updated entity schema field model.
        """
        update_diff_names = list(update_diff.keys())
        update_props = BaseFieldProperties(**update_diff)
        self.name = (
            update_props.name
            if "name" in update_diff_names and update_props.name is not None
            else self.name
        )
        self.systemName = (
            update_props.warehouse_name
            if "warehouse_name" in update_diff_names
            and update_props.warehouse_name is not None
            else self.systemName
        )
        self.isRequired = (
            update_props.required
            if "required" in update_diff_names and update_props.required is not None
            else self.isRequired
        )
        self.isMulti = (
            update_props.is_multi if "is_multi" in update_diff_names else self.isMulti
        )
        self.isParent = (
            update_props.parent_link
            if "parent_link" in update_diff_names
            else self.isParent
        )
        self.description = (
            update_props.tooltip if "tooltip" in update_diff_names else self.description
        )
        if "entity_link" in update_diff_names and update_props.entity_link:
            if benchling_service is None:
                raise ValueError(
                    "Benchling SDK must be provided to update entity link field."
                )
            linked_schema = EntitySchemaModel.get_one_cached(
                benchling_service, update_props.entity_link
            )
            self.linkDefinition = FieldLinkDefinitionModel(
                id=linked_schema.id,
                typename=BenchlingLinkDefinitionType(linked_schema.typename.value),
            )
        if "type" in update_diff_names and update_props.type:
            linked_schema_type = (
                BenchlingEntitySchemaType(self.linkDefinition.typename.value)
                if self.linkDefinition
                and self.linkDefinition.typename.is_entity_schema_type()
                else None
            )
            self.typename = convert_field_type_to_field_definition_type(
                update_props.type, linked_schema_type
            )
        if "dropdown_link" in update_diff_names and update_props.dropdown_link:
            if benchling_service is None:
                raise ValueError(
                    "Benchling SDK must be provided to update dropdown field."
                )
            dropdown_summary_id = get_benchling_dropdown_summary_by_name(
                benchling_service, update_props.dropdown_link
            ).id
            self.linkDefinition = FieldLinkDefinitionModel(
                id=dropdown_summary_id,
                typename=BenchlingLinkDefinitionType.DROPDOWN,
            )
        self.displayPrecision = (
            update_props.decimal_places
            if "decimal_places" in update_diff_names
            else self.displayPrecision
        )
        if "unit_name" in update_diff_names:
            if update_props.unit_name is None:
                self.unit = None
            else:
                if benchling_service is None:
                    raise ValueError(
                        "Benchling SDK must be provided to update unit field."
                    )
                self.unit = UnitModel(
                    id=get_unit_id_from_name(benchling_service, update_props.unit_name)
                )
        return self


class EntitySchemaFieldInputModel(BaseModel):
    """A pydantic model for a field definition input to the v3 create entity schema and set-field-definitions endpoints.
    Benchling rejects properties that do not apply to the field's `type`, so only the applicable ones are set.
    Existing fields passed to set-field-definitions must have `id` set, otherwise Benchling creates a new field.
    Dump with `exclude_none=True`, since Benchling rejects nulls for every property except `linkDefinitionId`."""

    id: str | None = None
    name: str
    systemName: str
    type: BenchlingFieldDefinitionInputType
    isRequired: bool
    description: str | None = None
    archived: bool | None = None
    archiveReason: str | None = None
    isMulti: bool | None = None
    isParent: bool | None = None
    linkDefinitionId: str | None = None
    dropdownId: str | None = None
    unitId: str | None = None
    numericMin: float | None = None
    numericMax: float | None = None
    displayPrecision: int | None = None

    @model_serializer(mode="wrap")
    def _serialize(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data = handler(self)
        if self.type.requires_link_definition_id():
            data["linkDefinitionId"] = self.linkDefinitionId
        return data

    @classmethod
    def from_field_model(
        cls, field: EntitySchemaFieldModel
    ) -> EntitySchemaFieldInputModel:
        """Generates an EntitySchemaFieldInputModel for an existing field, so it is kept as is when passed to set-field-definitions.

        Parameters
        ----------
        field : EntitySchemaFieldModel
            The field definition, as returned by the v3 API.

        Returns
        -------
        EntitySchemaFieldInputModel
            A pydantic model for a v3 field definition input that updates the existing field.
        """
        field_type = convert_field_definition_type_to_field_definition_input_type(
            field.typename
        )
        link_id = field.linkDefinition.id if field.linkDefinition else None
        is_numeric = field_type.is_numeric()
        return cls(
            id=field.id,
            name=field.name,
            systemName=field.systemName,
            type=field_type,
            isRequired=field.isRequired,
            description=field.description,
            archived=True if field.archived else None,
            archiveReason=field.archiveReason if field.archived else None,
            isMulti=(field.isMulti or False)
            if field_type.supports_is_multi()
            else None,
            isParent=field.isParent if field_type.is_schema_link() else None,
            linkDefinitionId=link_id
            if field_type.requires_link_definition_id()
            else None,
            dropdownId=link_id
            if field_type == BenchlingFieldDefinitionInputType.DROPDOWN
            else None,
            unitId=field.unit.id if field.unit and field_type.supports_unit() else None,
            numericMin=field.numericMin if is_numeric else None,
            numericMax=field.numericMax if is_numeric else None,
            displayPrecision=field.displayPrecision
            if field_type.supports_display_precision()
            else None,
        )

    @classmethod
    def from_benchling_props(
        cls,
        field_props: BaseFieldProperties,
        benchling_service: BenchlingService,
    ) -> EntitySchemaFieldInputModel:
        """Generates an EntitySchemaFieldInputModel from the given internal definition of benchling field properties.

        Parameters
        ----------
        field_props : BaseFieldProperties
            The field properties.
        benchling_service : BenchlingService
            The Benchling service instance used to look up linked schemas, dropdowns, and units.

        Returns
        -------
        EntitySchemaFieldInputModel
            A pydantic model for a v3 field definition input.
        """
        if field_props.type is None:
            raise ValueError(f"Field {field_props.warehouse_name} must have a type.")
        link_definition_id = None
        linked_schema_type = None
        if field_props.entity_link is not None:
            linked_schema = EntitySchemaModel.get_one_cached(
                benchling_service, field_props.entity_link
            )
            link_definition_id = linked_schema.id
            linked_schema_type = linked_schema.typename
        field_type = convert_field_type_to_field_definition_input_type(
            field_props.type, linked_schema_type
        )
        dropdown_id = None
        if field_props.dropdown_link is not None:
            dropdown_id = get_benchling_dropdown_summary_by_name(
                benchling_service, field_props.dropdown_link
            ).id
        unit_id = None
        if field_props.unit_name is not None and field_type.supports_unit():
            unit_id = get_unit_id_from_name(benchling_service, field_props.unit_name)
        return cls(
            name=field_props.name,
            systemName=field_props.warehouse_name,
            type=field_type,
            isRequired=field_props.required or False,
            description=field_props.tooltip,
            isMulti=(field_props.is_multi or False)
            if field_type.supports_is_multi()
            else None,
            isParent=field_props.parent_link if field_type.is_schema_link() else None,
            linkDefinitionId=link_definition_id
            if field_type.requires_link_definition_id()
            else None,
            dropdownId=dropdown_id,
            unitId=unit_id,
            displayPrecision=field_props.decimal_places
            if field_type.supports_display_precision()
            else None,
        )


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

    @classmethod
    def from_name_template_part(
        cls, part: NameTemplatePart, fields: list[EntitySchemaFieldModel]
    ) -> NameTemplatePartModel:
        data = part.model_dump()
        field_reference = None
        if wh_field_name := data.get("wh_field_name"):
            field = next((f for f in fields if f.systemName == wh_field_name), None)
            if field is None:
                raise ValueError(f"Field {wh_field_name} not found in fields")
            if (
                part.component_type == NameTemplatePartType.CHILD_ENTITY_LOT_NUMBER
                or part.component_type
                == NameTemplatePartType.LINKED_BIOENTITY_REGISTRY_IDENTIFIER
            ) and not field.isParent:
                raise ValueError(
                    f"Field {wh_field_name} is not a parent link field. The field for type {part.component_type} must be a parent link field."
                )
            field_reference = NameTemplateFieldReferenceModel(id=field.id)
        text = data.get("value")
        configuration = (
            NameTemplatePartConfigurationModel(field=field_reference, text=text)
            if field_reference is not None or text is not None
            else None
        )
        return cls(type=part.component_type, configuration=configuration)

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


class NameTemplatePartConfigurationInputModel(BaseModel):
    """A pydantic model for the configuration of a name template part input to the v3 entity schema endpoints.
    Set `text` for TEXT and SEPARATOR parts, and `fieldId` for parts that reference a field."""

    text: str | None = None
    fieldId: str | None = None


class NameTemplatePartInputModel(BaseModel):
    """A pydantic model for a single name template part input to the v3 entity schema endpoints."""

    type: NameTemplatePartType
    configuration: NameTemplatePartConfigurationInputModel | None = None

    @classmethod
    def from_name_template_part_model(
        cls, part: NameTemplatePartModel
    ) -> NameTemplatePartInputModel:
        """Generates a NameTemplatePartInputModel from a name template part, as returned by the v3 API."""
        configuration = None
        if part.configuration and part.configuration.field:
            configuration = NameTemplatePartConfigurationInputModel(
                fieldId=part.configuration.field.id
            )
        elif part.configuration and part.configuration.text is not None:
            configuration = NameTemplatePartConfigurationInputModel(
                text=part.configuration.text
            )
        return cls(type=part.type, configuration=configuration)


class NameTemplateInputModel(BaseModel):
    """A pydantic model for the name template input to the v3 entity schema endpoints.
    Dump with `exclude_none=True`, since Benchling rejects unset configuration properties."""

    nameTemplateParts: list[NameTemplatePartInputModel] = []
    shouldOrderPartsBySequence: bool = False

    @classmethod
    def from_name_template_model(
        cls, name_template: NameTemplateModel
    ) -> NameTemplateInputModel:
        """Generates a NameTemplateInputModel from a name template, as returned by the v3 API."""
        return cls(
            nameTemplateParts=[
                NameTemplatePartInputModel.from_name_template_part_model(part)
                for part in name_template.parts
            ],
            shouldOrderPartsBySequence=name_template.shouldOrderPartsBySequence,
        )


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
    def get_all(
        cls,
        benchling_service: BenchlingService,
        wh_schema_names: set[str] | None = None,
        include_archived: bool = False,
    ) -> list[EntitySchemaModel]:
        schemas_data = list_entity_schemas_with_fields_v3(
            benchling_service, include_archived
        )
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
            schemas_data = list_entity_schemas_v3(benchling_service)
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
        schema_with_fields = attach_entity_schema_field_definitions_v3(
            benchling_service, schema
        )
        return cls.model_validate(schema_with_fields)

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

    def _move_field(self, field: EntitySchemaFieldModel, index: int) -> None:
        self.fields.remove(field)
        self.fields.insert(index, field)

    def archive_field(
        self,
        wh_field_name: str,
        index: int | None = None,
        archive_reason: str = "Made in error",
    ) -> EntitySchemaModel:
        """Archives a field from the entity schema by its warehouse field name. If index is given, the field is moved to that position.
        Returns the full EntitySchemaModel with the field archived."""
        field = self.get_field(wh_field_name)
        if field.archived:
            raise ValueError(f"Field '{wh_field_name}' already archived.")
        field.archived = True
        field.archiveReason = archive_reason
        if index is not None:
            self._move_field(field, index)
        return self

    def unarchive_field(
        self, wh_field_name: str, index: int | None = None
    ) -> EntitySchemaModel:
        """Unarchives a field from the entity schema by its warehouse field name. If index is given, the field is moved to that position.
        Returns the full EntitySchemaModel with the field unarchived."""
        field = self.get_field(wh_field_name)
        if not field.archived:
            raise ValueError(f"Field '{wh_field_name}' not archived.")
        field.archived = False
        field.archiveReason = None
        if index is not None:
            self._move_field(field, index)
        return self

    def reorder_fields(self, new_order: list[str]) -> EntitySchemaModel:
        """Given a new order of warehouse field names, reorders the fields in the entity schema. Fields not in new_order are kept at the end in their current order.
        Returns the full EntitySchemaModel with the fields reordered."""
        order_dict = {name: index for index, name in enumerate(new_order)}
        sorted_fields = sorted(
            [field for field in self.fields if field.systemName in order_dict],
            key=lambda field: order_dict[field.systemName],
        )
        remaining_fields = [
            field for field in self.fields if field.systemName not in order_dict
        ]
        self.fields = sorted_fields + remaining_fields
        return self

    def update_name_template(
        self, update_name_template: BaseNameTemplate
    ) -> EntitySchemaModel:
        """Updates the name template with only the properties set on update_name_template. Returns the full EntitySchemaModel with the name template updated."""
        update_diff_names = update_name_template.model_dump(exclude_unset=True).keys()
        current = self.nameTemplate or NameTemplateModel(
            shouldOrderPartsBySequence=False
        )
        self.nameTemplate = NameTemplateModel(
            parts=[
                NameTemplatePartModel.from_name_template_part(part, self.fields)
                for part in update_name_template.parts or []
            ]
            if "parts" in update_diff_names
            else current.parts,
            shouldOrderPartsBySequence=update_name_template.order_name_parts_by_sequence
            or False
            if "order_name_parts_by_sequence" in update_diff_names
            else current.shouldOrderPartsBySequence,
        )
        return self

    def to_entity_schema_input_update_model(
        self, update_diff: dict[str, Any]
    ) -> EntitySchemaInputModel:
        """Converts the entity schema model to an EntitySchemaInputModel, with only the updated properties set.
        Dump the result with `exclude_unset=True` to get the body for the v3 update entity schema endpoint."""
        update_diff_names = list(update_diff.keys())
        update_props = BaseSchemaProperties(**update_diff)
        entity_type = convert_entity_schema_type_to_entity_type(self.typename)
        if (
            "entity_type" in update_diff_names
            and update_props.entity_type != entity_type
        ):
            raise ValueError(
                f"Cannot change the entity type of schema {self.systemName} from {entity_type} to {update_props.entity_type}."
            )
        updates: dict[str, Any] = {}
        if "naming_strategies" in update_diff_names:
            updates["availableRegistrationNamingOptions"] = list(
                update_props.naming_strategies or []
            )
        if "mixture_schema_config" in update_diff_names:
            mixture_config = update_props.mixture_schema_config
            updates["allowMeasuredIngredients"] = (
                mixture_config.allowMeasuredIngredients if mixture_config else None
            )
            updates["componentLotTextEnabled"] = (
                mixture_config.componentLotTextEnabled if mixture_config else None
            )
            updates["componentLotStorageEnabled"] = (
                mixture_config.componentLotStorageEnabled if mixture_config else None
            )
        if "use_registry_id_as_label" in update_diff_names:
            updates["useRegistryIdForItemDisplayLabel"] = (
                update_props.use_registry_id_as_label
            )
        if "include_registry_id_in_chips" in update_diff_names:
            updates["includeRegistryIdInChips"] = (
                update_props.include_registry_id_in_chips
            )
        if "show_bases_in_expanded_view" in update_diff_names:
            updates["showResidues"] = update_props.show_bases_in_expanded_view
        if "constraint_fields" in update_diff_names:
            # The v3 constraint input has no way to set unique residues, so sequence constraints are dropped here.
            constraint_field_names = [
                f
                for f in update_props.constraint_fields or set()
                if not SequenceConstraint.is_sequence_constraint(f)
            ]
            updates["constraint"] = (
                EntitySchemaConstraintInputModel(
                    fieldDefinitionNames=constraint_field_names
                )
                if constraint_field_names
                else None
            )
        if "prefix" in update_diff_names:
            updates["itemIdPrefix"] = update_props.prefix
        if "warehouse_name" in update_diff_names:
            updates["systemName"] = update_props.warehouse_name
        if "name" in update_diff_names:
            updates["name"] = update_props.name
        current_values = {
            "entity_type": entity_type,
            "name": self.name,
            "systemName": self.systemName,
            "itemIdPrefix": self.itemIdPrefix,
            "organizationId": self.organization.id,
        }
        return EntitySchemaInputModel.model_construct(
            _fields_set=set(updates.keys()), **{**current_values, **updates}
        )

    def get_internal_name_template_parts(self) -> list[NameTemplatePart]:
        if self.nameTemplate is None:
            return []
        return [
            part.to_name_template_part(self.fields) for part in self.nameTemplate.parts
        ]


class EntitySchemaConstraintInputModel(BaseModel):
    """A pydantic model for the uniqueness constraint input to the v3 create entity schema endpoints."""

    fieldDefinitionNames: list[str] = []


class EntitySchemaInputModel(BaseModel):
    """A pydantic model for the body of the v3 create entity schema endpoints (e.g. POST /api/v3/custom-entity-schema).
    `entity_type` picks the endpoint and is not sent in the body. Registry properties are only set on registry schemas,
    `showResidues` only on sequence schemas, and the ingredient/component lot properties only on mixture schemas."""

    entity_type: BenchlingEntityType = Field(exclude=True)
    name: str
    systemName: str
    itemIdPrefix: str
    organizationId: str
    description: str = ""
    fieldDefinitions: list[EntitySchemaFieldInputModel] = []
    availableRegistrationNamingOptions: list[BenchlingNamingStrategy] | None = None
    constraint: EntitySchemaConstraintInputModel | None = None
    nameTemplate: NameTemplateInputModel | None = None
    includeRegistryIdInChips: bool | None = None
    useRegistryIdForItemDisplayLabel: bool | None = None
    showResidues: bool | None = None
    allowMeasuredIngredients: bool | None = None
    componentLotTextEnabled: bool | None = None
    componentLotStorageEnabled: bool | None = None

    @classmethod
    def from_benchling_props(
        cls,
        benchling_props: SchemaProperties,
        fields: list[BaseFieldProperties],
        benchling_service: BenchlingService,
    ) -> EntitySchemaInputModel:
        """Generates an EntitySchemaInputModel from the given internal definition of benchling schema properties.

        Parameters
        ----------
        benchling_props : SchemaProperties
            The schema properties.
        fields : list[BaseFieldProperties]
            List of field properties.
        benchling_service : BenchlingService
            The Benchling service instance used to fetch additional data if needed.

        Returns
        -------
        EntitySchemaInputModel
            A pydantic model for the v3 create entity schema endpoint.
        """
        entity_type = benchling_props.entity_type
        is_registry_schema = entity_type != BenchlingEntityType.ENTRY
        # The v3 constraint input has no way to set unique residues, so sequence constraints are dropped here.
        sequence_constraints = {c.value for c in SequenceConstraint}
        constraint_field_names = [
            f
            for f in benchling_props.constraint_fields or set()
            if f not in sequence_constraints
        ]
        mixture_config = benchling_props.mixture_schema_config
        return cls(
            entity_type=entity_type,
            name=benchling_props.name,
            systemName=benchling_props.warehouse_name,
            itemIdPrefix=benchling_props.prefix,
            organizationId=benchling_service.organization_id,
            availableRegistrationNamingOptions=list(benchling_props.naming_strategies)
            if is_registry_schema and benchling_props.naming_strategies
            else None,
            constraint=EntitySchemaConstraintInputModel(
                fieldDefinitionNames=constraint_field_names
            )
            if is_registry_schema and constraint_field_names
            else None,
            includeRegistryIdInChips=benchling_props.include_registry_id_in_chips
            if is_registry_schema
            else None,
            useRegistryIdForItemDisplayLabel=benchling_props.use_registry_id_as_label
            if is_registry_schema
            else None,
            showResidues=(benchling_props.show_bases_in_expanded_view or False)
            if entity_type.is_sequence()
            else None,
            allowMeasuredIngredients=mixture_config.allowMeasuredIngredients
            if mixture_config
            else None,
            componentLotTextEnabled=mixture_config.componentLotTextEnabled
            if mixture_config
            else None,
            componentLotStorageEnabled=mixture_config.componentLotStorageEnabled
            if mixture_config
            else None,
            fieldDefinitions=[
                EntitySchemaFieldInputModel.from_benchling_props(
                    field_props, benchling_service
                )
                for field_props in fields
            ],
        )
