import importlib.util
from pathlib import Path

from liminal.connection.benchling_connection import BenchlingConnection


def _check_env_file(env_file_path: Path) -> None:
    """Raises an exception if the env.py file does not exist at the given path."""
    if not env_file_path.exists():
        raise Exception(
            f"No {env_file_path} file found. Run `liminal init` or check your current working directory for liminal/env.py."
        )


def read_local_env_file(
    env_file_path: Path, benchling_tenant: str
) -> tuple[str, BenchlingConnection]:
    """Imports the env.py file from the current working directory and returns the CURRENT_REVISION_ID variable along with the BenchlingConnection object.
    The env.py file is expected to have the CURRENT_REVISION_ID variable set to the revision id you are currently on.
    The BenchlingConnection object is expected to be defined and have connection information for the Benchling API client and internal API.
    """
    _check_env_file(env_file_path)
    module_path = Path.cwd() / env_file_path
    spec = importlib.util.spec_from_file_location(env_file_path.stem, module_path)
    if spec is None or spec.loader is None:
        raise Exception(f"Could not find {env_file_path}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for attr_name in dir(module):
        bc = getattr(module, attr_name)
        if isinstance(bc, BenchlingConnection):
            if not (
                benchling_tenant == bc.tenant_name
                or benchling_tenant == bc.tenant_alias
            ):
                continue
            if not bc.api_client_id or not bc.api_client_secret:
                raise Exception(
                    "api_client_id and api_client_secret must be provided in BenchlingConnection in liminal/env.py. This is necessary for the migration service."
                )
            if not bc.internal_api_admin_email or not bc.internal_api_admin_password:
                raise Exception(
                    "internal_api_admin_email and internal_api_admin_password must be provided in BenchlingConnection in liminal/env.py. This is necessary for the migration service."
                )
            try:
                current_revision_id: str = getattr(
                    module, bc.current_revision_id_var_name
                )
                return current_revision_id, bc
            except Exception as e:
                raise Exception(
                    f"CURRENT_REVISION_ID variable not found in liminal/env.py. Given variable name: {bc.current_revision_id_var_name}"
                ) from e
    raise Exception(
        f"BenchlingConnection with tenant name or alias {benchling_tenant} not found in liminal/env.py. Please update the env.py file with a correctly defined BenchlingConnection."
    )


def update_env_revision_id(
    env_file_path: Path, benchling_env: str, revision_id: str
) -> None:
    """Updates the CURRENT_REVISION_ID variable in the env.py file to the given revision id."""
    env_file_content = env_file_path.read_text().split("\n")
    for i, line in enumerate(env_file_content):
        if f"{benchling_env}_CURRENT_REVISION_ID =" in line:
            env_file_content[i] = (
                f'{benchling_env}_CURRENT_REVISION_ID = "{revision_id}"'
            )
    env_file_path.write_text("\n".join(env_file_content))
