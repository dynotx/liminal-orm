import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from liminal.connection.benchling_service import BenchlingService
from liminal.enums.benchling_entity_schema_endpoints import (
    BenchlingEntitySchemaEndpoints,
)
from liminal.enums.benchling_entity_type import BenchlingEntityType
from liminal.mappers import convert_entity_type_to_entity_schema_endpoint

EARLY_ACCESS_HEADER = {"EARLY-ACCESS": "true"}


def list_entity_schemas_v3(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch entity schemas from all v3 schema endpoints."""
    entity_schemas = []
    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(
                _list_entity_schemas_for_endpoint_v3,
                benchling_service,
                endpoint,
            )
            for endpoint in BenchlingEntitySchemaEndpoints
        ]
        for future in as_completed(futures):
            entity_schemas.extend(future.result())

    return entity_schemas


def _list_entity_schemas_for_endpoint_v3(
    benchling_service: BenchlingService, endpoint: BenchlingEntitySchemaEndpoints
) -> list[dict[str, Any]]:
    """Fetch entity schemas from one v3 schema endpoint."""
    response = benchling_service.api.get_response(
        url=f"/api/v3/{endpoint.value}/items",
        additional_headers=EARLY_ACCESS_HEADER,
    )
    parsed_response = response.parsed
    if parsed_response is None:
        raise ValueError(f"No response body returned for {endpoint.value} schemas.")
    return parsed_response.get("items", [])


def list_entity_schema_field_definitions_v3(
    benchling_service: BenchlingService, field_definitions_url: str
) -> list[dict[str, Any]]:
    """Fetch an entity schema's field definitions from the v3 API."""
    relative_url = field_definitions_url.split(".benchling.com/", 1)[-1]
    response = benchling_service.api.get_response(
        url=relative_url,
        additional_headers=EARLY_ACCESS_HEADER,
    )
    parsed_response = response.parsed
    if parsed_response is None:
        raise ValueError("No response body returned for entity schema fields.")
    if isinstance(parsed_response, list):
        return parsed_response
    return parsed_response.get("items", [])


def _fetch_entity_schema_field_definitions(
    benchling_service: BenchlingService, entity_schema: dict[str, Any]
) -> None:
    field_definitions_url = entity_schema.get("fieldDefinitions")
    if not isinstance(field_definitions_url, str):
        return
    entity_schema["fields"] = list_entity_schema_field_definitions_v3(
        benchling_service, field_definitions_url
    )


def list_entity_schemas_with_fields_v3(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch all entity schemas and their field definitions from the v3 API."""
    entity_schemas = list_entity_schemas_v3(benchling_service)

    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(
                _fetch_entity_schema_field_definitions,
                benchling_service,
                entity_schema,
            )
            for entity_schema in entity_schemas
        ]
        for future in as_completed(futures):
            future.result()

    return entity_schemas


def create_entity_schema_v3(
    benchling_service: BenchlingService,
    entity_type: BenchlingEntityType,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a new entity schema.
    """
    endpoint = convert_entity_type_to_entity_schema_endpoint(entity_type)
    response = benchling_service.api.post_response(
        url=f"/api/v3/{endpoint.value}", body=payload
    )
    if not (200 <= response.status_code < 300):
        raise Exception("Failed to create entity schema:", response.content)
    return json.loads(response.content)


def archive_entity_schema_v3(
    benchling_service: BenchlingService,
    entity_type: BenchlingEntityType,
    entity_schema_id: str,
    archive_reason: str = "Made in error",
) -> dict[str, Any]:
    """
    Archive an entity schema.
    """
    endpoint = convert_entity_type_to_entity_schema_endpoint(entity_type)
    response = benchling_service.api.patch_response(
        url=f"/api/v3/{endpoint.value}/{entity_schema_id}",
        body={"archived": True, "archiveReason": archive_reason},
    )
    if not (200 <= response.status_code < 300):
        raise Exception("Failed to archive entity schema:", response.content)
    return json.loads(response.content)


def unarchive_entity_schema_v3(
    benchling_service: BenchlingService,
    entity_type: BenchlingEntityType,
    entity_schema_id: str,
) -> dict[str, Any]:
    """
    Unarchive an entity schema.
    """
    endpoint = convert_entity_type_to_entity_schema_endpoint(entity_type)
    response = benchling_service.api.patch_response(
        url=f"/api/v3/{endpoint.value}/{entity_schema_id}",
        body={"archived": False},
    )
    if not (200 <= response.status_code < 300):
        raise Exception("Failed to unarchive entity schema:", response.content)
    return json.loads(response.content)


def update_entity_schema_properties_v3(
    benchling_service: BenchlingService,
    entity_type: BenchlingEntityType,
    entity_schema_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Update an entity schema's properties.
    """
    endpoint = convert_entity_type_to_entity_schema_endpoint(entity_type)
    response = benchling_service.api.patch_response(
        url=f"/api/v3/{endpoint.value}/{entity_schema_id}",
        body=payload,
    )
    if not (200 <= response.status_code < 300):
        raise Exception("Failed to update entity schema properties:", response.content)
    return json.loads(response.content)


def update_entity_schema_fields_v3(
    benchling_service: BenchlingService,
    entity_type: BenchlingEntityType,
    entity_schema_id: str,
    fields: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Replace an entity schema's field definitions.
    """
    endpoint = convert_entity_type_to_entity_schema_endpoint(entity_type)
    response = benchling_service.api.post_response(
        url=f"/api/v3/{endpoint.value}/{entity_schema_id}:set-field-definitions",
        body={"fieldDefinitions": fields},
    )
    if not (200 <= response.status_code < 300):
        raise Exception(
            "Failed to set entity schema field definitions:", response.content
        )
    return json.loads(response.content)
