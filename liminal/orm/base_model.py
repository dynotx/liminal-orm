from __future__ import annotations

import inspect
import logging
from types import FunctionType
from typing import TYPE_CHECKING, Any, Generic, Type, TypeVar  # noqa: UP035

import pandas as pd  # type: ignore
from sqlalchemy import DATETIME, Boolean, ForeignKey, String
from sqlalchemy import Column as SqlColumn
from sqlalchemy.orm import Query, RelationshipProperty, Session, relationship
from sqlalchemy.orm.decl_api import declared_attr

from liminal.base.base_dropdown import BaseDropdown
from liminal.base.base_validation_filters import BaseValidatorFilters
from liminal.connection.benchling_service import BenchlingService
from liminal.entity_schemas.utils import get_benchling_entity_schemas
from liminal.enums import BenchlingNamingStrategy
from liminal.enums.benchling_entity_type import BenchlingEntityType
from liminal.enums.sequence_constraint import SequenceConstraint
from liminal.orm.base import Base
from liminal.orm.base_tables.user import User
from liminal.orm.name_template import NameTemplate
from liminal.orm.name_template_parts import FieldPart
from liminal.orm.schema_properties import SchemaProperties
from liminal.utils import is_valid_wh_name
from liminal.validation import BenchlingValidatorReport

if TYPE_CHECKING:
    from liminal.orm.column import Column

T = TypeVar("T", bound="BaseModel")

LOGGER = logging.getLogger(__name__)


class BaseModel(Generic[T], Base):
    """Base class for all Benchling entities. Defines all common columns for entity tables in postgres benchling warehouse."""

    __abstract__ = True
    __schema_properties__: SchemaProperties
    __name_template__: NameTemplate = NameTemplate(
        parts=[], order_name_parts_by_sequence=False
    )

    _existing_schema_warehouse_names: set[str] = set()
    _existing_schema_names: set[str] = set()
    _existing_schema_prefixes: list[str] = []

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        warehouse_name = cls.__schema_properties__.warehouse_name
        cls.__tablename__ = warehouse_name + "$raw"
        if "__schema_properties__" not in cls.__dict__ or not isinstance(
            cls.__schema_properties__, SchemaProperties
        ):
            raise NotImplementedError(
                f"{cls.__name__} must define 'schema_properties' class attribute"
            )
        if warehouse_name in cls._existing_schema_warehouse_names:
            raise ValueError(
                f"Warehouse name '{warehouse_name}' is already used by another subclass."
            )
        if cls.__schema_properties__.name in cls._existing_schema_names:
            raise ValueError(
                f"Schema name '{cls.__schema_properties__.name}' is already used by another subclass."
            )
        model_columns = {
            c[0]: c[1] for c in cls.__dict__.items() if isinstance(c[1], SqlColumn)
        }
        column_wh_names = set(model_columns.keys())
        column_names = [c.properties.name for c in model_columns.values()]
        if len(column_names) != len(set(column_names)):
            raise ValueError("Schema cannot have columns with duplicate Column names.")

        # Validate constraints
        invalid_constraints = [
            c
            for c in cls.__schema_properties__.constraint_fields
            if c
            not in column_wh_names | set(SequenceConstraint._value2member_map_.keys())
        ]
        if invalid_constraints:
            raise ValueError(
                f"Constraints {', '.join(invalid_constraints)} are not fields on schema {cls.__schema_properties__.name}."
            )
        sequence_constraints = [
            SequenceConstraint(c)
            for c in cls.__schema_properties__.constraint_fields
            if SequenceConstraint.is_sequence_constraint(c)
        ]
        if len(sequence_constraints) > 1:
            raise ValueError(
                "Only one sequence constraint field can be set for a schema."
            )
        sequence_constraint = sequence_constraints[0] if sequence_constraints else None
        match sequence_constraint:
            case SequenceConstraint.BASES:
                if not cls.__schema_properties__.entity_type.is_nt_sequence():
                    raise ValueError(
                        "`bases` constraint is only supported for nucleotide sequence entities."
                    )
            case SequenceConstraint.AMINO_ACIDS_IGNORE_CASE:
                if (
                    cls.__schema_properties__.entity_type
                    != BenchlingEntityType.AA_SEQUENCE
                ):
                    raise ValueError(
                        "`amino_acids_ignore_case` constraint is only supported for aa_sequence entities."
                    )
            case SequenceConstraint.AMINO_ACIDS_EXACT_MATCH:
                if (
                    cls.__schema_properties__.entity_type
                    != BenchlingEntityType.AA_SEQUENCE
                ):
                    raise ValueError(
                        "`amino_acids_exact_match` constraint is only supported for aa_sequence entities."
                    )
        # Validate naming strategies
        if any(
            BenchlingNamingStrategy.is_template_based(strategy)
            for strategy in cls.__schema_properties__.naming_strategies
        ):
            if not cls.__name_template__.parts:
                raise ValueError(
                    "Name template must be set when using template-based naming strategies."
                )
        # Validate name template
        if cls.__name_template__:
            if not cls.__schema_properties__.entity_type.is_nt_sequence():
                if cls.__name_template__.order_name_parts_by_sequence is True:
                    raise ValueError(
                        "order_name_parts_by_sequence is only supported for sequence entities. Must be set to False if entity type is not a sequence."
                    )
            if cls.__name_template__.parts:
                field_parts = [
                    p for p in cls.__name_template__.parts if isinstance(p, FieldPart)
                ]
                for field_part in field_parts:
                    if field_part.wh_field_name not in column_wh_names:
                        raise ValueError(
                            f"{cls.__schema_properties__.warehouse_name}: Field name template part {field_part.wh_field_name} is not a column on field warehouse name on schema."
                        )
        cls._existing_schema_warehouse_names.add(warehouse_name)
        cls._existing_schema_names.add(cls.__schema_properties__.name)
        cls._existing_schema_prefixes.append(cls.__schema_properties__.prefix.lower())

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
                f"No model subclass found for the following class names or warehouse names: {', '.join(missing_models)}. Please ensure the entity schema model(s) are imported or defined."
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
    def validate_model_definition(cls) -> bool:
        model_columns = cls.get_columns_dict(exclude_base_columns=True)
        properties = {n: c.properties for n, c in model_columns.items()}
        errors = []
        if (
            cls._existing_schema_prefixes.count(
                cls.__schema_properties__.prefix.lower()
            )
            > 1
        ):
            LOGGER.warning(
                f"{cls.__name__}: schema prefix '{cls.__schema_properties__.prefix}' is already used by another subclass. Please ensure fieldsets=True in BenchlingConnection you are updating/creating this schema."
            )
        for wh_name, field in properties.items():
            try:
                if field.entity_link:
                    if field.entity_link not in [
                        s.__schema_properties__.warehouse_name
                        for s in cls.__base__.get_all_subclasses()
                    ]:
                        breakpoint()
                        raise ValueError(
                            f"Field {wh_name}: could not find entity link {field.entity_link} as a warehouse name for any currently defined schemas."
                        )
                if field.dropdown_link:
                    if field.dropdown_link not in [
                        d.__benchling_name__ for d in BaseDropdown.get_all_subclasses()
                    ]:
                        raise ValueError(
                            f"Field {wh_name}: could not find dropdown link {field.dropdown_link} as a name to any defined dropdowns."
                        )
                if not is_valid_wh_name(wh_name):
                    raise ValueError(
                        f"Field {wh_name}: invalid warehouse name '{wh_name}'. It should only contain alphanumeric characters and underscores."
                    )
            except ValueError as e:
                errors.append(str(e))
        if errors:
            raise ValueError(
                f"Invalid field properties for schema {cls.__tablename__}: {' '.join(errors)}"
            )
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
    def get_id(cls, benchling_service: BenchlingService) -> str:
        """Connects to Benchling and returns the id of the schema using the __schema_properties__.name.

        Parameters
        ----------
        benchling_service : BenchlingService
            The Benchling service to use.

        Returns
        -------
        str
            The id of the schema.
        """
        all_schemas = get_benchling_entity_schemas(benchling_service)

        schemas_found_by_name = [
            s for s in all_schemas if s.name == cls.__schema_properties__.name
        ]
        if len(schemas_found_by_name) == 0:
            raise ValueError(
                f"No schema found with name '{cls.__schema_properties__.name}'."
            )
        else:
            schema = schemas_found_by_name[0]
            return schema.id

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
        DataFrame
            A pandas dataframe of all entities from the database.
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
        """Runs all validators for all entities returned from the query and returns a list of reports.
        This returns a report for each entity, validator pair, regardless of whether the validation passed or failed.

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
            List of reports from running all validators on all entities returned from the query.
        """
        results: list[BenchlingValidatorReport] = []
        table: list[T] = cls.apply_base_filters(
            cls.query(session), base_filters=base_filters
        ).all()
        LOGGER.info(f"Validating {len(table)} entities for {cls.__name__}...")
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
        """Runs all validators for all entities returned from the query and returns reports as a pandas dataframe.

        Parameters
        ----------
        session : Session
            Benchling database session.
        base_filters: BaseValidatorFilters
            Filters to apply to the query.

        Returns
        -------
        pd.Dataframe
            Dataframe of reports from running all validators on all entities returned from the query.
        """
        results = cls.validate(session, base_filters, only_invalid)
        return pd.DataFrame([r.model_dump() for r in results])
