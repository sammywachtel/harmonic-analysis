# Harmonic Analysis Development Commands

.PHONY: help format lint test quality setup clean

help:  ## Show this help
	@echo "🎯 Harmonic Analysis Development Commands:"
	@echo "make setup     - Setup development environment"
	@echo "make format    - Auto-fix code formatting and imports"
	@echo "make lint      - Run all quality checks"
	@echo "make test      - Run test suite"
	@echo "make quality   - Run comprehensive quality check"
	@echo "make clean     - Clean build artifacts"

setup:  ## Setup development environment
	python scripts/setup_dev_env.py

format:  ## Auto-fix formatting and imports
	python scripts/quality_check.py --fix

lint:  ## Run linting checks
	python scripts/quality_check.py

test:  ## Run test suite
	pytest tests/ -v

quality:  ## Run comprehensive quality check
	python scripts/quality_check.py

clean:  ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
