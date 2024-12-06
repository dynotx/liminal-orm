import traceback

from rich import print

from liminal.base.base_operation import BaseOperation
from liminal.base.compare_operation import CompareOperation
from liminal.connection import BenchlingService
from liminal.dropdowns.compare import compare_dropdowns
from liminal.entity_schemas.compare import compare_entity_schemas


def get_full_migration_operations(
    benchling_service: BenchlingService,
    dropdown_schema_names: set[str] | None = None,
    entity_schema_names: set[str] | None = None,
) -> list[CompareOperation]:
    """
    This generates the full list of operations for a migration.
    It compares the dropdowns and entity schemas defined in code to the Benchling instance it is pointed at
    and generates the operations to bring Benchling up to date with the code.
    """
    entity_schema_operations: list[CompareOperation] = []
    dropdown_operations: list[CompareOperation] = []
    if not dropdown_schema_names or len(dropdown_schema_names) > 0:
        dropdown_comparison = compare_dropdowns(
            benchling_service, dropdown_schema_names
        )
        dropdown_operations = [
            op for ops_list in dropdown_comparison.values() for op in ops_list
        ]
        if len(dropdown_operations) == 0:
            print(
                f"[bold]Dropdowns are in sync for {benchling_service.benchling_tenant} tenant!"
            )
        else:
            print(
                f"[bold]Dropdowns are out of sync for {benchling_service.benchling_tenant} tenant."
            )

    if not entity_schema_names or len(entity_schema_names) > 0:
        entity_schema_comparison = compare_entity_schemas(
            benchling_service, entity_schema_names
        )
        entity_schema_operations = [
            compare_op
            for compare_ops_list in entity_schema_comparison.values()
            for compare_op in compare_ops_list
        ]
        if len(entity_schema_operations) == 0:
            print(
                f"[bold]Entity schemas are in sync for {benchling_service.benchling_tenant} tenant!"
            )
        else:
            print(
                f"[bold]Entity schemas are out of sync for {benchling_service.benchling_tenant} tenant."
            )

    all_operations: list[CompareOperation] = (
        dropdown_operations + entity_schema_operations
    )
    return sorted(all_operations)


def execute_operations(
    benchling_service: BenchlingService, operations: list[BaseOperation]
) -> bool:
    """This runs the given operations. It validates the operations and then executes them."""
    for o in operations:
        o.validate(benchling_service)

    print("[bold]Executing operations...")
    index = 1
    for o in operations:
        print(f"{index}. {o.describe_operation()}")
        try:
            o.execute(benchling_service)
        except Exception as e:
            traceback.print_exc()
            print(f"[bold red]Error executing operation {o.__class__.__name__}: {e}]")
            return False
        index += 1
    return True


def execute_operations_dry_run(
    benchling_service: BenchlingService, operations: list[BaseOperation]
) -> None:
    """This runs the given operations in dry run mode. It only prints a description of the operations and validates them."""
    print("[bold]Executing dry run of operations...")
    index = 1
    for o in operations:
        print(f"{index}. {o.describe()}")
        o.validate(benchling_service)
        index += 1
