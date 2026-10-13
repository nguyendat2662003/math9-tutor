.PHONY: install test lint api eval

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check . && ruff format --check .

api:
	python -m uvicorn api.main:app --reload --port 8000

eval:
	python evals/run.py --set smoke
