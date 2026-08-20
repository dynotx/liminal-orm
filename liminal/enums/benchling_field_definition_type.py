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
    BLOB_LINK_FIELD_DEFINITION = "BlobLinkFieldDefinition"
    DROPDOWN_LINK_FIELD_DEFINITION = "DropdownLinkFieldDefinition"
    ANY_ENTITY_LINK_FIELD_DEFINITION = "AnyEntityLinkFieldDefinition"
    CUSTOM_ENTITY_LINK_FIELD_DEFINITION = "CustomEntityLinkFieldDefinition"
    FIELDSET_LINK_FIELD_DEFINITION = "FieldsetLinkFieldDefinition"
    ENTRY_LINK_FIELD_DEFINITION = "EntryLinkFieldDefinition"
