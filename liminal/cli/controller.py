from pathlib import Path

from rich import print

from liminal.connection.benchling_service import BenchlingService
from liminal.dropdowns.generate_files import generate_all_dropdown_files
from liminal.entity_schemas.generate_files import generate_all_entity_schema_files
from liminal.migrate.components import execute_operations, get_full_migration_operations
from liminal.migrate.revisions_timeline import RevisionsTimeline


def generate_all_files(benchling_service: BenchlingService, write_path: Path) -> None:
    """Initializes all the dropdown and entity schema files from your Benchling tenant and writes to the given path.
    Creates and writes to the dropdowns/ and entity_schemas/ directories.
    Note: This will overwrite any existing dropdowns or entity schemas that exist in the given path.

    Parameters
    ----------
    benchling_service : BenchlingService
        The Benchling service object that is connected to a specified Benchling tenant.
    write_path : Path
        The path to write the generated files to.
    """
    generate_all_dropdown_files(benchling_service, write_path)
    generate_all_entity_schema_files(benchling_service, write_path)


def autogenerate_revision_file(
    benchling_service: BenchlingService,
    write_dir_path: Path,
    description: str,
    current_revision_id: str,
) -> None:
    """Generates a revision file by comparing locally defined schemas to the given Benchling tenant.
    The revision file contains a unique revision id, the down_revision_id (which is the latest revision id that this revision is based on),
    and a list of operations to be performed to upgrade or downgrade the Benchling tenant.
    It writes this standard revision file to liminal/versions/ for the user to review/edit and then run at a later time.

    Parameters
    ----------
    benchling_service : BenchlingService
        The Benchling service object that is connected to a specified Benchling tenant.
    write_dir_path : Path
        The directory path where the revision file will be written to.
    description : str
        A description of the revision being generated. This will also be included in the file name.
    """
    revision_timeline = RevisionsTimeline(write_dir_path)
    if current_revision_id != revision_timeline.get_latest_revision().id:
        raise Exception(
            f"Your target Benchling tenant is not up to date with the latest revision ({revision_timeline.get_latest_revision().id}). Please upgrade to the latest revision before generating a new revision."
        )
    compare_ops = get_full_migration_operations(benchling_service)
    write_path = revision_timeline.write_new_revision(description, compare_ops)
    if write_path is None:
        print("[bold green]No changes needed. Skipping revision file generation.")
    else:
        print(f"[bold green]Revision file generated at {write_path}")


def upgrade_benchling_tenant(
    benchling_service: BenchlingService,
    versions_dir_path: Path,
    current_revision_id: str,
    upgrade_descriptor: str,
) -> str:
    """Upgrades the given Benchling tenant based on the provided upgrade descriptor.
    The upgrade descriptor can be a revision id, "head", or a number of steps to upgrade from the current revision (+n).
    First retrieves the operations to upgrade from the current revision to the target revision using the upgrade function defined in the revision files, then executes the operations.

    Parameters
    ----------
    benchling_service : BenchlingService
        The Benchling service object that is connected to a specified Benchling tenant.
    versions_dir_path : Path
        The directory path where the revision files are stored.
    current_revision_id : str
        The current revision id.
    upgrade_descriptor : str
        The upgrade descriptor.

    Returns
    -------
    str
        The target revision id.
    """
    revisions_timeline = RevisionsTimeline(versions_dir_path)
    if current_revision_id not in revisions_timeline.revisions_map.keys():
        raise Exception(
            f"CURRENT_REVISION_ID in liminal/env.py ({current_revision_id}) is invalid and not found in any of the revision file names."
        )
    revision_id = None
    if upgrade_descriptor == "head":
        revision_id = revisions_timeline.get_latest_revision().id
        try:
            operations_dict = revisions_timeline.get_upgrade_operations(
                current_revision_id, revision_id
            )
        except Exception as e:
            raise Exception(f"Error with upgrade descriptor {upgrade_descriptor}: {e}")
    elif upgrade_descriptor.startswith("+"):
        try:
            steps = int(upgrade_descriptor[1:])
            if steps <= 0:
                raise Exception("Error.")
        except Exception:
            raise Exception(
                f"Error with upgrade descriptor {upgrade_descriptor}. Use '+n' where n is a positive number."
            )
        if revisions_timeline.get_revision_index(current_revision_id) - steps < 0:
            raise Exception(
                f"Error with upgrade descriptor {upgrade_descriptor}. Attempting to upgrade {upgrade_descriptor} steps from {current_revision_id} when there are {revisions_timeline.get_revision_index(current_revision_id)} possible upgrade revisions left before reaching the latest revision."
            )
        revision_id = revisions_timeline.get_nth_revision(current_revision_id, steps).id
        operations_dict = revisions_timeline.get_upgrade_operations(
            current_revision_id, revision_id
        )
    elif upgrade_descriptor in revisions_timeline.revisions_map.keys():
        revision_id = upgrade_descriptor
        operations_dict = revisions_timeline.get_upgrade_operations(
            current_revision_id, revision_id
        )
    else:
        raise Exception(
            f"Error with upgrade descriptor {upgrade_descriptor}. Must be 'head', '+n', or a valid revision id."
        )

    print(
        f"[bold]Upgrading from {current_revision_id} to {revision_id}. {revisions_timeline.get_absolute_distance(current_revision_id, revision_id)} revision file(s) away..."
    )
    for index, (revision_ops_id, operations) in enumerate(operations_dict.items()):
        print(
            f"[dim]Revision id: {revision_ops_id}... ({index + 1}/{len(operations_dict)})"
        )
        success = execute_operations(benchling_service, operations)
        if not success:
            raise Exception(
                f"Upgrade in revision {revision_ops_id} failed. Check the output for more details."
            )
    return revision_id


def downgrade_benchling_tenant(
    benchling_service: BenchlingService,
    versions_dir_path: Path,
    current_revision_id: str,
    downgrade_str: str,
) -> str:
    """Downgrades the given Benchling tenant based on the provided downgrade descriptor.
    The downgrade descriptor can be a revision id, or a number of steps to downgrade from the current revision (-n).
    First retrieves the operations to downgrade from the current revision to the target revision using the downgrade function defined in the revision files, then executes the operations.

    Parameters
    ----------
    benchling_service : BenchlingService
        The Benchling service object that is connected to a specified Benchling tenant.
    versions_dir_path : Path
        The directory path where the revision files are stored.
    current_revision_id : str
        The current revision id.
    downgrade_str : str
        The downgrade descriptor.

    Returns
    -------
    str
        The target revision id.
    """
    revisions_timeline = RevisionsTimeline(versions_dir_path)
    if current_revision_id not in revisions_timeline.revisions_map.keys():
        raise Exception(
            f"CURRENT_REVISION_ID in liminal/env.py ({current_revision_id}) is invalid and not found in any of the revision file names."
        )
    revision_id = None
    if downgrade_str.startswith("-"):
        try:
            steps = int(downgrade_str[1:])
            if steps <= 0:
                raise Exception("Error.")
        except Exception:
            raise Exception(
                f"Error with downgrade descriptor {downgrade_str}. Use '-n' where n is a positive number."
            )
        if revisions_timeline.get_revision_index(current_revision_id) + steps >= len(
            revisions_timeline.revisions_map.keys()
        ):
            raise Exception(
                f"Error with downgrade descriptor {downgrade_str}. Attempting to downgrade {downgrade_str} steps from {current_revision_id} when there are {len(revisions_timeline.revisions_map.keys()) - revisions_timeline.get_revision_index(current_revision_id)} possible downgrade revisions left before reaching the earliest revision."
            )
        revision_id = revisions_timeline.get_nth_revision(
            current_revision_id, (steps * -1)
        ).id
        operations_dict = revisions_timeline.get_downgrade_operations(
            current_revision_id, revision_id
        )
    elif downgrade_str in revisions_timeline.revisions_map.keys():
        revision_id = downgrade_str
        operations_dict = revisions_timeline.get_downgrade_operations(
            current_revision_id, revision_id
        )
    else:
        raise Exception(
            f"Error with downgrade descriptor {downgrade_str}. Must be '-n', or a valid revision id."
        )

    print(
        f"[bold]Downgrading from {current_revision_id} to {revision_id}. {revisions_timeline.get_absolute_distance(current_revision_id, revision_id)} revision file(s) away..."
    )
    for index, (revision_ops_id, operations) in enumerate(operations_dict.items()):
        print(
            f"[dim]Revision id: {revision_ops_id}... ({index + 1}/{len(operations_dict)})"
        )
        success = execute_operations(benchling_service, operations)
        if not success:
            raise Exception(
                f"Downgrade in revision {revision_ops_id} failed. Check the output for more details."
            )
    return revision_id
