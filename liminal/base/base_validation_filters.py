from datetime import date

from pydantic import BaseModel


class BaseValidatorFilters(BaseModel):
    """
    This class is used to pass base filters to benchling warehouse database queries.
    These columns are found on all tables in the benchling warehouse database.

    Parameters
    ----------
    created_date_start: date | None
        Start date for created date filter.
    created_date_end: date | None
        End date for created date filter.
    updated_date_start: date | None
        Start date for updated date filter.
    updated_date_end: date | None
        End date for updated date filter.
    entity_ids: list[str] | None
        List of entity IDs to filter by.
    creator_full_names: list[str] | None
        List of creator full names to filter by.
    """

    created_date_start: date | None = None
    created_date_end: date | None = None
    updated_date_start: date | None = None
    updated_date_end: date | None = None
    entity_ids: list[str] | None = None
    creator_full_names: list[str] | None = None
