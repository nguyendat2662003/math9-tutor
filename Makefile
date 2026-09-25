.PHONY: install test lint api eval demo ui web

demo:
	python tools/demo_draw.py --file demo/de.txt --out demo/out

ui:
	python -m streamlit run apps/demo_streamlit.py

web:
	cd apps/web && npm run dev

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check . && ruff format --check .

api:
	python -m uvicorn apps.api.main:app --reload --port 8000

eval:
	python evals/run.py --set smoke
