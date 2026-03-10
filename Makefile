.PHONY: build up down clean

PORT ?= 5005

build: venv/.built

venv/.built: requirements.txt
	@echo "Creating virtual environment and installing dependencies..."
	@python3 -m venv venv
	@venv/bin/pip install -q -r requirements.txt
	@echo "Installing NLP models..."
	@venv/bin/python -m spacy download en_core_web_sm
	@venv/bin/python -m spacy download fr_core_news_sm
	@touch venv/.built

up: build
	@echo "Starting Semantix Breaker on port $(PORT)..."
	@FLASK_APP=src/app.py FLASK_ENV=development venv/bin/python src/app.py

down:
	@echo "Stopping Semantix Breaker process on port $(PORT)..."
	@PIDS=$$(lsof -ti:$(PORT)); \
	if [ ! -z "$$PIDS" ]; then \
		kill -9 $$PIDS; \
		echo "App securely stopped."; \
	else \
		echo "No app running on port $(PORT)."; \
	fi

clean:
	@echo "Cleaning up..."
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf src/__pycache__
	@echo "Cleanup complete."
