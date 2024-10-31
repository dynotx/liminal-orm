1. Let's say you want to revert changes made to your Benchling tenant. You can do this by downgrading to a previous revision. This will run the downgrade operations defined in the revision file and revert the tenant back to the previous state. This is a useful tool to revert accidental changes made to your Benchling tenant and maintain the history of your schema changes.

2. In your CLI in Liminal's root directory (that contains the `liminal/` path), run the following command:

    ```bash
    liminal downgrade <benchling_tenant> <downgrade_descriptor>
    ```

    !!! note "The downgrade descriptor"
        The downgrade descriptor can be one of:

        - `revision_id`: The ID of the revision to downgrade to. Ex: `"d28335bffaba"`
        - `-<n>`: The `n` revisions before the current revision. Ex: `-1` will downgrade to the revision before the current revision.
