from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from liminal.connection.benchling_service import BenchlingService
from liminal.utils import MAX_CONCURRENT_REQUESTS, list_all_items_v3

_RESULT_SCHEMA_API_PATH = "/api/v3/result-schema"


def list_results_schemas(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch result schemas from the v3 API. Result schemas carry an organization but no registry,
    so they are scoped to the organization that owns the connection's registry."""
    return list_all_items_v3(
        benchling_service,
        f"{_RESULT_SCHEMA_API_PATH}/items",
        organization_scoped=True,
    )


def list_result_schema_field_definitions(
    benchling_service: BenchlingService, result_schema_id: str
) -> list[dict[str, Any]]:
    """Fetch a result schema's field definitions from the v3 API."""
    return list_all_items_v3(
        benchling_service,
        f"{_RESULT_SCHEMA_API_PATH}/{result_schema_id}/field-definitions/items",
    )


def attach_result_schema_field_definitions(
    benchling_service: BenchlingService, result_schema: dict[str, Any]
) -> dict[str, Any]:
    result_schema["fields"] = list_result_schema_field_definitions(
        benchling_service, result_schema["id"]
    )
    return result_schema


def list_results_schemas_with_fields(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch all result schemas and their field definitions from the v3 API."""
    result_schemas = list_results_schemas(benchling_service)

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        list(
            executor.map(
                partial(attach_result_schema_field_definitions, benchling_service),
                result_schemas,
            )
        )

    return result_schemas
