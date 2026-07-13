# Contributing to behave-tables

Thanks for your interest in contributing! This guide covers the basics.

## Setup

```bash
git clone https://github.com/MathiasPaulenko/behave-tables.git
cd behave-tables
make dev
```

This installs the package with dev dependencies (pytest, ruff, behave) and pydantic.

## Development workflow

```bash
make lint        # check code style
make lint-fix    # auto-fix lint issues
make test        # run tests
make test-cov    # run tests with coverage report
```

## Before submitting a PR

1. All tests must pass: `make test`
2. Coverage must stay at 100%: `make test-cov`
3. No lint errors: `make lint`
4. Write clear commit messages (conventional commits preferred)

## Adding a new feature

1. Write tests first
2. Implement the feature
3. Ensure 100% coverage
4. Update `README.md` and `CHANGELOG.md`
5. Submit a PR with a clear description

## Release process

Releases are automated via GitHub Actions:

1. Bump version in `pyproject.toml`, `__init__.py`, and `CHANGELOG.md`
2. Commit and push to `main`
3. Tag with `vX.Y.Z` and push the tag
4. The `release.yml` workflow builds and publishes to PyPI automatically
