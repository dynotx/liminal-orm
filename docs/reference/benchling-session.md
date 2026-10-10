## BenchlingService: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/connection/benchling_service.py)

The BenchlingService class takes in a BenchlingConnection object and is used to directly interact with Benchling's SDK and Postgres warehouse. This class is surfaced for users so that there is one standard interface for interacting with Benchling around your codebase. Liminal's BenchlingService handles all session management and is a subclass of Benchling's SDK, so all functionality of Benchling's SDK is available.

```python
from liminal.connection import BenchlingConnection
from liminal.connection import BenchlingService

connection = BenchlingConnection(
    ...
)
benchling_service = BenchlingService(connection, use_db=True) # enable all connections

# Use Benchling SDK
entity = benchling_service.custom_entities.get_by_id("my-entity-id")

# Use to query Postgres warehouse using SQLAlchemy
with benchling_service() as session:
    entity = session.query(Pizza).all()
```

### Parameters

- **connection: BenchlingConnection**

    The connection object that contains the credentials for the Benchling tenant.

- **use_api: bool**

    Whether to connect to the Benchling SDK. Defaults to True. (See Benchling SDK documentation [here](https://docs.benchling.com/docs/getting-started-with-the-sdk))

- **use_db: bool**

    Whether to connect to the Benchling Postgres warehouse. Defaults to False. See SQLAlchemy documentation [here](https://www.sqlalchemy.org/) for more information.

- **client_decorator: Optional[BenchlingApiClientDecorator] = None**

    An optional function that receives the default BenchlingApiClient and returns a
    customized one. Forwarded to the Benchling SDK. A common use is raising the HTTP
    timeout, which otherwise defaults to 10 seconds: ``lambda c: c.with_timeout(60)``.