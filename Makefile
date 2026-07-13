.PHONY: install dev lint test test-cov clean build

install:
	pip install -e .

dev:
	pip install -e ".[dev,pydantic]"

lint:
	ruff check .

lint-fix:
	ruff check . --fix

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov --cov-report=term-missing

clean:
	rm -rf dist/ build/ *.egg-info/ .coverage htmlcov/ coverage.xml .pytest_cache/ .ruff_cache/

build:
	python -m build
