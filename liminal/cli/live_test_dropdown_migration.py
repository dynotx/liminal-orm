import uuid

from liminal.base.base_operation import BaseOperation
from liminal.connection.benchling_service import BenchlingService
from liminal.dropdowns.operations import (
    ArchiveDropdown,
    ArchiveDropdownOption,
    CreateDropdown,
    CreateDropdownOption,
    ReorderDropdownOptions,
    UnarchiveDropdown,
    UpdateDropdownName,
    UpdateDropdownOption,
)
from liminal.migrate.components import execute_operations, execute_operations_dry_run


def mock_dropdown_full_migration(
    benchling_service: BenchlingService, test_dropdown_name: str, dry_run: bool = True
) -> None:
    """This test is a full migration of a dropdown, including renaming, creating, updating, archiving, and unarchiving options.
    This is meant to test the connection of all dropdown operations and can be run multiple times if successful.
    If this test fails at any point, ensure that the dropdown in benchling is archived and renamed to an arbitrary value.
    If dry_run is set to False, the operations will be executed.
    If dry_run is set to True, the operations will be executed in dry run mode and only the description of the operations will be printed.
    """
    random_id = f"{str(uuid.uuid4())[0:8]}_arch"

    dropdown_options = ["Option 1", "Option 2"]
    create_dropdown_op = CreateDropdown(test_dropdown_name, dropdown_options)

    update_dropdown_op = UpdateDropdownName(
        test_dropdown_name, f"{test_dropdown_name}_{random_id}"
    )
    test_dropdown_name = f"{test_dropdown_name}_{random_id}"

    create_dropdown_option_op = CreateDropdownOption(
        test_dropdown_name, "Option 3 New", 2
    )

    update_dropdown_option_op = UpdateDropdownOption(
        test_dropdown_name, "Option 3 New", "Option 3"
    )

    archive_dropdown_option_op = ArchiveDropdownOption(test_dropdown_name, "Option 3")

    unarchive_dropdown_option_op = CreateDropdownOption(
        test_dropdown_name, "Option 3", 1
    )

    reorder_dropdown_options_op = ReorderDropdownOptions(
        test_dropdown_name, ["Option 1", "Option 2", "Option 3"]
    )

    archive_dropdown_op = ArchiveDropdown(test_dropdown_name)

    unarchive_dropdown_op = UnarchiveDropdown(test_dropdown_name)

    rearchive_dropdown_op = ArchiveDropdown(test_dropdown_name)

    ops: list[BaseOperation] = [
        create_dropdown_op,
        update_dropdown_op,
        create_dropdown_option_op,
        update_dropdown_option_op,
        archive_dropdown_option_op,
        unarchive_dropdown_option_op,
        reorder_dropdown_options_op,
        archive_dropdown_op,
        unarchive_dropdown_op,
        rearchive_dropdown_op,
    ]
    execute_operations_dry_run(ops) if dry_run else execute_operations(
        benchling_service, ops
    )
    print("Dry run migration complete!") if dry_run else print("Migration complete!")
