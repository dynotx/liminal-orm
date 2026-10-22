from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from benchling_sdk.errors import BenchlingError

from liminal.connection.benchling_connection import BenchlingConnection
from liminal.connection.benchling_service import (
    AmbiguousRegistryError,
    BenchlingService,
)
from liminal.dropdowns.api import list_dropdowns
from liminal.dropdowns.operations import CreateDropdown
from liminal.dropdowns.utils import get_benchling_dropdowns_dict
from liminal.entity_schemas.api import list_entity_schemas
from liminal.entity_schemas.entity_schema_models import EntitySchemaModel
from liminal.enums import BenchlingEntitySchemaEndpointType
from liminal.results_schemas.api import list_results_schemas

MAIN = SimpleNamespace(id="src_main", name="Main", owner=SimpleNamespace(id="ent_main"))
OTHER = SimpleNamespace(
    id="src_other", name="Other", owner=SimpleNamespace(id="ent_other")
)


_TENANT_REGISTRIES: list[Any] = []


@pytest.fixture(autouse=True)
def _fake_registry_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """Serves the v2 registry list and the v3 registry lookup from _TENANT_REGISTRIES."""
    monkeypatch.setattr(
        BenchlingService,
        "registry",
        property(lambda _self: SimpleNamespace(registries=lambda: _TENANT_REGISTRIES)),
    )

    def fake_get(_service: Any, url: str) -> Any:
        registry_id = url.rsplit("/", 1)[-1]
        for r in _TENANT_REGISTRIES:
            if r.id == registry_id:
                return SimpleNamespace(parsed={"id": r.id, "owner": {"id": r.owner.id}})
        raise BenchlingError(
            status_code=404, headers={}, json=None, content=None, parsed=None
        )

    monkeypatch.setattr("liminal.utils.rate_limited_get_v3", fake_get)


def _service(registries: list[Any], registry_id: str | None = None) -> BenchlingService:
    _TENANT_REGISTRIES[:] = registries
    connection = BenchlingConnection(
        tenant_name="test-tenant",
        api_client_id="test-id",
        api_client_secret="test-secret",
        registry_id=registry_id,
    )
    return BenchlingService(connection, use_api=False)


def _schema(system_name: str, registry: Any) -> dict[str, Any]:
    return {
        "id": f"ts_{system_name}_{registry.id}",
        "systemName": system_name,
        "registry": {"id": registry.id},
        "organization": {"id": registry.owner.id},
    }


def _dropdown(name: str, registry: Any) -> dict[str, Any]:
    return {
        "id": f"sfs_{name}_{registry.id}",
        "name": name,
        "registry": {"id": registry.id},
        "archived": False,
        "options": [],
    }


class TestRegistryResolution:
    def test_single_registry_without_name_is_unchanged(self) -> None:
        service = _service([MAIN])
        assert service.registry_id == "src_main"
        assert service.organization_id == "ent_main"
        assert not service._is_registry_scoped
        assert not service._has_unresolved_registry

    def test_several_registries_without_name_raise_clear_error(self) -> None:
        service = _service([MAIN, OTHER])
        assert service._has_unresolved_registry
        with pytest.raises(ValueError, match="Set registry_id"):
            service.registry_id
        with pytest.raises(ValueError, match="Set registry_id"):
            service.organization_id

    def test_registry_id_selects_registry_and_owner(self) -> None:
        service = _service([MAIN, OTHER], registry_id="src_other")
        assert service.registry_id == "src_other"
        assert service.organization_id == "ent_other"
        assert not service._has_unresolved_registry

    def test_unknown_registry_id_raises(self) -> None:
        service = _service([MAIN, OTHER], registry_id="src_missing")
        with pytest.raises(ValueError, match="registry src_missing not found"):
            service.registry_id

    def test_registry_id_is_fetched_from_v3(self) -> None:
        connection = BenchlingConnection(
            tenant_name="test-tenant",
            api_client_id="test-id",
            api_client_secret="test-secret",
            registry_id="src_other",
        )
        service = BenchlingService(connection, use_api=False)
        response = SimpleNamespace(
            parsed={"id": "src_other", "owner": {"id": "ent_other"}}
        )
        with patch("liminal.utils.rate_limited_get_v3", return_value=response) as get:
            assert service.organization_id == "ent_other"
            assert service.registry_id == "src_other"
        get.assert_called_once_with(service, "/api/v3/registry/src_other")


class TestScopeFilter:
    def test_unscoped_keeps_every_record(self) -> None:
        service = _service([MAIN, OTHER])
        assert service._is_in_registry_scope(_schema("plasmid", OTHER))
        assert service._is_in_registry_scope({"id": "no_owner"})

    def test_scoped_matches_registry_then_organization(self) -> None:
        service = _service([MAIN, OTHER], registry_id="src_main")
        assert service._is_in_registry_scope(_schema("plasmid", MAIN))
        assert not service._is_in_registry_scope(_schema("plasmid", OTHER))
        assert service._is_in_registry_scope({"organization": {"id": "ent_main"}})
        assert not service._is_in_registry_scope({"organization": {"id": "ent_other"}})
        assert not service._is_in_registry_scope({"id": "no_owner"})


class TestListFunctions:
    def test_entity_schemas_are_scoped(self) -> None:
        records = [_schema("plasmid", MAIN), _schema("plasmid", OTHER)]
        first_endpoint = next(iter(BenchlingEntitySchemaEndpointType))

        def fake_list(_service: Any, endpoint: Any, _include_archived: bool) -> list:
            return records if endpoint == first_endpoint else []

        with patch(
            "liminal.entity_schemas.api._list_entity_schemas_for_endpoint",
            side_effect=fake_list,
        ):
            scoped = list_entity_schemas(
                _service([MAIN, OTHER], registry_id="src_main")
            )
            unscoped = list_entity_schemas(_service([MAIN, OTHER]))

        assert [s["registry"]["id"] for s in scoped] == ["src_main"]
        assert len(unscoped) == 2

    def test_dropdowns_are_scoped(self) -> None:
        records = [_dropdown("Species", MAIN), _dropdown("Species", OTHER)]
        with patch("liminal.dropdowns.api.list_all_items_v3", return_value=records):
            scoped = list_dropdowns(_service([MAIN, OTHER], registry_id="src_other"))
        assert [d["registry"]["id"] for d in scoped] == ["src_other"]

    def test_results_schemas_are_scoped_by_organization(self) -> None:
        records = [
            {
                "id": "assaysch_1",
                "systemName": "assay",
                "organization": {"id": "ent_main"},
            },
            {
                "id": "assaysch_2",
                "systemName": "assay",
                "organization": {"id": "ent_other"},
            },
        ]
        with patch(
            "liminal.results_schemas.api.list_all_items_v3", return_value=records
        ):
            scoped = list_results_schemas(
                _service([MAIN, OTHER], registry_id="src_main")
            )
        assert [s["id"] for s in scoped] == ["assaysch_1"]


class TestAmbiguousLookups:
    @pytest.fixture(autouse=True)
    def _skip_field_fetch(self) -> Any:
        with (
            patch(
                "liminal.entity_schemas.entity_schema_models.attach_entity_schema_field_definitions",
                side_effect=lambda _service, schema: schema,
            ),
            patch.object(EntitySchemaModel, "model_validate", side_effect=lambda s: s),
        ):
            yield

    def test_repeated_name_on_unresolved_tenant_raises(self) -> None:
        schemas = [_schema("plasmid", MAIN), _schema("plasmid", OTHER)]
        with pytest.raises(AmbiguousRegistryError, match="2 entity schemas"):
            EntitySchemaModel.get_one(_service([MAIN, OTHER]), "plasmid", schemas)

    def test_repeated_name_on_single_registry_tenant_is_unchanged(self) -> None:
        schemas = [_schema("plasmid", MAIN), _schema("plasmid", MAIN)]
        schema: Any = EntitySchemaModel.get_one(_service([MAIN]), "plasmid", schemas)
        assert schema is schemas[0]

    def test_dropdowns_dict_raises_on_shared_names(self) -> None:
        records = [_dropdown("Species", MAIN), _dropdown("Species", OTHER)]
        with (
            patch(
                "liminal.dropdowns.utils.list_dropdowns_with_options",
                return_value=records,
            ),
            pytest.raises(AmbiguousRegistryError, match="Species"),
        ):
            get_benchling_dropdowns_dict(_service([MAIN, OTHER]))


class TestCreateValidation:
    def test_create_dropdown_without_registry_fails_before_writing(self) -> None:
        with (
            patch(
                "liminal.dropdowns.operations.dropdown_exists_in_benchling",
                return_value=False,
            ),
            pytest.raises(ValueError, match="choose where to create this dropdown"),
        ):
            CreateDropdown("Species", ["Human"]).validate(_service([MAIN, OTHER]))

    def test_create_dropdown_validation_is_unchanged_for_single_registry(self) -> None:
        with patch(
            "liminal.dropdowns.operations.dropdown_exists_in_benchling"
        ) as exists:
            CreateDropdown("Species", ["Human"]).validate(_service([MAIN]))
        exists.assert_not_called()

    def test_unarchiving_existing_dropdown_still_validates(self) -> None:
        with patch(
            "liminal.dropdowns.operations.dropdown_exists_in_benchling",
            return_value=True,
        ):
            CreateDropdown("Species", ["Human"]).validate(_service([MAIN, OTHER]))
