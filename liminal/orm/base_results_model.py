from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar  # noqa: UP035

from sqlalchemy import DATETIME, Boolean, ForeignKey, String
from sqlalchemy import Column as SqlColumn
from sqlalchemy.orm import RelationshipProperty, relationship
from sqlalchemy.orm.decl_api import declared_attr

from liminal.orm.base import Base
from liminal.orm.results_schema_properties import ResultsSchemaProperties

# if TYPE_CHECKING:
#     from liminal.orm.column import Column

T = TypeVar("T")

logger = logging.getLogger(__name__)


class BaseResultsModel(Generic[T], Base):
    __abstract__ = True
    __schema_properties__: ResultsSchemaProperties

    @declared_attr
    def creator_id(cls) -> SqlColumn:
        return SqlColumn(
            "creator_id$", String, ForeignKey("user$raw.id"), nullable=True
        )

    @declared_attr
    def creator(cls) -> RelationshipProperty:
        return relationship("User", foreign_keys=[cls.creator_id])

    id = SqlColumn("id", String, nullable=True, primary_key=True)
    archived = SqlColumn("archived$", Boolean, nullable=True)
    archive_purpose = SqlColumn("archive_purpose$", String, nullable=True)
    created_at = SqlColumn("created_at$", DATETIME, nullable=True)
    entry_id = SqlColumn("entry_id$", String, nullable=True)
    modified_at = SqlColumn("modified_at$", DATETIME, nullable=True)
    run_id = SqlColumn("run_id$", String, nullable=True)
    v3_id = SqlColumn("v3_id$", String, nullable=True)

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        warehouse_name = cls.__schema_properties__.warehouse_name
        cls.__tablename__ = warehouse_name + "$raw"
