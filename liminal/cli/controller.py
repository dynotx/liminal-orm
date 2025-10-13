from pathlib import Path

from rich import print

from liminal.connection.benchling_service import BenchlingService
from liminal.dropdowns.generate_files import generate_all_dropdown_files
from liminal.entity_schemas.generate_files import generate_all_entity_schema_files
from liminal.migrate.components import execute_operations, get_full_migration_operations
from liminal.migrate.revisions_timeline import RevisionsTimeline
from liminal.results_schemas.generate_files import generate_all_results_schema_files


def generate_all_files(
    benchling_service: BenchlingService,
    write_path: Path,
    entity_schemas_flag: bool = True,
    dropdowns_flag: bool = True,
    results_schemas_flag: bool = True,
    overwrite: bool = False,
) -> None:
    """Initializes all the dropdown, entity schema, and results schema files from your Benchling tenant and writes to the given path.
    Creates and writes to the dropdowns/, entity_schemas/, and results_schemas/ directories.
    Note: By default, this will overwrite any existing dropdowns, entity schemas, or results schemas that exist in the given path.

    Parameters
    ----------
    benchling_service : BenchlingService
        The Benchling service object that is connected to a specified Benchling tenant.
    write_path : Path
        The path to write the generated files to.
    entity_schemas_flag : bool
        Whether to generate the entity schema files in the entity_schemas/ directory.
    dropdowns_flag : bool
        Whether to generate the dropdown files in the dropdowns/ directory.
    results_schemas_flag : bool
        Whether to generate the results schema files in the results_schemas/ directory.
    overwrite : bool
        Whether to overwrite existing the existing write_path directory.
    """
    if dropdowns_flag:
        generate_all_dropdown_files(benchling_service, write_path, overwrite)
    if entity_schemas_flag:
        generate_all_entity_schema_files(benchling_service, write_path, overwrite)
    if results_schemas_flag:
        generate_all_results_schema_files(benchling_service, write_path, overwrite)


def autogenerate_revision_file(
    benchling_service: BenchlingService,
    revisions_timeline: RevisionsTimeline,
    description: str,
    current_revision_id: str,
    compare: bool = True,
) -> None:
    """Generates a revision file by comparing locally defined schemas to the given Benchling tenant.
    The revision file contains a unique revision id, the down_revision_id (which is the latest revision id that this revision is based on),
    and a list of operations to be performed to upgrade or downgrade the Benchling tenant.
    It writes this standard revision file to liminal/versions/ for the user to review/edit and then run at a later time.

    Parameters
    ----------
    benchling_service : BenchlingService
        The Benchling service object that is connected to a specified Benchling tenant.
    revisions_timeline : RevisionsTimeline
        The revisions timeline object.
    description : str
        A description of the revision being generated. This will also be included in the file name.
    current_revision_id : str
        The current revision id.
    compare : bool
        Whether to compare the locally defined schemas to the given Benchling tenant.
    """
    if current_revision_id not in revisions_timeline.revisions_map.keys():
        raise Exception(
            f"Your target Benchling tenant is currently at revision_id {current_revision_id}. This does not exist within your revision timeline in any of your revision files. Ensure your current revision_id for your tenant is correct. The current local head revision is {revisions_timeline.get_latest_revision().id}"
        )
    if current_revision_id != revisions_timeline.get_latest_revision().id:
        raise Exception(
            f"Your target Benchling tenant is currently at revision_id {current_revision_id}, which is not up to date with the local head revision ({revisions_timeline.get_latest_revision().id}). Please upgrade your tenant to the latest revision before generating a new revision."
        )
    if compare:
        compare_ops = get_full_migration_operations(benchling_service)
    else:
        compare_ops = []
    write_path = revisions_timeline.write_new_revision(description, compare_ops)
    print(f"[bold green]Revision file generated at {write_path}")


def upgrade_benchling_tenant(
    benchling_service: BenchlingService,
    revisions_timeline: RevisionsTimeline,
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
    revisions_timeline : RevisionsTimeline
        The revisions timeline object.
    current_revision_id : str
        The current revision id.
    upgrade_descriptor : str
        The upgrade descriptor.

    Returns
    -------
    str
        The target revision id.
    """
    if current_revision_id not in revisions_timeline.revisions_map.keys():
        raise Exception(
            f"current remote revision_id ({current_revision_id}) is invalid and not found in any of the revision file names."
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
    revisions_timeline: RevisionsTimeline,
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
    if current_revision_id not in revisions_timeline.revisions_map.keys():
        raise Exception(
            f"current remote revision_id ({current_revision_id}) is invalid and not found in any of the revision file names."
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
