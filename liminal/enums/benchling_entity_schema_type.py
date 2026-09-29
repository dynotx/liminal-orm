from liminal.base.str_enum import StrEnum


class BenchlingEntitySchemaType(StrEnum):
    """This enum represents the different entity schema types returned by the v3 API as `__typename`."""

    AA_SEQUENCE = "AaSequenceSchema"
    CUSTOM_ENTITY = "CustomEntitySchema"
    DNA_OLIGO = "DnaOligoSchema"
    DNA_SEQUENCE = "DnaSequenceSchema"
    ENTRY = "EntrySchema"
    MIXTURE = "MixtureSchema"
    MOLECULE = "MoleculeSchema"
    RNA_OLIGO = "RnaOligoSchema"
    RNA_SEQUENCE = "RnaSequenceSchema"
