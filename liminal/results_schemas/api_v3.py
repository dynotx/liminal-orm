from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from liminal.connection.benchling_service import BenchlingService
from liminal.utils import MAX_CONCURRENT_REQUESTS, list_all_items_v3

_RESULT_SCHEMA_API_PATH = "/api/v3/result-schema"


def list_results_schemas_v3(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch result schemas from the v3 API."""
    return list_all_items_v3(benchling_service, f"{_RESULT_SCHEMA_API_PATH}/items")


def list_result_schema_field_definitions_v3(
    benchling_service: BenchlingService, result_schema_id: str
) -> list[dict[str, Any]]:
    """Fetch a result schema's field definitions from the v3 API."""
    return list_all_items_v3(
        benchling_service,
        f"{_RESULT_SCHEMA_API_PATH}/{result_schema_id}/field-definitions/items",
    )


def list_results_schemas_with_fields_v3(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch all result schemas and their field definitions from the v3 API."""
    result_schemas = list_results_schemas_v3(benchling_service)

    def _attach_fields(result_schema: dict[str, Any]) -> None:
        result_schema["fields"] = list_result_schema_field_definitions_v3(
            benchling_service, result_schema["id"]
        )

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        list(executor.map(_attach_fields, result_schemas))

    return result_schemas
