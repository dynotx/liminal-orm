import shutil
from pathlib import Path

from rich import print

from liminal.base.base_dropdown import BaseDropdown
from liminal.connection.benchling_service import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdowns_dict
from liminal.entity_schemas.utils import get_converted_tag_schemas
from liminal.enums import BenchlingEntityType, BenchlingFieldType
from liminal.mappers import convert_benchling_type_to_python_type
from liminal.orm.name_template import NameTemplate
from liminal.utils import to_pascal_case, to_snake_case


def get_entity_mixin(entity_type: BenchlingEntityType) -> str:
    type_to_mixin_map = {
        BenchlingEntityType.ENTRY: "EntryMixin",
        BenchlingEntityType.MIXTURE: "MixtureMixin",
        BenchlingEntityType.MOLECULE: "MoleculeMixin",
        BenchlingEntityType.CUSTOM_ENTITY: "CustomEntityMixin",
        BenchlingEntityType.DNA_SEQUENCE: "DnaSequenceMixin",
        BenchlingEntityType.DNA_OLIGO: "DnaOligoMixin",
        BenchlingEntityType.RNA_OLIGO: "RnaOligoMixin",
        BenchlingEntityType.RNA_SEQUENCE: "RnaSequenceMixin",
        BenchlingEntityType.AA_SEQUENCE: "AaSequenceMixin",
    }
    if entity_type not in type_to_mixin_map:
        raise ValueError(f"Unknown entity type: {entity_type}")
    return type_to_mixin_map[entity_type]


def get_file_subdirectory(entity_type: BenchlingEntityType) -> str:
    type_to_subdir_map = {
        BenchlingEntityType.CUSTOM_ENTITY: "custom_entities",
        BenchlingEntityType.DNA_SEQUENCE: "dna_sequences",
        BenchlingEntityType.DNA_OLIGO: "dna_oligos",
        BenchlingEntityType.RNA_OLIGO: "rna_oligos",
        BenchlingEntityType.RNA_SEQUENCE: "rna_sequences",
        BenchlingEntityType.AA_SEQUENCE: "aa_sequences",
        BenchlingEntityType.ENTRY: "entries",
        BenchlingEntityType.MIXTURE: "mixtures",
        BenchlingEntityType.MOLECULE: "molecules",
    }
    if entity_type not in type_to_subdir_map:
        raise ValueError(f"Unknown entity type: {entity_type}")
    return type_to_subdir_map[entity_type]


TAB = "    "


def generate_all_entity_schema_files(
    benchling_service: BenchlingService, write_path: Path, overwrite: bool = False
) -> None:
    """Generate all entity schema files from your Benchling tenant and writes to the given entity_schemas/ path.
    This is used to initialize your code for Liminal and transfer the information from your Benchling tenant to your local codebase.

    Parameters
    ----------
    benchling_service : BenchlingService
        The Benchling service object that is connected to a specified Benchling tenant.
    write_path : Path
        The path to write the generated files to. entity_schemas/ directory will be created within this path.
    overwrite : bool
        Whether to overwrite existing files in the entity_schemas/ directory.
    """
    write_path = write_path / "entity_schemas"
    if write_path.exists() and overwrite:
        shutil.rmtree(write_path)
        print(f"[dim]Removed directory: {write_path}")
    if not write_path.exists():
        write_path.mkdir(parents=True, exist_ok=True)
        print(f"[green]Created directory: {write_path}")

    models = get_converted_tag_schemas(benchling_service)
    has_date = False
    subdirectory_map: dict[str, list[tuple[str, str]]] = {}
    subdirectory_num_files_written: dict[str, int] = {}
    dropdown_name_to_classname_map = _get_dropdown_name_to_classname_map(
        benchling_service
    )
    wh_name_to_classname: dict[str, str] = {
        sp.warehouse_name: to_pascal_case(sp.name) for sp, _, _ in models
    }

    for schema_properties, name_template, columns in models:
        classname = to_pascal_case(schema_properties.name)

    for schema_properties, name_template, columns in models:
        classname = to_pascal_case(schema_properties.name)
        filename = to_snake_case(schema_properties.name) + ".py"
        columns = {key: columns[key] for key in columns}
        import_strings = [
            "from sqlalchemy import Column as SqlColumn",
            "from liminal.orm.column import Column",
            "from liminal.orm.base_model import BaseModel",
            "from liminal.orm.schema_properties import SchemaProperties",
            f"from liminal.orm.mixins import {get_entity_mixin(schema_properties.entity_type)}",
        ]
        import_strings.append(
            "from liminal.enums import BenchlingEntityType, BenchlingFieldType"
        )
        if "naming_strategies" in schema_properties.model_dump(
            exclude_unset=True, exclude_defaults=True
        ):
            import_strings[-1] = import_strings[-1] + ", BenchlingNamingStrategy"

        init_strings = [f"{TAB}def __init__(", f"{TAB}self,"]
        column_strings = []
        dropdowns = []
        relationship_strings = []
        for col_name, col in columns.items():
            column_props = col.column_dump()
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
            column_string = f"""{TAB}{col_name}: SqlColumn = Column({column_props_string.rstrip(",")})"""
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
                        f"""{TAB}{col_name}_entity = single_relationship("{wh_name_to_classname[col.entity_link]}", {col_name})"""
                    )
                    import_strings.append(
                        "from liminal.orm.relationship import single_relationship"
                    )
                else:
                    relationship_strings.append(
                        f"""{TAB}{col_name}_entities = multi_relationship("{wh_name_to_classname[col.entity_link]}", {col_name})"""
                    )
                    import_strings.append(
                        "from liminal.orm.relationship import multi_relationship"
                    )
        for col_name, col in columns.items():
            if not col.required and col.type:
                init_strings.append(
                    f"""{TAB}{col_name}: {convert_benchling_type_to_python_type(col.type).__name__} | None = None,"""
                )
        init_strings.append("):")
        for col_name in columns.keys():
            init_strings.append(f"{TAB}self.{col_name} = {col_name}")
        if len(dropdowns) > 0:
            import_strings.append(f"from ...dropdowns import {', '.join(dropdowns)}")
        if name_template != NameTemplate():
            import_strings.append("from liminal.orm.name_template import NameTemplate")
            parts_imports = [
                f"from liminal.orm.name_template_parts import {', '.join(set([part.__class__.__name__ for part in name_template.parts]))}"
            ]
            import_strings.extend(parts_imports)
        for col_name, col in columns.items():
            if col.dropdown_link:
                init_strings.append(
                    TAB
                    + dropdown_name_to_classname_map[col.dropdown_link]
                    + f".validate({col_name})"
                )

        columns_string = "\n".join(column_strings)
        relationship_string = "\n".join(relationship_strings)
        import_string = "\n".join(list(set(import_strings)))
        init_string = f"\n{TAB}".join(init_strings) if len(columns) > 0 else ""
        full_content = f"""{import_string}


class {classname}(BaseModel, {get_entity_mixin(schema_properties.entity_type)}):
    __schema_properties__ = {schema_properties.__repr__()}
    {f"__name_template__ = {name_template.__repr__()}" if name_template != NameTemplate() else ""}

{columns_string}

{relationship_string}

{init_string}

"""
        subdirectory_name = get_file_subdirectory(schema_properties.entity_type)
        write_directory_path = write_path / subdirectory_name
        if not subdirectory_map.get(subdirectory_name):
            subdirectory_map[subdirectory_name] = []
            subdirectory_num_files_written[subdirectory_name] = 0
        subdirectory_map[subdirectory_name].append((filename, classname))
        write_directory_path.mkdir(exist_ok=True)
        if overwrite or not (write_directory_path / filename).exists():
            with open(write_directory_path / filename, "w") as file:
                file.write(full_content)
            subdirectory_num_files_written[subdirectory_name] += 1

    for subdir, names in subdirectory_map.items():
        if subdirectory_num_files_written[subdir] > 0:
            init_content = (
                "\n".join(
                    f"from .{filename[:-3]} import {classname}"
                    for filename, classname in names
                )
                + "\n"
            )
            with open(write_path / subdir / "__init__.py", "w") as file:
                file.write(init_content)

    if sum(subdirectory_num_files_written.values()) > 0:
        with open(write_path / "__init__.py", "w") as file:
            file.write(
                "\n".join(
                    f"from .{subdir} import * # noqa"
                    for subdir in subdirectory_map.keys()
                )
                + "\n"
            )
            print(
                f"[green]Generated {write_path / '__init__.py'} with {sum(subdirectory_num_files_written.values())} entity schema files written."
            )
    else:
        print(
            "[green dim]No new entity schema files to be written. If you want to overwrite existing files, run with -o flag."
        )


def _get_dropdown_name_to_classname_map(
    benchling_service: BenchlingService,
) -> dict[str, str]:
    """Gets the dropdown name to classname map.
    If there are dropdowns imported, use BenchlingDropdown.get_all_subclasses()
    Otherwise, it will query for Benchling dropdowns and use those.
    """
    if len(BaseDropdown.get_all_subclasses()) > 0:
        return {
            dropdown.__benchling_name__: dropdown.__name__
            for dropdown in BaseDropdown.get_all_subclasses()
        }
    benchling_dropdowns = get_benchling_dropdowns_dict(benchling_service)
    return {
        dropdown_name: to_pascal_case(dropdown_name)
        for dropdown_name in benchling_dropdowns.keys()
    }
