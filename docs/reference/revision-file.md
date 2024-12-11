## Example Revision File

Below is an example of a revision file that gets generated by the `liminal autogenerate` command. This flow was heavily inspired by the [Alembic](https://alembic.sqlalchemy.org/en/latest/) migration workflow. When `liminal upgrade` is run, the operations in the `upgrade()` function are executed and when `liminal downgrade` is run, the operations in the `downgrade()` function are executed. Each revision is linearly linked to a previous revision, creating a timeline of revisions/operations. This allows for the user to traverse the history of their Benchling model.

```python
'''
test

Revision ID: c3a9cd009713
Revises: d28335bffaba
Create Date: 2024-10-26 10:33:26.390965
'''

import liminal.external as b

# revision identifiers, used by Liminal.
revision = "c3a9cd009713"
down_revision = "d28335bffaba"


# ### commands auto generated by Liminal - please review (and adjust if needed)! ###
def upgrade() -> list[b.BaseOperation]:
    return [b.ArchiveEntitySchemaField('pizza', 'dough')]

# ### commands auto generated by Liminal - please review (and adjust if needed)! ###
def downgrade() -> list[b.BaseOperation]:
    return [b.UnarchiveEntitySchemaField('pizza', 'dough')]
```

!!! warning
    Generated revision files cannot detect changes to changes in warehouse names.
    In order to resolve this, you must manually edit the revision file.

    Updating Entity Schema warehouse name:
    ```python
    b.UpdateEntitySchema('old_warehouse_name', 
        b.BaseSchemaProperties(warehouse_name='new_warehouse_name')
    )
    ```

    Updating Entity Schema Field warehouse name:
    ```python
    b.UpdateEntitySchemaField('entity_schema_warehouse_name', 'field_warehouse_name', 
    b.BaseFieldProperties(warehouse_name='new_warehouse_name')
    )
    ```

    Updating Dropdown warehouse name:
    ```python
    b.UpdateDropdown('old_warehouse_name', 
        b.BaseDropdownProperties(warehouse_name='new_warehouse_name')
    )
    ```