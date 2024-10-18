from unittest.mock import Mock, patch

from benchling_sdk.models import Dropdown

from liminal.base.base_dropdown import BaseDropdown
from liminal.dropdowns.compare import compare_dropdowns
from liminal.dropdowns.operations import (
    ArchiveDropdown,
    ArchiveDropdownOption,
    CreateDropdown,
    CreateDropdownOption,
    ReorderDropdownOptions,
    UnarchiveDropdown,
)


class TestDropdownCompare:
    def test_create_dropdown(self, mock_benchling_dropdown: type[BaseDropdown]) -> None:
        with (
            patch(
                "liminal.dropdowns.compare.get_benchling_dropdowns_dict"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.base.base_dropdown.BaseDropdown.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_benchling_entity_schemas.return_value = {}
            mock_get_all_subclasses.return_value = [mock_benchling_dropdown]
            ops = compare_dropdowns(mock_benchling_sdk)
            assert len(ops["ExampleDropdown"]) == 1
            assert isinstance(ops["ExampleDropdown"][0].op, CreateDropdown)
            assert ops["ExampleDropdown"][0].op.dropdown_name == "Example Dropdown"

    def test_unarchive_dropdown(
        self,
        mock_benchling_dropdowns_archived: dict[str, Dropdown],
        mock_benchling_dropdown: type[BaseDropdown],
    ) -> None:
        with (
            patch(
                "liminal.dropdowns.compare.get_benchling_dropdowns_dict"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.base.base_dropdown.BaseDropdown.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_benchling_entity_schemas.return_value = (
                mock_benchling_dropdowns_archived
            )
            mock_get_all_subclasses.return_value = [mock_benchling_dropdown]
            ops = compare_dropdowns(mock_benchling_sdk)
            assert len(ops["ExampleDropdown"]) == 3
            assert isinstance(ops["ExampleDropdown"][0].op, UnarchiveDropdown)
            assert isinstance(ops["ExampleDropdown"][1].op, CreateDropdownOption)
            assert isinstance(ops["ExampleDropdown"][2].op, CreateDropdownOption)
            assert ops["ExampleDropdown"][0].op.dropdown_name == "Example Dropdown"

    def test_archive_dropdown(
        self,
        mock_benchling_dropdowns: dict[str, Dropdown],
        mock_benchling_dropdown: type[BaseDropdown],
    ) -> None:
        with (
            patch(
                "liminal.dropdowns.compare.get_benchling_dropdowns_dict"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.base.base_dropdown.BaseDropdown.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_benchling_entity_schemas.return_value = mock_benchling_dropdowns
            mock_get_all_subclasses.return_value = [mock_benchling_dropdown]
            ops = compare_dropdowns(mock_benchling_sdk)
            assert len(ops["Archive"]) == 1
            assert isinstance(ops["Archive"][0].op, ArchiveDropdown)
            assert ops["Archive"][0].op.dropdown_name == "False Example Dropdown"

    def test_update_dropdown_options_archive_option(
        self,
        mock_benchling_dropdowns: dict[str, Dropdown],
        mock_benchling_dropdown: type[BaseDropdown],
        mock_false_benchling_dropdown_1: type[BaseDropdown],
    ) -> None:
        with (
            patch(
                "liminal.dropdowns.compare.get_benchling_dropdowns_dict"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.base.base_dropdown.BaseDropdown.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_benchling_entity_schemas.return_value = mock_benchling_dropdowns
            mock_get_all_subclasses.return_value = [
                mock_benchling_dropdown,
                mock_false_benchling_dropdown_1,
            ]
            ops = compare_dropdowns(mock_benchling_sdk)
            assert len(ops["FalseExampleDropdown"]) == 1
            assert isinstance(ops["FalseExampleDropdown"][0].op, ArchiveDropdownOption)
            assert (
                ops["FalseExampleDropdown"][0].op.dropdown_name
                == "False Example Dropdown"
            )

    def test_update_dropdown_options_create_option(
        self,
        mock_benchling_dropdowns: dict[str, Dropdown],
        mock_benchling_dropdown: type[BaseDropdown],
        mock_false_benchling_dropdown_3: type[BaseDropdown],
    ) -> None:
        with (
            patch(
                "liminal.dropdowns.compare.get_benchling_dropdowns_dict"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.base.base_dropdown.BaseDropdown.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_benchling_entity_schemas.return_value = mock_benchling_dropdowns
            mock_get_all_subclasses.return_value = [
                mock_benchling_dropdown,
                mock_false_benchling_dropdown_3,
            ]
            ops = compare_dropdowns(mock_benchling_sdk)
            assert len(ops["FalseExampleDropdown"]) == 1
            assert isinstance(ops["FalseExampleDropdown"][0].op, CreateDropdownOption)
            assert (
                ops["FalseExampleDropdown"][0].op.dropdown_name
                == "False Example Dropdown"
            )

    def test_update_dropdown_options_reorder(
        self,
        mock_benchling_dropdowns: dict[str, Dropdown],
        mock_benchling_dropdown: type[BaseDropdown],
        mock_false_benchling_dropdown_reorder: type[BaseDropdown],
    ) -> None:
        with (
            patch(
                "liminal.dropdowns.compare.get_benchling_dropdowns_dict"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.base.base_dropdown.BaseDropdown.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_benchling_entity_schemas.return_value = mock_benchling_dropdowns
            mock_get_all_subclasses.return_value = [
                mock_benchling_dropdown,
                mock_false_benchling_dropdown_reorder,
            ]
            ops = compare_dropdowns(mock_benchling_sdk)
            assert len(ops["FalseExampleDropdown"]) == 1
            assert isinstance(ops["FalseExampleDropdown"][0].op, ReorderDropdownOptions)
            assert (
                ops["FalseExampleDropdown"][0].op.dropdown_name
                == "False Example Dropdown"
            )

    def test_update_dropdown_options_complex(
        self,
        mock_benchling_dropdowns: dict[str, Dropdown],
        mock_benchling_dropdown: type[BaseDropdown],
        mock_false_benchling_dropdown_complex: type[BaseDropdown],
    ) -> None:
        with (
            patch(
                "liminal.dropdowns.compare.get_benchling_dropdowns_dict"
            ) as mock_get_benchling_entity_schemas,
            patch(
                "liminal.base.base_dropdown.BaseDropdown.get_all_subclasses"
            ) as mock_get_all_subclasses,
        ):
            mock_benchling_sdk = Mock()
            mock_get_benchling_entity_schemas.return_value = mock_benchling_dropdowns
            mock_get_all_subclasses.return_value = [
                mock_benchling_dropdown,
                mock_false_benchling_dropdown_complex,
            ]
            ops = compare_dropdowns(mock_benchling_sdk)
            assert len(ops["FalseExampleDropdown"]) == 2
            assert isinstance(ops["FalseExampleDropdown"][0].op, CreateDropdownOption)
            assert isinstance(ops["FalseExampleDropdown"][1].op, ReorderDropdownOptions)
            assert (
                ops["FalseExampleDropdown"][0].op.dropdown_name
                == "False Example Dropdown"
            )
