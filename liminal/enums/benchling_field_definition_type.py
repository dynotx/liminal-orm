from __future__ import annotations

from liminal.base.str_enum import StrEnum


class BenchlingFieldDefinitionType(StrEnum):
    TEXT_FIELD_DEFINITION = "TextFieldDefinition"
    LONG_TEXT_FIELD_DEFINITION = "LongTextFieldDefinition"
    INTEGER_FIELD_DEFINITION = "IntegerFieldDefinition"
    FLOAT_FIELD_DEFINITION = "FloatFieldDefinition"
    BOOLEAN_FIELD_DEFINITION = "BooleanFieldDefinition"
    DATE_FIELD_DEFINITION = "DateFieldDefinition"
    DATETIME_FIELD_DEFINITION = "DateTimeFieldDefinition"
    JSON_FIELD_DEFINITION = "JsonFieldDefinition"
    AA_SEQUENCE_LINK_FIELD_DEFINITION = "AaSequenceLinkFieldDefinition"
    ANTIBODY_LINK_FIELD_DEFINITION = "AntibodyLinkFieldDefinition"
    ASSAY_REQUEST_LINK_FIELD_DEFINITION = "AssayRequestLinkFieldDefinition"
    ASSAY_RESULT_LINK_FIELD_DEFINITION = "AssayResultLinkFieldDefinition"
    ASSAY_RUN_LINK_FIELD_DEFINITION = "AssayRunLinkFieldDefinition"
    BLOB_LINK_FIELD_DEFINITION = "BlobLinkFieldDefinition"
    CUSTOM_ENTITY_LINK_FIELD_DEFINITION = "CustomEntityLinkFieldDefinition"
    DNA_OLIGO_LINK_FIELD_DEFINITION = "DnaOligoLinkFieldDefinition"
    DNA_SEQUENCE_LINK_FIELD_DEFINITION = "DnaSequenceLinkFieldDefinition"
    DROPDOWN_LINK_FIELD_DEFINITION = "DropdownLinkFieldDefinition"
    ANY_ENTITY_LINK_FIELD_DEFINITION = "AnyEntityLinkFieldDefinition"
    ENTRY_LINK_FIELD_DEFINITION = "EntryLinkFieldDefinition"
    EQUIPMENT_LINK_FIELD_DEFINITION = "EquipmentLinkFieldDefinition"
    FIELDSET_LINK_FIELD_DEFINITION = "FieldsetLinkFieldDefinition"
    MIXTURE_LINK_FIELD_DEFINITION = "MixtureLinkFieldDefinition"
    MOLECULE_LINK_FIELD_DEFINITION = "MoleculeLinkFieldDefinition"
    OLIGO_CONJUGATE_LINK_FIELD_DEFINITION = "OligoConjugateLinkFieldDefinition"
    OLIGO_DUPLEX_LINK_FIELD_DEFINITION = "OligoDuplexLinkFieldDefinition"
    RNA_SEQUENCE_LINK_FIELD_DEFINITION = "RnaSequenceLinkFieldDefinition"
    RNA_OLIGO_LINK_FIELD_DEFINITION = "RnaOligoLinkFieldDefinition"
    STORABLE_LINK_FIELD_DEFINITION = "StorableLinkFieldDefinition"
    SYSTEM_CATEGORY_LINK_FIELD_DEFINITION = "SystemCategoryLinkFieldDefinition"

    @classmethod
    def is_primitive(cls, field_definition_type: BenchlingFieldDefinitionType) -> bool:
        return field_definition_type in {
            cls.TEXT_FIELD_DEFINITION,
            cls.LONG_TEXT_FIELD_DEFINITION,
            cls.INTEGER_FIELD_DEFINITION,
            cls.FLOAT_FIELD_DEFINITION,
            cls.BOOLEAN_FIELD_DEFINITION,
            cls.DATE_FIELD_DEFINITION,
            cls.DATETIME_FIELD_DEFINITION,
            cls.JSON_FIELD_DEFINITION,
        }

    @classmethod
    def is_dropdown_link(
        cls, field_definition_type: BenchlingFieldDefinitionType
    ) -> bool:
        return field_definition_type == cls.DROPDOWN_LINK_FIELD_DEFINITION

    @classmethod
    def is_entity_link(
        cls, field_definition_type: BenchlingFieldDefinitionType
    ) -> bool:
        return field_definition_type in {
            cls.AA_SEQUENCE_LINK_FIELD_DEFINITION,
            cls.ANTIBODY_LINK_FIELD_DEFINITION,
            cls.CUSTOM_ENTITY_LINK_FIELD_DEFINITION,
            cls.DNA_OLIGO_LINK_FIELD_DEFINITION,
            cls.DNA_SEQUENCE_LINK_FIELD_DEFINITION,
            cls.ANY_ENTITY_LINK_FIELD_DEFINITION,
            cls.EQUIPMENT_LINK_FIELD_DEFINITION,
            cls.FIELDSET_LINK_FIELD_DEFINITION,
            cls.MIXTURE_LINK_FIELD_DEFINITION,
            cls.MOLECULE_LINK_FIELD_DEFINITION,
            cls.OLIGO_CONJUGATE_LINK_FIELD_DEFINITION,
            cls.OLIGO_DUPLEX_LINK_FIELD_DEFINITION,
            cls.RNA_SEQUENCE_LINK_FIELD_DEFINITION,
            cls.RNA_OLIGO_LINK_FIELD_DEFINITION,
        }
