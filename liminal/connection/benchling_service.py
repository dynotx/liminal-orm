import logging
from typing import Any

import requests
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.benchling import Benchling
from benchling_sdk.helpers.retry_helpers import RetryStrategy
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, configure_mappers
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from liminal.connection.benchling_connection import BenchlingConnection

logger = logging.getLogger(__name__)


class BenchlingService(Benchling):
    """
    Class that creates a connection object that can be used to connect to Benchling's API, database, or internal API.
    This inherits from LiminalBenchlingService, which takes in credentials and connects the specified services.

    Parameters
    ----------
    connection: BenchlingConnection
        The connection object that contains the credentials for the Benchling tenant.
    use_api: bool
        Whether to connect to the Benchling SDK. Requires api_client_id and api_client_secret from the connection object.
    use_db: bool = False
        Whether to connect to the Benchling Postgres database. Requires warehouse_connection_string from the connection object.
    use_internal_api: bool = False
        Whether to connect to the Benchling internal API. Requires internal_api_admin_email and internal_api_admin_password from the connection object.
    """

    def __init__(
        self,
        connection: BenchlingConnection,
        use_api: bool = True,
        use_db: bool = False,
        use_internal_api: bool = False,
    ) -> None:
        self.connection = connection
        self._session: Session | None = None
        self.use_api = use_api
        self.benchling_tenant = connection.tenant_name
        if use_api:
            retry_strategy = RetryStrategy(max_tries=10)
            auth_method = ClientCredentialsOAuth2(
                client_id=connection.api_client_id,
                client_secret=connection.api_client_secret,
                token_url=f"https://{connection.tenant_name}.benchling.com/api/v2/token",
            )
            url = f"https://{connection.tenant_name}.benchling.com"
            super().__init__(
                url=url, auth_method=auth_method, retry_strategy=retry_strategy
            )
            logger.info(f"Tenant {connection.tenant_name}: Connected to Benchling API.")
        self.use_db = use_db
        if use_db:
            if connection.warehouse_connection_string:
                self.engine: Engine = create_engine(
                    connection.warehouse_connection_string
                )
                configure_mappers()
                logger.info(
                    f"Tenant {connection.tenant_name}: Connected to Benchling read-only Postgres warehouse."
                )
            else:
                raise ValueError(
                    "use_db is True but warehouse_connection_string not provided in BenchlingConnection."
                )
        self.use_internal_api = use_internal_api
        if use_internal_api:
            if (
                connection.internal_api_admin_email
                and connection.internal_api_admin_password
            ):
                csrf_token, session = self.autogenerate_auth(
                    connection.tenant_name,
                    connection.internal_api_admin_email,
                    connection.internal_api_admin_password,
                )
                self.custom_post_cookies = {
                    "session": session,
                }
                self.custom_post_headers = {
                    "X-Csrftoken": csrf_token,
                    "Referer": f"https://{connection.tenant_name}.benchling.com/",
                    "Content-Type": "application/json",
                }
                logger.info(
                    f"Tenant {connection.tenant_name}: Connected to Benchling internal API."
                )
            else:
                raise ValueError(
                    "use_internal_api is True but internal_api_admin_email and internal_api_admin_password not provided in BenchlingConnection."
                )

    @property
    def session(self) -> Session:
        """Returns a session made by the sessionmaker"""
        return self.get_session()

    @property
    def registry_id(self) -> str:
        # This assumes there is only one registry (which has always been the case at DynoTx)
        registries = self.registry.registries()
        assert len(registries) == 1
        return registries[0].id

    def __enter__(self) -> Session:
        self._session = self.get_session()
        return self._session

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_val:
            self._session.rollback()
        self._session.close()
        self._session = None

    def get_session(self) -> Session:
        """Provides a wrapper around getting sessions which enables batch inserts"""
        if not self.use_db:
            raise ValueError(
                "Database connection not initialized! Initialize with 'use_db = True'"
            )
        session = Session(self.engine)
        session.info["environment"] = self.connection.tenant_name
        return session

    def cleanup(self) -> None:
        """Closes all sessions and cleans up engine"""
        self.engine.dispose()

    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(ValueError),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def autogenerate_auth(
        cls, benchling_tenant: str, email: str, password: str
    ) -> tuple[str, str]:
        with requests.Session() as session:
            homepage = session.get(f"https://{benchling_tenant}.benchling.com/signin")
            soup = BeautifulSoup(homepage.content, features="lxml")
            input = soup.find(id="csrf_token")
            csrf_token = input.get("value")
            assert isinstance(csrf_token, str)
            login_payload = {
                "csrf_token": csrf_token,
                "username": email,
                "password": password,
                "signout_on_close": "y",
            }
            signin_response = session.post(
                f"https://{benchling_tenant}.benchling.com/signin",
                data=login_payload,
                headers={
                    "Referer": f"https://{benchling_tenant}.benchling.com/signin",
                },
            )
            if not signin_response.ok:
                raise ValueError(
                    f"Failed to sign in to Benchling: {signin_response.text}"
                )
            if not signin_response.headers.get("Set-Cookie"):
                raise ValueError(
                    f"Failed to sign in to Benchling: {signin_response.text}"
                )
            return csrf_token, signin_response.headers["Set-Cookie"].split("; Secure")[
                0
            ].removeprefix("session=")
