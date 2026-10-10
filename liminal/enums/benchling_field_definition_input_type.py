from __future__ import annotations

from liminal.base.str_enum import StrEnum


class BenchlingFieldDefinitionInputType(StrEnum):
    """This enum represents the `type` of a field definition when creating or setting field definitions through the v3 API."""

    TEXT = "TEXT"
    LONG_TEXT = "LONG_TEXT"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATE_TIME = "DATE_TIME"
    DROPDOWN = "DROPDOWN"
    BLOB_LINK = "BLOB_LINK"
    ATTACHMENT_LINK = "ATTACHMENT_LINK"
    ENTRY_LINK = "ENTRY_LINK"
    STORAGE_LINK = "STORAGE_LINK"
    ENTITY_LINK = "ENTITY_LINK"
    AA_SEQUENCE_LINK = "AA_SEQUENCE_LINK"
    CUSTOM_ENTITY_LINK = "CUSTOM_ENTITY_LINK"
    DNA_OLIGO_LINK = "DNA_OLIGO_LINK"
    DNA_SEQUENCE_LINK = "DNA_SEQUENCE_LINK"
    MIXTURE_LINK = "MIXTURE_LINK"
    MOLECULE_LINK = "MOLECULE_LINK"
    RNA_OLIGO_LINK = "RNA_OLIGO_LINK"
    RNA_SEQUENCE_LINK = "RNA_SEQUENCE_LINK"
    DNA_PART_LINK = "DNA_PART_LINK"
    RNA_PART_LINK = "RNA_PART_LINK"
    TRANSCRIPTION_LINK = "TRANSCRIPTION_LINK"
    TRANSLATION_LINK = "TRANSLATION_LINK"

    def is_schema_link(self) -> bool:
        """Whether the field links to a specific schema, and so supports `isParent`."""
        return self in {
            self.AA_SEQUENCE_LINK,
            self.CUSTOM_ENTITY_LINK,
            self.DNA_OLIGO_LINK,
            self.DNA_SEQUENCE_LINK,
            self.MIXTURE_LINK,
            self.MOLECULE_LINK,
            self.RNA_OLIGO_LINK,
            self.RNA_SEQUENCE_LINK,
            self.DNA_PART_LINK,
            self.RNA_PART_LINK,
            self.TRANSCRIPTION_LINK,
            self.TRANSLATION_LINK,
        }

    def requires_link_definition_id(self) -> bool:
        """Whether the field definition input requires `linkDefinitionId`, even if it is null."""
        return self.is_schema_link() or self == self.STORAGE_LINK

    def supports_is_multi(self) -> bool:
        return self.is_schema_link() or self in {
            self.DROPDOWN,
            self.BLOB_LINK,
            self.ATTACHMENT_LINK,
            self.ENTRY_LINK,
            self.STORAGE_LINK,
            self.ENTITY_LINK,
        }

    def is_numeric(self) -> bool:
        return self in {self.INTEGER, self.FLOAT, self.DECIMAL}

    def supports_display_precision(self) -> bool:
        return self in {self.FLOAT, self.DECIMAL}

    def supports_unit(self) -> bool:
        return self.is_numeric()
