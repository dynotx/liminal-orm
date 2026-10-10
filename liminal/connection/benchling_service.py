import logging
import warnings
from typing import TYPE_CHECKING, Any

from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.benchling import Benchling, BenchlingApiClientDecorator
from benchling_sdk.helpers.retry_helpers import RetryStrategy
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, configure_mappers

from liminal.base.properties.base_field_properties import BaseFieldProperties
from liminal.base.properties.base_schema_properties import BaseSchemaProperties
from liminal.connection.benchling_connection import BenchlingConnection
from liminal.enums import (
    BenchlingEntityType,
    BenchlingFieldType,
    BenchlingNamingStrategy,
)

if TYPE_CHECKING:
    from liminal.entity_schemas.entity_schema_models_v3 import EntitySchemaModel

LOGGER = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

REMOTE_LIMINAL_SCHEMA_NAME = "liminal_remote"
REMOTE_REVISION_ID_FIELD_WH_NAME = "revision_id"


class SSODisabledError(ValueError):
    pass


class BenchlingService(Benchling):
    """
    Class that creates a connection object that can be used to connect to Benchling's API, database, or internal API.

    Parameters
    ----------
    connection: BenchlingConnection
        The connection object that contains the credentials for the Benchling tenant.
    use_api: bool
        Whether to connect to the Benchling SDK. Requires api_client_id and api_client_secret from the connection object.
    use_db: bool = False
        Whether to connect to the Benchling Postgres database. Requires warehouse_connection_string from the connection object.
    use_internal_api: bool = False
        DEPRECATED: Liminal no longer uses Benchling's internal API, so this is ignored. It will be removed in v6.
    client_decorator: BenchlingApiClientDecorator | None = None
        An optional function that receives the default BenchlingApiClient and returns a
        customized one. Forwarded to the Benchling SDK. A common use is raising the HTTP
        timeout, which otherwise defaults to 10 seconds: ``lambda c: c.with_timeout(60)``.
    """

    def __init__(
        self,
        connection: BenchlingConnection,
        use_api: bool = True,
        use_db: bool = False,
        use_internal_api: bool = False,
        client_decorator: BenchlingApiClientDecorator | None = None,
    ) -> None:
        if use_internal_api:
            warnings.warn(
                "Deprecated BenchlingService argument set: use_internal_api. Liminal no longer uses Benchling's internal API, so it is ignored. Remove it from your BenchlingService, since it will be removed in v6.",
                FutureWarning,
                stacklevel=2,
            )
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
                url=url,
                auth_method=auth_method,
                retry_strategy=retry_strategy,
                client_decorator=client_decorator,
            )
            LOGGER.info(f"Tenant {connection.tenant_name}: Connected to Benchling API.")
        self.use_db = use_db
        if use_db:
            if connection.warehouse_connection_string:
                self.engine: Engine = create_engine(
                    connection.warehouse_connection_string
                )
                configure_mappers()
                LOGGER.info(
                    f"Tenant {connection.tenant_name}: Connected to Benchling read-only Postgres warehouse."
                )
            else:
                raise ValueError(
                    "use_db is True but warehouse_connection_string not provided in BenchlingConnection."
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

    @property
    def organization_id(self) -> str:
        # This assumes there is only one registry (which has always been the case at DynoTx)
        registries = self.registry.registries()
        assert len(registries) == 1
        return registries[0].owner.id

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

    def _get_remote_liminal_schema(self) -> "EntitySchemaModel | None":
        """Fetches the liminal_remote entity schema with its field definitions.
        Returns None if the schema doesn't exist."""
        from liminal.entity_schemas.entity_schema_models_v3 import EntitySchemaModel

        return EntitySchemaModel.get_one(self, REMOTE_LIMINAL_SCHEMA_NAME)

    def get_remote_revision_id(self) -> str:
        """
        Searches for the liminal_remote schema, where the revision_id is stored.
        This schema contains the remote revision_id in the name of the revision_id field.

        Returns the remote revision_id stored on the entity.
        """

        try:
            liminal_schema = self._get_remote_liminal_schema()
        except Exception:
            raise ValueError(
                f"Did not find any schema name '{REMOTE_LIMINAL_SCHEMA_NAME}'. Run a liminal migration to populate your registry with the Liminal entity that stores the remote revision_id."
            )
        revision_id_fields = [
            f
            for f in liminal_schema.fields
            if f.systemName == REMOTE_REVISION_ID_FIELD_WH_NAME and not f.archived
        ]
        if len(revision_id_fields) == 1:
            revision_id = revision_id_fields[0].name
            assert revision_id is not None, "No revision_id set in field name."
            return revision_id
        else:
            raise ValueError(
                f"Error finding field on {REMOTE_LIMINAL_SCHEMA_NAME} schema with warehouse_name {REMOTE_REVISION_ID_FIELD_WH_NAME}. Check schema fields to ensure this field exists and is defined according to documentation."
            )

    def upsert_remote_revision_id(self, revision_id: str) -> bool:
        """Updates or inserts a remote Liminal schema into your tenant with the given revision_id stored in the name of a field.
        If the 'liminal_remote' schema is found, check and make sure a field with warehouse_name 'revision_id' is present. If both are present, update the revision_id stored within the name.
        If no schema is found, create the liminal_remote entity schema.

        Parameters
        ----------
        revision_id : str
            revision_id of migration file to set in Benchling on remote liminal entity.

        Returns
        -------
        CustomEntity
            remote liminal entity with updated revision_id field.
        """
        liminal_schema = self._get_remote_liminal_schema()
        if liminal_schema is None:
            # No liminal_remote schema found. Create schema.
            from liminal.entity_schemas.operations import CreateEntitySchema

            CreateEntitySchema(
                schema_properties=BaseSchemaProperties(
                    name=REMOTE_LIMINAL_SCHEMA_NAME,
                    warehouse_name=REMOTE_LIMINAL_SCHEMA_NAME,
                    prefix=REMOTE_LIMINAL_SCHEMA_NAME,
                    entity_type=BenchlingEntityType.CUSTOM_ENTITY,
                    naming_strategies={BenchlingNamingStrategy.NEW_IDS},
                ),
                fields=[
                    BaseFieldProperties(
                        name=revision_id,
                        warehouse_name=REMOTE_REVISION_ID_FIELD_WH_NAME,
                        type=BenchlingFieldType.TEXT,
                        parent_link=False,
                        is_multi=False,
                        required=True,
                    )
                ],
            ).execute(self)
            LOGGER.info(
                f"Created {REMOTE_LIMINAL_SCHEMA_NAME} schema for tracking the remote revision id."
            )
            return True
        # liminal_remote schema found. Check if revision_id field exists on it.
        revision_id_fields = [
            f
            for f in liminal_schema.fields
            if f.systemName == REMOTE_REVISION_ID_FIELD_WH_NAME and not f.archived
        ]
        if len(revision_id_fields) == 1:
            revision_id_field = revision_id_fields[0]
            if revision_id_field.name == revision_id:
                return False
            else:
                # liminal_remote schema found, revision_id field found. Update revision_id field on it with given revision_id.
                from liminal.entity_schemas.operations import UpdateEntitySchemaField

                UpdateEntitySchemaField(
                    liminal_schema.systemName,
                    revision_id_field.systemName,
                    BaseFieldProperties(name=revision_id),
                ).execute(self)
                return True
        else:
            raise ValueError(
                f"Error finding field on {REMOTE_LIMINAL_SCHEMA_NAME} schema with warehouse_name {REMOTE_REVISION_ID_FIELD_WH_NAME}. Check schema fields to ensure this field exists and is defined according to documentation."
            )
