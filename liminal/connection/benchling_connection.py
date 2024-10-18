import keyword
import re

from pydantic import BaseModel, model_validator


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
        The email of the internal API admin.
    internal_api_admin_password: str | None = None
        The password of the internal API admin.
    """

    tenant_name: str
    tenant_alias: str | None = None
    current_revision_id_var_name: str = ""
    api_client_id: str | None = None
    api_client_secret: str | None = None
    warehouse_connection_string: str | None = None
    internal_api_admin_email: str | None = None
    internal_api_admin_password: str | None = None

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
