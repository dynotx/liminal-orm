from pathlib import Path

from rich import print

from liminal.connection.benchling_service import BenchlingService
from liminal.dropdowns.utils import get_benchling_dropdowns_dict
from liminal.entity_schemas.utils import get_converted_tag_schemas
from liminal.enums import BenchlingEntityType, BenchlingFieldType
from liminal.mappers import convert_benchling_type_to_python_type
from liminal.utils import pascalize, to_snake_case


def get_entity_mixin(entity_type: BenchlingEntityType) -> str:
    type_to_mixin_map = {
        BenchlingEntityType.ENTRY: "EntryMixin",
        BenchlingEntityType.MIXTURE: "MixtureMixin",
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
    }
    if entity_type not in type_to_subdir_map:
        raise ValueError(f"Unknown entity type: {entity_type}")
    return type_to_subdir_map[entity_type]


def generate_all_entity_schema_files(
    benchling_service: BenchlingService, write_path: Path
) -> None:
    write_path = write_path / "entity_schemas"
    if not write_path.exists():
        write_path.mkdir(parents=True, exist_ok=True)
        print(f"[green]Created directory: {write_path}")

    models = get_converted_tag_schemas(benchling_service)
    tab = "    "
    has_date = False
    subdirectory_map: dict[str, list[tuple[str, str]]] = {}
    benchling_dropdowns = get_benchling_dropdowns_dict(benchling_service)
    dropdown_name_to_classname_map: dict[str, str] = {
        dropdown_name: pascalize(dropdown_name)
        for dropdown_name in benchling_dropdowns.keys()
    }
    wh_name_to_classname: dict[str, str] = {
        sp.warehouse_name: pascalize(sp.name) for sp, _ in models
    }

    for schema_properties, columns in models:
        classname = pascalize(schema_properties.name)

    for schema_properties, columns in models:
        classname = pascalize(schema_properties.name)
        filename = to_snake_case(schema_properties.name) + ".py"
        columns = {key: columns[key] for key in columns}
        import_strings = [
            "from sqlalchemy import Column as SqlColumn",
            "from sqlalchemy.orm import Query, Session",
            "from liminal.orm.column import Column",
            "from liminal.orm.base_model import BaseModel",
            "from liminal.orm.schema_properties import SchemaProperties",
            "from liminal.enums import BenchlingEntityType, BenchlingFieldType, BenchlingNamingStrategy",
            "from liminal.validation import BenchlingValidator",
            f"from liminal.orm.mixins import {get_entity_mixin(schema_properties.entity_type)}",
        ]
        init_strings = [f"{tab}def __init__(", f"{tab}self,"]
        column_strings = []
        dropdowns = []
        relationship_strings = []
        for col_name, col in columns.items():
            dropdown_classname = None
            if col.dropdown_link:
                dropdown_classname = dropdown_name_to_classname_map[col.dropdown_link]
                dropdowns.append(dropdown_classname)
            column_strings.append(
                f"""{tab}{col_name}: SqlColumn = Column(name="{col.name}", type={str(col.type)}, required={col.required}{', is_multi=True' if col.is_multi else ''}{', parent_link=True' if col.parent_link else ''}{f', entity_link="{col.entity_link}"' if col.entity_link else ''}{f', dropdown={dropdown_classname}' if dropdown_classname else ''}{f', tooltip="{col.tooltip}"' if col.tooltip else ''})"""
            )
            if col.required and col.type:
                init_strings.append(
                    f"""{tab}{col_name}: {convert_benchling_type_to_python_type(col.type).__name__},"""
                )

            if col.type == BenchlingFieldType.DATE:
                if not has_date:
                    import_strings.append("from datetime import datetime")
            if (
                col.type == BenchlingFieldType.ENTITY_LINK
                and col.entity_link is not None
            ):
                if not col.is_multi:
                    relationship_strings.append(
                        f"""{tab}{col_name}_entity = single_relationship("{wh_name_to_classname[col.entity_link]}", {col_name})"""
                    )
                    import_strings.append(
                        "from liminal.orm.relationship import single_relationship"
                    )
                else:
                    relationship_strings.append(
                        f"""{tab}{col_name}_entities = multi_relationship("{wh_name_to_classname[col.entity_link]}", "{classname}", "{col_name}")"""
                    )
                    import_strings.append(
                        "from liminal.orm.relationship import multi_relationship"
                    )
        for col_name, col in columns.items():
            if not col.required and col.type:
                init_strings.append(
                    f"""{tab}{col_name}: {convert_benchling_type_to_python_type(col.type).__name__} | None = None,"""
                )
        init_strings.append("):")
        for col_name in columns.keys():
            init_strings.append(f"{tab}self.{col_name} = {col_name}")
        if len(dropdowns) > 0:
            import_strings.append(f"from ...dropdowns import {', '.join(dropdowns)}")
        for col_name, col in columns.items():
            if col.dropdown_link:
                init_strings.append(
                    tab
                    + dropdown_name_to_classname_map[col.dropdown_link]
                    + f".validate({col_name})"
                )

        columns_string = "\n".join(column_strings)
        relationship_string = "\n".join(relationship_strings)
        import_string = "\n".join(list(set(import_strings)))
        init_string = f"\n{tab}".join(init_strings) if len(columns) > 0 else ""
        functions_string = f"""
    @classmethod
    def query(self, session: Session) -> Query:
        return session.query({classname})

    def get_validators(self) -> list[BenchlingValidator]:
        return []"""

        content = f"""{import_string}


class {classname}(BaseModel, {get_entity_mixin(schema_properties.entity_type)}):
    __schema_properties__ = {schema_properties.__repr__()}

{columns_string}

{relationship_string}

{init_string}

{functions_string}
"""
        write_directory_path = write_path / get_file_subdirectory(
            schema_properties.entity_type
        )
        subdirectory_map[get_file_subdirectory(schema_properties.entity_type)] = (
            subdirectory_map.get(
                get_file_subdirectory(schema_properties.entity_type), []
            )
            + [(filename, classname)]
        )
        write_directory_path.mkdir(exist_ok=True)
        with open(write_directory_path / filename, "w") as file:
            file.write(content)

    for subdir, names in subdirectory_map.items():
        init_content = (
            "\n".join(
                f"from .{filename[:-3]} import {classname}"
                for filename, classname in names
            )
            + "\n"
        )
        with open(write_path / subdir / "__init__.py", "w") as file:
            file.write(init_content)

    with open(write_path / "__init__.py", "w") as file:
        file.write(
            "\n".join(
                f"from .{subdir} import * # noqa" for subdir in subdirectory_map.keys()
            )
            + "\n"
        )
        print(
            f"[green]Generated {write_path / '__init__.py'} with {len(models)} entity schema imports."
        )
