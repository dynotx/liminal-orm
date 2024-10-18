from datetime import date

from pydantic import BaseModel


class BaseValidatorFilters(BaseModel):
    """
    This class is used to pass base filters to benchling warehouse database queries.
    These columns are found on all tables in the benchling warehouse database.
    """

    created_date_start: date | None = None
    created_date_end: date | None = None
    updated_date_start: date | None = None
    updated_date_end: date | None = None
    entity_ids: list[str] | None = None
    creator_full_names: list[str] | None = None
