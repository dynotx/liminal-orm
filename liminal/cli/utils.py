import importlib.util
from logging import Logger
from pathlib import Path
import sys

from liminal.connection.benchling_connection import BenchlingConnection

LOGGER = Logger(name=__name__)


def _check_liminal_directory_initialized(liminal_dir_path: Path) -> None:
    """Raises an exception if the liminal directory does not exist at the given path."""
    if not liminal_dir_path.exists() or not liminal_dir_path.is_dir():
        raise Exception(
            "Liminal directory not found at current working directory. Run `liminal init` or check your current working directory."
        )
    else:
        if not (liminal_dir_path / "env.py").exists():
            raise Exception(
                "No liminal/env.py file found. Run `liminal init` or check your current working directory for liminal/env.py."
            )


def read_local_liminal_dir(
    liminal_dir_path: Path, benchling_tenant: str
) -> BenchlingConnection:
    """Imports the env.py file from /liminal/env.py and returns the BenchlingConnection object.
    The BenchlingConnection object is expected to be defined and have connection information for the Benchling API client and internal API.
    """
    _check_liminal_directory_initialized(liminal_dir_path)
    env_file_path = liminal_dir_path / "env.py"
    return _read_local_env_file(env_file_path, benchling_tenant)


def _read_local_env_file(
    env_file_path: Path, benchling_tenant: str
) -> BenchlingConnection:
    """Imports the env.py file from the current working directory and returns the BenchlingConnection object.
    The BenchlingConnection object is expected to be defined and have connection information for the Benchling API client and internal API.
    """
    module_path = Path.cwd() / env_file_path
    spec = importlib.util.spec_from_file_location(env_file_path.stem, module_path)
    if spec is None or spec.loader is None:
        raise Exception(f"Could not find {env_file_path}.")
    module = importlib.util.module_from_spec(spec)

    parent_dir = str(module_path.parent.parent)
    sys_path_modified = False
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        sys_path_modified = True
    try:
        spec.loader.exec_module(module)
    finally:
        if sys_path_modified:
            sys.path.remove(parent_dir)

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
            return bc
    raise Exception(
        f"BenchlingConnection with tenant name or alias {benchling_tenant} not found in liminal/env.py. Please update the env.py file with a correctly defined BenchlingConnection."
    )
