from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# This is necessary for SQLAlchemy, all DBmodels inherit from Base, either directly or indirectly.
# apply a naming convention to the metadata instance (for use in alembic revisions)

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class _BaseMixin:
    # Liminal models annotate columns as `name: SqlColumn = Column(...)`, including generated
    # model files. SQLAlchemy 2.0 rejects non-`Mapped[]` annotations on mapped attributes unless
    # this flag is set; SQLAlchemy 1.4 ignores it. Keeps existing user models working on both.
    __allow_unmapped__ = True


meta = MetaData(naming_convention=convention)
Base = declarative_base(metadata=meta, cls=_BaseMixin)
