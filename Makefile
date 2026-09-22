.PHONY: install test lint api eval demo ui

demo:
	python tools/demo_draw.py --file demo/de.txt --out demo/out

ui:
	streamlit run apps/demo_streamlit.py

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check . && ruff format --check .

api:
	uvicorn apps.api.main:app --reload --port 8000

eval:
	python evals/run.py --set smoke
