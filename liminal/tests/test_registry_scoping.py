from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from liminal.connection.benchling_connection import BenchlingConnection
from liminal.connection.benchling_service import BenchlingService
from liminal.dropdowns.api import list_dropdowns
from liminal.entity_schemas.api import list_entity_schemas
from liminal.enums import BenchlingEntitySchemaEndpointType
from liminal.results_schemas.api import list_results_schemas

MAIN = SimpleNamespace(id="src_main", name="Main", owner=SimpleNamespace(id="ent_main"))
OTHER = SimpleNamespace(
    id="src_other", name="Other", owner=SimpleNamespace(id="ent_other")
)


_TENANT_REGISTRIES: list[Any] = []


def _registry_page() -> Any:
    return SimpleNamespace(
        parsed={
            "items": [
                {"id": r.id, "owner": {"id": r.owner.id}} for r in _TENANT_REGISTRIES
            ]
        }
    )


@contextmanager
def _v3_api(handler: Callable[[str], list[dict[str, Any]]]) -> Iterator[None]:
    """Serves the v3 registry list from _TENANT_REGISTRIES and every other v3 list from handler."""

    def fake_get(_service: Any, url: str) -> Any:
        if url.startswith("/api/v3/registry/items"):
            return _registry_page()
        return SimpleNamespace(parsed={"items": handler(url)})

    with patch("liminal.utils.rate_limited_get_v3", side_effect=fake_get):
        yield


@pytest.fixture(autouse=True)
def _fake_registry_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """Serves the v3 registry list from _TENANT_REGISTRIES."""
    monkeypatch.setattr(
        "liminal.utils.rate_limited_get_v3",
        lambda _service, _url: _registry_page(),
    )


def _service(
    registries: list[Any], registry_id: str | None = None, use_api: bool = True
) -> BenchlingService:
    _TENANT_REGISTRIES[:] = registries
    connection = BenchlingConnection(
        tenant_name="test-tenant",
        api_client_id="test-id",
        api_client_secret="test-secret",
        registry_id=registry_id,
    )
    return BenchlingService(connection, use_api=use_api)


def _schema(system_name: str, registry: Any) -> dict[str, Any]:
    """Entity schema records carry the owning organization but no registry."""
    return {
        "id": f"ts_{system_name}_{registry.id}",
        "systemName": system_name,
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
    def test_single_registry_without_name_resolves(self) -> None:
        service = _service([MAIN])
        assert service.registry_id == "src_main"
        assert service.organization_id == "ent_main"

    def test_several_registries_without_name_fail_on_init(self) -> None:
        with pytest.raises(ValueError, match="does not allow ambiguous registries"):
            _service([MAIN, OTHER])

    def test_single_registry_with_name_is_not_ambiguous(self) -> None:
        service = _service([MAIN], registry_id="src_main")
        assert not service.has_ambiguous_registries()
        assert service.registry_id == "src_main"

    def test_several_registries_with_name_are_not_ambiguous(self) -> None:
        service = _service([MAIN, OTHER], registry_id="src_main")
        assert not service.has_ambiguous_registries()

    def test_registry_id_selects_registry_and_owner(self) -> None:
        service = _service([MAIN, OTHER], registry_id="src_other")
        assert service.registry_id == "src_other"
        assert service.organization_id == "ent_other"

    def test_unknown_registry_id_on_single_registry_raises(self) -> None:
        service = _service([MAIN], registry_id="src_missing")
        with pytest.raises(ValueError, match="registry src_missing not found"):
            service.registry_id

    def test_without_api_registries_are_not_listed_on_init(self) -> None:
        with patch("liminal.utils.rate_limited_get_v3") as get:
            _service([MAIN, OTHER], use_api=False)
        get.assert_not_called()

    def test_unknown_registry_id_raises_on_access_not_init(self) -> None:
        service = _service([MAIN, OTHER], registry_id="src_missing")
        with pytest.raises(ValueError, match="registry src_missing not found"):
            service.registry_id

    def test_registries_are_listed_once(self) -> None:
        with patch(
            "liminal.utils.rate_limited_get_v3", return_value=_registry_page()
        ) as get:
            service = _service([MAIN, OTHER], registry_id="src_other")
            service.registry_id
            service.organization_id
        get.assert_called_once()
        # The registry list rejects an archived filter.
        url = get.call_args.args[1]
        assert url.startswith("/api/v3/registry/items")
        assert "archived" not in url


class TestScopeFilter:
    def test_registry_scope_matches_registry(self) -> None:
        service = _service([MAIN, OTHER], registry_id="src_main")
        assert service.is_in_registry_scope(_dropdown("Species", MAIN))
        assert not service.is_in_registry_scope(_dropdown("Species", OTHER))
        assert not service.is_in_registry_scope(_schema("plasmid", MAIN))
        assert not service.is_in_registry_scope({"id": "no_owner"})

    def test_organization_scope_matches_organization(self) -> None:
        service = _service([MAIN, OTHER], registry_id="src_main")
        assert service.is_in_organization_scope(_schema("plasmid", MAIN))
        assert not service.is_in_organization_scope(_schema("plasmid", OTHER))
        assert not service.is_in_organization_scope({"id": "no_owner"})

    def test_single_registry_without_name_scopes_to_it(self) -> None:
        service = _service([MAIN])
        assert service.is_in_organization_scope(_schema("plasmid", MAIN))
        assert not service.is_in_organization_scope(_schema("plasmid", OTHER))


def _results_schema(registry: Any) -> dict[str, Any]:
    return {
        "id": f"assaysch_{registry.id}",
        "systemName": "assay",
        "organization": {"id": registry.owner.id},
    }


def _list_entity_schemas(service: BenchlingService) -> list[dict[str, Any]]:
    first_endpoint = next(iter(BenchlingEntitySchemaEndpointType))
    records = [_schema("plasmid", MAIN), _schema("plasmid", OTHER)]

    def handler(url: str) -> list[dict[str, Any]]:
        return records if url.startswith(f"/api/v3/{first_endpoint.value}/") else []

    with _v3_api(handler):
        return list_entity_schemas(service)


def _list_dropdowns(service: BenchlingService) -> list[dict[str, Any]]:
    records = [_dropdown("Species", MAIN), _dropdown("Species", OTHER)]
    with _v3_api(lambda _url: records):
        return list_dropdowns(service)


def _list_results_schemas(service: BenchlingService) -> list[dict[str, Any]]:
    records = [_results_schema(MAIN), _results_schema(OTHER)]
    with _v3_api(lambda _url: records):
        return list_results_schemas(service)


# Each lister returns records from both MAIN and OTHER. `owner_of` reads the scoping value off a
# record and `scope_of` gives the value a registry should produce: the registry id for dropdowns,
# the owning organization id for entity schemas and results schemas.
_LISTERS = pytest.mark.parametrize(
    "lister, owner_of, scope_of",
    [
        (
            _list_entity_schemas,
            lambda r: r["organization"]["id"],
            lambda reg: reg.owner.id,
        ),
        (_list_dropdowns, lambda r: r["registry"]["id"], lambda reg: reg.id),
        (
            _list_results_schemas,
            lambda r: r["organization"]["id"],
            lambda reg: reg.owner.id,
        ),
    ],
    ids=["entity_schemas", "dropdowns", "results_schemas"],
)


class TestListFunctions:
    @_LISTERS
    def test_one_registry_without_name_keeps_only_that_registry(
        self, lister: Callable, owner_of: Callable, scope_of: Callable
    ) -> None:
        results = lister(_service([MAIN]))
        assert [owner_of(r) for r in results] == [scope_of(MAIN)]

    @_LISTERS
    def test_two_registries_without_name_raise(
        self, lister: Callable, owner_of: Callable, scope_of: Callable
    ) -> None:
        with pytest.raises(ValueError, match="does not allow ambiguous registries"):
            lister(_service([MAIN, OTHER]))

    @_LISTERS
    def test_two_registries_with_name_keep_only_that_registry(
        self, lister: Callable, owner_of: Callable, scope_of: Callable
    ) -> None:
        results = lister(_service([MAIN, OTHER], registry_id="src_other"))
        assert [owner_of(r) for r in results] == [scope_of(OTHER)]
