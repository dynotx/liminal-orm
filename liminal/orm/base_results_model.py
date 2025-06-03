from __future__ import annotations

import inspect
import logging
from types import FunctionType
from typing import Any, Generic, TypeVar  # noqa: UP035

import pandas as pd  # type: ignore
from sqlalchemy import DATETIME, Boolean, ForeignKey, String
from sqlalchemy import Column as SqlColumn
from sqlalchemy.orm import Query, RelationshipProperty, Session, relationship
from sqlalchemy.orm.decl_api import declared_attr

from liminal.base.base_validation_filters import BaseValidatorFilters
from liminal.connection.benchling_service import BenchlingService
from liminal.orm.base import Base
from liminal.orm.base_tables.user import User
from liminal.orm.results_schema_properties import ResultsSchemaProperties
from liminal.results_schemas.utils import get_benchling_results_schemas
from liminal.validation import BenchlingValidatorReport

T = TypeVar("T")

logger = logging.getLogger(__name__)


class BaseResultsModel(Generic[T], Base):
    """Base class for all results models. Defines all common columns for results tables in Postgres Benchling warehouse."""

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
            query = query.filter(cls.v3_id.in_(base_filters.entity_ids))
        if base_filters.creator_full_names:
            query = query.filter(User.name.in_(base_filters.creator_full_names))
        return query

    @classmethod
    def get_id(cls, benchling_service: BenchlingService) -> str:
        """Connects to Benchling and returns the id of the results schema using the __schema_properties__.name.

        Parameters
        ----------
        benchling_service : BenchlingService
            The Benchling service to use.

        Returns
        -------
        str
            The id of the results schema.
        """
        all_schemas = get_benchling_results_schemas(benchling_service)

        schemas_found_by_name = [
            s for s in all_schemas if s.name == cls.__schema_properties__.name
        ]
        if len(schemas_found_by_name) == 0:
            raise ValueError(
                f"No results schema found with name '{cls.__schema_properties__.name}'."
            )
        else:
            schema = schemas_found_by_name[0]
            return schema.id

    @classmethod
    def all(cls, session: Session) -> list[T]:
        """Uses the get_query method to retrieve all results schema rows from the database.

        Parameters
        ----------
        session : Session
            Benchling database session.

        Returns
        -------
        list[T]
            List of all results schema rows from the database.
        """
        return cls.query(session).all()

    @classmethod
    def df(cls, session: Session) -> pd.DataFrame:
        """Uses the get_query method to retrieve all results schema rows from the database.

        Parameters
        ----------
        session : Session
            Benchling database session.

        Returns
        -------
        pd.DataFrame
            A pandas dataframe of all results schema rows from the database.
        """
        query = cls.query(session)
        return pd.read_sql(query.statement, session.connection())

    @classmethod
    def query(cls, session: Session) -> Query:
        """Abstract method that users can override to define a specific query
        to retrieve results schema rows from the database and cover any distinct relationships.

        Parameters
        ----------
        session : Session
            Benchling database session.

        Returns
        -------
        Query
            sqlalchemy query to retrieve results schema rows from the database.
        """
        return session.query(cls)

    @classmethod
    def get_validators(cls) -> list[FunctionType]:
        """Returns a list of all validators defined on the class. Validators are functions that are decorated with @validator."""
        validators = []
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if hasattr(method, "_is_liminal_validator"):
                validators.append(method)
        return validators

    @classmethod
    def validate(
        cls,
        session: Session,
        base_filters: BaseValidatorFilters | None = None,
        only_invalid: bool = False,
    ) -> list[BenchlingValidatorReport]:
        """Runs all validators for all results schema rows returned from the query and returns a list of reports.
        This returns a report for each results schema row, validator pair, regardless of whether the validation passed or failed.

        Parameters
        ----------
        session : Session
            Benchling database session.
        base_filters: BaseValidatorFilters
            Filters to apply to the query.
        only_invalid: bool
            If True, only returns reports for entities that failed validation.

        Returns
        -------
        list[BenchlingValidatorReport]
            List of reports from running all validators on all results schema rows returned from the query.
        """
        results: list[BenchlingValidatorReport] = []
        table: list[T] = cls.apply_base_filters(
            cls.query(session), base_filters=base_filters
        ).all()
        logger.info(
            f"Validating {len(table)} results schema rows for {cls.__name__}..."
        )
        validator_functions = cls.get_validators()
        for entity in table:
            for validator_func in validator_functions:
                report: BenchlingValidatorReport = validator_func(entity)
                if only_invalid and report.valid:
                    continue
                results.append(report)
        return results

    @classmethod
    def validate_to_df(
        cls,
        session: Session,
        base_filters: BaseValidatorFilters | None = None,
        only_invalid: bool = False,
    ) -> pd.DataFrame:
        """Runs all validators for all results schema rows returned from the query and returns reports as a pandas dataframe.

        Parameters
        ----------
        session : Session
            Benchling database session.
        base_filters: BaseValidatorFilters
            Filters to apply to the query.

        Returns
        -------
        pd.Dataframe
            Dataframe of reports from running all validators on all results schema rows returned from the query.
        """
        results = cls.validate(session, base_filters, only_invalid)
        return pd.DataFrame([r.model_dump() for r in results])
