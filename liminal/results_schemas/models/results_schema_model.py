from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from liminal.connection.benchling_service import BenchlingService
from liminal.results_schemas.api_v3 import list_results_schemas_with_fields_v3
from liminal.enums import BenchlingFieldDefinitionType


class ResultsSchemaFieldLinkDefinitionModel(BaseModel):
    id: str
    typename: str = Field(alias="__typename")

    model_config = ConfigDict(populate_by_name=True)


class ResultsSchemaFieldModel(BaseModel):
    id: str
    name: str
    systemName: str
    isRequired: bool
    derivationType: str
    archived: bool
    archiveReason: str | None = None
    description: str | None = None
    createdAt: datetime
    modifiedAt: datetime
    typename: BenchlingFieldDefinitionType = Field(alias="__typename")
    isMulti: bool | None = None
    isParent: bool | None = None
    linkDefinition: ResultsSchemaFieldLinkDefinitionModel | None = None
    numericMin: float | None = None
    numericMax: float | None = None
    displayPrecision: int | None = None
    unit: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


class ResultsSchemaModel(BaseModel):
    """A pydantic model to define a results schema, which is used when querying for results schemas from Benchling's internal API."""

    archived: bool
    archive_reason: str | None = None
    fields: list[ResultsSchemaFieldModel]
    id: str
    name: str
    systemName: str | None = None
    organization: Any | None
    typename: str = Field(alias="__typename")

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def get_all_json(
        cls,
        benchling_service: BenchlingService,
    ) -> list[dict[str, Any]]:
        """This function gets all results schemas from Benchling's internal API, returning the raw JSON data.

        Parameters
        ----------
        benchling_service : BenchlingService
            The benchling service to use to get the results schemas.

        Returns
        -------
        list[dict[str, Any]]
            A list of results schemas, in their raw JSON format.
        """
        return list_results_schemas_with_fields_v3(benchling_service)

    @classmethod
    def get_all(
        cls,
        benchling_service: BenchlingService,
        names: set[str] | None = None,
    ) -> list[ResultsSchemaModel]:
        """This function gets all results schemas from Benchling's internal API.
        If a list of names is provided, the function will only return the results schemas with the given names.

        Parameters
        ----------
        benchling_service : BenchlingService
            The benchling service to use to get the results schemas.
        names : set[str] | None, optional
            The set of names to filter the results schemas by. If not provided, all results schemas will be returned.

        Returns
        -------
        list[ResultsSchemaModel]
            A list of results schema models.
        """
        schemas_data = cls.get_all_json(benchling_service)
        filtered_schemas: list[ResultsSchemaModel] = []
        if names:
            for schema in schemas_data:
                if schema["name"] in names:
                    filtered_schemas.append(cls.model_validate(schema))
                if len(filtered_schemas) == len(names):
                    break
        else:
            for schema in schemas_data:
                try:
                    filtered_schemas.append(cls.model_validate(schema))
                except Exception as e:
                    print(f"Error validating schema {schema['name']}: {e}")
        return filtered_schemas

    @classmethod
    def get_one(
        cls,
        benchling_service: BenchlingService,
        name: str,
        schemas_data: list[dict[str, Any]] | None = None,
    ) -> ResultsSchemaModel:
        """This function gets a singular results schema, and raises an error if a schema with the given name is not found.

        Parameters
        ----------
        benchling_service : BenchlingService
            The benchling service to use to get the results schema.
        name : str
            The name of the results schema to search for.
        schemas_data : list[dict[str, Any]] | None
            The list of results schemas to search through, to avoid making extra API calls. If not provided, the function will get all results schemas from Benchling.

        Returns
        -------
        ResultsSchemaModel
            The corresponding results schema model.
        """
        if schemas_data is None:
            schemas_data = cls.get_all_json(benchling_service)
        schema = next(
            (
                schema
                for schema in schemas_data
                if schema["name"] == name
                # and schema["registryId"] == benchling_service.registry_id
            ),
            None,
        )
        if schema is None:
            raise ValueError(
                f"Schema {name} not found in Benchling {benchling_service.benchling_tenant}."
            )
        return cls.model_validate(schema)

    @classmethod
    @lru_cache(maxsize=100)
    def get_one_cached(
        cls,
        benchling_service: BenchlingService,
        name: str,
    ) -> ResultsSchemaModel:
        """This function gets a singular results schema from Benchling and caches it."""
        return cls.get_one(benchling_service, name)
