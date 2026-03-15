.PHONY: install dev test lint process

install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

dev:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

lint:
	python -m ruff check backend/ tests/ --fix

process:
	@if [ -z "$(URL)" ]; then echo "Usage: make process URL=https://..."; exit 1; fi
	python run_pipeline.py --url "$(URL)"
