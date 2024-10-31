
## Entity Schema: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/base_model.py)

Below is an example of a custom entity schema defined in code. The properties defined in the `SchemaProperties` object and for `Column` objects
align with the properties shown on the Benchling website. This is how Liminal defines your Benchling entity schema in code. Any of these properties
can be manipulated to change the definition of the entity schema. Any updates to the schema or the addition/archival of schemas are automatically
detected by Liminal's migration service. Refer to the [First Migration](../getting-started/first-migration.md) page to run your first migration.

```python
from liminal.orm.schema_properties import SchemaProperties
from liminal.orm.column import Column
from liminal.validation import BenchlingValidator
from liminal.enums import BenchlingEntityType, BenchlingFieldType, BenchlingNamingStrategy
from sqlalchemy.orm import Query, Session
from liminal.orm.mixins import CustomEntityMixin
from liminal.orm.base_model import BaseModel
from sqlalchemy import Column as SqlColumn
from pizzahouse.dropdowns import Toppings

class Pizza(BaseModel, CustomEntityMixin):
    __schema_properties__ = SchemaProperties(
        name="Pizza",
        warehouse_name="pizza",
        prefix="PI",
        entity_type=BenchlingEntityType.CUSTOM_ENTITY,
        naming_strategies={
            BenchlingNamingStrategy.REPLACE_NAME_WITH_ID,
            BenchlingNamingStrategy.IDS_FROM_NAMES,
            BenchlingNamingStrategy.NEW_IDS,
        },
        mixture_schema_config=None,
    )

    dough = Column(name="dough", type=BenchlingFieldType.TEXT, required=True)
    cook_temp = Column(name="cook_temp", type=BenchlingFieldType.INTEGER, required=False)
    cook_time = Column(name="cook_time", type=BenchlingFieldType.INTEGER, required=False)
    toppings = Column(name="toppings", type=BenchlingFieldType.DROPDOWN, required=False, dropdown=Toppings)
    customer_review = Column(name="customer_review", type=BenchlingFieldType.INTEGER, required=False)

    def __init__(
        self,
        dough: str,
        cook_temp: int | None = None,
        cook_time: int | None = None,
        customer_review: int | None = None,
    ):
        self.dough = dough
        self.cook_temp = cook_temp
        self.cook_time = cook_time
        self.customer_review = customer_review


    @classmethod
    def query(self, session: Session) -> Query:
        return session.query(Pizza)

    def get_validators(self) -> list[BenchlingValidator]:
        return []
```

## Schema Properties: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/schema_properties.py)

### Parameters

**name: str**

> The name of the entity schema. Must be unique across all entity schemas.
**warehouse_name: str**

> The warehouse name of the entity schema. Must be unique across all entity schemas.
!!! note
    The warehouse names are used as keys across liminal and are used as entity_link values in Columns.

**prefix: str**

> The prefix of the entity schema. Must be unique across all entity schemas.

**entity_type: BenchlingEntityType**

> The type of entity schema. Type must be one of the values from the [BenchlingEntityType](https://github.com/dynotx/liminal-orm/blob/main/liminal/enums/benchling_entity_type.py) enum.

**naming_strategies: set[BenchlingNamingStrategy]**

> The naming strategies for the entity schema. Must be a set of values from the [BenchlingNamingStrategy](https://github.com/dynotx/liminal-orm/blob/main/liminal/enums/benchling_naming_strategy.py) enum.

**mixture_schema_config: MixtureSchemaConfig | None**

> The mixture schema configuration for the entity schema. Must be defined as a [MixtureSchemaConfig](https://github.com/dynotx/liminal-orm/blob/main/liminal/base/properties/base_schema_properties.py) object.

## Column: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/column.py)

### Parameters

**name: str**

> The external facing name of the column.

**type: BenchlingFieldType**

> The type of the field. Type must be one of the values from the [BenchlingFieldType](https://github.com/dynotx/liminal-orm/blob/main/liminal/enums/benchling_field_type.py) enum.

**required: bool**

> Whether the field is required.

**is_multi: bool = False**

> Whether the field is a multi-value field. Defaults to False.

**parent_link: bool = False**

> Whether the field is a parent link field. Defaults to False.

**dropdown: Type[BaseDropdown] | None = None**

> The dropdown object for the field. The dropdown object must inherit from BaseDropdown and the type of the Column must be `BenchlingFieldType.DROPDOWN`. Defaults to None.

**entity_link: str | None = None**

> The entity link for the field. The entity link must be the `warehouse_name` as a string of the entity schema that the field is linking to. The type of the Column must be `BenchlingFieldType.ENTITY_LINK` in order to be valid. Defaults to None.

**tooltip: str | None = None**

> The tooltip for the field. Defaults to None.

## Notes

- Note that the Entity Schema definition in Liminal does not cover 100% of the properties that can be set through the Benchling website. However, the goal is to have 100% parity! If you find any missing properties that are not covered in the definition or migration service, please open an issue on [Github](https://github.com/dynotx/liminal-orm/issues). In the meantime, you can manually set the properties through the Benchling website.

## Validators: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/validation/__init__.py)

As seen in the example above, the `get_validators` method is used to define a list of validators for the entity schema. These validators run on entities of the schema that are queried from Benchling's Postgres database. For example:

```python
pizza_entity = Pizza.query(session).first()

# Validate a single entity from a query
report = CookTempValidator().validate(pizza_entity)

# Validate all entities for a schema
reports = Pizza.validate(session)
```

The list of validators within `get_validators` are used to run on all entities of the schema.

The `BenchlingValidator` object is used to define the validator classes, that can be defined with custom logic to validate entities of a schema. Refer to the [Validators](./validators.md) page to learn more about how to define validators.
