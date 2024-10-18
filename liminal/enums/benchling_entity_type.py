from liminal.base.str_enum import StrEnum


class BenchlingEntityType(StrEnum):
    """This enum represents the different entity types that can be created in Benchling."""

    CUSTOM_ENTITY = "custom_entity"
    DNA_SEQUENCE = "dna_sequence"
    DNA_OLIGO = "dna_oligo"
    RNA_OLIGO = "rna_oligo"
    RNA_SEQUENCE = "rna_sequence"
    AA_SEQUENCE = "aa_sequence"
    ENTRY = "entry"
    MIXTURE = "mixture"
