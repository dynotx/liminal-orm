from typing import cast

from benchling_api_client.v2.benchling_client import BenchlingApiClient

from liminal.connection.benchling_connection import BenchlingConnection
from liminal.connection.benchling_service import BenchlingService

# The Benchling SDK defaults the per-request HTTP timeout to 10 seconds.
SDK_DEFAULT_TIMEOUT_SECONDS = 10


def _connection() -> BenchlingConnection:
    return BenchlingConnection(
        tenant_name="test-tenant",
        api_client_id="test-id",
        api_client_secret="test-secret",
    )


class TestBenchlingServiceClientDecorator:
    def test_default_timeout_is_sdk_default(self) -> None:
        service = BenchlingService(_connection(), use_db=False)
        assert service._client.get_timeout() == SDK_DEFAULT_TIMEOUT_SECONDS

    def test_client_decorator_is_forwarded_to_sdk(self) -> None:
        def raise_timeout(client: BenchlingApiClient) -> BenchlingApiClient:
            # with_timeout is typed to return the base Client but preserves the subclass.
            return cast(BenchlingApiClient, client.with_timeout(60))

        service = BenchlingService(
            _connection(), use_db=False, client_decorator=raise_timeout
        )

        assert service._client.get_timeout() == 60
