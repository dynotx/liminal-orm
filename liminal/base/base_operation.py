from abc import ABC, abstractmethod
from typing import Any, ClassVar

from liminal.connection.benchling_service import BenchlingService

"""
Order of operations based on order class var:
    1. CreateDropdown
    2. UpdateDropdownName
    3. UnarchiveDropdown
    4. CreateDropdownOption
    5. UpdateDropdownOption
    6. ArchiveDropdownOption
    7. ReorderDropdownOptions
    8. CreateSchema
    9. UpdateSchema
    10. UnarchiveSchema
    11. CreateField
    12. UnarchiveField
    13. UpdateField
    14. ArchiveField
    15. ReorderFields
    16. ArchiveSchema
    17. ArchiveDropdown
"""


class BaseOperation(ABC):
    """A class that represents a callable operation to be run during a Benchling schema migration."""

    order: ClassVar[int] = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def validate(self, benchling_service: BenchlingService) -> None:
        """Validate the operation before running it. This is not called at runtime,
        but is used to validate operations before a migration is run."""
        pass

    @abstractmethod
    def execute(self, benchling_service: BenchlingService) -> dict[str, Any]:
        """Execute the operation using the given Benchling SDK instance.

        Parameters
        ----------
        benchling_service : BenchlingService
            The BenchlingService to connect to the given Benchling tenant with.


        Returns
        -------
        dict[str, Any]
            The contents of the response from the operation.
        """
        raise NotImplementedError

    @abstractmethod
    def describe_operation(self) -> str:
        """Returns a description of what the CallableOperation will do."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        """Returns a description of what the state of the comparison is."""
        raise NotImplementedError

    def __repr__(self) -> str:
        """Generates a string representation of the class so that it can be executed."""
        args = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            if isinstance(v, str):
                args.append(f"'{v}'")
            else:
                args.append(f"{v.__repr__()}")
        return f"{self.__class__.__name__}({', '.join(args)})"

    def revision_file_string(self) -> str:
        """Generates an exact string representation of the operation that can be evaluated.
        Imports in external module as b so that it can be evaluated in the revision file."""
        import liminal.external as b

        liminal_imports = [c for c in dir(b) if not c.startswith("_")]
        op_str = repr(self)
        for i in liminal_imports:
            if f"{i}(" in op_str:
                op_str = op_str.replace(f"{i}(", f"b.{i}(")
            if f"{i}." in op_str:
                op_str = op_str.replace(f"{i}.", f"b.{i}.")
        return op_str

    def __lt__(self, other: "BaseOperation") -> bool:
        return self.order < other.order
