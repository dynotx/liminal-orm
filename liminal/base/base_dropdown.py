from abc import ABC
from typing import Any


class BaseDropdown(ABC):
    """_summary_

    Parameters
    ----------
    __benchling_name__: str
        The name of the dropdown in Benchling. There can be no duplicate dropdown names in Benchling.
    __allowed_values__: list[str]
        The list of values for the dropdown. Order matters and reflects the order of the dropdown in Benchling. Values must be unique.
    """

    __benchling_name__: str
    __allowed_values__: list[str]

    _existing_benchling_names: set[str] = set()

    def __new__(cls, **kwargs: Any) -> "BaseDropdown":
        if not hasattr(cls, "__allowed_values__"):
            raise ValueError(f"{cls.__name__} must define __allowed_values__")
        if not hasattr(cls, "__benchling_name__") or not cls.__benchling_name__:
            raise ValueError(f"{cls.__name__} must define __benchling_name__")
        if len(cls.__allowed_values__) != len(set(cls.__allowed_values__)):
            raise ValueError(
                f"{cls.__name__} must have unique values in __allowed_values__"
            )

        if cls.__benchling_name__ in cls._existing_benchling_names:
            raise ValueError(
                f"{cls.__benchling_name__} is already used as a benchling name."
            )
        cls._existing_benchling_names.add(cls.__benchling_name__)
        return super().__new__(cls, **kwargs)

    @classmethod
    def validate(cls, *values: str | None) -> None:
        err_values = []
        for value in values:
            if value and value not in cls.__allowed_values__:
                err_values.append(value)
        if len(err_values) > 0:
            raise ValueError(
                f"{', '.join(err_values)} are not valid {cls.__benchling_name__} dropdown values."
            )

    @classmethod
    def get_all_subclasses(
        cls, names: set[str] | None = None
    ) -> list[type["BaseDropdown"]]:
        if names is None:
            return cls.__subclasses__()
        dropdowns = {
            name: subclass
            for subclass in cls.__subclasses__()
            for name in names
            if name in (subclass.__name__, subclass.__benchling_name__)
        }
        if len(dropdowns.keys()) != len(set(names)):
            missing_dropdowns = set(names) - set(dropdowns.keys())
            raise ValueError(
                f"No dropdown subclass found for the following class names or warehouse names: {', '.join(missing_dropdowns)}"
            )
        return list(dropdowns.values())
