from typing import Any, Type  # noqa: UP035

from sqlalchemy import ARRAY, ForeignKey
from sqlalchemy import Column as SqlColumn

from liminal.base.base_dropdown import BaseDropdown
from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.enums import BenchlingFieldType
from liminal.mappers import convert_benchling_type_to_sql_alchemy_type


class Column(SqlColumn):
    """A wrapper class around sqlalchemy.Column that includes benchling properties to be used in benchling schema generation.
    It converts the given benchling type to a sqlalchemy type and instantiates a sqlalchemy Column.

    Parameters
    ----------
    name : str
        The external facing name of the field.
    type : BenchlingFieldType
        The type of the field.
    required : bool
        Whether the field is required.
    is_multi : bool = False
        Whether the field is a multi-value field.
    parent_link : bool = False
        Whether the entity link field is a parent of the entity schema.
    dropdown : Type[BaseDropdown] | None = None
        The dropdown for the field.
    entity_link : str | None = None
        The warehouse name of the entity the field links to.
    tooltip : str | None = None
        The tooltip text for the field.
    """

    def __init__(
        self,
        name: str,
        type: BenchlingFieldType,
        required: bool,
        is_multi: bool = False,
        parent_link: bool = False,
        tooltip: str | None = None,
        dropdown: Type[BaseDropdown] | None = None,  # noqa: UP006
        entity_link: str | None = None,
        **kwargs: Any,
    ):
        """Initializes a Benchling Column object. Validates the type BenchlingFieldType maps to a valid sqlalchemy type.
        Raises an error if the type is a dropdown and a dropdown is not passed in."""
        properties = BaseFieldProperties(
            name=name,
            type=type,
            required=required,
            is_multi=is_multi,
            parent_link=parent_link,
            dropdown_link=dropdown.__benchling_name__ if dropdown else None,
            entity_link=entity_link,
            tooltip=tooltip,
        )
        self.properties = properties

        nested_sql_type = convert_benchling_type_to_sql_alchemy_type(type)
        sqlalchemy_type = ARRAY(nested_sql_type) if is_multi else nested_sql_type
        if dropdown and type != BenchlingFieldType.DROPDOWN:
            raise ValueError("Dropdown can only be set if the field type is DROPDOWN.")
        if dropdown is None and type == BenchlingFieldType.DROPDOWN:
            raise ValueError("Dropdown must be set if the field type is DROPDOWN.")
        if entity_link and type != BenchlingFieldType.ENTITY_LINK:
            raise ValueError(
                "Entity link can only be set if the field type is ENTITY_LINK."
            )
        if parent_link and type != BenchlingFieldType.ENTITY_LINK:
            raise ValueError(
                "Parent link can only be set if the field type is ENTITY_LINK."
            )
        if type in BenchlingFieldType.get_non_multi_select_types() and is_multi is True:
            raise ValueError(f"Field type {type} cannot have multi-value set as True.")
        self.sqlalchemy_type = sqlalchemy_type
        foreign_key = None
        if type == BenchlingFieldType.ENTITY_LINK and entity_link:
            foreign_key = ForeignKey(f"{entity_link}$raw.id")
        super().__init__(
            self.sqlalchemy_type,
            foreign_key,
            nullable=not required,
            info={"benchling_properties": properties},
            **kwargs,
        )

    @classmethod
    def from_sql_alchemy_column(cls, column: SqlColumn) -> "Column":
        """Given a sqlalchemy Column generated from a Benchling Column, create a Benchling Column using the benchling_properties stored in the Column.info dictionary.

        Parameters
        ----------
        column : Column
            A sqlalchemy Column generated from a Benchling Column.

        Returns
        -------
        A Benchling Column
        """
        if (
            properties := column.info.get("benchling_properties", None)
        ) is None or not isinstance(properties, BaseFieldProperties):
            raise ValueError(
                f"Could not set benchling properties for column {column.name}. Please check that the column has a valid benchling properties set."
            )
        return Column(**properties.model_dump())

    def _constructor(self, *args: Any, **kwargs: Any) -> SqlColumn:
        """Returns a new instance of the SqlAlchemy Column class."""
        return SqlColumn(*args, **kwargs)
