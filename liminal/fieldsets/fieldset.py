from liminal.orm.base_model import BaseModel
from liminal.orm.fieldset_schema_properties import FieldsetSchemaProperties
from liminal.orm.name_template import NameTemplate


class Fieldset(BaseModel):
    __schema_properties__: FieldsetSchemaProperties
    __name_template__: NameTemplate = NameTemplate(
        parts=[], order_name_parts_by_sequence=False
    )

    