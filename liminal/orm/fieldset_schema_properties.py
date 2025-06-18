from __future__ import annotations

from liminal.base.properties.base_schema_properties import (
    BaseSchemaProperties,
)
from liminal.enums import BenchlingEntityType, BenchlingNamingStrategy


class FieldsetSchemaProperties(BaseSchemaProperties):
    name: str
    system_name: str
    prefix: str | None = None
    entity_type: BenchlingEntityType | None = None
    naming_strategies: set[BenchlingNamingStrategy]
