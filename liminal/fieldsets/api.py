import json
from typing import Any

import requests

from liminal.connection.benchling_service import BenchlingService


def create_fieldset(
    benchling_service: BenchlingService, payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Create a new fieldset.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/fieldsets",
            data=json.dumps(payload),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to create fieldset:", response.content)
        return response.json()


def archive_fieldsets(
    benchling_service: BenchlingService, fieldset_ids: list[str]
) -> dict[str, Any]:
    """
    Archive a list of fieldset ids.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/fieldsets:bulk-archive",
            data=json.dumps({"ids": fieldset_ids, "purpose": "Made in error"}),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to archive fieldsets:", response.content)
        return response.json()


def unarchive_fieldsets(
    benchling_service: BenchlingService, fieldset_ids: list[str]
) -> dict[str, Any]:
    """
    Unarchive a list of fieldset ids.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/fieldsets:bulk-unarchive",
            data=json.dumps({"ids": fieldset_ids}),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to unarchive fieldsets:", response.content)
        return response.json()


def update_fieldset(
    benchling_service: BenchlingService, fieldset_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Update the fieldset with a new field.
    """
    with requests.Session() as session:
        response = session.patch(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/fieldsets/{fieldset_id}",
            data=json.dumps(payload),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to update fieldset:", response.content)
        return response.json()


def create_fieldset_field(
    benchling_service: BenchlingService, fieldset_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Create a new field in a fieldset.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/fieldsets/{fieldset_id}/fields",
            data=json.dumps(payload),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to create fieldset field:", response.content)
        return response.json()


def update_fieldset_field(
    benchling_service: BenchlingService,
    fieldset_id: str,
    field_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a new field in a fieldset.
    """
    with requests.Session() as session:
        response = session.patch(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/fieldsets/{fieldset_id}/fields/{field_id}",
            data=json.dumps(payload),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to update fieldset field:", response.content)
        return response.json()


def delete_fieldset_field(
    benchling_service: BenchlingService,
    fieldset_id: str,
    field_id: str,
) -> dict[str, Any]:
    """
    Delete a field from a fieldset.
    """
    with requests.Session() as session:
        response = session.delete(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/fieldsets/{fieldset_id}/fields/{field_id}",
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to update fieldset field:", response.content)
        return response.json()
