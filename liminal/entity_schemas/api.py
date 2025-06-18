import json
from typing import Any

import requests

from liminal.connection import BenchlingService
from liminal.utils import await_queued_response


def create_entity_schema(
    benchling_service: BenchlingService, payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Create a new entity schema.
    """
    response = benchling_service.api.post_response(
        url="/api/v2-alpha/entity-schemas", body=payload
    )
    if not (200 <= response.status_code < 300):
        raise Exception("Failed to create entity schema:", response.content)
    return json.loads(response.content)


def archive_tag_schemas(
    benchling_service: BenchlingService, entity_schema_ids: list[str]
) -> dict[str, Any]:
    """
    Archive a list of entity schema ids.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/tag-schemas:bulk-archive",
            data=json.dumps({"ids": entity_schema_ids, "purpose": "Made in error"}),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to archive tag schemas:", response.content)
        return response.json()


def unarchive_tag_schemas(
    benchling_service: BenchlingService, entity_schema_ids: list[str]
) -> dict[str, Any]:
    """
    Unarchive a list of entity schema ids.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/tag-schemas:bulk-unarchive",
            data=json.dumps({"ids": entity_schema_ids}),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to unarchive tag schemas:", response.content)
        return response.json()


def update_tag_schema(
    benchling_service: BenchlingService, entity_schema_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Update the tag schema with a new field.
    """
    with requests.Session() as session:
        queued_response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/tag-schemas/{entity_schema_id}/actions/update",
            data=json.dumps(payload),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not queued_response.ok:
            raise Exception("Failed to update tag schema:", queued_response.content)
        return await_queued_response(
            queued_response.json()["status_url"], benchling_service
        )


def set_tag_schema_name_template(
    benchling_service: BenchlingService, entity_schema_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Update the tag schema name template. Must be in a separate endpoint compared to update_tag_schema.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/tag-schemas/{entity_schema_id}/actions/set-name-template",
            data=json.dumps(payload),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to set tag schema name template:", response.content)
        return response.json()


def add_fieldset_to_schema(
    benchling_service: BenchlingService, entity_schema_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Add a fieldset to a schema.
    """
    with requests.Session() as session:
        response = session.post(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schemas/{entity_schema_id}/fieldsets",
            data=json.dumps(payload),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not response.ok:
            raise Exception("Failed to add fieldset to schema:", response.content)
        return response.json()


def delete_fieldset_from_schema(
    benchling_service: BenchlingService,
    entity_schema_id: str,
    fieldset_id: str,
    schema_prefix_replacement: str,
) -> dict[str, Any]:
    """
    Delete a fieldset from a schema and set new schema prefix.
    """
    with requests.Session() as session:
        queued_response = session.delete(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schemas/{entity_schema_id}/fieldsets/{fieldset_id}",
            data=json.dumps({"schemaPrefixReplacement": schema_prefix_replacement}),
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        if not queued_response.ok:
            raise Exception(
                "Failed to delete fieldset from schema:", queued_response.content
            )
        return await_queued_response(
            queued_response.json()["status_url"], benchling_service
        )
