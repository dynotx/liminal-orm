from __future__ import annotations

from functools import lru_cache
from typing import Any

import requests
from pydantic import BaseModel

from liminal.connection.benchling_service import BenchlingService
from liminal.entity_schemas.tag_schema_models import TagSchemaFieldModel


class ResultsSchemaModel(BaseModel):
    """A pydantic model to define a results schema, which is used when querying for results schemas from Benchling's internal API."""

    allFields: list[TagSchemaFieldModel]
    archiveRecord: dict[str, str] | None
    fields: list[TagSchemaFieldModel]
    id: str
    name: str | None
    organization: Any | None
    permissions: dict[str, bool] | None
    prefix: str | None
    publishedDataTableColumns: Any | None
    requestTaskSchemaIds: list[Any] | None
    requestTemplateIds: list[Any] | None
    sampleGroupSchema: Any | None
    schemaType: str
    sqlIdentifier: str | None

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

        with requests.Session() as session:
            response = session.get(
                f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/result-schemas",
                headers=benchling_service.custom_post_headers,
                cookies=benchling_service.custom_post_cookies,
            )
        if not response.ok:
            raise Exception("Failed to get result schemas.")
        return response.json()["data"]

    @classmethod
    def get_all(
        cls,
        benchling_service: BenchlingService,
        wh_schema_names: set[str] | None = None,
    ) -> list[ResultsSchemaModel]:
        """This function gets all results schemas from Benchling's internal API.
        If a list of warehouse names is provided, the function will only return the results schemas with the given warehouse names.

        Parameters
        ----------
        benchling_service : BenchlingService
            The benchling service to use to get the results schemas.
        wh_schema_names : set[str] | None, optional
            The set of warehouse names to filter the results schemas by. If not provided, all results schemas will be returned.

        Returns
        -------
        list[ResultsSchemaModel]
            A list of results schema models.
        """
        schemas_data = cls.get_all_json(benchling_service)
        filtered_schemas: list[ResultsSchemaModel] = []
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
    ) -> ResultsSchemaModel:
        """This function gets a singular results schema, and raises an error if a schema with the given warehouse name is not found.

        Parameters
        ----------
        benchling_service : BenchlingService
            The benchling service to use to get the results schema.
        wh_schema_name : str
            The warehouse name of the results schema to search for.
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
    ) -> ResultsSchemaModel:
        """This function gets a singular results schema from Benchling and caches it."""
        return cls.get_one(benchling_service, wh_schema_name)
