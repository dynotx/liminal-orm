from datetime import datetime
from pathlib import Path

import pytest
from benchling_sdk.models import ArchiveRecord, Dropdown, DropdownOption
from sqlalchemy import Column as SqlColumn

from liminal.base.base_dropdown import BaseDropdown
from liminal.base.properties.base_field_properties import BaseFieldProperties as Props
from liminal.enums import BenchlingEntityType
from liminal.enums import BenchlingFieldType as Type
from liminal.enums.benchling_naming_strategy import BenchlingNamingStrategy
from liminal.orm.base_model import BaseModel
from liminal.orm.column import Column
from liminal.orm.schema_properties import SchemaProperties

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_benchling_dropdown() -> type[BaseDropdown]:
    class ExampleDropdown(BaseDropdown):
        __benchling_name__ = "Example Dropdown"
        __allowed_values__ = ["OPTION_1", "OPTION_2"]

    return ExampleDropdown


@pytest.fixture
def mock_false_benchling_dropdown() -> type[BaseDropdown]:
    class FalseExampleDropdown(BaseDropdown):
        __benchling_name__ = "False Example Dropdown"
        __allowed_values__ = ["OPTION_1", "OPTION_2"]

    return FalseExampleDropdown


@pytest.fixture
def mock_false_benchling_dropdown_1() -> type[BaseDropdown]:
    class FalseExampleDropdown(BaseDropdown):
        __benchling_name__ = "False Example Dropdown"
        __allowed_values__ = ["OPTION_1"]

    return FalseExampleDropdown


@pytest.fixture
def mock_false_benchling_dropdown_3() -> type[BaseDropdown]:
    class FalseExampleDropdown(BaseDropdown):
        __benchling_name__ = "False Example Dropdown"
        __allowed_values__ = ["OPTION_1", "OPTION_2", "OPTION_3"]

    return FalseExampleDropdown


@pytest.fixture
def mock_false_benchling_dropdown_reorder() -> type[BaseDropdown]:
    class FalseExampleDropdown(BaseDropdown):
        __benchling_name__ = "False Example Dropdown"
        __allowed_values__ = ["OPTION_2", "OPTION_1"]

    return FalseExampleDropdown


@pytest.fixture
def mock_false_benchling_dropdown_complex() -> type[BaseDropdown]:
    class FalseExampleDropdown(BaseDropdown):
        __benchling_name__ = "False Example Dropdown"
        __allowed_values__ = ["OPTION_3", "OPTION_2", "OPTION_1"]

    return FalseExampleDropdown


@pytest.fixture
def mock_benchling_dropdowns() -> dict[str, Dropdown]:
    return {
        "Example Dropdown": Dropdown(
            name="Example Dropdown",
            archive_record=None,
            options=[
                DropdownOption(name="OPTION_1", id="1", archive_record=None),
                DropdownOption(name="OPTION_2", id="2", archive_record=None),
            ],
        ),
        "False Example Dropdown": Dropdown(
            name="False Example Dropdown",
            archive_record=None,
            options=[
                DropdownOption(name="OPTION_1", id="1", archive_record=None),
                DropdownOption(name="OPTION_2", id="2", archive_record=None),
            ],
        ),
    }


@pytest.fixture
def mock_benchling_dropdowns_archived() -> dict[str, Dropdown]:
    return {
        "Example Dropdown": Dropdown(
            name="Example Dropdown",
            archive_record=ArchiveRecord(reason="Made in error"),
            options=[
                DropdownOption(
                    name="OPTION_1",
                    id="1",
                    archive_record=ArchiveRecord(reason="Made in error"),
                ),
                DropdownOption(
                    name="OPTION_2",
                    id="2",
                    archive_record=ArchiveRecord(reason="Made in error"),
                ),
            ],
        ),
    }


@pytest.fixture
def mock_benchling_schema(
    mock_benchling_dropdown: type[BaseDropdown],
) -> list[tuple[SchemaProperties, dict[str, Props]]]:
    schema_props = SchemaProperties(
        name="Mock Entity",
        warehouse_name="mock_entity",
        prefix="MockEntity",
        entity_type=BenchlingEntityType.CUSTOM_ENTITY,
        naming_strategies=[BenchlingNamingStrategy.NEW_IDS],
    )
    fields = {
        "enum_field": Props(
            name="Enum Field",
            type=Type.DROPDOWN,
            required=False,
            is_multi=False,
            dropdown_link=mock_benchling_dropdown.__benchling_name__,
            parent_link=False,
            entity_link=None,
            tooltip=None,
            _archived=False,
        ),
        "string_field_req": Props(
            name="String Field Required",
            type=Type.TEXT,
            required=True,
            is_multi=False,
            parent_link=False,
            dropdown_link=None,
            entity_link=None,
            tooltip=None,
            _archived=False,
        ),
        "string_field_not_req": Props(
            name="String Field Not Required",
            type=Type.TEXT,
            required=False,
            is_multi=False,
            parent_link=False,
            dropdown_link=None,
            entity_link=None,
            tooltip=None,
            _archived=False,
        ),
        "string_field_tooltip": Props(
            name="String Field Not Required",
            type=Type.TEXT,
            required=False,
            is_multi=False,
            parent_link=False,
            dropdown_link=None,
            entity_link=None,
            tooltip="test tooltip",
            _archived=False,
        ),
        "float_field": Props(
            name="Float Field",
            type=Type.DECIMAL,
            required=False,
            is_multi=False,
            parent_link=False,
            dropdown_link=None,
            entity_link=None,
            tooltip=None,
            _archived=False,
        ),
        "integer_field": Props(
            name="Integer Field",
            type=Type.INTEGER,
            required=False,
            is_multi=False,
            parent_link=False,
            dropdown_link=None,
            entity_link=None,
            tooltip=None,
            _archived=False,
        ),
        "datetime_field": Props(
            name="Datetime Field",
            type=Type.DATE,
            required=False,
            is_multi=False,
            parent_link=False,
            dropdown_link=None,
            entity_link=None,
            tooltip=None,
            _archived=False,
        ),
        "list_dropdown_field": Props(
            name="List Dropdown Field",
            type=Type.DROPDOWN,
            required=False,
            is_multi=True,
            dropdown_link=mock_benchling_dropdown.__benchling_name__,
            parent_link=False,
            entity_link=None,
            tooltip=None,
            _archived=False,
        ),
        "archived_field": Props(
            name="Archived Field",
            type=Type.TEXT,
            required=False,
            is_multi=False,
            _archived=True,
        ),
        "wh_name_field_different": Props(
            name="Different Wh Name Field",
            type=Type.TEXT,
            required=False,
            is_multi=False,
            parent_link=False,
            dropdown_link=None,
            entity_link=None,
            tooltip=None,
            _archived=False,
        ),
    }
    return [(schema_props, fields)]


@pytest.fixture
def mock_benchling_schema_one(
    mock_benchling_dropdown: type[BaseDropdown],
) -> list[tuple[SchemaProperties, dict[str, Props]]]:
    schema_props = SchemaProperties(
        name="Mock Entity One",
        warehouse_name="mock_entity_one",
        prefix="MockEntityOne",
        entity_type=BenchlingEntityType.CUSTOM_ENTITY,
        naming_strategies=[BenchlingNamingStrategy.NEW_IDS],
    )
    fields = {
        "enum_field": Props(
            name="Enum Field",
            type=Type.DROPDOWN,
            required=False,
            is_multi=False,
            dropdown_link=mock_benchling_dropdown.__benchling_name__,
            _archived=False,
        ),
        "string_field_req": Props(
            name="String Field Required",
            type=Type.TEXT,
            required=True,
            is_multi=False,
            _archived=False,
        ),
        "string_field_not_req": Props(
            name="String Field Not Required",
            type=Type.TEXT,
            required=False,
            is_multi=False,
            _archived=False,
        ),
        "float_field": Props(
            name="Float Field",
            type=Type.DECIMAL,
            required=False,
            is_multi=False,
            _archived=False,
        ),
        "integer_field": Props(
            name="Integer Field",
            type=Type.INTEGER,
            required=False,
            is_multi=False,
            _archived=False,
        ),
        "datetime_field": Props(
            name="Datetime Field",
            type=Type.DATE,
            required=False,
            is_multi=False,
            _archived=False,
        ),
        "list_dropdown_field": Props(
            name="List Dropdown Field",
            type=Type.DROPDOWN,
            required=False,
            is_multi=True,
            dropdown_link=mock_benchling_dropdown.__benchling_name__,
            _archived=False,
        ),
    }
    return [(schema_props, fields)]


@pytest.fixture
def mock_benchling_schema_archived() -> list[tuple[SchemaProperties, dict[str, Props]]]:
    schema_props = SchemaProperties(
        name="Mock Entity Small",
        warehouse_name="mock_entity_small",
        prefix="MockEntitySmall",
        entity_type=BenchlingEntityType.CUSTOM_ENTITY,
        naming_strategies=[BenchlingNamingStrategy.NEW_IDS],
        _archived=True,
    )
    fields = {
        "string_field_req": Props(
            name="String Field Required",
            type=Type.TEXT,
            required=True,
            parent_link=False,
            is_multi=False,
            tooltip=None,
            dropdown_link=None,
            entity_link=None,
            _archived=False,
        ),
        "string_field_req_2": Props(
            name="String Field Required 2",
            type=Type.TEXT,
            required=True,
            parent_link=False,
            is_multi=False,
            _archived=False,
        ),
    }
    return [(schema_props, fields)]


@pytest.fixture
def mock_benchling_subclass(mock_benchling_dropdown) -> list[type[BaseModel]]:  # type: ignore[no-untyped-def]
    class MockEntity(BaseModel):
        __schema_properties__ = SchemaProperties(
            name="Mock Entity",
            warehouse_name="mock_entity",
            prefix="MockEntity",
            entity_type=BenchlingEntityType.CUSTOM_ENTITY,
            naming_strategies=[BenchlingNamingStrategy.NEW_IDS],
        )
        enum_field: SqlColumn = Column(
            name="Enum Field",
            type=Type.DROPDOWN,
            required=False,
            is_multi=False,
            dropdown=mock_benchling_dropdown,
        )
        string_field_req: SqlColumn = Column(
            name="String Field Required", type=Type.TEXT, required=True, is_multi=False
        )
        string_field_not_req: SqlColumn = Column(
            name="String Field Not Required",
            type=Type.TEXT,
            required=False,
            is_multi=False,
        )
        string_field_tooltip: SqlColumn = Column(
            name="String Field Not Required",
            type=Type.TEXT,
            required=False,
            is_multi=False,
            tooltip="test tooltip",
        )
        float_field: SqlColumn = Column(
            name="Float Field", type=Type.DECIMAL, required=False, is_multi=False
        )
        integer_field: SqlColumn = Column(
            name="Integer Field", type=Type.INTEGER, required=False, is_multi=False
        )
        datetime_field: SqlColumn = Column(
            name="Datetime Field", type=Type.DATE, required=False, is_multi=False
        )
        list_dropdown_field: SqlColumn = Column(
            name="List Dropdown Field",
            type=Type.DROPDOWN,
            required=False,
            is_multi=True,
            dropdown=mock_benchling_dropdown,
        )
        archived_field: SqlColumn = Column(
            name="Archived Field",
            type=Type.TEXT,
            required=False,
            is_multi=False,
            _archived=True,
        )
        different_wh_name_field: SqlColumn = Column(
            name="Different Wh Name Field",
            type=Type.TEXT,
            required=False,
            is_multi=False,
            _warehouse_name="wh_name_field_different",
        )

        def __init__(
            self,
            enum_field: str,
            string_field_req: str,
            string_field_not_req: str,
            float_field: float,
            integer_field: int,
            datetime_field: datetime,
            list_dropdown_field: list[str],
        ) -> None:
            self.enum_field = enum_field
            self.string_field_req = string_field_req
            self.string_field_not_req = string_field_not_req
            self.float_field = float_field
            self.integer_field = integer_field
            self.datetime_field = datetime_field
            self.list_dropdown_field = list_dropdown_field

    return [MockEntity]  # type: ignore[type-abstract]


@pytest.fixture
def mock_benchling_subclass_small() -> list[type[BaseModel]]:
    class MockEntitySmall(BaseModel):
        __schema_properties__ = SchemaProperties(
            name="Mock Entity Small",
            warehouse_name="mock_entity_small",
            prefix="MockEntitySmall",
            entity_type=BenchlingEntityType.CUSTOM_ENTITY,
            naming_strategies=[BenchlingNamingStrategy.NEW_IDS],
        )
        string_field_req: SqlColumn = Column(
            name="String Field Required", type=Type.TEXT, required=True, is_multi=False
        )

    return [MockEntitySmall]  # type: ignore[type-abstract]


@pytest.fixture
def mock_benchling_subclasses(mock_benchling_dropdown) -> list[type[BaseModel]]:  # type: ignore[no-untyped-def]
    class MockEntityTwo(BaseModel):
        __schema_properties__ = SchemaProperties(
            name="Mock Entity Two",
            warehouse_name="mock_entity_two_wh",
            prefix="MockEntityTwo",
            entity_type=BenchlingEntityType.CUSTOM_ENTITY,
            naming_strategies=[BenchlingNamingStrategy.NEW_IDS],
        )
        parent_link_field: SqlColumn = Column(
            name="Parent Link Field",
            type=Type.ENTITY_LINK,
            required=False,
            entity_link="mock_entity_one",
            parent_link=True,
        )

        def __init__(
            self,
            parent_link_field: str | None = None,
        ) -> None:
            self.parent_link_field = parent_link_field

    class MockEntityOne(BaseModel):
        __schema_properties__ = SchemaProperties(
            name="Mock Entity One",
            warehouse_name="mock_entity_one",
            prefix="MockEntityOne",
            entity_type=BenchlingEntityType.CUSTOM_ENTITY,
            naming_strategies=[BenchlingNamingStrategy.NEW_IDS],
        )
        enum_field: SqlColumn = Column(
            name="Enum Field",
            type=Type.DROPDOWN,
            required=False,
            is_multi=False,
            dropdown=mock_benchling_dropdown,
        )
        string_field_req: SqlColumn = Column(
            name="String Field Required", type=Type.TEXT, required=True, is_multi=False
        )
        string_field_not_req: SqlColumn = Column(
            name="String Field Not Required",
            type=Type.TEXT,
            required=False,
            is_multi=False,
        )
        float_field: SqlColumn = Column(
            name="Float Field", type=Type.DECIMAL, required=False, is_multi=False
        )
        integer_field: SqlColumn = Column(
            name="Integer Field", type=Type.INTEGER, required=False, is_multi=False
        )
        datetime_field: SqlColumn = Column(
            name="Datetime Field", type=Type.DATE, required=False, is_multi=False
        )
        list_dropdown_field: SqlColumn = Column(
            name="List Dropdown Field",
            type=Type.DROPDOWN,
            required=False,
            is_multi=True,
            dropdown=mock_benchling_dropdown,
        )
        entity_link_field: SqlColumn = Column(
            name="Entity Link Field",
            type=Type.ENTITY_LINK,
            required=False,
            is_multi=False,
            entity_link="mock_entity_two_wh",
        )

        def __init__(
            self,
            enum_field: str,
            string_field_req: str,
            string_field_not_req: str,
            float_field: float,
            integer_field: int,
            datetime_field: datetime,
            list_dropdown_field: list[str],
        ) -> None:
            self.enum_field = enum_field
            self.string_field_req = string_field_req
            self.string_field_not_req = string_field_not_req
            self.float_field = float_field
            self.integer_field = integer_field
            self.datetime_field = datetime_field
            self.list_dropdown_field = list_dropdown_field

    return [MockEntityOne, MockEntityTwo]  # type: ignore[type-abstract]
