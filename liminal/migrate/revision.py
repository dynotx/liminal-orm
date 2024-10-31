from __future__ import annotations

import ast
import uuid
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

import liminal.external as b  # noqa: F401
from liminal.base.base_operation import BaseOperation
from liminal.utils import to_snake_case


class Revision(BaseModel):
    """A revision object that represents a single revision file for Liminal.
    Revision files in the versions directory are parsed into these revision objects and new revision files are generated from this class.
    A Revision represents a set of changes or operations to be made against a Benchling tenant.

    Parameters
    ----------
    id : str
        The unique identifier for the revision.
    description : str
        The description of the revision.
    up_revision_id : str | None
        The next sequential revision id of the revision that this revision will link to. This is not surfaced in the revision file, but is used internally to determine order.
    down_revision_id : str | None
        The previous revision id of the revision that this revision links to. This is surfaced in the revision file.
    operations : list[BaseOperation]
        The list of operations that are part of this revision.
    """

    id: str
    description: str
    up_revision_id: str | None = None
    down_revision_id: str | None = None
    upgrade_operations: list[BaseOperation] = []  # noqa: UP006
    downgrade_operations: list[BaseOperation] = []  # noqa: UP006

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def revision_file_name(self) -> str:
        """The generated name of the revision file that this revision object represents."""
        return f"{self.id}_{to_snake_case(self.description)}.py"

    @classmethod
    def new_id(cls) -> str:
        """Generates a new random revision id."""
        return uuid.uuid4().hex[:12]

    @classmethod
    def parse_from_file(cls, file_path: Path) -> Revision:
        """
        Given a revision file path, parses the file and returns a Revision object.
        Because the up_revision_id isn't part of the file, it is not set here but done in the validate function.
        """
        with open(file_path) as file:
            source = file.read()
            tree = ast.parse(source)

        revision_id: str
        nodes = list(ast.walk(tree))
        revision_nodes = [
            node
            for node in nodes
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "revision"
        ]
        if len(revision_nodes) == 0:
            raise Exception(f"No revision variable found in {file_path}")
        if len(revision_nodes) > 1:
            raise Exception(
                f"Multiple revision variables found in {file_path}. There must be only one."
            )
        revision_id = ast.literal_eval(revision_nodes[0].value)

        down_revision_id: str | None
        down_revision_nodes = [
            node
            for node in nodes
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "down_revision"
        ]
        if len(down_revision_nodes) == 0:
            raise Exception(f"No down_revision variable found in {file_path}")
        elif len(down_revision_nodes) > 1:
            raise Exception(
                f"Multiple down_revision variables found in {file_path}. There must be only one."
            )
        down_revision_id = ast.literal_eval(down_revision_nodes[0].value)

        def _get_operations_from_func(
            func_name: Literal["upgrade", "downgrade"],
        ) -> list[BaseOperation]:
            funcs = [
                n
                for n in nodes
                if isinstance(n, ast.FunctionDef) and n.name == func_name
            ]
            if len(funcs) == 0:
                raise Exception(
                    f"No {func_name} function found in {file_path} with function def {func_name}."
                )
            if len(funcs) > 1:
                raise Exception(
                    f"Multiple {func_name} functions found in {file_path}. There must be only one."
                )
            func_source = ast.get_source_segment(source, funcs[0])
            if (
                not isinstance(func_source, str)
                or f"def {func_name}() -> list[b.BaseOperation]:" not in func_source
            ):
                raise Exception(
                    f"Upgrade function was not found as a string in {file_path}"
                )
            local_dict: Mapping = {}
            exec(func_source, globals(), local_dict)
            operations = local_dict[func_name]()
            if operations is None:
                raise Exception(
                    f"No list of operations found for {file_path} in the {func_name} function."
                )
            if not isinstance(operations, list) or not all(
                isinstance(op, BaseOperation) for op in operations
            ):
                raise Exception(
                    f"After executing {func_name} in file {file_path}, the content of the function was not a list of BaseOperation objects."
                )
            return operations

        message: str
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring is None:
                    raise Exception(f"No docstring found for {file_path}")
                message = docstring.split("\n")[0]
        if not message:
            raise Exception(f"No message found for {file_path}")

        return Revision(
            id=revision_id,
            down_revision_id=down_revision_id,
            description=message,
            upgrade_operations=_get_operations_from_func("upgrade"),
            downgrade_operations=_get_operations_from_func("downgrade"),
        )

    def write_revision_file(self, dir_path: Path) -> Path:
        """Generates the contents of a revision file from this revision object.

        Parameters
        ----------
        dir_path : Path
            The path to the directory where the revision file should be written.

        Returns
        -------
        Path
            The path to the revision file that was written.
        """
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        upgrade_operation_strings = [
            o.revision_file_string() for o in self.upgrade_operations
        ]
        downgrade_operation_strings = [
            o.revision_file_string() for o in self.downgrade_operations
        ]
        upgrade_ops_string = ",\n        ".join(upgrade_operation_strings)
        downgrade_ops_string = ",\n        ".join(downgrade_operation_strings)

        revision_file_contents = f"""
'''
{self.description}

Revision ID: {self.id}
Revises: {self.down_revision_id}
Create Date: {created_date}
'''

import liminal.external as b

# revision identifiers, used by Liminal.
revision = "{self.id}"
down_revision = {f'"{self.down_revision_id}"' if self.down_revision_id else None}


# ### commands auto generated by Liminal - please review (and adjust if needed)! ###
def upgrade() -> list[b.BaseOperation]:
    return [{upgrade_ops_string}]

# ### commands auto generated by Liminal - please review (and adjust if needed)! ###
def downgrade() -> list[b.BaseOperation]:
    return [{downgrade_ops_string}]
"""
        with open(dir_path / self.revision_file_name, "w") as file:
            file.write(revision_file_contents)
        return dir_path / self.revision_file_name
