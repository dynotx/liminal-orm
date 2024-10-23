from pathlib import Path

from rich import print

from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdowns_dict
from liminal.utils import pascalize, to_snake_case


def generate_all_dropdown_files(
    benchling_service: BenchlingService, write_path: Path
) -> None:
    """Generate all dropdown files from your Benchling tenant and writes to the given dropdowns/ path.
    This is used to initialize your code for Liminal and transfer the information from your Benchling tenant to your local codebase.
    Note: This will overwrite any existing dropdowns that exist in the given path.
    """
    write_path = write_path / "dropdowns"
    if not write_path.exists():
        write_path.mkdir(parents=True, exist_ok=True)
        print(f"[green]Created directory: {write_path}")

    dropdowns = get_benchling_dropdowns_dict(benchling_service)
    file_names_to_classname = []
    for dropdown_name, dropdown_options in dropdowns.items():
        dropdown_values = [option.name for option in dropdown_options.options]
        options_list = str(dropdown_values).replace("'", '"')
        classname = pascalize(dropdown_name)
        dropdown_content = f"""
from liminal.base.base_dropdown import BaseDropdown


class {classname}(BaseDropdown):
    __benchling_name__ = "{dropdown_name}"
    __allowed_values__ = {options_list}
"""
        filename = to_snake_case(dropdown_name) + ".py"
        with open(write_path / filename, "w") as file:
            file.write(dropdown_content)
        file_names_to_classname.append((filename, classname))

    file_names_to_classname.sort(key=lambda x: x[0])
    import_statements: str = "\n".join(
        f"from .{filename[:-3]} import {classname}"
        for filename, classname in file_names_to_classname
    )
    with open(write_path / "__init__.py", "w") as file:
        file.write(import_statements)
        print(
            f"[green]Generated {write_path / '__init__.py'} with {len(file_names_to_classname)} dropdown imports."
        )
