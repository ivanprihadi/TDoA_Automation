markdown
# 🚀 TDOA System - Quick Start Guide

## 5-Minute Setup

### 1. Prerequisites
- Python 3.8+
- 3x Raspberry Pi dengan RTL-SDR
- IQ data files (.dat format)

### 2. Installation

```bash  
# Clone & enter directory  
git clone <repo>  
cd tdoa_automation_app  

# Create virtual environment  
python -m venv venv  
source venv/bin/activate  

# Install dependencies  
pip install -r requirements.txt  

# Configure  
cp config.json.example config.json  
nano config.json  # Edit dengan RPi addresses & coordinates  
3. Run Application
bash
# Development
python main.py

# Production
gunicorn -w 4 main:app
Then open: http://localhost:5000

Basic Usage
Step 1: Prepare Files
Record 3 IQ files dari RX1, RX2, RX3
Upload ke recorded_data/ folder
Atau gunakan SSH to pull dari RPi
Step 2: Processing
Go to Processing tab
Select 3 files (RX1, RX2, RX3)
Configure parameters (optional)
Click Start Processing
Step 3: View Results
Results automatically appear in Results tab
Download HTML map
Export data as CSV/JSON
Common Tasks
Download Files from RPi
bash
scp pi@192.168.1.101:/home/pi/recorded_data/*.dat recorded_data/
View Logs
bash
tail -f logs/app.log
Run with Docker
bash
docker-compose up -d
open http://localhost:5000
Troubleshooting
Issue	Solution
Port 5000 in use	Change port in main.py
Files not found	Check recorded_data/ directory
Config error	Validate JSON: python -m json.tool config.json
RPi connection fails	Test: ping <rpi-ip>
Next Steps
Read full README.md
Check SETUP.md for detailed setup
Explore API Documentation
Enjoy your TDOA journey! 🛰️

python

---

## **🔟 FILE: `Makefile`** (UPDATED - Lebih lengkap)

**Lokasi:** `tdoa_automation_app/Makefile`

```makefile  
.PHONY: help install test lint format clean run dev docker-build docker-run  

.DEFAULT_GOAL := help  

# ==================== HELP ====================  
help:  
	@echo "╔════════════════════════════════════════════════════════════════╗"  
	@echo "║         TDOA Automation System - Available Commands            ║"  
	@echo "╚════════════════════════════════════════════════════════════════╝"  
	@echo ""  
	@echo "📦 Installation:"  
	@echo "   make install          Install dependencies"  
	@echo "   make install-dev      Install with development tools"  
	@echo ""  
	@echo "▶️  Running:"  
	@echo "   make run              Run development server"  
	@echo "   make dev              Run with auto-reload"  
	@echo "   make prod             Run production server"  
	@echo ""  
	@echo "🧪 Testing & Quality:"  
	@echo "   make test             Run unit tests"  
	@echo "   make test-fast        Run quick tests"  
	@echo "   make coverage         Generate coverage report"  
	@echo "   make lint             Run code linting"  
	@echo "   make format           Format code with black"  
	@echo "   make type-check       Run type checker"  
	@echo ""  
	@echo "🐳 Docker:"  
	@echo "   make docker-build     Build Docker image"  
	@echo "   make docker-run       Start Docker container"  
	@echo "   make docker-stop      Stop Docker container"  
	@echo "   make docker-logs      View container logs"  
	@echo "   make docker-shell     Open shell in container"  
	@echo ""  
	@echo "🧹 Maintenance:"  
	@echo "   make clean            Clean temporary files"  
	@echo "   make reset            Reset all changes"  
	@echo "   make validate-config  Validate configuration"  
	@echo ""  
	@echo "📊 All Checks:"  
	@echo "   make check            Run all linters & tests"  
	@echo ""  

# ==================== INSTALLATION ====================  
install:  
	@echo "Installing dependencies..."  
	pip install -r requirements.txt  
	@echo "✓ Installation complete"  

install-dev:  
	@echo "Installing with development dependencies..."  
	pip install -r requirements.txt  
	pip install pytest pytest-cov black flake8 mypy  
	@echo "✓ Development environment ready"  

# ==================== RUNNING ====================  
run:  
	@echo "Starting development server on http://localhost:5000..."  
	python main.py  

dev:  
	@echo "Starting with auto-reload..."  
	FLASK_ENV=development FLASK_DEBUG=1 python main.py  

prod:  
	@echo "Starting production server..."  
	gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 main:app  

# ==================== TESTING ====================  
test:  
	@echo "Running full test suite..."  
	pytest tests/ -v --cov=backend --cov-report=html --cov-report=term  

test-fast:  
	@echo "Running quick tests..."  
	pytest tests/ -v --tb=short  

coverage:  
	@echo "Generating coverage report..."  
	pytest tests/ --cov=backend --cov-report=html  
	@echo "Report saved to htmlcov/index.html"  

# ==================== CODE QUALITY ====================  
lint:  
	@echo "Running linter..."  
	flake8 backend/ tests/ main.py --max-line-length=120 --count  

format:  
	@echo "Formatting code..."  
	black backend/ tests/ main.py  
	isort backend/ tests/ main.py  
	@echo "✓ Code formatted"  

type-check:  
	@echo "Running type checker..."  
	mypy backend/ --ignore-missing-imports  

check: lint type-check test  
	@echo "✓ All checks passed!"  

# ==================== DOCKER ====================  
docker-build:  
	@echo "Building Docker image..."  
	docker build -t tdoa-automation:latest .  
	@echo "✓ Docker image built"  

docker-run:  
	@echo "Starting Docker container..."  
	docker-compose up -d  
	@echo "✓ Running at http://localhost:5000"  
	docker ps | grep tdoa  

docker-stop:  
	@echo "Stopping Docker container..."  
	docker-compose down  
	@echo "✓ Stopped"  

docker-logs:  
	docker-compose logs -f tdoa-app  

docker-shell:  
	docker-compose exec tdoa-app bash  

# ==================== CLEANUP ====================  
clean:  
	@echo "Cleaning temporary files..."  
	find . -type f -name "*.pyc" -delete  
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true  
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true  
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true  
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true  
	rm -rf build/ dist/ htmlcov/ .coverage  
	@echo "✓ Cleaned"  

reset:  
	@echo "Resetting all changes..."  
	make clean  
	git checkout -- .  
	git clean -fd  
	@echo "✓ Reset complete"  

# ==================== VALIDATION ====================  
validate-config:  
	@echo "Validating configuration..."  
	python3 -m json.tool config.json > /dev/null && echo "✓ Config valid"  

# ==================== UTILITIES ====================  
.PHONY: all  
all: clean install test lint  

version:  
	@python -c "import sys; print(f'Python {sys.version}')"  
	@pip --version  
	@echo "Project: TDOA Automation System v1.0.0"  