# [Liminal ORM](#liminal-orm)

Liminal ORM<sup>1</sup> is a Python package that builds on top of [Benchling](https://www.benchling.com/)'s LIMS<sup>2</sup> platform to keep your Benchling schemas and downstream code dependencies in sync. Liminal provides an ORM framework using [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) that allows you to define all your Benchling schemas in code. This creates a single source of truth that Benchling managers can use to keep multiple tenants in sync. This enables a code-first approach for managing Benchling tenants and accessing Benchling data. With the schemas defined in code, you can now take advantage of the additional capabilities that the Liminal toolkit provides. This includes:

- The ability to run migrations to your Benchling tenant(s) through an easy to use CLI<sup>3</sup>.
- One source of truth defined in code for your Benchling schema model that your many Benchling tenants can stay in sync with.
- Easy to implement validation rules to reflect business logic for all of your Benchling entities.
- Strongly typed queries for all your Benchling entities.
- CI/CD integration with GitHub Actions to ensure that your Benchling schemas and code are always in sync.
- And more!

Benchling is an industry standard cloud platform for life sciences R&D. Liminal builds on top of Benchling's platform and assumes that you already have a Benchling tenant set up and have (or have access to) an admin user account. If not, learn more about getting started with Benchling [here](https://www.benchling.com/explore-benchling)!

For a full and in-depth overview of Liminal, please refer to our [full documentation](coming soon). Below is a [quickstart guide](#getting-started) to get you Liminal set up in your project.

Reach out in the [Discussions](https://github.com/dynotx/liminal-orm/discussions) forum with any questions or to simply introduce yourself! If you run into any issues, during setup or usage, don't hesitate to post in [Issues](https://github.com/dynotx/liminal-orm/issues) or reach out directly at <opensource@dynotx.com>. You can expect responses within 48 hours :)

<img width="793" alt="liminal_simple_graph" src="https://github.com/user-attachments/assets/52e32cd0-3407-49f5-b100-5763bee3830c">

## Table of Contents

- [Overview](#liminal-orm)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Setup](#setup)
  - [Migration](#migration)
  - [Toolkit](#toolkit)
- [Community](#community)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Footnotes](#footnotes)

## [Getting Started](#getting-started)

Note: Liminal requires you to have (or have access to) an admin user account for your Benchling tenant. If you run into any issues, please reach out to us on the [Discussions](https://github.com/dynotx/liminal-orm/discussions/categories/q-a) forum and we'll be happy to help!

### [Installation](#installation)

via pip: `pip install liminal-orm`

via github: `python -m pip install git+https://github.com/dynotx/liminal-orm.git --ignore-installed`

### [Setup](#setup)

1. `cd` into the directory where you want to instantiate your *Liminal environment*. This will be the root directory where your schemas will live. Note: the Liminal CLI must always be run from within this root directory.

2. Run `liminal init` to initialize your Liminal project. This will create a liminal/ directory with an env.py file and a versions/ directory with an empty first revision file.

3. Populate the env.py file with your Benchling connection information, following the instructions in the file. For example:

    ```python
    from liminal.connection import BenchlingConnection

    PROD_CURRENT_REVISION_ID = "12b31776a755b"

    # It is highly recommended to use a secrets manager to store your credentials.
    connection = BenchlingConnection(
        tenant_name="pizzahouse-prod",
        tenant_alias="prod",
        current_revision_id_var_name="PROD_CURRENT_REVISION_ID",
        api_client_id="my-secret-api-client-id",
        api_client_secret="my-secret-api-client-secret",
        warehouse_connection_string="my-warehouse-connection-string",
        internal_api_admin_email="my-secret-internal-api-admin-email",
        internal_api_admin_password="my-secret-internal-api-admin-password",
    )
    ```

4. If your Benchling tenant has pre-existing schemas, run `liminal generate-files` to populate the root directory with the schema files. Your file structure should now look like this:

    ```text
    benchling/
        liminal/
            env.py
            versions/
                <revision_id>_initial_init_revision.py
        dropdowns/
            ...
        entity_schemas/
            ...
    ```

5. Add your schema imports to the env.py file. For example:

    ```python
    from pizzahouse.dropdowns import *
    from pizzahouse.entity_schemas import *
    ...
    ```

6. Set up is complete! You're now ready to start using your schemas defined in code as the single source of truth for your Benchling tenant(s). Refer to the [Migration](#migration) section to learn about how you make a change to your Benchling schema model. Refer to the [Toolkit](#toolkit) section to learn about the additional features the Liminal toolkit provides.

## [Migration](#migration)

This section will walk you through the process of making a change to your Benchling schema model and syncing it to your Benchling tenant(s).

1. Make a change to your Benchling schema model!

2. Run `liminal autogenerate <benchling_tenant_name> <description_of_changes>` to generate a new revision file. For example: `liminal autogenerate prod "new oven schema"`. This will create a new revision file in the `versions/` directory. This revision file defines the set of steps (or "operations") that will be needed to make the targeted Benchling tenant up to date with the changes made in the schema model.

    If I have multiple Benchling tenants, do I have to run `autogenerate` for each tenant?

    No, Liminal only keeps a single thread of revision history that are linked together for easy upgrade/downgrade. In the case of multiple tenants that need to stay in sync together, we recommend pointing `autogenerate` at your production tenant, or the tenant that acts as the production environment. When ready, you can then apply the revision to all your tenants.

3. Review the generated revision file and set of operations to ensure that it is accurate.

4. Run `liminal upgrade <benchling_tenant_name> <upgrade_descriptor>` to migrate your Benchling tenant(s) to the new schema. For example: `liminal upgrade prod head`. This will apply the revision to the targeted Benchling tenant. For example: `liminal upgrade prod head` will apply the revision to the production tenant.

5. Check out your changes on your Benchling tenant(s)!

## [Toolkit](#toolkit)

With your schemas defined in code, you can now take advantage of the additional capabilities that the Liminal toolkit provides.

1. Entity validation: Easily create custom validation rules for your Benchling entities.

    ```python
    from dyno.liminal.orm.base_model import BaseModel
    from dyno.liminal.orm.mixins import CustomEntityMixin

    class Pizza(BaseModel, CustomEntityMixin):
        ...

        @validator(BenchlingReportLevel.HIGH)
        def cook_temp_time(self):
            if self.cook_time is not None and self.cook_temp is None:
                raise ValueError("Cook temp is required if cook time is set")
            if self.cook_time is None and self.cook_temp is not None:
                raise ValueError("Cook time is required if cook temp is set")
    ```

2. Strongly typed queries: Write type-safe queries using SQLAlchemy to access your Benchling entities.

    ```python
    with BenchlingSession(benchling_connection, with_db=True) as session:
        pizza = session.query(Pizza).filter(Pizza.name == "Margherita").first()
        print(pizza)
    ```

3. CI/CD integration: Use Liminal to automatically generate and apply your revision files to your Benchling tenant(s) as part of your CI/CD pipeline.

4. And more to come!

## [Community](#community)

We're excited to hear from you! Feel free to introduce yourself on the [Liminal GitHub Discussions page](https://github.com/dynotx/liminal-orm/discussions/categories/intros)

Please refer to [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) to learn more about how to interact with the community.

Please refer to [GOVERNANCE.md](./GOVERNANCE.md) to learn more about the project's governance structure.

## [Contributing](#contributing)

Contributions of any kind are welcome and encouraged! This ranges from feedback and feature requests all the way to code contributions.
Please refer to [CONTRIBUTING.md](./CONTRIBUTING.md) to learn how to contribute to Liminal!

## [License](#license)

Liminal ORM is distributed under the [Apache License, Version 2.0](./LICENSE.md).

## [Acknowledgements](#acknowledgements)

This project could not have been started without the support of Dyno Therapeutics and the help of the following people.

- [Steve Northup](https://github.com/steve-dyno): For being an incredibly supportive manager and mentor, making key technical contributions, and providing guidance on the project's direction.
- [Joyce Samson](https://github.com/samsonjoyce): For being Liminal's first power user at Dyno Therapeutics, providing valuable feedback that informed the project's direction, and coming up with Liminal's name.
- [David Levy-Booth](https://github.com/davidlevybooth): For providing leadership and guidance on releasing this as an open source software.
- The rest of the Dyno team...

## [Footnotes](#footnotes)

ORM<sup>1</sup>: Object-Relational Mapper. An ORM is a piece of software designed to translate between the data representations used by databases and those used in object-oriented programming. In this case, Liminal provides an ORM layer built specifically for Benchling that allows for users to quickly and easily define Benchling entities in code. [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) is the underlying ORM that Liminal uses to interact with your Benchling tenant(s) and is an open-source software that is an industry standard software.

LIMS<sup>2</sup>: Laboratory Information Management System. A LIMS is a piece of software that allows you to effectively manage samples and associated data. [Benchling](https://www.benchling.com/) is an industry-leading LIMS software.

CLI<sup>3</sup>: Command Line Interface. A CLI is a piece of software that allows you to interact with a software program via the command line. Liminal provides a CLI that allows you to interact with your Liminal environment. This project uses [Typer](https://github.com/fastapi/typer) to construct the CLI
