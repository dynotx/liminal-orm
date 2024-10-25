from typing import Any

import requests
from benchling_sdk.models import ArchiveRecord as BenchlingArchiveRecord
from benchling_sdk.models import Dropdown, DropdownOption, DropdownSummary
from pydantic import BaseModel

from liminal.connection import BenchlingService
from liminal.orm.base_model import BaseModel as BenchlingBaseModel


class ArchiveRecord(BaseModel):
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


def get_benchling_dropdown_id_name_map(
    benchling_service: BenchlingService,
) -> dict[str, str]:
    return {d.id: d.name for d in get_benchling_dropdown_summaries(benchling_service)}


def get_benchling_dropdown_summaries(
    benchling_service: BenchlingService,
) -> list[DropdownSummary]:
    return [
        dropdown
        for sublist in benchling_service.dropdowns.list()
        for dropdown in sublist
    ]


def get_benchling_dropdown_summary_by_name(
    benchling_service: BenchlingService, name: str
) -> DropdownSummary:
    for dropdown in get_benchling_dropdown_summaries(benchling_service):
        if dropdown.name == name:
            return dropdown
    raise Exception(f"Dropdown {name} not found in given list.")


def get_benchling_dropdown_by_name(
    benchling_service: BenchlingService, name: str
) -> Dropdown:
    dropdown = None
    for d in get_benchling_dropdown_summaries(benchling_service):
        if d.name == name:
            dropdown = d
    if dropdown is None:
        raise Exception(
            f"Dropdown {name} not found in Benchling {benchling_service.benchling_tenant}."
        )
    return benchling_service.dropdowns.get_by_id(dropdown.id)


def get_benchling_dropdowns_dict(
    benchling_service: BenchlingService,
    include_archived: bool = False,
) -> dict[str, Dropdown]:
    def _convert_dropdown_from_json(
        d: dict[str, Any], include_archived: bool = False
    ) -> Dropdown:
        all_options = d["allSchemaFieldSelectorOptions"]
        if not include_archived:
            all_options = [o for o in all_options if not o["archiveRecord"]]
        return Dropdown(
            id=d["id"],
            name=d["name"],
            archive_record=BenchlingArchiveRecord(reason=d["archiveRecord"]["purpose"])
            if d["archiveRecord"]
            else None,
            options=[
                DropdownOption(
                    name=o["name"],
                    id=o["id"],
                    archive_record=BenchlingArchiveRecord(
                        reason=o["archiveRecord"]["purpose"]
                    )
                    if o["archiveRecord"]
                    else None,
                )
                for o in all_options
            ],
        )

    with requests.Session() as session:
        request = session.get(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schema-field-selectors/?registryId={benchling_service.registry_id}",
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
        all_dropdowns = request.json()["selectorsByRegistryId"][
            benchling_service.registry_id
        ]
        if not include_archived:
            all_dropdowns = [d for d in all_dropdowns if not d["archiveRecord"]]
    dropdowns = {
        d["name"]: _convert_dropdown_from_json(d, include_archived)
        for d in all_dropdowns
    }
    return dropdowns


def dropdown_exists_in_benchling(
    benchling_service: BenchlingService, name: str
) -> bool:
    return name in get_benchling_dropdown_summaries(benchling_service)


def get_schemas_with_dropdown(dropdown_name: str) -> list[str]:
    schemas_with_dropdown = []
    for model in BenchlingBaseModel.get_all_subclasses():
        for props_dict in [
            m.info["benchling_properties"]
            for m in list(model.__table__.columns)
            if len(m.info.keys()) > 0
        ]:
            if props_dict.dropdown_link == dropdown_name:
                schemas_with_dropdown.append(model.__schema_properties__.name)
    return schemas_with_dropdown
