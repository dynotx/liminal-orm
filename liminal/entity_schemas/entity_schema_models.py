from __future__ import annotations

from pydantic import BaseModel

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdown_summary_by_name
from liminal.entity_schemas.tag_schema_models import TagSchemaModel
from liminal.enums import BenchlingEntityType
from liminal.mappers import convert_field_type_to_api_field_type
from liminal.orm.schema_properties import MixtureSchemaConfig, SchemaProperties


class FieldLinkShortModel(BaseModel):
    """A pydantic model to define a short representation of a field link for an entity schema field."""

    tagSchema: dict[str, str] | None = None
    folderItemType: str | None = None


class CreateEntitySchemaFieldModel(BaseModel):
    """A pydantic model to define a field for the create entity schema endpoint.
    This model is used as input for the benchling alpha create entity schema endpoint."""

    name: str
    systemName: str
    fieldType: str
    isMulti: bool
    isRequired: bool
    isParentLink: bool = False
    dropdownId: str | None = None
    link: FieldLinkShortModel | None = None

    @classmethod
    def from_benchling_props(
        cls,
        field_props: BaseFieldProperties,
        benchling_service: BenchlingService | None = None,
    ) -> CreateEntitySchemaFieldModel:
        """Generates a CreateEntitySchemaFieldModel from the given internal definition of benchling field properties.

        Parameters
        ----------
        field_props : BaseFieldProperties
            The field properties.
        benchling_service : BenchlingService | None
            The Benchling service instance used to fetch additional data if needed.

        Returns
        -------
        CreateEntitySchemaFieldModel
            A pydantic model for the create entity schema field endpoint.
        """
        tag_schema = None
        folder_item_type = None
        if field_props.entity_link is not None:
            if benchling_service is None:
                raise ValueError(
                    "Benchling SDK must be provided to update entity link field."
                )
            entity_link_schema_id = TagSchemaModel.get_one(
                benchling_service, field_props.entity_link
            ).id
            tag_schema = {"id": entity_link_schema_id}
        if field_props.type:
            folder_item_type = convert_field_type_to_api_field_type(field_props.type)[1]

        dropdown_summary_id = None
        if field_props.dropdown_link is not None:
            if benchling_service is None:
                raise ValueError(
                    "Benchling SDK must be provided to update dropdown field."
                )
            dropdown_summary_id = get_benchling_dropdown_summary_by_name(
                benchling_service, field_props.dropdown_link
            ).id
        return CreateEntitySchemaFieldModel(
            name=field_props.name,
            systemName=field_props.warehouse_name,
            isMulti=field_props.is_multi,
            isRequired=field_props.required,
            isParentLink=field_props.parent_link,
            fieldType=field_props.type,
            dropdownId=dropdown_summary_id,
            link=FieldLinkShortModel(
                tagSchema=tag_schema, folderItemType=folder_item_type
            ),
        )


class CreateEntitySchemaModel(BaseModel):
    """A pydantic model for the create entity schema endpoint.
    This model is used as input for the benchling alpha create entity schema endpoint."""

    fields: list[CreateEntitySchemaFieldModel]
    name: str
    prefix: str
    registryId: str
    type: BenchlingEntityType
    mixtureSchemaConfig: MixtureSchemaConfig | None = None
    labelingStrategies: list[str] | None = None

    @classmethod
    def from_benchling_props(
        cls,
        benchling_props: SchemaProperties,
        fields: list[BaseFieldProperties],
        benchling_service: BenchlingService,
    ) -> CreateEntitySchemaModel:
        """Generates a CreateEntitySchemaModel from the given internal definition of benchling schema properties.

        Parameters
        ----------
        benchling_props : Benchling SchemaProperties
            The schema properties.
        fields : list[Benchling FieldProperties]
            List of field properties.
        benchling_service : BenchlingService | None
            The Benchling service instance used to fetch additional data if needed.

        Returns
        -------
        CreateEntitySchemaModel
            A pydantic model for the create entity schema endpoint.
        """
        return cls(
            name=benchling_props.name,
            prefix=benchling_props.prefix,
            registryId=benchling_service.registry_id,
            type=benchling_props.entity_type,
            mixtureSchemaConfig=benchling_props.mixture_schema_config,
            labelingStrategies=[s.value for s in benchling_props.naming_strategies],
            fields=[
                CreateEntitySchemaFieldModel.from_benchling_props(
                    field_props, benchling_service
                )
                for field_props in fields
            ],
        )
