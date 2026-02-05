from __future__ import annotations

from functools import lru_cache
from typing import Any

import requests
from pydantic import BaseModel

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.base.properties.base_name_template import BaseNameTemplate
from liminal.base.properties.base_schema_properties import BaseSchemaProperties
from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_summary_by_name
from liminal.enums import (
    BenchlingAPIFieldType,
    BenchlingFieldType,
    BenchlingFolderItemType,
    BenchlingSequenceType,
)
from liminal.enums.name_template_part_type import NameTemplatePartType
from liminal.enums.sequence_constraint import SequenceConstraint
from liminal.mappers import (
    convert_entity_type_to_api_entity_type,
    convert_field_type_to_api_field_type,
)
from liminal.orm.name_template_parts import (
    NameTemplatePart,
)
from liminal.orm.schema_properties import MixtureSchemaConfig
from liminal.unit_dictionary.utils import get_unit_id_from_name


class FieldRequiredLinkShortModel(BaseModel):
    """A pydantic model to define a short representation of a tag schema link for a tag schema field."""

    entitySchemaFieldPath: Any | None = None
    folderItemType: BenchlingFolderItemType | None = None
    schemaInterface: Any | None = None
    tagSchema: dict[str, Any] | None = None
    storableSchema: dict[str, Any] | None = None


class NameTemplatePartModel(BaseModel):
    """A pydantic model to define a part of a name template."""

    type: NameTemplatePartType
    fieldId: str | None = None
    text: str | None = None
    datetimeFormat: str | None = None

    @classmethod
    def from_name_template_part(
        cls, part: NameTemplatePart, fields: list[TagSchemaFieldModel] | None = None
    ) -> NameTemplatePartModel:
        data = part.model_dump()
        field_id = None
        if wh_field_name := data.get("wh_field_name"):
            field = next((f for f in fields if f.systemName == wh_field_name), None)
            if field is None:
                raise ValueError(f"Field {wh_field_name} not found in fields")
            field_id = field.apiId
            if (
                part.component_type == NameTemplatePartType.CHILD_ENTITY_LOT_NUMBER
                or part.component_type
                == NameTemplatePartType.LINKED_BIOENTITY_REGISTRY_IDENTIFIER
            ):
                if not field.isParentLink:
                    raise ValueError(
                        f"Field {wh_field_name} is not a parent link field. The field for type {part.component_type} must be a parent link field."
                    )
        return cls(
            type=part.component_type,
            fieldId=field_id,
            text=data.get("value"),
        )

    def to_name_template_part(
        self, fields: list[TagSchemaFieldModel] | None = None
    ) -> NameTemplatePart:
        part_cls = NameTemplatePart.resolve_type(self.type)
        if self.fieldId:
            field = next((f for f in fields if f.apiId == self.fieldId), None)
            if field is None:
                raise ValueError(f"Field {self.fieldId} not found in fields")
            return part_cls(wh_field_name=field.systemName, value=self.text)
        return part_cls(value=self.text)


class TagSchemaConstraint(BaseModel):
    """
    A class to define a constraint on an entity schema.
    """

    areUniqueResiduesCaseSensitive: bool | None = None
    fields: list[TagSchemaFieldModel] | None = None
    uniqueCanonicalSmiles: bool | None = None
    uniqueResidues: bool | None = None

    @classmethod
    def from_constraint_fields(
        cls,
        constraint_fields: list[TagSchemaFieldModel],
        sequence_constraint: SequenceConstraint | None = None,
    ) -> TagSchemaConstraint:
        """
        Generates a Constraint object from a set of constraint fields to create a constraint on a schema.
        """
        uniqueResidues = False
        areUniqueResiduesCaseSensitive = False
        match sequence_constraint:
            case SequenceConstraint.BASES:
                uniqueResidues = True
            case SequenceConstraint.AMINO_ACIDS_IGNORE_CASE:
                uniqueResidues = True
            case SequenceConstraint.AMINO_ACIDS_EXACT_MATCH:
                uniqueResidues = True
                areUniqueResiduesCaseSensitive = True
        return cls(
            fields=constraint_fields,
            uniqueResidues=uniqueResidues,
            uniqueCanonicalSmiles=False,
            areUniqueResiduesCaseSensitive=areUniqueResiduesCaseSensitive,
        )


class UpdateTagSchemaModel(BaseModel):
    """A pydantic model to define the input for the internal tag schema update endpoint."""

    prefix: str | None = None
    sqlIdentifier: str | None = None
    name: str | None = None

    folderItemType: BenchlingFolderItemType | None = None
    iconId: str | None = None
    labelingStrategies: list[str] | None = None
    mixtureSchemaConfig: MixtureSchemaConfig | None = None
    sequenceType: BenchlingSequenceType | None = None
    shouldCreateAsOligo: bool | None = None
    showResidues: bool | None = None
    includeRegistryIdInChips: bool | None = None
    useOrganizationCollectionAliasForDisplayLabel: bool | None = None
    constraint: TagSchemaConstraint | None = None


class CreateTagSchemaFieldModel(BaseModel):
    """A pydantic model to define a field for the internal tag schema update endpoint that allows for adding a new field to an existing schema."""

    fieldType: str
    isMulti: bool
    isRequired: bool
    isParentLink: bool = False
    schemaFieldSelectorId: str | None = None
    systemName: str
    name: str
    requiredLink: FieldRequiredLinkShortModel | None = None
    tooltipText: str | None = None
    decimalPrecision: int | None = None
    unitApiIdentifier: str | None = None

    @classmethod
    def from_props(
        cls,
        new_props: BaseFieldProperties,
        benchling_service: BenchlingService | None = None,
    ) -> CreateTagSchemaFieldModel:
        """Generates a CreateTagSchemaFieldModel from the given internal definition of benchling field properties.

        Parameters
        ----------
        wh_field_name : str
            The warehouse n ame of the field.
        new_props : BaseFieldProperties
            The field properties.
        benchling_service : BenchlingService | None
            The benchling service to use to get the dropdown summary id if needed.

        Returns
        -------
        CreateTagSchemaFieldModel
            A pydantic model for the add tag schema field endpoint.
        """
        assert new_props.type is not None, "Field must have a type."
        api_field_type, folder_item_type = convert_field_type_to_api_field_type(
            new_props.type
        )

        tagSchema = None
        if new_props.type in BenchlingFieldType.get_entity_link_types():
            if new_props.entity_link is not None:
                if benchling_service is None:
                    raise ValueError(
                        "Benchling SDK must be provided to update entity link field."
                    )
                if new_props.entity_link is not None:
                    tagSchema = TagSchemaModel.get_one(
                        benchling_service, new_props.entity_link
                    ).model_dump()

        dropdown_summary_id = None
        if new_props.dropdown_link is not None:
            if benchling_service is None:
                raise ValueError(
                    "Benchling SDK must be provided to update dropdown field."
                )
            dropdown_summary_id = get_benchling_dropdown_summary_by_name(
                benchling_service, new_props.dropdown_link
            ).id
        unit_api_identifier = None
        if new_props.unit_name:
            if benchling_service is None:
                raise ValueError("Benchling SDK must be provided to update unit field.")
            unit_api_identifier = get_unit_id_from_name(
                benchling_service, new_props.unit_name
            )
        return cls(
            name=new_props.name,
            systemName=new_props.warehouse_name,
            isMulti=new_props.is_multi,
            isRequired=new_props.required,
            isParentLink=new_props.parent_link,
            fieldType=api_field_type,
            schemaFieldSelectorId=dropdown_summary_id,
            requiredLink=FieldRequiredLinkShortModel(
                folderItemType=folder_item_type,
                tagSchema=tagSchema,
            ),
            tooltipText=new_props.tooltip,
            unitApiIdentifier=unit_api_identifier,
            decimalPrecision=new_props.decimal_places,
        )


class TagSchemaFieldModel(BaseModel):
    """A pydantic model to define a field for the Benchling's internal representation of an entity schema, also known as a tag schema.
    This model is used to define the a field of a tag schema that is retrieved from their internal api."""

    id: int | None
    fieldType: BenchlingAPIFieldType
    name: str | None
    apiId: str | None
    archiveRecord: dict[str, str] | None
    dbId: int | None
    decimalPrecision: int | None
    description: str | None
    displayName: str | None
    isComputed: bool | None
    isConvertedFromLink: bool | None
    isIntegration: bool | None
    isMulti: bool | None
    isParentLink: bool | None
    isRequired: bool | None
    isSingleLink: bool | None
    isSnapshot: bool | None
    isUneditable: bool | None
    legalTextSelectorId: str | None
    numericMax: int | None
    numericMin: int | None
    requiredLink: FieldRequiredLinkShortModel | None
    schemaFieldSelectorId: str | None
    strictSelector: bool | None
    systemName: str
    tooltipText: str | None
    unitApiIdentifier: str | None
    unitSymbol: str | None = None

    def update_from_props(
        self,
        update_diff: dict[str, Any],
        benchling_service: BenchlingService | None = None,
    ) -> TagSchemaFieldModel:
        """Updates the tag schema field given the field properties defined in code.

        Parameters
        ----------
        update_diff : dict[str, Any]
            A dictionary of the field properties dif to update the tag schema field with.
            Only the fields that are in the dictionary are updated in the tag schema field model.
        benchling_service : BenchlingService | None
            The benchling service to use to get the dropdown summary id if needed.

        Returns
        -------
        TagSchemaFieldModel
            A pydantic model for the update tag schema field endpoint.
        """
        update_diff_names = list(update_diff.keys())
        update_props = BaseFieldProperties(**update_diff)
        self.name = update_props.name if "name" in update_diff_names else self.name
        self.systemName = (
            update_props.warehouse_name
            if "warehouse_name" in update_diff_names
            and update_props.warehouse_name is not None
            else self.systemName
        )
        self.isRequired = (
            update_props.required
            if "required" in update_diff_names
            else self.isRequired
        )
        self.isMulti = (
            update_props.is_multi if "is_multi" in update_diff_names else self.isMulti
        )
        self.isParentLink = (
            update_props.parent_link
            if "parent_link" in update_diff_names
            else self.isParentLink
        )
        self.tooltipText = (
            update_props.tooltip if "tooltip" in update_diff_names else self.tooltipText
        )
        if "type" in update_diff_names and update_props.type:
            api_field_type, folder_item_type = convert_field_type_to_api_field_type(
                update_props.type
            )
            self.fieldType = api_field_type
            self.requiredLink = FieldRequiredLinkShortModel(
                folderItemType=folder_item_type
            )
        if "entity_link" in update_diff_names and update_props.entity_link:
            if benchling_service is None:
                raise ValueError(
                    "Benchling SDK must be provided to update entity link field."
                )
            entity_link_tag_schema = TagSchemaModel.get_one(
                benchling_service, update_props.entity_link
            ).model_dump()
            if self.requiredLink is None:
                raise ValueError(f"Required link on field {self.name} not found.")
            self.requiredLink.tagSchema = entity_link_tag_schema

        else:
            entity_link_tag_schema = None
        if "dropdown_link" in update_diff_names and update_props.dropdown_link:
            if benchling_service is None:
                raise ValueError(
                    "Benchling SDK must be provided to update dropdown field."
                )
            dropdown_summary_id = get_benchling_dropdown_summary_by_name(
                benchling_service, update_props.dropdown_link
            ).id
            self.schemaFieldSelectorId = dropdown_summary_id
        self.decimalPrecision = (
            update_props.decimal_places
            if "decimal_places" in update_diff_names
            else self.decimalPrecision
        )
        if "unit_name" in update_diff_names:
            if update_props.unit_name is None:
                self.unitApiIdentifier = None
            else:
                if benchling_service is None:
                    raise ValueError(
                        "Benchling SDK must be provided to update unit field."
                    )
                self.unitApiIdentifier = get_unit_id_from_name(
                    benchling_service, update_props.unit_name
                )
        return self


class TagSchemaModel(BaseModel):
    """A pydantic model to define a tag schema, which is Benchling's internal representation of an entity schema."""

    allFields: list[TagSchemaFieldModel]
    archiveRecord: dict[str, str] | None
    authParentOption: str | None
    batchSchemaId: str | None
    childEntitySchemaSummaries: list[Any] | None
    constraint: TagSchemaConstraint | None
    containableType: str | None
    fields: list[TagSchemaFieldModel]
    folderItemType: BenchlingFolderItemType
    hoistedTagSchemaGraphs: list[Any] | None
    iconId: str | None
    id: str
    includeRegistryIdInChips: bool | None
    isContainable: bool | None
    labelingStrategies: list[str]
    mixtureSchemaConfig: MixtureSchemaConfig | None
    name: str | None
    nameTemplateParts: list[NameTemplatePartModel] | None
    permissions: dict[str, bool] | None
    prefix: str | None
    registryId: str | None
    resultSchema: Any | None
    sequenceType: BenchlingSequenceType | None
    shouldCreateAsOligo: bool | None
    shouldOrderNamePartsBySequence: bool | None
    showResidues: bool | None
    sqlIdentifier: str
    useOrganizationCollectionAliasForDisplayLabel: bool | None
    useRandomOrgAlias: bool | None

    @classmethod
    def get_all_json(
        cls,
        benchling_service: BenchlingService,
    ) -> list[dict[str, Any]]:
        with requests.Session() as session:
            response = session.get(
                f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/tag-schemas/",
                headers=benchling_service.custom_post_headers,
                cookies=benchling_service.custom_post_cookies,
            )
        if not response.ok:
            raise Exception("Failed to get tag schemas.")
        return response.json()["data"]

    @classmethod
    def get_all(
        cls,
        benchling_service: BenchlingService,
        wh_schema_names: set[str] | None = None,
    ) -> list[TagSchemaModel]:
        schemas_data = cls.get_all_json(benchling_service)
        filtered_schemas: list[TagSchemaModel] = []
        if wh_schema_names:
            for schema in schemas_data:
                if schema["sqlIdentifier"] in wh_schema_names:
                    filtered_schemas.append(cls.model_validate(schema))
                if len(filtered_schemas) == len(wh_schema_names):
                    break
        else:
            for schema in schemas_data:
                try:
                    filtered_schemas.append(cls.model_validate(schema))
                except Exception as e:
                    print(f"Error validating schema {schema['sqlIdentifier']}: {e}")
        return filtered_schemas

    @classmethod
    def get_one(
        cls,
        benchling_service: BenchlingService,
        wh_schema_name: str,
        schemas_data: list[dict[str, Any]] | None = None,
    ) -> TagSchemaModel:
        if schemas_data is None:
            schemas_data = cls.get_all_json(benchling_service)
        schema = next(
            (
                schema
                for schema in schemas_data
                if schema["sqlIdentifier"] == wh_schema_name
                and schema["registryId"] == benchling_service.registry_id
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
    ) -> TagSchemaModel:
        return cls.get_one(benchling_service, wh_schema_name)

    def get_field(self, wh_field_name: str) -> TagSchemaFieldModel:
        """Returns a field from the tag schema by its warehouse field name."""
        for field in self.allFields:
            if field.systemName == wh_field_name:
                return field
        raise ValueError(f"Field '{wh_field_name}' not found in schema")

    def get_internal_name_template_parts(self) -> list[NameTemplatePart]:
        return [
            part.to_name_template_part(self.fields) for part in self.nameTemplateParts
        ]

    def update_schema_props(self, update_diff: dict[str, Any]) -> TagSchemaModel:
        """Updates the schema properties given the schema properties defined in code."""
        update_diff_names = list(update_diff.keys())
        update_props = BaseSchemaProperties(**update_diff)
        if update_props.entity_type and "entity_type" in update_diff_names:
            folder_item_type, sequence_type = convert_entity_type_to_api_entity_type(
                update_props.entity_type
            )
            self.folderItemType = folder_item_type
            self.sequenceType = sequence_type
        if "naming_strategies" in update_diff_names:
            self.labelingStrategies = [o.value for o in update_props.naming_strategies]
        if "mixture_schema_config" in update_diff_names:
            self.mixtureSchemaConfig = update_props.mixture_schema_config
        if "use_registry_id_as_label" in update_diff_names:
            self.useOrganizationCollectionAliasForDisplayLabel = (
                update_props.use_registry_id_as_label
            )
        if "include_registry_id_in_chips" in update_diff_names:
            self.includeRegistryIdInChips = update_props.include_registry_id_in_chips
        if "show_bases_in_expanded_view" in update_diff_names:
            self.showResidues = update_props.show_bases_in_expanded_view

        if "constraint_fields" in update_diff_names:
            if update_props.constraint_fields:
                sequence_constraint = next(
                    (
                        SequenceConstraint(c)
                        for c in update_props.constraint_fields
                        if SequenceConstraint.is_sequence_constraint(c)
                    ),
                    None,
                )
                update_props.constraint_fields = {
                    c
                    for c in update_props.constraint_fields
                    if not SequenceConstraint.is_sequence_constraint(c)
                }
                constraint_fields = [
                    f
                    for f in self.fields
                    if f.systemName in update_props.constraint_fields
                ]
                self.constraint = TagSchemaConstraint.from_constraint_fields(
                    constraint_fields, sequence_constraint
                )
            else:
                self.constraint = None

        self.prefix = (
            update_props.prefix if "prefix" in update_diff_names else self.prefix
        )

        set_sql_identifier = (
            update_props.warehouse_name
            if "warehouse_name" in update_diff_names
            else self.sqlIdentifier
        )
        assert type(set_sql_identifier) is str
        self.sqlIdentifier = set_sql_identifier
        self.name = update_props.name if "name" in update_diff_names else self.name
        return self

    def update_name_template(
        self, update_name_template: BaseNameTemplate
    ) -> TagSchemaModel:
        update_diff_names = update_name_template.model_dump(exclude_unset=True).keys()
        self.nameTemplateParts = (
            [
                NameTemplatePartModel.from_name_template_part(part, self.fields)
                for part in update_name_template.parts
            ]
            if "parts" in update_diff_names
            else self.nameTemplateParts
        )
        self.shouldOrderNamePartsBySequence = (
            update_name_template.order_name_parts_by_sequence
            if "order_name_parts_by_sequence" in update_diff_names
            else self.shouldOrderNamePartsBySequence
        )
        return self

    def update_field(
        self,
        benchling_service: BenchlingService,
        wh_field_name: str,
        update_diff: dict[str, Any],
    ) -> TagSchemaModel:
        """Given a warehouse field name and field properties, updates the field of the tag schema. Returns a full TagSchemaModel with the field updated."""
        field = self.get_field(wh_field_name)
        field = field.update_from_props(update_diff, benchling_service)
        return self

    def update_field_wh_name(
        self, old_wh_field_name: str, new_wh_field_name: str
    ) -> TagSchemaModel:
        """Updates the warehouse field name of a field in the tag schema. Returns a full TagSchemaModel with the field updated."""
        field = self.get_field(old_wh_field_name)
        field.systemName = new_wh_field_name
        return self

    def archive_field(self, wh_field_name: str) -> TagSchemaModel:
        """Archives a field from the tag schema by its warehouse field name. Returns a full TagSchemaModel with the field archived."""
        field = self.get_field(wh_field_name)
        if field.archiveRecord is not None:
            raise ValueError(f"Field '{wh_field_name}' already archived.")
        field.archiveRecord = {"purpose": "Made in error"}
        return self

    def unarchive_field(self, wh_field_name: str) -> TagSchemaModel:
        """Unarchives a field from the tag schema by its warehouse field name. Returns a full TagSchemaModel with the field unarchived."""
        field = self.get_field(wh_field_name)
        if field.archiveRecord is None:
            raise ValueError(f"Field '{wh_field_name}' not archived.")
        field.archiveRecord = None
        return self

    def reorder_fields(self, new_order: list[str]) -> TagSchemaModel:
        """Given a new order of warehouse field names, reorders the fields in the tag schema. Returns a full TagSchemaModel with the fields reordered."""
        fields_for_update = self.allFields
        order_dict = {name: index for index, name in enumerate(new_order)}

        sorted_fields = sorted(
            [field for field in fields_for_update if field.systemName in order_dict],
            key=lambda field: order_dict[field.systemName],
        )
        remaining_fields = [
            field for field in fields_for_update if field.systemName not in order_dict
        ]
        sorted_fields.extend(remaining_fields)
        self.allFields = sorted_fields
        return self
