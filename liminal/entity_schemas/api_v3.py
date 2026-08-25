from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from liminal.connection.benchling_service import BenchlingService
import json

from liminal.enums.benchling_entity_schema_endpoints import (
    BenchlingEntitySchemaEndpoints,
)
from liminal.enums.benchling_entity_type import BenchlingEntityType
from liminal.mappers import convert_entity_type_to_entity_schema_endpoint


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


def list_entity_schemas_v3(benchling_service: BenchlingService) -> list[dict[str, Any]]:
    """
    Fetches all entity schemas from each schema endpoint and expands their fieldDefinitions
    to contain the actual response data rather than just URLs. All endpoints (and each
    endpoint's nested fieldDefinitions fetches) are requested concurrently via a thread pool.
    """
    all_schemas = []
    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(_fetch_entity_schema_type_endpoint, benchling_service, endpoint)
            for endpoint in BenchlingEntitySchemaEndpoints
        ]
        for future in as_completed(futures):
            all_schemas.extend(future.result())

    return all_schemas


def _fetch_field_definitions(benchling_service: BenchlingService, schema: dict) -> None:
    field_definitions_url = schema.get("fieldDefinitions")
    if not isinstance(field_definitions_url, str):
        return

    field_definitions_url_rel = field_definitions_url.split(".benchling.com/", 1)[-1]
    schema["fields"] = benchling_service.api.get_response(
        url=field_definitions_url_rel, additional_headers={"EARLY-ACCESS": "true"}
    ).parsed


def _fetch_entity_schema_type_endpoint(
    benchling_service: BenchlingService, endpoint: BenchlingEntitySchemaEndpoints
) -> list[dict[str, Any]]:
    response = benchling_service.api.get_response(
        url=f"/api/v3/{endpoint.value}/items",
        additional_headers={"EARLY-ACCESS": "true"},
    )
    parsed_response = response.parsed
    if parsed_response is None:
        raise ValueError(f"No response body returned for {endpoint.value} schemas.")
    schemas = parsed_response["items"]
    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(_fetch_field_definitions, benchling_service, schema)
            for schema in schemas
        ]
        for future in as_completed(futures):
            future.result()

    return schemas
