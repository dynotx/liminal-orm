import json
from typing import Any

from benchling_sdk.models import DropdownCreate, DropdownOption

from liminal.connection import BenchlingService

_DROPDOWN_API_PATH = "/api/v3/dropdown"

EARLY_ACCESS_HEADER = {"EARLY-ACCESS": "true"}


def _response_json(response: Any, operation: str) -> dict[str, Any]:
    """Return a successful Benchling API response as JSON."""
    if not 200 <= response.status_code < 300:
        raise RuntimeError(
            f"Failed to {operation}: {response.status_code} {response.content.decode()}"
        )
    return json.loads(response.content)


def _convert_dropdown_option_to_v3(option: DropdownOption) -> dict[str, Any]:
    v3_option_dict: dict[str, Any] = {"name": option.name}
    if option.id is not None:
        v3_option_dict["id"] = option.id
        if option.archive_record is not None:
            v3_option_dict["archiveReason"] = option.archive_record.purpose  # type: ignore
            v3_option_dict["archived"] = True
        else:
            v3_option_dict["archived"] = False
    return v3_option_dict


def list_dropdowns_v3(
    benchling_service: BenchlingService, include_archived: bool = True
) -> list[dict[str, Any]]:
    """Fetch dropdowns from the v3 API."""
    url_suffix = "/items?archived.anyOf=true,false" if include_archived else "/items"
    response = benchling_service.api.get_response(
        url=f"/api/v3/dropdown/{url_suffix}",
        additional_headers=EARLY_ACCESS_HEADER,
    )
    return response.parsed.get("items", [])


def list_dropdown_options_v3(
    benchling_service: BenchlingService, dropdown_id: str
) -> list[dict[str, Any]]:
    """Fetch a dropdown's options from the v3 API."""
    response = benchling_service.api.get_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}/options/items",
        additional_headers=EARLY_ACCESS_HEADER,
    )
    return response.parsed.get("items", [])


def create_dropdown(
    benchling_service: BenchlingService, new_dropdown: DropdownCreate
) -> dict[str, Any]:
    """Create a dropdown."""
    dropdown = benchling_service.dropdowns.create(dropdown=new_dropdown)
    return {dropdown.id: dropdown}


def update_dropdown_name(
    benchling_service: BenchlingService, dropdown_id: str, new_name: str
) -> dict[str, Any]:
    """Rename a dropdown."""
    response = benchling_service.api.patch_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}",
        body={"name": new_name},
        additional_headers=EARLY_ACCESS_HEADER,
    )
    return _response_json(response, "update dropdown name")


def update_dropdown_options(
    benchling_service: BenchlingService, dropdown_id: str, options: list[DropdownOption]
) -> dict[str, Any]:
    """Replace a dropdown's ordered options."""
    response = benchling_service.api.patch_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}",
        body={"options": [_convert_dropdown_option_to_v3(o) for o in options]},
        additional_headers=EARLY_ACCESS_HEADER,
    )
    return _response_json(response, "update dropdown options")


def archive_dropdown(
    benchling_service: BenchlingService,
    dropdown_id: str,
    reason: str = "Made in error",
) -> dict[str, Any]:
    """Archive a dropdown."""
    response = benchling_service.api.patch_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}",
        body={"archived": True, "archiveReason": reason},
        additional_headers=EARLY_ACCESS_HEADER,
    )
    return _response_json(response, "archive dropdown")


def unarchive_dropdown(
    benchling_service: BenchlingService, dropdown_id: str
) -> dict[str, Any]:
    """Restore an archived dropdown."""
    response = benchling_service.api.patch_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}",
        body={"archived": False},
        additional_headers=EARLY_ACCESS_HEADER,
    )
    return _response_json(response, "unarchive dropdown")
