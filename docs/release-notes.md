For full release notes, please visit the [GitHub Releases page](https://github.com/dynotx/liminal-orm/releases). Release versions follow [semantic versioning](https://semver.org/). This page will document migration steps needed for major and minor version changes.

## v4.5.0

[![github](https://img.shields.io/badge/github-v4.5.0-blue)](https://github.com/dynotx/liminal-orm/releases/tag/4.5.0) [![pypi](https://img.shields.io/pypi/v/liminal-orm/4.5.0.svg)](https://pypi.org/project/liminal-orm/4.5.0/)

### 🗒️ Summary

v4.5.0 release adds support for using Liminal with Benchling tenants where SSO is required or optional. When SSO is enabled, Liminal can authenticate access to Benchling’s internal API with the user's credentials. Liminal uses Playwright, a widely used Python package for automating modern browsers, web testing, and scripting.

In your env.py file, internal_api_admin_email and internal_api_admin_password no longer need to be set in the BenchlingConnection class. If they are unset and SSO is required or optional in your Benchling tenant, Liminal will open a Playwright browser session and prompt the user to log into their SSO. After the user finishes logging in, Liminal will use the authenticated Benchling session to access Benchling’s internal API

- PR [#203](https://github.com/dynotx/liminal-orm/pull/203): support for Benchling SSO authentication.

### Upgrade Steps (Optional)

1.  If you have a Benchling tenant where SSO is required or optional and want to use the Playwright SSO login flow, remove the `internal_api_admin_email` and `internal_api_admin_password` properties from the BenchlingConnection class in your env.py file. 
2. Run `liminal current <benchling_tenant_name>` to test. Reach out if you have any issues or questions!

## v4.0.0

[![github](https://img.shields.io/badge/github-v4.0.0-blue)](https://github.com/dynotx/liminal-orm/releases/tag/4.0.0) [![pypi](https://img.shields.io/pypi/v/liminal-orm/4.0.0.svg)](https://pypi.org/project/liminal-orm/4.0.0/)

### 🗒️ Summary

The v4.0.0 brings the ability to define results schemas in code using Liminal. Results tables are used to capture experimental and assay data in lab notebooks. With a single command, you can define all of your results schemas as classes in your codebase using Liminal's framework. This enables a simple and strongly-typed way of accessing this data, and the ability to create custom validation rules for your results. For full details, check out the [results schemas](../reference/results-schemas) documentation! This release also adds functionality to the `liminal generate-files` command to allow for more flexibility (run `liminal generate-files --help` for full details). Support for deprecated features has been extended to the release of v5.0.0.

### Upgrade Steps

- PR [#133](https://github.com/dynotx/liminal-orm/pull/133): results schemas!

1. **Upgrade step**: Follow the getting started guide to [generate your results schema classes](../getting-started/synchronizing-results-schemas/).

## v3.2.0

[![github](https://img.shields.io/badge/github-v3.2.0-blue)](https://github.com/dynotx/liminal-orm/releases/tag/3.2.0) [![pypi](https://img.shields.io/pypi/v/liminal-orm/3.2.0.svg)](https://pypi.org/project/liminal-orm/3.2.0/)

### 🗒️ Summary

This release brings Liminal's CLI and logic closer to [Alembic's patterns](https://alembic.sqlalchemy.org/en/latest/api/commands.html), making it more familiar for users. It also fixes a couple bugs in a backwards compatible manner.

- Liminal now saves the tenant's revision_id within Benchling instead of tracking it locally within env.py. When a new migration is run, Liminal will save the 'remote' revision_id within a generated _liminal_remote schema.

- The `liminal current <ENV>` command now returns the revision_id from Benchling instead of the local env.py file. This is now the same pattern as Alembic.

- There is a new `liminal head <ENV>` command that returns the latest revision_id based on your local revision timeline in *versions/*. This is the same pattern as Alembic.

- `liminal autogenerate <ENV> '<message>'` is now `liminal revision <ENV> '<message>'`. This is now the same pattern as Alembic.

- Bug fixes with multi_relationship function and imports.

### Upgrade Steps

There are no upgrade steps for this release, but there are deprecation warnings that need to be resolved by the v4.0.0 release.

- The local `_CURRENT_REVISION_ID` variable is now longer used and should be deleted from your env.py file.

- The multi_relationship function arguments have changed, and should be updated accordingly. See the [multi_relationship](../reference/entity-schemas/#relationships-module) documentation for full details.

## v3.1.0

[![github](https://img.shields.io/badge/github-v3.1.0-blue)](https://github.com/dynotx/liminal-orm/releases/tag/3.1.0) [![pypi](https://img.shields.io/pypi/v/liminal-orm/3.1.0.svg)](https://pypi.org/project/liminal-orm/3.1.0/)

### 🗒️ Summary

This release adds the ability to define tenant-specific configuration flags for entity schemas. The goal of this is to reflect Benchling's tenant level configuration flags and propagate the logic across Liminal. We have started with the `schemas_enable_change_warehouse_name` flag. When set to `True`, this flag allows users to change the warehouse name of entity schemas and fields and migrate the changes to your tenants.

### Upgrade Steps

- PR [#120](https://github.com/dynotx/liminal-orm/pull/120): adds ability to define tenant-specific configuration flags for entity schemas.

1. **Upgrade step**: Remove the `warehouse_access` parameter from the `BenchlingConnection` object. Set the `config_flags` parameter on your `BenchlingConnection` object(s) to a `TenantConfigFlags` object. See documentation for [BenchlingConnection](../reference/benchling-connection) for full details.

## v3.0.0

[![github](https://img.shields.io/badge/github-v3.0.0-blue)](https://github.com/dynotx/liminal-orm/releases/tag/3.0.0) [![pypi](https://img.shields.io/pypi/v/liminal-orm/3.0.0.svg)](https://pypi.org/project/liminal-orm/3.0.0/)

### 🗒️ Summary

v3.0.0 release brings Liminal's coverage of entity schemas to 100% parity with Benchling, a big milestone in Liminal's roadmap!! Any property that can be defined on Entity Schemas in Benchling can now be defined and migrated through Liminal. With this release, user's will now be able to define unit aware fields and "Show bases in expanded view" in their Liminal models defined in code.

- `show_bases_in_expanded_view` has been added to the `SchemaProperties` parameters
<img width="968" alt="Screenshot 2025-02-20 at 8 26 34 AM" src="https://github.com/user-attachments/assets/b01fe696-6d6b-4f9e-9349-f577de3f6b29" />

***

- `unit_name` and `decimal_places` has been added to the `Column` parameters.
<img width="587" alt="Screenshot 2025-02-20 at 8 25 30 AM" src="https://github.com/user-attachments/assets/a4f6fe8c-652c-4fa0-89b0-abe45fa6d7a3" />

Next up are results schemas 🚀

### Upgrade Steps

- PR [#114](https://github.com/dynotx/liminal-orm/pull/114): adds ability to define unit aware fields for entity schema fields.
- PR [#113](https://github.com/dynotx/liminal-orm/pull/113): adds ability to define `show_bases_in_expanded_view` for entity schema fields.

1. **Upgrade step**: The guidance for migrating to v3.0.0 is after you've upgraded your liminal package to the latest version, regenerate your schemas defined in code using `liminal generate-files <benchling_tenant> -p [<write_path>]`. This will write your dropdown/schema files based on your Benchling tenant to a specified path, this time with the new properties that are now covered by Liminal. If you do not have many enitty schemas, it may be easier to manually update your schema files with the new properties. Note, you may have to comment out the schema/dropdown imports in your `env.py` file before generating the files since there may be some breaking changes to your current schema/dropdown files.

## v2.0.0

### 🗒️ Summary

v2.0.0 brings Liminal closer to reaching 100% parity with Benchling Entity Schemas. This release introduces the ability to define namesets, chip naming properties, and constraints on your Liminal entity schema models. Validation has also gone through a major change making it MUCH easier to define custom business logic as validation rules for entities. Now, users can use the `@liminal_validator` decorator to define validation functions within Liminal models. When TestSchema.validate() is run, these decorated functions are run on all queried entity rows from the Benchling warehouse, catching any `Exceptions` raised and returned a `BenchlingValidatorReport`.

- `constraint_fields`, `include_registry_id_in_chips`, `use_registry_id_as_label` added to SchemaProperties parameters. `__name_template__` can now be defined on Liminal models
<img width="1193" alt="Screenshot 2025-02-05 at 10 30 40 AM" src="https://github.com/user-attachments/assets/59d03096-8d95-46a5-b4d0-c18c01331363" />

***

- New pattern for defining validation rules

```python
from liminal.validation import ValidationSeverity, liminal_validator

class Pizza(BaseModel, CustomEntityMixin):
    ...

    @liminal_validator
    def cook_time_and_temp_validator(self) -> None:
        if self.cook_time is not None and self.cook_temp is None:
            raise ValueError("Cook temp is required if cook time is set")
        if self.cook_time is None and self.cook_temp is not None:
            raise ValueError("Cook time is required if cook temp is set")
```

Next release will aim to finish off coverage for Entity Schemas!

### Upgrade Steps

- PR [#88](https://github.com/dynotx/liminal-orm/pull/88): adds ability to defined name templates for entity schemas
- PR [#84](https://github.com/dynotx/liminal-orm/pull/84): adds ability to define chip naming for entity schemas
- PR [#82](https://github.com/dynotx/liminal-orm/pull/82): adds ability to define constraints for entity schemas.

1. **Upgrade step**: The guidance for migrating to v2.0.0 is to regenerate your schemas defined in code using `liminal generate-files <benchling_tenant> -p [<write_path>]`. This will recreate your dropdown/schema files, this time with the new properties covered by Liminal. If you do not have many enitty schemas, it may be easier to manually update your schema files with the new properties.

- PR [#68](https://github.com/dynotx/liminal-orm/pull/68): refactors how validators are done in Liminal using a decorator pattern. Refer to the [validators](https://dynotx.github.io/liminal-orm/reference/validators/) page for full details on implementation.

2. **Upgrade step**: If you don't have validators defined, no action is needed! Otherwise, you will need to manually refactor your validators to use the new pattern.

## v1.1.0

[![github](https://img.shields.io/badge/github-v1.1.0-blue)](https://github.com/dynotx/liminal-orm/releases/tag/1.1.0) [![pypi](https://img.shields.io/pypi/v/liminal-orm/1.1.0.svg)](https://pypi.org/project/liminal-orm/1.1.0/)

### Upgrade Steps

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
