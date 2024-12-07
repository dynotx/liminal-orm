from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Type, TypeVar  # noqa: UP035

import pandas as pd  # type: ignore
from sqlalchemy import DATETIME, Boolean, ForeignKey, String
from sqlalchemy import Column as SqlColumn
from sqlalchemy.orm import Query, RelationshipProperty, Session, relationship
from sqlalchemy.orm.decl_api import declared_attr

from liminal.base.base_validation_filters import BaseValidatorFilters
from liminal.orm.base import Base
from liminal.orm.schema_properties import SchemaProperties
from liminal.orm.user import User
from liminal.validation import (
    BenchlingValidator,
    BenchlingValidatorReport,
)

if TYPE_CHECKING:
    from liminal.orm.column import Column

T = TypeVar("T", bound="BaseModel")

logger = logging.getLogger(__name__)


class BaseModel(Generic[T], Base):
    """Base class for all Benchling entities. Defines all common columns for entity tables in postgres benchling warehouse."""

    __abstract__ = True
    __schema_properties__: SchemaProperties

    _existing_schema_warehouse_names: set[str] = set()
    _existing_schema_names: set[str] = set()
    _existing_schema_prefixes: set[str] = set()

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        if "__schema_properties__" not in cls.__dict__ or not isinstance(
            cls.__schema_properties__, SchemaProperties
        ):
            raise NotImplementedError(
                f"{cls.__name__} must define 'schema_properties' class attribute"
            )
        warehouse_name = cls.__schema_properties__.warehouse_name
        if warehouse_name in cls._existing_schema_warehouse_names:
            raise ValueError(
                f"Warehouse name '{warehouse_name}' is already used by another subclass."
            )
        if cls.__schema_properties__.name in cls._existing_schema_names:
            raise ValueError(
                f"Schema name '{cls.__schema_properties__.name}' is already used by another subclass."
            )
        if cls.__schema_properties__.prefix.lower() in cls._existing_schema_prefixes:
            raise ValueError(
                f"Schema prefix '{cls.__schema_properties__.prefix}' is already used by another subclass."
            )

        cls._existing_schema_warehouse_names.add(warehouse_name)
        cls._existing_schema_names.add(cls.__schema_properties__.name)
        cls._existing_schema_prefixes.add(cls.__schema_properties__.prefix.lower())
        cls.__tablename__ = warehouse_name + "$raw"

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
    folder_id = SqlColumn("folder_id$", String, nullable=True)
    modified_at = SqlColumn("modified_at$", DATETIME, nullable=True)
    name = SqlColumn("name$", String, nullable=True)
    schema = SqlColumn("schema", String, nullable=True)
    schema_id = SqlColumn("schema_id$", String, nullable=True)
    source_id = SqlColumn("source_id", String, nullable=True)
    url = SqlColumn("url$", String, nullable=True)

    @classmethod
    def get_all_subclasses(cls, names: set[str] | None = None) -> list[Type[BaseModel]]:  # noqa: UP006
        """Returns all subclasses of this class."""
        all_subclasses: list[Type[BaseModel]] = cls.__subclasses__()  # noqa: UP006
        if names is None:
            return all_subclasses
        models = {
            name: subclass
            for subclass in all_subclasses
            for name in names
            if name
            in (subclass.__name__, subclass.__schema_properties__.warehouse_name)
        }
        if len(models.keys()) != len(set(names)):
            missing_models = set(names) - set(models.keys())
            raise ValueError(
                f"No model subclass found for the following class names or warehouse names: {', '.join(missing_models)}"
            )
        return list(models.values())

    @classmethod
    def get_columns_dict(
        cls, exclude_base_columns: bool = False, exclude_archived: bool = True
    ) -> dict[str, Column]:
        """Returns a dictionary of all benchling columns in the class. Benchling Column saves an instance of itself to the sqlalchemy Column info property.
        This function retrieves the info property and returns a dictionary of the columns.
        """
        fields_to_exclude = []
        if exclude_base_columns:
            for base_model in cls.__bases__:
                fields_to_exclude.extend(
                    [
                        c.name
                        for c in base_model.__dict__.values()
                        if isinstance(c, SqlColumn)
                    ]
                )
            fields_to_exclude.append("creator_id$")
        columns = [c for c in cls.__table__.columns if c.name not in fields_to_exclude]
        if exclude_archived:
            columns = [c for c in columns if not c.properties._archived]
        return {c.name: c for c in columns}

    @classmethod
    def validate_model(cls) -> bool:
        model_columns = cls.get_columns_dict(exclude_base_columns=True)
        properties = {n: c.properties for n, c in model_columns.items()}
        errors = []
        for wh_name, field in properties.items():
            try:
                field.validate_column(wh_name)
            except ValueError as e:
                errors.append(str(e))
        if errors:
            raise ValueError(f"Invalid field properties: {' '.join(errors)}")
        return True

    @classmethod
    def apply_base_filters(
        cls,
        query: Query,
        filter_archived: bool = True,
        filter_unregistered: bool = True,
        base_filters: BaseValidatorFilters | None = None,
    ) -> Query:
        """Applies the base model filters to the given query."""
        if filter_archived:
            query = query.filter(cls.archived.is_(False))
        if filter_unregistered:
            if hasattr(cls, "is_registered"):
                query = query.filter(cls.is_registered.is_(True))

        if base_filters is None:
            return query
        if base_filters.created_date_start:
            query = query.filter(cls.created_at >= base_filters.created_date_start)
        if base_filters.created_date_end:
            query = query.filter(cls.created_at <= base_filters.created_date_end)
        if base_filters.updated_date_start:
            query = query.filter(cls.modified_at >= base_filters.updated_date_start)
        if base_filters.updated_date_end:
            query = query.filter(cls.modified_at <= base_filters.updated_date_end)
        if base_filters.entity_ids:
            query = query.filter(cls.id.in_(base_filters.entity_ids))
        if base_filters.creator_full_names:
            query = query.filter(User.name.in_(base_filters.creator_full_names))
        return query

    @classmethod
    def all(cls, session: Session) -> list[T]:
        """Uses the get_query method to retrieve all entities from the database.

        Parameters
        ----------
        session : Session
            Benchling database session.

        Returns
        -------
        list[T]
            List of all entities from the database.
        """
        return cls.query(session).all()

    @classmethod
    def df(cls, session: Session) -> pd.DataFrame:
        """Uses the get_query method to retrieve all entities from the database.

        Parameters
        ----------
        session : Session
            Benchling database session.

        Returns
        -------
        list[T]
            List of all entities from the database.
        """
        query = cls.query(session)
        return pd.read_sql(query.statement, session.connection())

    @classmethod
    def query(cls, session: Session) -> Query:
        """Abstract method that users can override to define a specific query
        to retrieve entities from the database and cover any distinct relationships.

        Parameters
        ----------
        session : Session
            Benchling database session.

        Returns
        -------
        Query
            sqlalchemy query to retrieve entities from the database.
        """
        return session.query(cls)

    @abstractmethod
    def get_validators(self) -> list[BenchlingValidator]:
        """Abstract method that all subclasses must implement. Each subclass will have a differently defined list of
        validators to validate the entity. These validators will be run on each entity returned from the query.
        """
        raise NotImplementedError

    @classmethod
    def validate(
        cls, session: Session, base_filters: BaseValidatorFilters | None = None
    ) -> list[BenchlingValidatorReport]:
        """Runs all validators for all entities returned from the query and returns a list of reports.

        Parameters
        ----------
        session : Session
            Benchling database session.
        base_filters: BenchlingBaseValidatorFilters
            Filters to apply to the query.

        Returns
        -------
        list[BenchlingValidatorReport]
            List of reports from running all validators on all entities returned from the query.
        """
        results: list[BenchlingValidatorReport] = []
        table: list[T] = cls.apply_base_filters(
            cls.query(session), base_filters=base_filters
        ).all()
        logger.info(f"Validating {len(table)} entities for {cls.__name__}...")
        for entity in table:
            for validator in entity.get_validators():
                report: BenchlingValidatorReport = validator.validate(entity)
                results.append(report)
        return results

    @classmethod
    def validate_to_df(
        cls, session: Session, base_filters: BaseValidatorFilters | None = None
    ) -> pd.DataFrame:
        """Runs all validators for all entities returned from the query and returns reports as a pandas dataframe.

        Parameters
        ----------
        session : Session
            Benchling database session.
        base_filters: BenchlingBaseValidatorFilters
            Filters to apply to the query.

        Returns
        -------
        pd.Dataframe
            Dataframe of reports from running all validators on all entities returned from the query.
        """
        results = cls.validate(session, base_filters)
        return pd.DataFrame([r.model_dump() for r in results])
