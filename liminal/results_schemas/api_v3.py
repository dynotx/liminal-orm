from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from liminal.connection.benchling_service import BenchlingService

_RESULT_SCHEMA_API_PATH = "/api/v3/result-schema"

EARLY_ACCESS_HEADER = {"EARLY-ACCESS": "true"}


def list_results_schemas_v3(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch result schemas from the v3 API."""
    response = benchling_service.api.get_response(
        url=f"{_RESULT_SCHEMA_API_PATH}/items",
        additional_headers=EARLY_ACCESS_HEADER,
    )
    return response.parsed.get("items", [])


def list_result_schema_field_definitions_v3(
    benchling_service: BenchlingService, result_schema_id: str
) -> list[dict[str, Any]]:
    """Fetch a result schema's field definitions from the v3 API."""
    response = benchling_service.api.get_response(
        url=f"{_RESULT_SCHEMA_API_PATH}/{result_schema_id}/field-definitions/items",
        additional_headers=EARLY_ACCESS_HEADER,
    )
    return response.parsed.get("items", [])


def _fetch_result_schema_field_definitions(
    benchling_service: BenchlingService, result_schema: dict[str, Any]
) -> None:
    result_schema["fields"] = list_result_schema_field_definitions_v3(
        benchling_service, result_schema["id"]
    )


def list_results_schemas_with_fields_v3(
    benchling_service: BenchlingService,
) -> list[dict[str, Any]]:
    """Fetch all result schemas and their field definitions from the v3 API."""
    result_schemas = list_results_schemas_v3(benchling_service)

    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(
                _fetch_result_schema_field_definitions,
                benchling_service,
                result_schema,
            )
            for result_schema in result_schemas
        ]
        for future in as_completed(futures):
            future.result()

    return result_schemas
