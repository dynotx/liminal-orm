1. You have changes you need to make to your Benchling schema model. Manipulate your schema classes defined in code and make changes where needed. When you are finished, you are ready to run your first migration!

    !!! info "Manipulating schemas"
        For an overview of what is covered by Liminal and can be defined in code, please see the [Reference](../reference/entity-schemas.md) section to get detailed documentation on the different class properties. When making changes, anything that Liminal covers should be manipulated in code. Otherwise, your schemas defined in code will become out of sync with your Benchling tenant. Any properties that Liminal does not cover should be manipulated through the Benchling UI, as Liminal cannot track changes to these properties.

2. In your CLI in Liminal's root directory (that contains the `liminal/` path), run the following command:

    ```bash
    liminal upgrade <benchling_tenant> <upgrade_descriptor>
    ```

    Example: `liminal upgrade prod "remove dough column from pizza schema"`.

    This will automatically generate a new revision file in the `versions/` directory. This revision file defines the set of steps (or "operations") that will be needed to make the targeted Benchling tenant up to date with the changes made in the schema model.

    !!! question "If I have multiple Benchling tenants, do I have to run `autogenerate` for each tenant?"

        No, Liminal only keeps a single thread of revision history so that each revision file has a linear link. In the case of multiple tenants that need to stay in sync together, we recommend pointing `autogenerate` at your production tenant, or the tenant that acts as the production environment. This will ensure there is a consistent history that your other tenants can follow. When ready, you can then apply the revision to all your tenants.

3. Review the generated revision file and set of operations to ensure that it is accurate.

    ### Example Revision File

    ```python
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

    This looks correct! I wanted to archive the `dough` column from the `pizza` entity schema.

4. Once you've reviewed the revision file and are ready to apply the changes, run the following command:

    ```bash
    liminal upgrade <benchling_tenant_name> <upgrade_descriptor>
    ```

    !!! note "The upgrade descriptor"
        The upgrade descriptor can be one of:

        - `head` to upgrade to the latest revision.
        - `revision_ID` to upgrade to a specific revision. Ex: `"c3a9cd009713"`
        - `+<n>` to upgrade to the revision `n` revisions after the current revision. Ex: `"+1"` will upgrade to the revision after the current revision.

    In this case, we run `liminal upgrade prod head` to upgrade to apply the revision to the production tenant.

    !!! tip
        If you have multiple Benchling tenants, you can run `liminal upgrade` multiple times pointing to different tenants to upgrade them. It is recommended to run against your test tenant first to ensure the changes are applied as expected.

5. You should see output indicating that the revision was applied successfully. Check your Benchling tenant to ensure the changes were applied as expected!