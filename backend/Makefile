.PHONY: install test lint api eval demo ui

demo:
	python tools/demo_draw.py --file demo/de.txt --out demo/out

ui:
	python -m streamlit run demo_streamlit.py

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
