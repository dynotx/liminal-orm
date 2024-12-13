from sqlalchemy import Column
from sqlalchemy.types import Boolean, String

from liminal.orm.base import Base


class Schema(Base):
    __tablename__ = "schema$raw"

    id = Column("id", String, nullable=True, primary_key=True)
    schema_type = Column("schema_type", String, nullable=True)
    name = Column("name", String, nullable=True)
    system_name = Column("system_name", String, nullable=True)
    archived = Column("archived$", Boolean, nullable=True)
    archive_purpose = Column("archive_purpose$", String, nullable=True)

    def __init__(
        self,
        id: str,
        schema_type: str,
        name: str,
        system_name: str,
        archived: bool,
        archive_purpose: str,
    ):
        self.id = id
        self.schema_type = schema_type
        self.name = name
        self.system_name = system_name
        self.archived = archived
        self.archive_purpose = archive_purpose
