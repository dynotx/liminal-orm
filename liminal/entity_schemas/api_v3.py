import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from liminal.utils import (
    EARLY_ACCESS_HEADER,
    MAX_CONCURRENT_REQUESTS,
    await_task_v3,
    list_all_items_v3,
)
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
    """Fetch all entity schemas, including archived ones, from one v3 schema endpoint."""
    return list_all_items_v3(
        benchling_service, f"/api/v3/{endpoint.value}/items?archived.anyOf=true,false"
    )


def list_entity_schema_field_definitions_v3(
    benchling_service: BenchlingService, field_definitions_url: str
) -> list[dict[str, Any]]:
    """Fetch an entity schema's field definitions, including archived ones, from the v3 API.
    Archived fields are needed because set-field-definitions rejects a list that leaves out any existing field."""
    relative_url = field_definitions_url.split(".benchling.com/", 1)[-1]
    separator = "&" if "?" in relative_url else "?"
    return list_all_items_v3(
        benchling_service, f"{relative_url}{separator}archived.anyOf=true,false"
    )


def attach_entity_schema_field_definitions_v3(
    benchling_service: BenchlingService, entity_schema: dict[str, Any]
) -> dict[str, Any]:
    field_definitions_url = entity_schema.get("fieldDefinitions")
    if not isinstance(field_definitions_url, str):
        raise ValueError(
            "Provided entity schema does not have fieldDefinitions property."
        )
    entity_schema["fields"] = list_entity_schema_field_definitions_v3(
        benchling_service, field_definitions_url
    )
    return entity_schema


def list_entity_schemas_with_fields_v3(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch all entity schemas and their field definitions from the v3 API."""
    entity_schemas = list_entity_schemas_v3(benchling_service)

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        list(executor.map(attach_entity_schema_field_definitions_v3, entity_schemas))

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
        url=f"/api/v3/{endpoint.value}",
        body=payload,
        additional_headers=EARLY_ACCESS_HEADER,
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
        additional_headers=EARLY_ACCESS_HEADER,
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
        additional_headers=EARLY_ACCESS_HEADER,
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
        additional_headers=EARLY_ACCESS_HEADER,
    )
    if not (200 <= response.status_code < 300):
        raise Exception("Failed to update entity schema properties:", response.content)
    return json.loads(response.content)


def update_entity_schema_field_definitions_v3(
    benchling_service: BenchlingService,
    entity_type: BenchlingEntityType,
    entity_schema_id: str,
    field_definitions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Replace an entity schema's field definitions.
    The endpoint starts an async task, so this polls the task until it succeeds and returns the final task response.
    """
    endpoint = convert_entity_type_to_entity_schema_endpoint(entity_type)
    response = benchling_service.api.post_response(
        url=f"/api/v3/{endpoint.value}/{entity_schema_id}:set-field-definitions",
        body={"fieldDefinitions": field_definitions},
        additional_headers=EARLY_ACCESS_HEADER,
    )
    if not (200 <= response.status_code < 300):
        raise Exception(
            "Failed to set entity schema field definitions:", response.content
        )
    task = json.loads(response.content)
    return await_task_v3(benchling_service, task["pollingUri"])
