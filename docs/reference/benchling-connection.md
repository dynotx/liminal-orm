## BenchlingConnection: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/connection/benchling_connection.py)

The `BenchlingConnection` class is used to define the connection information for a particular Benchling tenant. The BenchlingConnection class is defined in your `env.py` file and it also used to create a BenchlingService object. In the `env.py` file, the api_client is required for the BenchlingConnection object in orderto be used in the migration service. The BenchlingService can be imported from the liminal pacakage and be used to connect to [Benchling's SDK](https://docs.benchling.com/docs/getting-started-with-the-sdk), internal API, and/or Postgres warehouse.

```python
# Example BenchlingConnection definition
from liminal.connection import BenchlingConnection, TenantConfigFlags

# It is highly recommended to use a secrets manager to store your credentials.
connection = BenchlingConnection(
    tenant_name="pizzahouse-prod",
    tenant_alias="prod",
    api_client_id="my-secret-api-client-id",
    api_client_secret="my-secret-api-client-secret",
    warehouse_connection_string="my-warehouse-connection-string",
    config_flags=TenantConfigFlags()
)
```

### Parameters

- **tenant_name: str**

    The name of the tenant. ex: {tenant_name}.benchling.com

- **tenant_alias: Optional[str] = None**

    The alias of the tenant name. This is optional and is used as an alternate value when using the Liminal CLI

- **api_client_id: Optional[str] = None**

    The id of the API client.

- **api_client_secret: Optional[str] = None**

    The secret of the API client.

- **warehouse_connection_string: Optional[str] = None**

    The connection string for the warehouse.

- **internal_api_admin_email: Optional[str] = None**

    The email of the internal API admin. If SSO is not enabled or optional on your Benchling tenant, this email is used to log in to Benchling, and give Liminal the authenticated internal API session cookie.

- **internal_api_admin_password: Optional[str] = None**

    The password of the internal API admin. If SSO is not enabled or optional on your Benchling tenant, this password is used to log in to Benchling, and give Liminal the authenticated internal API session cookie.

- **chrome_profile_data_dir: Optional[str] = "~/.liminal/playwright_chrome_data/"**

    The directory to store the Chrome profile data for playwright. If SSO is enabled and required on your Benchling tenant,
    Liminal uses playwright so the user can log into Benchling in order to give Liminal the authenticated internal API session cookie.
    This directory is used to store playwright's persistent context, allowing the user to set up a persistent chrome profile.
    Set this to None in order to disable playwright's persistent context which enables automatic login.

- **fieldsets: bool = False**

    Whether your Benchling tenant has access to fieldsets.

- **config_flags: TenantConfigFlags = TenantConfigFlags()**

    Set of config flags that are configured on the tenant level, that defines specific features of the tenant. These can be updated on Benchling's end by contacting their support team.

    !!! note
        The `config_flags` parameter can be set as a dictionary of config flags or as a TenantConfigFlags object. The dictionary will be converted to a TenantConfigFlags object by Pydantic.

### TenantConfigFlags

Set of config flags that are configured on the tenant level. These can be updated on Benchling's end by contacting their support team.
Ask Benchling support to give you the full export of these flags.

- **schemas_enable_change_warehouse_name: bool = False**

    If set to False (default behavior), operations will raise an error at the validation step if the warehouse name is tried to be updated. If set to True, allows renaming schema and field warehouse names for all schema admins.

    !!! note
        Liminal assumes the Benchling generated warehouse names to be `to_snake_case(name)`.
