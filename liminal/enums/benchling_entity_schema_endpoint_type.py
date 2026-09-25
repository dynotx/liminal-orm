from liminal.base.str_enum import StrEnum


class BenchlingEntitySchemaEndpointType(StrEnum):
    """This enum represents the different entity schema endpoint types in Benchling."""

    CUSTOM_ENTITY = "custom-entity-schema"
    DNA_SEQUENCE = "dna-sequence-schema"
    DNA_OLIGO = "dna-oligo-schema"
    RNA_OLIGO = "rna-oligo-schema"
    RNA_SEQUENCE = "rna-sequence-schema"
    AA_SEQUENCE = "aa-sequence-schema"
    ENTRY = "entry-schema"
    MIXTURE = "mixture-schema"
    MOLECULE = "molecule-schema"
