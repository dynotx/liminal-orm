from __future__ import annotations

from liminal.base.str_enum import StrEnum


class BenchlingLinkDefinitionType(StrEnum):
    """This enum represents the type of object a link field points to, returned by the v3 API as `linkDefinition.__typename`."""

    AA_SEQUENCE_SCHEMA = "AaSequenceSchema"
    CUSTOM_ENTITY_SCHEMA = "CustomEntitySchema"
    DNA_OLIGO_SCHEMA = "DnaOligoSchema"
    DNA_SEQUENCE_SCHEMA = "DnaSequenceSchema"
    DROPDOWN = "Dropdown"
    ENTRY_SCHEMA = "EntrySchema"
    FIELDSET = "Fieldset"
    MIXTURE_SCHEMA = "MixtureSchema"
    MOLECULE_SCHEMA = "MoleculeSchema"
    RNA_OLIGO_SCHEMA = "RnaOligoSchema"
    RNA_SEQUENCE_SCHEMA = "RnaSequenceSchema"

    def is_entity_schema_type(self) -> bool:
        return self in {
            self.AA_SEQUENCE_SCHEMA,
            self.CUSTOM_ENTITY_SCHEMA,
            self.DNA_OLIGO_SCHEMA,
            self.DNA_SEQUENCE_SCHEMA,
            self.MIXTURE_SCHEMA,
            self.MOLECULE_SCHEMA,
            self.RNA_OLIGO_SCHEMA,
            self.RNA_SEQUENCE_SCHEMA,
        }
