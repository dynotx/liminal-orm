# Contributing to Liminal ORM

Thank you in advance for your contribution to Liminal! A contribution of any kind has an impact on the community. Remember to star the repo on GitHub and share Liminal with your colleagues to grow our community!

Everyone in the community has the ability to influence the roadmap of Liminal. Our goal is to create an open-source software product that enables code-first configuration and safe, yet accessible, change management for LIMS systems like Benchling.

Feel free to reach out at <opensource@dynotx.com> for any questions at all!

## Ways to Contribute

- **Code Contribution**: Help us improve the codebase by fixing bugs, adding new features, or improving documentation.
- **Raising an Issue**: Report bugs, suggest features, or provide feedback to help us improve.
- **Spread the Word**: Leave a star on the repo in GitHub, spread the word with coworkers, or growing and cultivating the community.
- **Add yourself as a User**: If your project or organization uses Liminal, add yourself to [USERS.md](USERS.md). This is a great way to help us prioritize Liminal's roadmap!

## Setup

1. Clone the repo

    `git clone https://github.com/dynotx/liminal-orm.git`

2. cd into the repo

    `cd liminal-orm`

3. Install Poetry

   Use the [Poetry Installation guide](https://python-poetry.org/docs/#installing-with-pipx)

3. Install Liminal dependencies

    `poetry install --all-extras`

4. Ensure python version matches Liminal's supported version

    Supported python versions of Liminal can be found in pyproject.toml. We recommend using [pyenv](https://github.com/pyenv/pyenv) to manage python versions.

5. Start developing :)

## Development cycle

Liminal uses [`pre-commit`](https://pre-commit.com/) hooks for enforcing formatting, linting, and mypy. Formatting and linting is done using [`ruff`](https://docs.astral.sh/ruff/) Every commit requires these to pass and you can run them manually using `pre-commit run` (use `-a` flag to run on all files). Commit with the `--no-verify` flag to avoid running the pre-commit hooks.

Please include tests when adding new functionality. Liminal uses [`pytest`](https://docs.pytest.org/en/stable/) for testing. Run this using `pytest liminal/` to run all tests. All tests must pass in order to merge in a Pull Request.

If making changes to the documentation (which is created using [`MKDocs-material`](https://squidfunk.github.io/mkdocs-material/)). Host and get a live preview of website using `mkdocs serve`.

## Making a Pull Request

Contributions to the codebase must be made by submitting a [Pull Request](https://github.com/dynotx/liminal-orm/pulls) to the `main` branch
