from typing import Any

from benchling_sdk.models import ArchiveRecord
from benchling_sdk.models import Dropdown, DropdownOption, DropdownSummary

from liminal.connection import BenchlingService
from liminal.dropdowns.api import list_dropdowns, list_dropdowns_with_options
from liminal.utils import to_pascal_case


def get_benchling_dropdown_id_name_map(
    benchling_service: BenchlingService,
) -> dict[str, str]:
    return {d.id: d.name for d in get_benchling_dropdown_summaries(benchling_service)}


def get_benchling_dropdown_name_to_classname_map(
    benchling_service: BenchlingService,
    include_archived: bool = False,
) -> dict[str, str]:
    """Gets the dropdown name to classname map by querying Benchling dropdowns and using the dropdown name to create the classname."""
    return {
        dropdown["name"]: to_pascal_case(dropdown["name"])
        for dropdown in list_dropdowns(
            benchling_service, include_archived=include_archived
        )
    }


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


def _convert_dropdown_from_v3_to_v2_sdk(
    dropdown: dict[str, Any], include_archived: bool
) -> Dropdown:
    options = dropdown.get("options", [])
    if not include_archived:
        options = [option for option in options if not option.get("archived", False)]

    return Dropdown(
        id=dropdown["id"],
        name=dropdown["name"],
        archive_record=ArchiveRecord(reason=dropdown["archiveReason"])
        if dropdown.get("archived", False)
        else None,
        options=[
            DropdownOption(
                id=option["id"],
                name=option["name"],
                archive_record=ArchiveRecord(reason=option["archiveReason"])
                if option.get("archived", False)
                else None,
            )
            for option in options
        ],
    )


def get_benchling_dropdowns_dict(
    benchling_service: BenchlingService,
    include_archived: bool = False,
    dropdown_names_for_options: set[str] | None = None,
) -> dict[str, Dropdown]:
    dropdowns = list_dropdowns_with_options(
        benchling_service,
        include_archived=include_archived,
        dropdown_names_for_options=dropdown_names_for_options,
    )
    return {
        dropdown["name"]: _convert_dropdown_from_v3_to_v2_sdk(
            dropdown, include_archived
        )
        for dropdown in dropdowns
    }


def dropdown_exists_in_benchling(
    benchling_service: BenchlingService, name: str
) -> bool:
    return any(
        d.name == name for d in get_benchling_dropdown_summaries(benchling_service)
    )


def get_schemas_with_dropdown(dropdown_name: str) -> list[str]:
    from liminal.orm.base_model import BaseModel as BenchlingBaseModel

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
