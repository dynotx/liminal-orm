import json
import logging
from typing import Any

import requests
from benchling_sdk.models import Dropdown, DropdownCreate, DropdownOption
from rich import print

from liminal.connection.benchling_service import BenchlingService

logger = logging.getLogger(__name__)


def create_dropdown(
    benchling_service: BenchlingService, new_dropdown: DropdownCreate
) -> dict[str, Dropdown]:
    """
    Create a new dropdown.
    """
    dropdown = benchling_service.dropdowns.create(dropdown=new_dropdown)
    return {dropdown.id: dropdown}


def update_dropdown_name(
    benchling_service: BenchlingService, dropdown_id: str, new_name: str
) -> dict[str, Any]:
    """
    Update the name of a dropdown.
    """
    with requests.Session() as session:
        response = session.patch(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schema-field-selectors/{dropdown_id}",
            data=json.dumps({"name": new_name}),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception(f"Failed to update dropdown name: {response.json()}")
        return response.json()


def archive_dropdown(
    benchling_service: BenchlingService, dropdown_id: str
) -> dict[str, Any]:
    """
    Archive a dropdown.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schema-field-selectors:bulk-archive",
            data=json.dumps({"ids": [dropdown_id], "purpose": "Made in error"}),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception(f"Failed to archive dropdown: {response.json()}")
        return response.json()


def unarchive_dropdown(
    benchling_service: BenchlingService, dropdown_id: str
) -> dict[str, Any]:
    """
    Unarchive a dropdown.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schema-field-selectors:bulk-unarchive",
            data=json.dumps({"ids": [dropdown_id]}),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception(f"Failed to unarchive dropdown: {response.json()}")
        return response.json()


def update_dropdown_options(
    benchling_service: BenchlingService, dropdown_id: str, options: list[DropdownOption]
) -> dict[str, Any]:
    """
    Update the options of a dropdown.
    """
    with requests.Session() as session:
        response = session.patch(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schema-field-selectors/{dropdown_id}",
            data=json.dumps(
                {"schemaFieldSelectorOptions": [o.to_dict() for o in options]}
            ),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception(response.json())
        return response.json()


def resubmit_archive_dropdown_option(
    benchling_service: BenchlingService,
    dropdown_id: str,
    option_to_remove: str,
    options: list[DropdownOption],
    selector_option_to_update: dict[str, Any],
) -> dict[str, Any]:
    """When archiving a dropdown option that is used as a field value in entities, we need to resubmit the request to update the dropdown options."""
    print(
        f"[bold yellow]WARNING:[/bold yellow] Option {option_to_remove} is used as a field value in {selector_option_to_update['numLinkedTags']} entities. Archiving it will not change the values of fields using this option, but it will hide search filter options for it."
    )
    while True:
        print(
            "[bold bright_cyan]Input Required:[/bold bright_cyan] Are you sure you want to archive?"
        )
        checkpoint = input("Enter 'c' to continue, 'q' to quit and rollback:")
        if checkpoint in ["c", "q"]:
            break
        print(
            "Invalid input. Please enter 'c' to continue or 'q' to quit and rollback."
        )
    if checkpoint == "q":
        raise ValueError("User requested rollback.")
    with requests.Session() as session:
        resubmitted_response = session.patch(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schema-field-selectors/{dropdown_id}",
            data=json.dumps(
                {
                    "schemaFieldSelectorOptions": [o.to_dict() for o in options],
                    "selectorOptionToUpdate": selector_option_to_update,
                }
            ),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
    if not resubmitted_response.ok:
        raise Exception(resubmitted_response.json())
    return resubmitted_response.json()


def resubmit_update_dropdown_option(
    benchling_service: BenchlingService,
    dropdown_id: str,
    old_option_name: str,
    options: list[DropdownOption],
    selector_option_to_update: dict[str, Any],
) -> dict[str, Any]:
    """When renaming a dropdown option that is used as a field value in entities, we need to resubmit the request to update the dropdown options."""
    print(
        f"[bold yellow]WARNING:[/bold yellow] Option {old_option_name} is used as a field value in {selector_option_to_update['numLinkedTags']} entities. Renaming it will change the values of all fields using this option to {selector_option_to_update['newName']}."
    )
    while True:
        print(
            "[bold bright_cyan]Input Required:[/bold bright_cyan] Are you sure you want to rename?"
        )
        checkpoint = input("Enter 'c' to continue, 'q' to quit and rollback:")
        if checkpoint in ["c", "q"]:
            break
        print(
            "Invalid input. Please enter 'c' to continue or 'q' to quit and rollback."
        )
    if checkpoint == "q":
        raise ValueError("User requested rollback.")
    with requests.Session() as session:
        resubmitted_response = session.patch(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schema-field-selectors/{dropdown_id}",
            data=json.dumps(
                {
                    "schemaFieldSelectorOptions": [o.to_dict() for o in options],
                    "selectorOptionToUpdate": selector_option_to_update,
                }
            ),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
    if not resubmitted_response.ok:
        raise Exception(resubmitted_response.json())
    return resubmitted_response.json()
