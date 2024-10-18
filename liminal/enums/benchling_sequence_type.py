from liminal.base.str_enum import StrEnum


class BenchlingSequenceType(StrEnum):
    DNA_SEQUENCE = "DNA_SEQUENCE"
    RNA_SEQUENCE = "RNA_SEQUENCE"
    DNA_OLIGO = "OLIGO"
    RNA_OLIGO = "RNA_OLIGO"
