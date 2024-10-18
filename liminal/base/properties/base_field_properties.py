from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, PrivateAttr

from liminal.base.base_dropdown import BaseDropdown
from liminal.enums import BenchlingFieldType
from liminal.orm.base_model import BaseModel as BenchlingBaseModel
from liminal.utils import is_valid_wh_name


class BaseFieldProperties(BaseModel):
    """A class that represents the properties of a field on an entity schema in Benchling.
    This is used to define properties in a benchling column and is used to generically define properties of a field.

    Parameters
    ----------
    name : str | None
        The external facing name of the field.
    type : BenchlingFieldType | None
        The type of the field.
    required : bool | None
        Whether the field is required.
    is_multi : bool | None
        Whether the field is a multi-value field.
    parent_link : bool | None
        Whether the entity link field is a parent of the entity schema.
    dropdown : Type[BaseDropdown] | str | None
        The dropdown for the field or the __benchling_name__ of the dropdown.
        If a string gets passed in, it gets converted to the dropdown class.
    entity_link : str | None
        The warehouse name of the entity schema that the field links to.
        If a string gets passed in, it gets converted to the entity schema class.
    tooltip : str | None
        The tooltip text for the field.
    _archived : bool | None
        Whether the field is archived in Benchling.
    """

    name: str | None = None
    type: BenchlingFieldType | None = None
    required: bool | None = None
    is_multi: bool | None = None
    parent_link: bool | None = None
    dropdown_link: str | None = None
    entity_link: str | None = None
    tooltip: str | None = None
    _archived: bool | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def set_archived(self, value: bool) -> BaseFieldProperties:
        self._archived = value
        return self

    def validate_column(self, wh_name: str) -> bool:
        """If the Field Properties are meant to represent a column in Benchling,
        this will validate the properties and ensure that the entity_link and dropdowns are valid names that exist in our code.
        """
        if self.entity_link:
            if self.entity_link not in [
                s.__schema_properties__.warehouse_name
                for s in BenchlingBaseModel.get_all_subclasses()
            ]:
                raise ValueError(
                    f"Could not find {self.entity_link} as a warehouse name for any currently defined schemas."
                )
        if self.dropdown_link:
            if self.dropdown_link not in [
                d.__benchling_name__ for d in BaseDropdown.get_all_subclasses()
            ]:
                raise ValueError(
                    f"Could not find {self.dropdown_link} as a name to any defined dropdowns."
                )
        if not is_valid_wh_name(wh_name):
            raise ValueError(
                f"Invalid warehouse name '{wh_name}'. It should only contain alphanumeric characters and underscores."
            )
        return True

    def merge(self, new_props: BaseFieldProperties) -> dict[str, Any]:
        """Returns a diff of the two given Benchling FieldProperties as a dictionary.
        If the field is different, set it as the new field.

        Parameters
        ----------
        new_props : Benchling FieldProperties
            The new properties of the field

        Returns
        -------
        dict[str, Any]
            The diff of the two given Benchling FieldProperties.
        """
        diff = {}
        for new_field_name, new_val in new_props.model_dump().items():
            if getattr(self, new_field_name) != new_val:
                diff[new_field_name] = new_val
        return diff

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseFieldProperties):
            return NotImplemented
        return self.model_dump() == other.model_dump()

    def __str__(self) -> str:
        return ", ".join(
            [f"{k}={v}" for k, v in self.model_dump(exclude_unset=True).items()]
        )

    def __repr__(self) -> str:
        """Generates a string representation of the class so that it can be executed."""
        return f"{self.__class__.__name__}({', '.join([f'{k}={v.__repr__()}' for k, v in self.model_dump(exclude_defaults=True).items()])})"
