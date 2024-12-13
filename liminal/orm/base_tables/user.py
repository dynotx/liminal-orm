from datetime import datetime

from sqlalchemy import DATETIME, Boolean, Column, String

from liminal.orm.base import Base


class User(Base):
    __tablename__ = "user$raw"

    id = Column(String, nullable=False, primary_key=True)
    created_at = Column(DATETIME, nullable=False)
    email = Column(String, nullable=False)
    handle = Column(String, nullable=False)
    is_suspended = Column(Boolean, nullable=False)
    name = Column(String, nullable=False)

    def __init__(
        self,
        id: str,
        created_at: datetime,
        email: str,
        handle: str,
        is_suspended: bool,
        name: str,
    ):
        self.id = id
        self.created_at = created_at
        self.email = email
        self.handle = handle
        self.is_suspended = is_suspended
        self.name = name
