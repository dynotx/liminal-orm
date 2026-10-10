import keyword
import re
import warnings

from pydantic import BaseModel, model_validator


class TenantConfigFlags(BaseModel):
    """Set of config flags that are configured on the tenant level. These can be updated on Benchling's end by contacting their support team.
    Ask Benchling support to give you the full export of these flags.

    Parameters
    ----------
    schemas_enable_change_warehouse_name: bool = False
        If enabled, allows renaming schema and field warehouse names for all schema admins. Default value is False for Benchling
    """

    schemas_enable_change_warehouse_name: bool = False


class BenchlingConnection(BaseModel):
    """Class that contains the connection information for a Benchling tenant.

    Parameters
    ----------
    tenant_name: str
        The name of the tenant. ex: {tenant_name}.benchling.com
    tenant_alias: str | None = None
        The alias of the tenant name. This is optional and is used as an alternate value when using the Liminal CLI
    current_revision_id_var_name: str = ""
        The name of the variable that contains the current revision id.
        If not provided, a derived name will be generated based on the tenant name/alias.
        Ex: {tenant_alias}_CURRENT_REVISION_ID or {tenant_name}_CURRENT_REVISION_ID if alias is not provided.
    api_client_id: str | None = None
        The id of the API client.
    api_client_secret: str | None = None
        The secret of the API client.
    warehouse_connection_string: str | None = None
        The connection string for the warehouse.
    internal_api_admin_email: str | None = None
        DEPRECATED: Liminal no longer uses Benchling's internal API, so this is ignored. It will be removed in v6.
    internal_api_admin_password: str | None = None
        DEPRECATED: Liminal no longer uses Benchling's internal API, so this is ignored. It will be removed in v6.
    playwright_data_dir: str | None = "~/.liminal/chrome_data/"
        The directory to store the playwright browser user data. If SSO is enabled and required on your Benchling tenant,
        Liminal uses playwright so the user can log into Benchling in order to give Liminal the authenticated internal API session cookie.
        This directory is used to store playwright's persistent context, allowing the user to set up a persistent chrome profile.
        Set this to None in order to disable playwright's persistent context which enables automatic login.
    fieldsets: bool = False
        Whether your Benchling tenant has access to fieldsets.
    config_flags: TenantConfigFlags = TenantConfigFlags()
        Set of config flags that are configured on the tenant level. These can be updated on Benchling's end by contacting their support team.
    """

    tenant_name: str
    tenant_alias: str | None = None
    current_revision_id_var_name: str = ""
    api_client_id: str
    api_client_secret: str
    warehouse_connection_string: str | None = None
    internal_api_admin_email: str | None = None
    internal_api_admin_password: str | None = None
    playwright_data_dir: str | None = "~/.liminal/playwright_chrome_data/"
    fieldsets: bool = False
    config_flags: TenantConfigFlags = TenantConfigFlags()

    @model_validator(mode="before")
    @classmethod
    def set_current_revision_id_var_name(cls, values: dict) -> dict:
        if not values.get("current_revision_id_var_name"):
            tenant_alias = values.get("tenant_alias")
            tenant_name = values.get("tenant_name")
            if tenant_alias:
                var_name = f"{tenant_alias}_CURRENT_REVISION_ID"
            else:
                var_name = f"{tenant_name}_CURRENT_REVISION_ID"

            # Ensure the variable name is valid
            var_name = re.sub(r"\W|^(?=\d)", "_", var_name)
            if not var_name.isidentifier() or keyword.iskeyword(var_name):
                raise ValueError(f"Invalid variable name: {var_name}")

            values["current_revision_id_var_name"] = var_name
        return values

    @model_validator(mode="after")
    def warn_deprecated_internal_api_credentials(self) -> "BenchlingConnection":
        if (
            self.internal_api_admin_email is not None
            or self.internal_api_admin_password is not None
        ):
            warnings.warn(
                "Deprecated BenchlingConnection properties set: internal_api_admin_email and internal_api_admin_password. Liminal no longer uses Benchling's internal API, so they are ignored. Remove them from your BenchlingConnection, since they will be removed in v6.",
                FutureWarning,
                stacklevel=3,
            )
        return self
