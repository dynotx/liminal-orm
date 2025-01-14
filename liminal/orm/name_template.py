from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, field_validator

from liminal.base.name_template_parts import NameTemplateParts, SeparatorPart
from liminal.base.properties.base_name_template import BaseNameTemplate


class NameTemplate(BaseNameTemplate):
    """
    This class is the validated class that is public facing and inherits from the BaseNameTemplate class.
    It has the same fields as the BaseNameTemplate class, but it is validated to ensure that the fields are valid.
    """

    parts: list[NameTemplateParts] = []
    order_name_parts_by_sequence: bool = False

    @field_validator("parts")
    def validate_parts(cls, v: list[NameTemplateParts]) -> list[NameTemplateParts]:
        if len(v) > 1 and all(isinstance(part, SeparatorPart) for part in v):
            raise ValueError(
                "This name template will produce an empty name because it only includes separators. Please include at least one non-separator component."
            )
        return v

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

    model_config = ConfigDict(arbitrary_types_allowed=True)
