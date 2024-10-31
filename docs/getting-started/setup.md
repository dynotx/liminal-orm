
1. `cd` into the directory where you want to instantiate your *Liminal environment*. This will be the root directory where your schemas will be defined. Note: the Liminal CLI must always be run from within this root directory.

2. Run `liminal init` in your CLI to initialize your *Liminal environment*. This will create a `liminal/` directory that contains an `env.py` file and a `versions/` directory.

    * The `env.py` file is used to store your Benchling connection information.
    * The `versions/` directory is used to store your revision files.

3. Populate the `env.py` file with your Benchling connection information, following the instructions in the file. For example:

    ```python
    from liminal.connection import BenchlingConnection

        PROD_CURRENT_REVISION_ID = "12b31776a755b"

        # It is highly recommended to use a secrets manager to store your credentials.
        connection = BenchlingConnection(
            tenant_name="pizzahouse-prod",
            tenant_alias="prod",
            current_revision_id_var_name="PROD_CURRENT_REVISION_ID",
            api_client_id="my-secret-api-client-id",
            api_client_secret="my-secret-api-client-secret",
            warehouse_connection_string="my-warehouse-connection-string",
            internal_api_admin_email="my-secret-internal-api-admin-email",
            internal_api_admin_password="my-secret-internal-api-admin-password",
    )
    ```

    * Required: The `api_client_id` and `api_client_secret` are used to connect to Benchling's SDK. For more information, see the [Benchling API documentation](https://docs.benchling.com/docs/getting-started-benchling-apps#calling-the-api-as-an-app).
    * Required: The `internal_api_admin_email` and `internal_api_admin_password` are used to connect to Benchling's API for the migration service. This must be the email and password used to log in to an Admin account.
    * Optional: The `warehouse_connection_string` is used to connect to Benchling's Postgres warehouse. This is optional, but recommended for querying the Benchling warehouse using SQLAlchemy.

    The `CURRENT_REVISION_ID` variable is used to store the current state of where your Benchling tenant lies on the revision timeline. The id is the `revision_id` of the revision file that has been applied to your Benchling tenant.

    !!! tip

        If you have multiple Benchling tenants you'd like to synchronize, you can define multiple Benchling connections in the `env.py` file by creating multiple `BenchlingConnection` objects and respective `CURRENT_REVISION_ID` variables. Use the optional `current_revision_id_var_name` parameter to link the variable to the `BenchlingConnection` object.

4. If your Benchling tenant has pre-existing schemas, run `liminal generate-files <benchling_tenant> [<write_path>]` to populate the root directory with your schema files from the given Benchling tenant. Your file structure should now look like this:

        pizzahouse/
            liminal/
                env.py
                versions/
                    <revision_id>_initial_init_revision.py
            dropdowns/
                ...
            entity_schemas/
                ...

    !!! tip
        It is recommended to generate files using your production Benchling tenant. These schemas will be used as the single source of truth for your production tenant as well as other tenants you may have.

5. Add your schema imports to the env.py file. For example:

    ```python
    from pizzahouse.dropdowns import *
    from pizzahouse.entity_schemas import *
    ```

    !!! warning

        This is necessary for Liminal to recognize what schemas exist in your environment.

6. **Set up is complete!** You're now ready to start using your schemas defined in code as the single source of truth for your Benchling tenant(s).
