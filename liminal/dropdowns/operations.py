from __future__ import annotations

import logging
from typing import Any, ClassVar

from benchling_sdk.models import (
    Dropdown,
    DropdownCreate,
    DropdownOption,
    DropdownOptionCreate,
)

from liminal.base.base_operation import BaseOperation
from liminal.connection import BenchlingService
from liminal.dropdowns.api import (
    archive_dropdown,
    create_dropdown,
    resubmit_archive_dropdown_option,
    resubmit_update_dropdown_option,
    unarchive_dropdown,
    update_dropdown_name,
    update_dropdown_options,
)
from liminal.dropdowns.utils import (
    ArchiveRecord,
    dropdown_exists_in_benchling,
    get_benchling_dropdown_by_name,
    get_benchling_dropdown_summary_by_name,
    get_schemas_with_dropdown,
)

logger = logging.getLogger(__name__)


class CreateDropdown(BaseOperation):
    order: ClassVar[int] = 10

    def __init__(self, dropdown_name: str, dropdown_options: list[str]) -> None:
        self.dropdown_name = dropdown_name
        self.dropdown_options = dropdown_options

    def execute(self, benchling_service: BenchlingService) -> dict[str, Dropdown]:
        try:
            dropdown = get_benchling_dropdown_by_name(
                benchling_service, self.dropdown_name
            )
        except Exception:
            dropdown = None
        if dropdown is None:
            options = [
                DropdownOptionCreate(name=option) for option in self.dropdown_options
            ]
            return create_dropdown(
                benchling_service,
                DropdownCreate(
                    name=self.dropdown_name,
                    options=options,
                    registry_id=benchling_service.registry_id,
                ),
            )
        else:
            if dropdown.archive_record is None:
                raise ValueError(f"Dropdown {self.dropdown_name} is already active")
            if self.dropdown_options == [o.name for o in dropdown.options]:
                return UnarchiveDropdown(self.dropdown_name).execute(benchling_service)
            else:
                raise ValueError(
                    f"Dropdown {self.dropdown_name} is different in code versus Benchling."
                )

    def describe_operation(self) -> str:
        return f"{self.dropdown_name}: Creating dropdown with options {self.dropdown_options}."

    def describe(self) -> str:
        return f"{self.dropdown_name}: Dropdown is not defined in Benchling but is defined in code."


class ArchiveDropdown(BaseOperation):
    order: ClassVar[int] = 190

    def __init__(self, dropdown_name: str) -> None:
        self.dropdown_name = dropdown_name

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        dropdown = get_benchling_dropdown_by_name(benchling_service, self.dropdown_name)
        if dropdown.archive_record is not None:
            raise ValueError(f"Dropdown {self.dropdown_name} is already archived.")
        return archive_dropdown(benchling_service, dropdown.id)

    def validate(self, benchling_service: BenchlingService) -> None:
        if schemas_with_dropdown := get_schemas_with_dropdown(self.dropdown_name):
            raise ValueError(
                f"Dropdown {self.dropdown_name} is used in schemas {schemas_with_dropdown}. Cannot archive a dropdown that is in use in non-archived fields."
            )

    def describe_operation(self) -> str:
        return f"{self.dropdown_name}: Archiving dropdown."

    def describe(self) -> str:
        return f"{self.dropdown_name}: Dropdown is defined in Benchling but not in code anymore."


class UnarchiveDropdown(BaseOperation):
    order: ClassVar[int] = 30

    def __init__(self, dropdown_name: str) -> None:
        self.dropdown_name = dropdown_name

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        dropdown = get_benchling_dropdown_by_name(benchling_service, self.dropdown_name)
        if dropdown.archive_record is None:
            raise ValueError(f"Dropdown {self.dropdown_name} is already active.")
        return unarchive_dropdown(benchling_service, dropdown.id)

    def describe_operation(self) -> str:
        return f"{self.dropdown_name}: Unarchiving dropdown."

    def describe(self) -> str:
        return f"{self.dropdown_name}: Dropdown is archived in Benchling but is defined in code again."


class UpdateDropdownName(BaseOperation):
    order: ClassVar[int] = 20

    def __init__(self, dropdown_name: str, new_dropdown_name: str) -> None:
        self.dropdown_name = dropdown_name
        self.new_dropdown_name = new_dropdown_name

    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        dropdown = get_benchling_dropdown_summary_by_name(
            benchling_service, self.dropdown_name
        )
        if dropdown_exists_in_benchling(benchling_service, self.new_dropdown_name):
            raise ValueError(
                f"Dropdown {self.new_dropdown_name} already exists in Benchling."
            )
        return update_dropdown_name(
            benchling_service, dropdown.id, self.new_dropdown_name
        )

    def describe_operation(self) -> str:
        return f"{self.dropdown_name}: Renaming dropdown warehouse name to {self.new_dropdown_name}."

    def describe(self) -> str:
        return f"{self.dropdown_name}: Dropdown in Benchling has a different warehouse name than in code."


class CreateDropdownOption(BaseOperation):
    order: ClassVar[int] = 40

    def __init__(
        self,
        dropdown_name: str,
        option_to_add: str,
        index: int,
    ) -> None:
        self.dropdown_name = dropdown_name
        self.option_to_add = option_to_add
        self.index = index

    def execute(self, benchling_service: BenchlingService) -> dict[str, Dropdown]:
        dropdown = get_benchling_dropdown_by_name(benchling_service, self.dropdown_name)
        options_for_update: list[DropdownOption] = [
            o for o in dropdown.options if o.archive_record is None
        ] + [o for o in dropdown.options if o.archive_record is not None]
        existing_option = next(
            (
                o
                for o in options_for_update
                if o.name == self.option_to_add and o.id is not None
            ),
            None,
        )
        # If the option exists
        if existing_option:
            # If the option exists and is archived
            if existing_option.archive_record is not None:
                existing_option.archive_record = None
                options_for_update.remove(existing_option)
                options_for_update.insert(self.index, existing_option)
            # If the option exists and is active
            else:
                logger.info(
                    f"Option {self.option_to_add} on dropdown {self.dropdown_name} already exists and is active in Benchling. Execution will be skipped."
                )
                return {}
        # If the option does not exist
        else:
            options_for_update.insert(
                self.index, DropdownOption(name=self.option_to_add)
            )
        try:
            return update_dropdown_options(
                benchling_service, dropdown.id, options_for_update
            )
        except Exception as e:
            raise Exception(f"Failed to create dropdown option: {e}")

    def describe_operation(self) -> str:
        return f"{self.dropdown_name}: Creating dropdown option '{self.option_to_add}' at index {self.index}."

    def describe(self) -> str:
        return f"{self.dropdown_name}: Option '{self.option_to_add}' is not defined in Benchling but is defined in code."


class ArchiveDropdownOption(BaseOperation):
    order: ClassVar[int] = 60

    def __init__(
        self,
        dropdown_name: str,
        option_to_remove: str,
        index: int | None = None,
    ) -> None:
        self.dropdown_name = dropdown_name
        self.option_to_remove = option_to_remove
        self.index = index

    def execute(self, benchling_service: BenchlingService) -> dict[str, Dropdown]:
        dropdown = get_benchling_dropdown_by_name(benchling_service, self.dropdown_name)
        option_archived = False
        for option in dropdown.options:
            if option.name == self.option_to_remove:
                if option.archive_record is not None:
                    logger.info(
                        f"Option {self.option_to_remove} on dropdown {self.dropdown_name} is already archived. Skipping archiving."
                    )
                    return {}
                else:
                    option.archive_record = ArchiveRecord(purpose="Made in error")  # type: ignore
                    option_archived = True
                    break
        if not option_archived:
            raise ValueError(
                f"Option {self.option_to_remove} on dropdown {self.dropdown_name} does not exist."
            )
        try:
            resubmit_payload = update_dropdown_options(
                benchling_service, dropdown.id, dropdown.options
            )
            if selector_option_to_update := resubmit_payload.get(
                "schemaFieldSelectorOptionToUpdate"
            ):
                return resubmit_archive_dropdown_option(
                    benchling_service,
                    dropdown.id,
                    self.option_to_remove,
                    dropdown.options,
                    selector_option_to_update,
                )
            return resubmit_payload
        except Exception as e:
            raise Exception(f"Failed to archive dropdown option: {e}")

    def describe_operation(self) -> str:
        return f"{self.dropdown_name}: Archiving dropdown option '{self.option_to_remove}'."

    def describe(self) -> str:
        return f"{self.dropdown_name}: Option '{self.option_to_remove}' is defined in Benchling but not in code."


class UpdateDropdownOption(BaseOperation):
    order: ClassVar[int] = 50

    def __init__(
        self, dropdown_name: str, old_option_name: str, new_option_name: str
    ) -> None:
        self.dropdown_name = dropdown_name
        self.old_option_name = old_option_name
        self.new_option_name = new_option_name

    def execute(self, benchling_service: BenchlingService) -> dict[str, Dropdown]:
        dropdown = get_benchling_dropdown_by_name(benchling_service, self.dropdown_name)
        option_updated = False
        for option in dropdown.options:
            if option.name == self.old_option_name:
                option.name = self.new_option_name
                option_updated = True
                break
            if option.name == self.new_option_name:
                raise ValueError(
                    f"Option {self.new_option_name} on dropdown {self.dropdown_name} already exists and is {'archived' if option.archive_record is not None else 'active'} in Benchling."
                )
        if not option_updated:
            raise ValueError(
                f"Option {self.old_option_name} on dropdown {self.dropdown_name} does not exist."
            )
        try:
            resubmit_payload = update_dropdown_options(
                benchling_service, dropdown.id, dropdown.options
            )
            if selector_option_to_update := resubmit_payload.get(
                "schemaFieldSelectorOptionToUpdate"
            ):
                return resubmit_update_dropdown_option(
                    benchling_service,
                    dropdown.id,
                    self.old_option_name,
                    dropdown.options,
                    selector_option_to_update,
                )
            return resubmit_payload
        except Exception as e:
            raise Exception(f"Failed to update dropdown option: {e}")

    def describe_operation(self) -> str:
        return f"{self.dropdown_name}: Renaming dropdown option from '{self.old_option_name}' to '{self.new_option_name}'."

    def describe(self) -> str:
        return f"{self.dropdown_name}: Option '{self.old_option_name}' in Benchling has name '{self.new_option_name}' in code."


class ReorderDropdownOptions(BaseOperation):
    order: ClassVar[int] = 70

    def __init__(self, dropdown_name: str, new_order: list[str]) -> None:
        self.dropdown_name = dropdown_name
        self.new_order = new_order

    def execute(self, benchling_service: BenchlingService) -> dict[str, Dropdown]:
        dropdown = get_benchling_dropdown_by_name(benchling_service, self.dropdown_name)
        options_for_update = self._get_reordered_options(dropdown)
        return update_dropdown_options(
            benchling_service, dropdown.id, options_for_update
        )

    def describe_operation(self) -> str:
        return f"{self.dropdown_name}: Reordering dropdown options."

    def describe(self) -> str:
        return f"{self.dropdown_name}: Dropdown in Benchling has options in a different order than in code."

    def _get_reordered_options(self, dropdown: Dropdown) -> list[DropdownOption]:
        order_dict = {name: index for index, name in enumerate(self.new_order)}

        sorted_options = sorted(
            [option for option in dropdown.options if option.name in order_dict],
            key=lambda option: order_dict[option.name],
        )
        remaining_options = [
            option for option in dropdown.options if option.name not in order_dict
        ]
        sorted_options.extend(remaining_options)
        return sorted_options
