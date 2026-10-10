from __future__ import annotations

from pydantic import BaseModel


class ResultsSchemaProperties(BaseModel):
    """
    This class is the validated class that is public facing, and represents the properties of a results schema properties.

    Parameters
    ----------
    name : str
        The name of the schema.
    warehouse_name : str
       The sql table name of the schema in the benchling warehouse.
    """

    name: str
    warehouse_name: str

    def __repr__(self) -> str:
        """Generates a string representation of the class so that it can be executed."""
        return f"{self.__class__.__name__}({', '.join([f'{k}={v.__repr__()}' for k, v in self.model_dump().items()])})"
