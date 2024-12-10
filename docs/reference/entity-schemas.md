
## Entity Schema: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/base_model.py)

Below is an example of a custom entity schema defined in code. All Liminal entity schema classes inherit from Liminal's [BaseModel](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/base_model.py) and uses [SQLAlchemy](https://www.sqlalchemy.org/) behind the scenes to create an ORM. Liminal provides base classes and clear abstractions to an easy and standardized way to define entity schemas in code. However, you are still able to use raw SQLAlchemy to interact with the schemas when necessary.

The properties defined in the `SchemaProperties` object and for `Column` objects
align with the properties shown on the Benchling website. This is how Liminal defines your Benchling entity schema in code. Any of these properties
can be manipulated to change the definition of the entity schema. Updates to the schema or the addition/archival of schemas are automatically
detected by Liminal's migration service, which is run using the `liminal autogenerate` command. Refer to the [First Migration](../getting-started/first-migration.md) page to run your first migration.

Below, we will go through the different components of defining an entity schema class.

```python
from liminal.orm.relationship import single_relationship
from liminal.orm.schema_properties import SchemaProperties
from liminal.orm.column import Column
from liminal.validation import BenchlingValidator
from liminal.enums import BenchlingEntityType, BenchlingFieldType, BenchlingNamingStrategy
from sqlalchemy.orm import Query, Session
from liminal.orm.mixins import CustomEntityMixin
from liminal.orm.base_model import BaseModel
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

    dough = Column(name="dough", type=BenchlingFieldType.ENTITY_LINK, required=True, entity_link="dough")
    cook_temp = Column(name="cook_temp", type=BenchlingFieldType.INTEGER, required=False)
    cook_time = Column(name="cook_time", type=BenchlingFieldType.INTEGER, required=False)
    toppings = Column(name="toppings", type=BenchlingFieldType.DROPDOWN, required=False, dropdown=Toppings)
    customer_review = Column(name="customer_review", type=BenchlingFieldType.INTEGER, required=False)
    slices = Column(name="slices", type=BenchlingFieldType.ENTITY_LINK, required=False, is_multi=True, entity_link="slice")

    dough_entity = single_relationship("Dough", dough)
    slice_entities = multi_relationship("Slice", "Pizza", "slices")

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

## Mixins: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/mixins.py)

All Liminal entity schema classes must inherit from one of the mixins in the [mixins](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/mixins.py) module. The mixin provides the base columns for the specific entity schema type. For example, the `CustomEntityMixin` provides the base columns for a custom entity schema. To learn more, check out the SQLAlchemy documentation [here](https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/mixins.html).

## Schema Properties: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/schema_properties.py)

### Parameters

**name: str**

> The name of the entity schema. Must be unique across all entity schemas.

**warehouse_name: str**

> The warehouse name of the entity schema. Must be unique across all entity schemas.

!!! note
    The warehouse names are used as keys across liminal and are used as entity_link values in Columns.

!!! warning
    If warehouse access is not enabled on your tenant, you will be unable to update the warehouse name.

    Liminal assumes the Benchling generated warehouse name to be `to_snake_case(name)`.

**prefix: str**

> The prefix of the entity schema. Must be unique across all entity schemas.

**entity_type: BenchlingEntityType**

> The type of entity schema. Type must be one of the values from the [BenchlingEntityType](https://github.com/dynotx/liminal-orm/blob/main/liminal/enums/benchling_entity_type.py) enum.

**naming_strategies: set[BenchlingNamingStrategy]**

> The naming strategies for the entity schema. Must be a set of values from the [BenchlingNamingStrategy](https://github.com/dynotx/liminal-orm/blob/main/liminal/enums/benchling_naming_strategy.py) enum.

**mixture_schema_config: MixtureSchemaConfig | None**

> The mixture schema configuration for the entity schema. Must be defined as a [MixtureSchemaConfig](https://github.com/dynotx/liminal-orm/blob/main/liminal/base/properties/base_schema_properties.py) object.

**_archived: bool | None = None**

> Private attribute used to set the archived status of the schema.

!!! tip
    When schemas (and fields) are archived, they still existing the Benchling warehouse. Using _archived is useful when you need to access archived data.

## Column: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/column.py)

!!! warning
    If warehouse access is not enabled on your tenant, you will be unable to update the warehouse name for fields.

    Liminal will enforce that the column variable name (which represents the warehouse name) matches the Benchling generated warehouse name, which Liminal assumes to be `to_snake_case(name)`.

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

**tooltip: str | None = None**

> The tooltip for the field. Defaults to None.

**dropdown: Type[BaseDropdown] | None = None**

> The dropdown object for the field. The dropdown object must inherit from BaseDropdown and the type of the Column must be `BenchlingFieldType.DROPDOWN`. Defaults to None.

**entity_link: str | None = None**

> The entity link for the field. The entity link must be the `warehouse_name` as a string of the entity schema that the field is linking to. The type of the Column must be `BenchlingFieldType.ENTITY_LINK` in order to be valid. Defaults to None.

**_archived: bool = False**

> Private attribute used to set the archived status of the column.  Useful when you need to access archived data and want to define archived fields.

**_warehouse_name: str | None = None**

> Private attribute used to set the warehouse name of the column. This is useful when the variable name is not the same as the warehouse name.

## Relationships: [module](https://github.com/dynotx/liminal-orm/blob/main/liminal/orm/relationship.py)

If there are columns that are entity links, that means the value of the column is the linked entity id or ids. You can easily define relationships using Liminal's wrapper functions around SQLAlchemy. The two relationships to define are `single_relationship` and `multi_relationship`, and examples are shown above.

```python
# single_relationship is used for a non-multi field where there is a one-to-one relationship from the current class to the target class.
single_relationship(target_class_name: str, entity_link_field: Column, backref: str | None = None) -> RelationshipProperty:

# multi_relationship is used for a multi field where there is a "one-to-many" relationship from the current class to the target class.
# NOTE: This is not a normal one-to-many relationship. The multi field is represented as a list of entity ids.
multi_relationship(target_class_name: str, current_class_name: str, entity_link_field_name: str) -> RelationshipProperty
```

!!! question "How do I access the joined entity or entities?"

    ```python
    connection = BenchlingConnection(...)
    benchling_service = BenchlingService(connection, use_db=True)

    with benchling_service as session:
        pizza_entity = session.query(Pizza).first()

        # NOTE: Accessing the relationship entities must be done within the session context.
        dough = pizza_entity.dough_entity
        slices = pizza_entity.slice_entities
    ```

## Custom Query

The `query()` method must be implemented for the entity schema class to define a custom query. This is useful if you want to add additional filtering or joins to the query.

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

## Additional Functionality

Below is additional functionality that is provided by the Liminal BaseModel class.

```python
connection = BenchlingConnection(...)
benchling_service = BenchlingService(connection, use_db=True)

with benchling_service as session:

    # Get all entities for a schema and return a dataframe
    df = Pizza.df(session)

    # Validate all entities for a schema and return a list of ValidatorReports
    reports = Pizza.validate(session)

    # Validate all entities for a schema and return a dataframe
    validated_df = Pizza.validate_to_df(session)
```

## Notes

- Note that the Entity Schema definition in Liminal does not cover 100% of the properties that can be set through the Benchling website. However, the goal is to have 100% parity! If you find any missing properties that are not covered in the definition or migration service, please open an issue on [Github](https://github.com/dynotx/liminal-orm/issues). In the meantime, you can manually set the properties through the Benchling website.
