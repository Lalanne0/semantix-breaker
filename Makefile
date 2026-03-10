.PHONY: build up down clean

PORT ?= 5005

build:
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Installing dependencies..."
	@venv/bin/pip install -q -r requirements.txt

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
