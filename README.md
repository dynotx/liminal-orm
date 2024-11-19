# [Liminal ORM](#liminal-orm)

[![PyPI version](https://img.shields.io/pypi/v/liminal-orm.svg)](https://pypi.org/project/liminal-orm/)
[![License](https://img.shields.io/github/license/dynotx/liminal-orm)](https://github.com/dynotx/liminal-orm/blob/main/LICENSE.md)
[![CI](https://github.com/dynotx/liminal-orm/actions/workflows/liminal.yml/badge.svg)](https://github.com/dynotx/liminal-orm/actions/workflows/liminal.yml)
[![Downloads](https://static.pepy.tech/personalized-badge/liminal-orm?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads)](https://pepy.tech/project/liminal-orm)

Liminal ORM<sup>1</sup> is an open-source Python package that builds on [Benchling's](https://www.benchling.com/) LIMS<sup>2</sup> platform and provides a simple, code-first approach for synchronizing and managing your Benchling schemas. Check out the [**full documentation here**](https://dynotx.github.io/liminal-orm/) and join our [**Slack community here**](https://join.slack.com/t/liminalorm/shared_invite/zt-2ujrp07s3-bctook4e~cAjn1LgOLVY~Q)!

Liminal provides an ORM framework using [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) along with a schema migration service inspired by [Alembic](https://alembic.sqlalchemy.org/en/latest/). This allows you to define your Benchling schemas in code and create a *single source of truth* that synchronizes between your upstream Benchling tenant(s) and downstream dependencies. By creating a standard interface and through using one-line CLI<sup>3</sup> commands, Liminal enables a code-first approach for managing Benchling tenants and accessing Benchling data. With the schemas defined in code, you can also take advantage of the additional capabilities that the Liminal toolkit provides. This includes:

- The ability to run migrations to your Benchling tenant(s) through an easy to use CLI.
- One source of truth defined in code for your Benchling schema model that your many Benchling tenants can stay in sync with.
- Easy to implement validation rules to reflect business logic for all of your Benchling entities.
- Strongly typed queries for all your Benchling entities.
- CI/CD integration with GitHub Actions to ensure that your Benchling schemas and code are always in sync.
- And more based on community contributions/feedback :)

If you are a Benchling user, try out Liminal by following the [**Quick Start Guide**](https://dynotx.github.io/liminal-orm/getting-started/prerequisites/)! Reach out in the [Discussions](https://github.com/dynotx/liminal-orm/discussions) forum with any questions or to simply introduce yourself! If there is something blocking you from using Liminal or you're having trouble setting Liminal up, please share in [Issues](https://github.com/dynotx/liminal-orm/issues) or reach out directly (contact information below). You can expect responses within 48 hours :)

Benchling is an industry standard cloud platform for life sciences R&D. Liminal builds on top of Benchling's platform and assumes that you already have a Benchling tenant set up and have (or have access to) an admin user account. If not, learn more about getting started with Benchling [here](https://www.benchling.com/explore-benchling)!

Nirmit Damania is the creator and current maintainer of Liminal (I post Liminal updates to [Discussions](https://github.com/dynotx/liminal-orm/discussions) and my [LinkedIn](https://www.linkedin.com/in/nirmit-damania/)). Most importantly, **you** have the ability to influence the future of Liminal! Any feedback, positive or negative, is highly encouraged and will be used to steer the direction of Liminal. Refer to the [Contributing guide](https://github.com/dynotx/liminal-orm/blob/main/CONTRIBUTING.md) to learn more about how you can contribute to Liminal.

⭐️ Leave a star on the repo to spread the word!
If you or your organization use Liminal, please consider adding yourself or your organization to the [Users](https://github.com/dynotx/liminal-orm/blob/main/USERS.md) list.

<img width="793" alt="liminal_simple_graph" src="https://github.com/user-attachments/assets/52e32cd0-3407-49f5-b100-5763bee3830c">

## Table of Contents

- [Overview](#liminal-orm)
- [Getting Started](#getting-started)
  - [Toolkit](#toolkit)
- [Mission](#mission)
- [Community](#community)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Footnotes](#footnotes)

## [Getting Started](#getting-started)

Note: Liminal requires you to have (or have access to) an admin user account for your Benchling tenant. If you run into any issues, please reach out to us on the [Discussions](https://github.com/dynotx/liminal-orm/discussions/categories/q-a) forum and we'll be happy to help!

Check out this [Quick Start Guide](https://dynotx.github.io/liminal-orm/getting-started/prerequisites/) to get you setup with Liminal!

## [Toolkit](#toolkit)

With your schemas defined in code, you can now take advantage of the additional capabilities that the Liminal toolkit provides.

1. Entity validation: Easily create custom validation rules for your Benchling entities.

    ```python
    from liminal.validation import BenchlingValidator, BenchlingValidatorReport, BenchlingReportLevel
    from liminal.orm.base_model import BaseModel

    class CookTempValidator(BenchlingValidator):
        """Validates that a field value is a valid enum value for a Benchling entity"""

        def validate(self, entity: type[BaseModel]) -> BenchlingValidatorReport:
            valid = True
            message = None
            if entity.cook_time is not None and entity.cook_temp is None:
                valid = False
                message = "Cook temp is required if cook time is set"
            if entity.cook_time is None and entity.cook_temp is not None:
                valid = False
                message = "Cook time is required if cook temp is set"
            return self.create_report(valid, BenchlingReportLevel.MED, entity, message)
    ```

2. Strongly typed queries: Write type-safe queries using SQLAlchemy to access your Benchling entities.

    ```python
    with BenchlingSession(benchling_connection, with_db=True) as session:
        pizza = session.query(Pizza).filter(Pizza.name == "Margherita").first()
        print(pizza)
    ```

3. CI/CD integration: Use Liminal to automatically generate and apply your revision files to your Benchling tenant(s) as part of your CI/CD pipeline.

4. And more to come!

## [Mission](#mission)

The democratization of software in Biotech is crucial. By building a community around complex, yet common, problems and creating open-source solutions, we can work together to tackle these challenges together and enable faster innovation in the industry. By breaking down the silos between private platforms, we can enable a more dynamic and open ecosystem. This was the motivation for Liminal's creation. Liminal's goal is to create an open-source software product that enables a standard, code-first approach to configuration and change management for LIMS systems. We started with Benchling, but the goal is to make Liminal the go-to solution for any LIMS system.

## [Community](#community)

We're excited to hear from you! Feel free to introduce yourself on the [Liminal GitHub Discussions page](https://github.com/dynotx/liminal-orm/discussions/categories/intros)

Please refer to [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) to learn more about how to interact with the community.

Please refer to [GOVERNANCE.md](./GOVERNANCE.md) to learn more about the project's governance structure.

## [Contributing](#contributing)

Contributions of any kind are welcome and encouraged! This ranges from feedback and feature requests all the way to code contributions.
Please refer to [CONTRIBUTING.md](./CONTRIBUTING.md) to learn how to contribute to Liminal!

## [License](#license)

Liminal ORM is distributed under the [Apache License, Version 2.0](./LICENSE.md).

## [Direct Contact](#direct-contact)

- Email: <opensource@dynotx.com>
- LinkedIn: [Nirmit Damania](https://www.linkedin.com/in/nirmit-damania/)

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
