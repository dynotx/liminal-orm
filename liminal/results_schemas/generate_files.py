from pathlib import Path

from rich import print

from liminal.connection import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdowns_dict
from liminal.enums import BenchlingFieldType
from liminal.mappers import convert_benchling_type_to_python_type
from liminal.orm.base_model import BaseModel
from liminal.results_schemas.utils import get_converted_results_schemas
from liminal.utils import to_pascal_case, to_snake_case

TAB = "    "


def generate_all_results_schema_files(
    benchling_service: BenchlingService, write_path: Path
) -> None:
    write_path = write_path / "results_schemas"
    if not write_path.exists():
        write_path.mkdir(parents=True, exist_ok=True)
        print(f"[green]Created directory: {write_path}")

    results_schemas = get_converted_results_schemas(benchling_service)
    benchling_dropdowns = get_benchling_dropdowns_dict(benchling_service)
    entity_schema_subclasses = BaseModel.get_all_subclasses()
    entity_schemas_wh_name_to_classname: dict[str, str] = {
        s.__schema_properties__.warehouse_name: s._sa_class_manager.class_.__name__
        for s in entity_schema_subclasses
    }
    dropdown_name_to_classname_map: dict[str, str] = {
        dropdown_name: to_pascal_case(dropdown_name)
        for dropdown_name in benchling_dropdowns.keys()
    }
    init_file_imports = []

    for schema_properties, field_properties_dict in results_schemas:
        has_date = False
        file_name = to_snake_case(schema_properties.warehouse_name) + ".py"
        schema_name = to_pascal_case(schema_properties.warehouse_name)
        init_file_imports.append(
            f"from .{to_snake_case(schema_properties.warehouse_name)} import {schema_name}"
        )
        import_strings = [
            "from sqlalchemy import Column as SqlColumn",
            "from liminal.orm.base_results_model import BaseResultsModel",
            "from liminal.orm.results_schema_properties import ResultsSchemaProperties",
            "from liminal.orm.column import Column",
            "from liminal.enums import BenchlingFieldType",
        ]
        init_strings = [f"{TAB}def __init__(", f"{TAB}self,"]
        column_strings = []
        dropdowns = []
        relationship_strings = []
        for col_name, col in field_properties_dict.items():
            column_props = col.model_dump(exclude_unset=True, exclude_none=True)
            dropdown_classname = None
            if col.dropdown_link:
                dropdown_classname = dropdown_name_to_classname_map[col.dropdown_link]
                dropdowns.append(dropdown_classname)
                column_props["dropdown_link"] = dropdown_classname
            column_props_string = ""
            for k, v in column_props.items():
                if k == "dropdown_link":
                    column_props_string += f"""dropdown={v},"""
                else:
                    column_props_string += f"""{k}={v.__repr__()},"""
            column_string = (
                f"""{TAB}{col_name}: SqlColumn = Column({column_props_string})"""
            )
            column_strings.append(column_string)
            if col.required and col.type:
                init_strings.append(
                    f"""{TAB}{col_name}: {convert_benchling_type_to_python_type(col.type).__name__},"""
                )

            if (
                col.type == BenchlingFieldType.DATE
                or col.type == BenchlingFieldType.DATETIME
            ):
                if not has_date:
                    import_strings.append("from datetime import datetime")
            if (
                col.type in BenchlingFieldType.get_entity_link_types()
                and col.entity_link is not None
            ):
                if not col.is_multi:
                    relationship_strings.append(
                        f"""{TAB}{col_name}_entity = single_relationship("{entity_schemas_wh_name_to_classname[col.entity_link]}", {col_name})"""
                    )
                    import_strings.append(
                        "from liminal.orm.relationship import single_relationship"
                    )
                else:
                    relationship_strings.append(
                        f"""{TAB}{col_name}_entities = multi_relationship("{entity_schemas_wh_name_to_classname[col.entity_link]}", {col_name})"""
                    )
                    import_strings.append(
                        "from liminal.orm.relationship import multi_relationship"
                    )
        for col_name, col in field_properties_dict.items():
            if not col.required and col.type:
                init_strings.append(
                    f"""{TAB}{col_name}: {convert_benchling_type_to_python_type(col.type).__name__} | None = None,"""
                )
        init_strings.append("):")
        for col_name in field_properties_dict.keys():
            init_strings.append(f"{TAB}self.{col_name} = {col_name}")
        if len(dropdowns) > 0:
            import_strings.append(f"from ..dropdowns import {', '.join(dropdowns)}")
        for col_name, col in field_properties_dict.items():
            if col.dropdown_link:
                init_strings.append(
                    TAB
                    + dropdown_name_to_classname_map[col.dropdown_link]
                    + f".validate({col_name})"
                )

        import_string = "\n".join(list(set(import_strings)))
        columns_string = "\n".join(column_strings)
        relationship_string = "\n".join(relationship_strings)
        init_string = (
            f"\n{TAB}".join(init_strings) if len(field_properties_dict) > 0 else ""
        )
        schema_content = f"""{import_string}


class {schema_name}(BaseResultsModel):
    __schema_properties__ = {schema_properties.__repr__()}

{columns_string}

{relationship_string}

{init_string}
"""

        with open(write_path / file_name, "w") as file:
            file.write(schema_content)

    with open(write_path / "__init__.py", "w") as file:
        file.write("\n".join(init_file_imports))
    print(
        f"[green]Generated {write_path / '__init__.py'} with {len(results_schemas)} entity schema imports."
    )
