from benchling_sdk.models import Dropdown

from liminal.base.base_dropdown import BaseDropdown
from liminal.base.compare_operation import CompareOperation
from liminal.connection import BenchlingService
from liminal.dropdowns.operations import (
    ArchiveDropdown,
    ArchiveDropdownOption,
    CreateDropdown,
    CreateDropdownOption,
    ReorderDropdownOptions,
    UnarchiveDropdown,
)
from liminal.dropdowns.utils import get_benchling_dropdowns_dict


def compare_dropdowns(
    benchling_service: BenchlingService, dropdown_names: set[str] | None = None
) -> dict[str, list[CompareOperation]]:
    dropdown_operations: dict[str, list[CompareOperation]] = {}
    benchling_dropdowns: dict[str, Dropdown] = get_benchling_dropdowns_dict(
        benchling_service, include_archived=True
    )
    processed_benchling_names = set()
    model_dropdowns = BaseDropdown.get_all_subclasses(dropdown_names)
    if dropdown_names:
        benchling_dropdowns = {
            name: benchling_dropdowns[name]
            for name in [d.__benchling_name__ for d in model_dropdowns]
        }
    archived_benchling_dropdown_names = [
        d
        for d in benchling_dropdowns.keys()
        if benchling_dropdowns[d].archive_record is not None
    ]
    active_benchling_dropdown_names = [
        d
        for d in benchling_dropdowns.keys()
        if benchling_dropdowns[d].archive_record is None
    ]
    dropdowns_to_unarchive = []
    for model_dropdown in model_dropdowns:
        ops: list[CompareOperation] = []
        if model_dropdown.__benchling_name__ in archived_benchling_dropdown_names:
            ops.append(
                CompareOperation(
                    op=UnarchiveDropdown(model_dropdown.__benchling_name__),
                    reverse_op=ArchiveDropdown(model_dropdown.__benchling_name__),
                )
            )
            dropdowns_to_unarchive.append(model_dropdown.__benchling_name__)
        if (
            model_dropdown.__benchling_name__ in active_benchling_dropdown_names
            or model_dropdown.__benchling_name__ in dropdowns_to_unarchive
        ):
            if model_dropdown.__benchling_name__ in dropdowns_to_unarchive:
                benchling_options = [
                    o.name
                    for o in benchling_dropdowns[
                        model_dropdown.__benchling_name__
                    ].options
                ]
            else:
                benchling_options = [
                    o.name
                    for o in benchling_dropdowns[
                        model_dropdown.__benchling_name__
                    ].options
                    if o.archive_record is None
                ]
            if (
                benchling_options != model_dropdown.__allowed_values__
                or model_dropdown.__benchling_name__ in dropdowns_to_unarchive
            ):
                if model_dropdown.__benchling_name__ in dropdowns_to_unarchive:
                    options_to_create = model_dropdown.__allowed_values__
                else:
                    options_to_create = [
                        o
                        for o in model_dropdown.__allowed_values__
                        if o not in benchling_options
                    ]
                options_to_archive = set(benchling_options) - set(
                    model_dropdown.__allowed_values__
                )
                recreated_benchling_options = [
                    o
                    for o in benchling_options
                    if o in model_dropdown.__allowed_values__
                ]
                recreated_model_options = [
                    o
                    for o in model_dropdown.__allowed_values__
                    if o in recreated_benchling_options
                ]
                for option in options_to_archive:
                    ops.append(
                        CompareOperation(
                            op=ArchiveDropdownOption(
                                model_dropdown.__benchling_name__,
                                option,
                                index=benchling_options.index(option),
                            ),
                            reverse_op=CreateDropdownOption(
                                model_dropdown.__benchling_name__,
                                option,
                                index=benchling_options.index(option),
                            ),
                        )
                    )
                for option in options_to_create:
                    ops.append(
                        CompareOperation(
                            op=CreateDropdownOption(
                                model_dropdown.__benchling_name__,
                                option,
                                index=model_dropdown.__allowed_values__.index(option),
                            ),
                            reverse_op=ArchiveDropdownOption(
                                model_dropdown.__benchling_name__,
                                option,
                                index=model_dropdown.__allowed_values__.index(option),
                            ),
                        )
                    )
                if recreated_benchling_options != recreated_model_options:
                    ops.append(
                        CompareOperation(
                            op=ReorderDropdownOptions(
                                model_dropdown.__benchling_name__,
                                model_dropdown.__allowed_values__,
                            ),
                            reverse_op=ReorderDropdownOptions(
                                model_dropdown.__benchling_name__,
                                recreated_benchling_options,
                            ),
                        )
                    )
        else:
            ops.append(
                CompareOperation(
                    op=CreateDropdown(
                        model_dropdown.__benchling_name__,
                        model_dropdown.__allowed_values__,
                    ),
                    reverse_op=ArchiveDropdown(model_dropdown.__benchling_name__),
                )
            )
        dropdown_operations[model_dropdown.__name__] = ops
        processed_benchling_names.add(model_dropdown.__benchling_name__)
    archive_ops: list[CompareOperation] = []
    for dropdown_to_archive in (
        set(active_benchling_dropdown_names) - processed_benchling_names
    ):
        archive_ops.append(
            CompareOperation(
                op=ArchiveDropdown(dropdown_to_archive),
                reverse_op=UnarchiveDropdown(dropdown_to_archive),
            )
        )
    dropdown_operations["Archive"] = archive_ops
    return dropdown_operations
