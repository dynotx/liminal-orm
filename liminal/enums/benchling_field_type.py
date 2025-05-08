from liminal.base.str_enum import StrEnum


class BenchlingFieldType(StrEnum):
    """This enum represents the different types a Benchling field can have on an entity schema."""

    AA_SEQUENCE_LINK = "aa_sequence_link"
    BLOB_LINK = "blob_link"
    CUSTOM_ENTITY_LINK = "custom_entity_link"
    DATE = "date"
    DATETIME = "datetime"
    DNA_SEQUENCE_LINK = "dna_sequence_link"
    PART_LINK = "part_link"
    TRANSLATION_LINK = "translation_link"
    DROPDOWN = "dropdown"
    ENTITY_LINK = "entity_link"
    ENTRY_LINK = "entry_link"
    DECIMAL = "float"
    INTEGER = "integer"
    LONG_TEXT = "long_text"
    MIXTURE_LINK = "mixture_link"
    STORAGE_LINK = "storage_link"
    TEXT = "text"
    JSON = "json"
    BOOLEAN = "boolean"

    @classmethod
    def get_non_multi_select_types(cls) -> list[str]:
        return [
            cls.TEXT,
            cls.LONG_TEXT,
            cls.DECIMAL,
            cls.INTEGER,
            cls.DATE,
            cls.DATETIME,
        ]

    @classmethod
    def get_entity_link_types(cls) -> list[str]:
        return [cls.ENTITY_LINK, cls.TRANSLATION_LINK, cls.PART_LINK]

    @classmethod
    def get_number_field_types(cls) -> list[str]:
        return [cls.INTEGER, cls.DECIMAL]
