from pathlib import Path
from typing import Literal

from liminal.base.base_operation import BaseOperation
from liminal.base.compare_operation import CompareOperation
from liminal.migrate.revision import Revision


class RevisionsTimeline:
    """A class that represents the timeline of revisions in the given versions directory path.
    The revisions timeline is used to track the order of revisions and to provide a way to navigate between revisions.
    A map of all revisions is maintained to allow for quick lookups by revision id.

    Parameters
    ----------
    versions_dir_path: Path
        The path to the directory containing the revision files.
    revisions_map: dict[str, Revision]
        A map of all revisions, keyed by revision id.
    """

    versions_dir_path: Path
    revisions_map: dict[str, Revision]

    def __init__(self, versions_dir_path: Path):
        self.versions_dir_path = versions_dir_path
        if not versions_dir_path.exists():
            raise Exception(
                f"No {versions_dir_path} directory found in working directory. Make sure a versions/ directory exists."
            )
        all_raw_revisions: list[Revision] = []
        for file_path in versions_dir_path.iterdir():
            all_raw_revisions.append(Revision.parse_from_file(file_path))
        self.revisions_map = self.validate_revisions(all_raw_revisions)

    def get_first_revision(self) -> Revision:
        """Gets the first revision in the timeline.
        There should be only one revision where down_revision_id is None, which is the base revision.
        """
        revisions = [
            r for r in self.revisions_map.values() if r.down_revision_id is None
        ]
        if len(revisions) == 0:
            raise Exception(
                "No first revision found. There should be one revision where down_revision_id == None."
            )
        if len(revisions) > 1:
            raise Exception(
                "Multiple revisions found with down_revision_id == None. There should be only one revision with this condition."
            )
        return revisions[0]

    def get_latest_revision(self) -> Revision:
        """Gets the last revision in the timeline.
        There should be only one revision where up_revision_id is None, which is the latest revision.
        """
        revisions = [r for r in self.revisions_map.values() if r.up_revision_id is None]
        if len(revisions) == 0:
            raise Exception(
                "Latest revision not found. There should be one revision where up_revision_id == None."
            )
        if len(revisions) > 1:
            raise Exception(
                "Multiple revisions found with up_revision_id == None. There should be only one revision with this condition."
            )
        return revisions[0]

    def get_nth_revision(self, revision_id: str, steps: int) -> Revision:
        """Gets the nth revision from the provided revision id in the direction specified by steps.

        Parameters
        ----------
        revision_id : str
            The revision id to start from.
        steps : int
            The number of steps to take from the provided revision id. Positive steps will move towards the latest revision. Negative steps will move towards the base revision.

        Returns
        -------
        Revision
            The nth revision from the provided revision id in the direction specified by steps.
        """
        revision = self.get_revision(revision_id)
        direction = "up_revision_id" if steps >= 0 else "down_revision_id"

        for _ in range(abs(steps)):
            next_id = getattr(revision, direction)
            revision = self.get_revision(next_id)

        return revision

    def get_distance(
        self, revision_id_1: str, revision_id_2: str, direction: Literal["up", "down"]
    ) -> int:
        """Gets the distance between two revisions in the given direction.

        Parameters
        ----------
        revision_id_1 : str
            The revision id to start from.
        revision_id_2 : str
            The revision id to find the distance to.
        direction : Literal["up", "down"]
            The direction to find the distance in.

        Returns
        -------
        int
            The number of steps between the two revisions in the given direction.
        """
        revision = self.get_revision(revision_id_1)
        revision_2 = self.get_revision(revision_id_2)
        count = 0
        while revision.id != revision_2.id:
            try:
                if direction == "up":
                    revision = self.get_revision(revision.up_revision_id)
                else:
                    revision = self.get_revision(revision.down_revision_id)
            except Exception:
                raise Exception(
                    f"{revision_id_2} is not a valid {direction} revision from {revision_id_1}."
                )
            count += 1
        return count

    def get_absolute_distance(self, revision_id_1: str, revision_id_2: str) -> int:
        """Gets the absolute distance between two revisions.
        The absolute distance is the number of steps needed to move from revision_id_1 to revision_id_2.

        Parameters
        ----------
        revision_id_1 : str
            The revision id to start from.
        revision_id_2 : str
            The revision id to find the distance to.

        Returns
        -------
        int
            The number of steps between the two revisions.
        """
        try:
            return self.get_distance(revision_id_1, revision_id_2, "up")
        except Exception:
            return self.get_distance(revision_id_1, revision_id_2, "down")

    def get_revision(self, revision_id: str | None) -> Revision:
        """Gets the revision from the revisions map based on the provided revision id.

        Parameters
        ----------
        revision_id : str | None
            The revision id to get.

        Returns
        -------
        Revision
            The revision with the provided revision id.
        """
        if not revision_id:
            raise Exception("No revision id provided.")
        try:
            return self.revisions_map[revision_id]
        except KeyError:
            raise Exception(f"No revision found with id {revision_id}.")

    def get_revision_index(self, revision_id: str) -> int:
        """Gets the index of the revision in the revisions map timeline.
        The index is the number of steps needed to move from the given revision to the latest revision.
        The index is 0-indexed, so the latest revision has an index of 0.
        """
        revision = self.get_revision(revision_id)
        count = 0
        while revision.up_revision_id is not None:
            try:
                revision = self.get_revision(revision.up_revision_id)
            except Exception:
                break
            count += 1
        return count

    def get_upgrade_operations(
        self, start_revision_id: str, end_revision_id: str
    ) -> dict[str, list[BaseOperation]]:
        """Gets the upgrade operations between two revisions. Key is the revision id and value is the list of operations to apply.
        The upgrade operations are the operations that need to be applied to the database to move from the start revision to the end revision.
        The list of operations DOES NOT include operations from the start revision but DOES include operations from the end revision.
        """
        distance = self.get_distance(start_revision_id, end_revision_id, "up")
        if distance == 0:
            raise Exception(
                f"Distance between {start_revision_id} and {end_revision_id} is 0. No upgrade operations found."
            )
        revision = self.get_revision(start_revision_id)
        operations_map: dict[str, list[BaseOperation]] = {}
        next_revision = self.get_revision(revision.up_revision_id)
        while next_revision.id != end_revision_id:
            operations_map[next_revision.id] = next_revision.upgrade_operations
            next_revision = self.get_revision(next_revision.up_revision_id)
        operations_map[end_revision_id] = next_revision.upgrade_operations
        return operations_map

    def get_downgrade_operations(
        self, start_revision_id: str, end_revision_id: str
    ) -> dict[str, list[BaseOperation]]:
        """Gets the downgrade operations between two revisions. This is the reverse of the operations in the Revision objects.
        The list of operations DOES include operations from the start revision but DOES NOT include operations from the end revision.
        """
        distance = self.get_distance(start_revision_id, end_revision_id, "down")
        if distance == 0:
            raise Exception(
                f"Distance between {start_revision_id} and {end_revision_id} is 0. No downgrade operations found."
            )
        revision = self.get_revision(start_revision_id)
        operations_map: dict[str, list[BaseOperation]] = {}
        while revision.id != end_revision_id:
            operations_map[revision.id] = revision.downgrade_operations
            revision = self.get_revision(revision.down_revision_id)
        return operations_map

    def write_new_revision(
        self, message: str, operations: list[CompareOperation]
    ) -> str | None:
        """Adds a new revision to the revisions map and writes the revision file to the versions directory if write is True.
        The added revision will be the latest revision.
        """
        new_revision = Revision(
            id=str(Revision.new_id()),
            description=message,
            up_revision_id=None,
            down_revision_id=self.get_latest_revision().id,
            upgrade_operations=[o.op for o in operations],
            downgrade_operations=reversed([o.reverse_op for o in operations]),
        )
        if len(operations) == 0:
            return None
        new_revision.write_revision_file(self.versions_dir_path)
        self.revisions_map[new_revision.id] = new_revision
        self.get_revision(
            new_revision.down_revision_id
        ).up_revision_id = new_revision.id
        return str(self.versions_dir_path / new_revision.revision_file_name)

    def init_versions(self, versions_dir_path: Path) -> Path:
        """Initializes the versions directory with a base revision.
        The base revision is the first revision in the timeline and has no down_revision_id and no operations.
        """
        new_revision = Revision(
            id=str(Revision.new_id()),
            description="Initial init revision",
            up_revision_id=None,
            down_revision_id=None,
            upgrade_operations=[],
            downgrade_operations=[],
        )
        self.revisions_map[new_revision.id] = new_revision
        revision_file_path = new_revision.write_revision_file(versions_dir_path)
        return revision_file_path

    @staticmethod
    def validate_revisions(all_raw_revisions: list[Revision]) -> dict[str, Revision]:
        """Validates the revisions to ensure that all revisions are valid and that there are no loops in the revisions.
        It goes through the given list of revisions and ensures that every revision id is unique, that there is a base revision, and that all revisions have valid links.
        It generates a map of all the revisions for quick lookups and adds up_revision_ids for each revision.

        Parameters
        ----------
        all_raw_revisions : list[Revision]
            The list of revisions to validate.

        Returns
        -------
        dict[str, Revision]
            A generated map of all the revisions, keyed by revision id.
        """
        all_revision_ids = [r.id for r in all_raw_revisions]
        revisions_map: dict[str, Revision] = {}
        if len(all_raw_revisions) == 0:
            return revisions_map

        # Check that all revision ids are unique
        duplicate_ids = set(
            [id for id in all_revision_ids if all_revision_ids.count(id) > 1]
        )
        if duplicate_ids:
            raise Exception(
                f"Revision ids are not unique. Please ensure all revision ids are unique. Found duplicate revision ids: {duplicate_ids}"
            )

        base_revisions = [r for r in all_raw_revisions if r.down_revision_id is None]
        if len(base_revisions) == 0:
            raise Exception(
                "No base revision found. There should be one revision where down_revision_id == None."
            )
        if len(base_revisions) > 1:
            raise Exception(
                f"Multiple revisions found with down_revision_id == None. There should be only one revision with this condition. Please investigate the revisions: {base_revisions}"
            )

        # Check that all revisions have valid links
        revision_to_validate = base_revisions[0]
        revisions_map[revision_to_validate.id] = revision_to_validate
        while len(revisions_map) < len(all_raw_revisions):
            up_revisions = [
                r
                for r in all_raw_revisions
                if revision_to_validate.id == r.down_revision_id
            ]
            if len(up_revisions) == 0:
                raise Exception(
                    f"No revisions found that include {revision_to_validate.id} as their down_revision_id. Please ensure all revisions have valid links."
                )
            if len(up_revisions) > 1:
                raise Exception(
                    f"Multiple revisions found that include {revision_to_validate.id} as their down_revision_id. Each revision should be the down_revision for only one other revision. Please investigate the revisions: {[r.id for r in up_revisions]}"
                )
            up_revision = up_revisions[0]
            revision_to_validate.up_revision_id = up_revision.id
            revision_to_validate = up_revision
            if revision_to_validate.id not in revisions_map:
                revisions_map[revision_to_validate.id] = revision_to_validate
            else:
                raise Exception(
                    f"Loop detected in revisions. Detected a cycle in the revisions where {revision_to_validate.id} is the down_revision for more than one revision. Please investigate."
                )
        return revisions_map
