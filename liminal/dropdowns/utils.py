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
) -> dict[str, Dropdown]:
    with requests.Session() as session:
        request = session.get(
            f"https://{benchling_service.benchling_tenant}.benchling.com/1/api/schema-field-selectors/?registryId={benchling_service.registry_id}",
            headers=benchling_service.custom_post_headers,
            cookies=benchling_service.custom_post_cookies,
        )
    return {
        d["name"]: Dropdown(
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
                for o in d["allSchemaFieldSelectorOptions"]
            ],
        )
        for d in request.json()["selectorsByRegistryId"][benchling_service.registry_id]
    }


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
