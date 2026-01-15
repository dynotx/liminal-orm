from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, PrivateAttr

from liminal.enums import BenchlingFieldType


class BaseFieldProperties(BaseModel):
    """A class that represents the properties of a field on an entity schema in Benchling.
    This is used to define properties in a benchling column and is used to generically define properties of a field.

    Parameters
    ----------
    name : str | None
        The external facing name of the field.
    warehouse_name : str | None
        The sql column name in the benchling warehouse.
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
    warehouse_name: str | None = None
    type: BenchlingFieldType | None = None
    required: bool | None = None
    is_multi: bool | None = None
    parent_link: bool | None = None
    dropdown_link: str | None = None
    entity_link: str | None = None
    tooltip: str | None = None
    decimal_places: int | None = None
    unit_name: str | None = None
    _archived: bool | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._archived = data.get("_archived", None)

    def set_archived(self, value: bool) -> BaseFieldProperties:
        self._archived = value
        return self

    def set_warehouse_name(self, wh_name: str) -> BaseFieldProperties:
        self.warehouse_name = wh_name
        return self

    def unset_tooltip(self) -> BaseFieldProperties:
        if "tooltip" in self.__pydantic_fields_set__:
            self.__pydantic_fields_set__.remove("tooltip")
        return self

    def unset_entity_link(self) -> BaseFieldProperties:
        if "entity_link" in self.__pydantic_fields_set__:
            self.__pydantic_fields_set__.remove("entity_link")
        return self

    def unset_unit_name(self) -> BaseFieldProperties:
        if "unit_name" in self.__pydantic_fields_set__:
            self.__pydantic_fields_set__.remove("unit_name")
        return self

    def validate_column_definition(self, wh_name: str) -> bool:
        """If the Field Properties are meant to represent a column in Benchling,
        this will validate the properties and ensure that the entity_link and dropdowns are valid names that exist in our code.
        """
        return True

    def column_dump(self) -> dict[str, Any]:
        """This function returns a model dump or dictionary of the field properties.
        However, it removes defaults based on the init in the Column class."""
        column_props = self.model_dump(exclude_unset=True, exclude_none=True)
        to_pop = []
        for k, v in column_props.items():
            if k == "is_multi" and v is False:
                to_pop.append(k)
            elif k == "parent_link" and v is False:
                to_pop.append(k)
        for k in to_pop:
            column_props.pop(k)
        return column_props

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
        return f"{self.__class__.__name__}({', '.join([f'{k}={v.__repr__()}' for k, v in self.model_dump(exclude_unset=True).items()])})"
