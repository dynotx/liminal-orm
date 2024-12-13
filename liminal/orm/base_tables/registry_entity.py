from datetime import datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import DATETIME, Boolean, String

from liminal.orm.base import Base
from liminal.orm.relationship import single_relationship


class RegistryEntity(Base):
    __tablename__ = "registry_entity$raw"

    id = Column("id", String, nullable=True, primary_key=True)
    archived = Column("archived$", Boolean, nullable=True)
    archive_purpose = Column("archive_purpose$", String, nullable=True)
    created_at = Column("created_at", DATETIME, nullable=True)
    creator_id = Column("creator_id", String, ForeignKey("user$raw.id"), nullable=True)
    file_registry_id = Column("file_registry_id", String, nullable=True)
    folder_id = Column("folder_id", String, nullable=True)
    modified_at = Column("modified_at", DATETIME, nullable=True)
    name = Column("name", String, nullable=True)
    project_id = Column("project_id", String, nullable=True)
    schema_id = Column("schema_id", String, nullable=True)
    source_id = Column("source_id", String, nullable=True)
    url = Column("url", String, nullable=True)
    validation_status = Column("validation_status", String, nullable=True)

    creator = single_relationship("User", creator_id)

    def __init__(
        self,
        id: str,
        archived: bool,
        archive_purpose: str,
        created_at: datetime,
        file_registry_id: str,
        folder_id: str,
        modified_at: datetime,
        name: str,
        project_id: str,
        schema: str,
        schema_id: str,
        source_id: str,
        url: str,
        validation_status: str,
    ):
        self.id = id
        self.archived = archived
        self.archive_purpose = archive_purpose
        self.created_at = created_at
        self.file_registry_id = file_registry_id
        self.folder_id = folder_id
        self.modified_at = modified_at
        self.name = name
        self.project_id = project_id
        self.schema = schema
        self.schema_id = schema_id
        self.source_id = source_id
        self.url = url
        self.validation_status = validation_status
