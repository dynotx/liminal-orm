from liminal.base.str_enum import StrEnum


class BenchlingAPIFieldType(StrEnum):
    """This enum represents the different types a Benchling field can have on an entity schema.
    These are ONLY USED FOR THE INTERNAL BENCHLING API."""

    BLOB_LINK = "ft_blob_link"
    DATE = "ft_date"
    DATETIME = "ft_datetime"
    ENTRY_LINK = "ft_entry_link"
    FILE_LINK = "ft_file_link"
    PART_LINK = "ft_part_link"
    TRANSLATION_LINK = "ft_translation_link"
    FLOAT = "ft_float"
    INTEGER = "ft_integer"
    LONG_TEXT = "ft_long_text"
    SELECTOR = "ft_selector"
    STORABLE_LINK = "ft_storable_link"
    STRING = "ft_string"
