import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from liminal.utils import MAX_CONCURRENT_REQUESTS, list_all_items_v3
from liminal.connection.benchling_service import BenchlingService
from liminal.enums import BenchlingEntitySchemaEndpointType, BenchlingEntityType
from liminal.mappers import convert_entity_type_to_entity_schema_endpoint


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
            for endpoint in BenchlingEntitySchemaEndpointType
        ]
        for future in as_completed(futures):
            entity_schemas.extend(future.result())

    return entity_schemas


def _list_entity_schemas_for_endpoint_v3(
    benchling_service: BenchlingService, endpoint: BenchlingEntitySchemaEndpointType
) -> list[dict[str, Any]]:
    """Fetch all entity schemas from one v3 schema endpoint."""
    return list_all_items_v3(benchling_service, f"/api/v3/{endpoint.value}/items")


def list_entity_schema_field_definitions_v3(
    benchling_service: BenchlingService, field_definitions_url: str
) -> list[dict[str, Any]]:
    """Fetch an entity schema's field definitions from the v3 API."""
    relative_url = field_definitions_url.split(".benchling.com/", 1)[-1]
    return list_all_items_v3(benchling_service, relative_url)


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

    def _attach_fields(entity_schema: dict[str, Any]) -> None:
        field_definitions_url = entity_schema.get("fieldDefinitions")
        if not isinstance(field_definitions_url, str):
            return
        entity_schema["fields"] = list_entity_schema_field_definitions_v3(
            benchling_service, field_definitions_url
        )

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        list(executor.map(_attach_fields, entity_schemas))

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
