.PHONY: install data train test demo evaluate serve verify docker-build docker-up clean

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

data:
	python -m training.generate_data

train:
	python -m training.train

test:
	python -m pytest -q

demo:
	python -m training.demo

evaluate:
	python -m fraud_engine.cli examples/high_risk_transaction.json

serve:
	uvicorn fraud_engine.api:app --reload

verify:
	python scripts/verify_project.py

docker-build:
	docker build -t hybrid-fraud-engine:local .

docker-up:
	docker compose up --build

clean:
	rm -rf .pytest_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
