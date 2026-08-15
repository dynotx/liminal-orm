import json
from typing import Any

from benchling_sdk.models import DropdownCreate, DropdownOption

from liminal.connection import BenchlingService

_DROPDOWN_API_PATH = "/api/v3/dropdowns"


def _response_json(response: Any, operation: str) -> dict[str, Any]:
    """Return a successful Benchling API response as JSON."""
    if not 200 <= response.status_code < 300:
        raise RuntimeError(
            f"Failed to {operation}: {response.status_code} {response.content.decode()}"
        )
    return json.loads(response.content)


def create_dropdown(
    benchling_service: BenchlingService, new_dropdown: DropdownCreate
) -> dict[str, Any]:
    """Create a dropdown."""
    response = benchling_service.api.post_response(
        url=_DROPDOWN_API_PATH, body=new_dropdown.to_dict()
    )
    return _response_json(response, "create dropdown")


def update_dropdown_name(
    benchling_service: BenchlingService, dropdown_id: str, new_name: str
) -> dict[str, Any]:
    """Rename a dropdown."""
    response = benchling_service.api.patch_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}", body={"name": new_name}
    )
    return _response_json(response, "update dropdown name")


def update_dropdown_options(
    benchling_service: BenchlingService, dropdown_id: str, options: list[DropdownOption]
) -> dict[str, Any]:
    """Replace a dropdown's ordered options."""
    response = benchling_service.api.patch_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}",
        body={"options": [option.to_dict() for option in options]},
    )
    return _response_json(response, "update dropdown options")


def archive_dropdown(
    benchling_service: BenchlingService,
    dropdown_id: str,
    reason: str = "Made in error",
) -> dict[str, Any]:
    """Archive a dropdown."""
    response = benchling_service.api.post_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}:archive", body={"reason": reason}
    )
    return _response_json(response, "archive dropdown")


def unarchive_dropdown(
    benchling_service: BenchlingService, dropdown_id: str
) -> dict[str, Any]:
    """Restore an archived dropdown."""
    response = benchling_service.api.post_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}:unarchive"
    )
    return _response_json(response, "unarchive dropdown")


def archive_dropdown_options(
    benchling_service: BenchlingService,
    dropdown_id: str,
    dropdown_option_ids: list[str],
    reason: str = "Made in error",
) -> dict[str, Any]:
    """Archive options belonging to a dropdown."""
    response = benchling_service.api.post_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}/options:archive",
        body={"dropdownOptionIds": dropdown_option_ids, "reason": reason},
    )
    return _response_json(response, "archive dropdown options")


def unarchive_dropdown_options(
    benchling_service: BenchlingService,
    dropdown_id: str,
    dropdown_option_ids: list[str],
) -> dict[str, Any]:
    """Restore options belonging to a dropdown."""
    response = benchling_service.api.post_response(
        url=f"{_DROPDOWN_API_PATH}/{dropdown_id}/options:unarchive",
        body={"dropdownOptionIds": dropdown_option_ids},
    )
    return _response_json(response, "unarchive dropdown options")
