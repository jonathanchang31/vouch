.PHONY: help install dev test test-cov bench lint format type check build clean examples-screenshots

PY ?= python
PIP ?= $(PY) -m pip

help:
	@echo "vouch developer targets"
	@echo ""
	@echo "  make install       editable install with dev extras"
	@echo "  make test          run pytest"
	@echo "  make test-cov      run pytest with coverage"
	@echo "  make bench         run the performance benchmark suite (needs pytest-benchmark)"
	@echo "  make lint          ruff check"
	@echo "  make format        ruff format (writes)"
	@echo "  make type          mypy"
	@echo "  make check         lint + type + test"
	@echo "  make build         build sdist + wheel"
	@echo "  make clean         remove caches, build artifacts, *.egg-info"
	@echo "  make examples-screenshots  re-render docs/img/examples/*.svg"

install:
	$(PIP) install -e '.[dev]'

dev: install

test:
	$(PY) -m pytest

test-cov:
	$(PY) -m pytest --cov=vouch --cov-report=term-missing --cov-report=xml

lint:
	$(PY) -m ruff check src tests

format:
	$(PY) -m ruff format src tests

type:
	$(PY) -m mypy src

check: lint type test

# the bench_*.py filenames don't match pytest's default python_files glob,
# so the override is required or zero benchmarks are collected.
bench:
	$(PY) -m pytest benchmarks/ --benchmark-only \
		-o python_files='bench_*.py test_*.py' \
		--benchmark-json=bench.json

examples-screenshots:
	$(PY) docs/img/examples/render.py

build:
	$(PY) -m pip install --upgrade build
	$(PY) -m build

clean:
	rm -rf build dist *.egg-info src/*.egg-info \
	       .pytest_cache .ruff_cache .mypy_cache .benchmarks \
	       coverage.xml .coverage htmlcov bench.json
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
