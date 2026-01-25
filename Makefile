.PHONY: help test test-cov coverage coverage-html coverage-xml clean install dev refresh

help:
	@echo "Available targets:"
	@echo "  test          Run tests"
	@echo "  test-cov      Run tests with coverage report"
	@echo "  coverage      Run tests and show coverage summary"
	@echo "  coverage-html Generate HTML coverage report"
	@echo "  coverage-xml  Generate XML coverage report (for CI)"
	@echo "  clean         Remove build artifacts and coverage files"
	@echo "  install       Install the tool via uv"
	@echo "  refresh       Reinstall the tool (force refresh cache)"
	@echo "  dev           Install dev dependencies"

test:
	uv run pytest

test-cov:
	uv run pytest --cov --cov-report=term-missing

coverage:
	uv run pytest --cov --cov-report=term-missing

coverage-html:
	uv run pytest --cov --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-xml:
	uv run pytest --cov --cov-report=xml
	@echo "Coverage report generated in coverage.xml"

coverage-all: coverage-html coverage-xml
	@echo "All coverage reports generated"

clean:
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage
	rm -rf __pycache__/
	rm -rf run_claude/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/
	rm -rf dist/
	rm -rf build/

install:
	uv tool install .

refresh:
	rm -rf ${HOME}/.local/share/uv/tools/run-claude
	uv tool install . --refresh --force --verbose
	run-claude status
dev:
	uv sync --dev
