import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from functools import partial

from liminal.enums.benchling_entity_schema_type import BenchlingEntitySchemaType
from liminal.utils import (
    EARLY_ACCESS_HEADER,
    MAX_CONCURRENT_REQUESTS,
    await_task_v3,
    list_all_items_v3,
)
from liminal.connection.benchling_service import BenchlingService
from liminal.enums import BenchlingEntitySchemaEndpointType, BenchlingEntityType
from liminal.mappers import (
    convert_entity_schema_type_to_entity_type,
    convert_entity_type_to_entity_schema_endpoint,
)


def list_entity_schemas_v3(
    benchling_service: BenchlingService,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    """Fetch entity schemas from all v3 schema endpoints."""
    entity_schemas = []
    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(
                _list_entity_schemas_for_endpoint_v3,
                benchling_service,
                endpoint,
                include_archived,
            )
            for endpoint in BenchlingEntitySchemaEndpointType
        ]
        for future in as_completed(futures):
            entity_schemas.extend(future.result())

    return entity_schemas


def _list_entity_schemas_for_endpoint_v3(
    benchling_service: BenchlingService,
    endpoint: BenchlingEntitySchemaEndpointType,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    """Fetch all entity schemas, including archived ones, from one v3 schema endpoint."""
    return list_all_items_v3(
        benchling_service,
        f"/api/v3/{endpoint.value}/items",
        include_archived,
    )


def list_entity_schema_field_definitions_v3(
    benchling_service: BenchlingService,
    entity_type: BenchlingEntityType,
    entity_schema_id: str,
    include_archived: bool = True,
) -> list[dict[str, Any]]:
    """Fetch an entity schema's field definitions, including archived ones, from the v3 API.
    Archived fields are needed because set-field-definitions rejects a list that leaves out any existing field."""
    return list_all_items_v3(
        benchling_service,
        f"/api/v3/{convert_entity_type_to_entity_schema_endpoint(entity_type).value}/{entity_schema_id}/field-definitions/items",
        include_archived=include_archived,
    )


def attach_entity_schema_field_definitions_v3(
    benchling_service: BenchlingService, entity_schema: dict[str, Any]
) -> dict[str, Any]:
    typename = BenchlingEntitySchemaType(entity_schema.get("__typename"))
    entity_type = convert_entity_schema_type_to_entity_type(typename)
    entity_schema_id = entity_schema.get("id")
    if entity_schema_id is None:
        raise ValueError("Entity schema does not have an id")
    entity_schema["fields"] = list_entity_schema_field_definitions_v3(
        benchling_service, entity_type, str(entity_schema_id)
    )
    return entity_schema


def list_entity_schemas_with_fields_v3(
    benchling_service: BenchlingService,
    include_archived: bool = False,
    wh_schema_names: set[str] | None = None,
    wh_schema_names_for_fields: set[str] | None = None,
    entity_schemas: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Fetch entity schemas and their field definitions from the v3 API.
    If wh_schema_names is given, only those schemas are returned.
    If wh_schema_names_for_fields is given, field definitions are only fetched for those schemas and the rest are returned without fields.
    Pass entity_schemas to reuse an already fetched schema list; fields are attached to those dicts in place."""
    if entity_schemas is None:
        entity_schemas = list_entity_schemas_v3(benchling_service, include_archived)
    if wh_schema_names is not None:
        entity_schemas = [
            s for s in entity_schemas if s["systemName"] in wh_schema_names
        ]
    schemas_needing_fields = [
        s
        for s in entity_schemas
        if wh_schema_names_for_fields is None
        or s["systemName"] in wh_schema_names_for_fields
    ]

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        list(
            executor.map(
                partial(attach_entity_schema_field_definitions_v3, benchling_service),
                schemas_needing_fields,
            )
        )

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
