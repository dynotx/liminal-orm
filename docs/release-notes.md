For full release notes, please visit the [GitHub Releases page](https://github.com/dynotx/liminal-orm/releases). Release versions follow [semantic versioning](https://semver.org/). This page will document only Major and Minor version changes that require user action, such as migration steps, when upgrading to the new version.

## v1.1.0

[![github](https://img.shields.io/badge/github-release-blue)](https://github.com/dynotx/liminal-orm/releases/tag/1.1.0) [![pypi](https://img.shields.io/pypi/v/liminal-orm.svg)](https://pypi.org/project/liminal-orm/1.1.0/)

### Upgrade Notes

- PR [#64](https://github.com/dynotx/liminal-orm/pull/64): makes query function optional in schema classes.
    - Remove query functions from schema classes, unless you have custom logic.
- PR [#72](https://github.com/dynotx/liminal-orm/pull/72): block warehouse name changes to operations.
    - BenchlingConnetion now takes in `warehouse_access` parameter. If you do not have warehouse access on your Benchling tenant, set this to `False`.
- PR [#53](https://github.com/dynotx/liminal-orm/pull/53): move field wh name to base field props.
    - Update historical revision files with changed operation signatures.

    ```python
    # Replace UpdateEntitySchemaName with...
    UpdateEntitySchema('old_warehouse_name', 
        BaseSchemaProperties(warehouse_name='new_warehouse_name'))

    # Replace UpdateEntitySchemaFieldName with...
    UpdateEntitySchemaField('entity_schema_warehouse_name', 
        'field_warehouse_name', 
        BaseFieldProperties(warehouse_name='new_warehouse_name'))

    # CreateEntitySchemaField no longer takes wh_field_name as a parameter. 
    # Now gets passed in via BaseFieldProperties.
    CreateEntitySchemaField('entity_schema_warehouse_name', 
        BaseFieldProperties(warehouse_name='new_warehouse_name', ...))

    # CreateEntitySchema takes in a list of fields instead of dict[str, Benchling FieldProperties]
    CreateEntitySchema(BaseSchemaProperties(...), [BaseFieldProperties(...), ...])
    ```

- PR [#63](https://github.com/dynotx/liminal-orm/pull/63): numpy and pandas version tightening.
    - numpy = “^1.23.5”
    - pandas = ">=1.5.3" --> “^1.5.3"
