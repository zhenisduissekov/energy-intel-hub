.PHONY: help up down dev test clean install lint format

# Default target
help: ## Show this help message
	@echo "Houston Energy Market Analytics Platform - Makefile Commands"
	@echo "============================================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Docker commands
up: ## Start all services with Docker Compose
	@echo "🚀 Starting Houston Energy Analytics Platform..."
	docker-compose up -d
	@echo "✅ Platform running at http://localhost:5000"

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	docker-compose down

restart: ## Restart all services
	@echo "🔄 Restarting platform..."
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

# Development commands
dev: ## Start development server locally
	@echo "🔧 Starting development server..."
	streamlit run app.py --server.port 5000 --server.address 0.0.0.0

install: ## Install Python dependencies
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install -r requirements-dev.txt

# Database commands
db-up: ## Start only PostgreSQL database
	docker-compose up -d postgres

db-migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	python scripts/migrate.py

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "⚠️ Resetting database..."
	docker-compose down -v
	docker-compose up -d postgres

# Quality assurance
test: ## Run all tests
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	pytest tests/ --cov=. --cov-report=html --cov-report=term

lint: ## Lint code with flake8
	@echo "🔍 Linting code..."
	flake8 app.py utils/ pages/ tests/

format: ## Format code with black
	@echo "🎨 Formatting code..."
	black app.py utils/ pages/ tests/

type-check: ## Type check with mypy
	@echo "🔍 Type checking..."
	mypy app.py utils/ pages/

# Security
security-scan: ## Scan for security vulnerabilities
	@echo "🔒 Scanning for security vulnerabilities..."
	safety check
	bandit -r utils/ pages/

# Docker build commands
build: ## Build Docker image
	@echo "🏗️ Building Docker image..."
	docker build -t houston-energy-analytics .

build-no-cache: ## Build Docker image without cache
	@echo "🏗️ Building Docker image (no cache)..."
	docker build --no-cache -t houston-energy-analytics .

# Deployment commands
deploy-local: ## Deploy locally with production settings
	@echo "🚀 Deploying locally..."
	docker-compose -f docker-compose.prod.yml up -d

# Data commands
data-fetch: ## Fetch latest market data
	@echo "📈 Fetching latest market data..."
	python scripts/fetch_data.py

data-backup: ## Backup database
	@echo "💾 Backing up database..."
	docker-compose exec postgres pg_dump -U $$POSTGRES_USER $$POSTGRES_DB > backup_$$(date +%Y%m%d_%H%M%S).sql

# Cleanup commands
clean: ## Clean up temporary files and containers
	@echo "🧹 Cleaning up..."
	docker system prune -f
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

clean-all: ## Clean everything including volumes
	@echo "🧹 Deep cleaning..."
	docker-compose down -v
	docker system prune -af
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Setup commands
setup: ## Initial setup for development
	@echo "⚙️ Setting up development environment..."
	cp .env.example .env
	pip install -r requirements-dev.txt
	pre-commit install

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	sphinx-build -b html docs/ docs/_build/

docs-serve: ## Serve documentation locally
	@echo "📚 Serving documentation..."
	cd docs/_build && python -m http.server 8080

# Performance
benchmark: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks..."
	python scripts/benchmark.py

profile: ## Profile application performance
	@echo "📊 Profiling application..."
	python -m cProfile -o profile.stats app.py

# Monitoring
health-check: ## Check application health
	@echo "🏥 Checking application health..."
	curl -f http://localhost:5000/_stcore/health || exit 1

# Environment management
env-example: ## Create example environment file
	@echo "📝 Creating .env.example..."
	cat > .env.example << 'EOF'
# Optional API Keys for Enhanced Data
EIA_API_KEY=your_eia_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FRED_API_KEY=your_fred_api_key_here

# Database Configuration
DATABASE_URL=postgresql://energy_user:secure_password@localhost:5432/energy_analytics
POSTGRES_USER=energy_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=energy_analytics

# Application Settings
STREAMLIT_SERVER_PORT=5000
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF

# Quick start
quick-start: env-example install up ## Quick start for new users
	@echo "🎉 Quick start complete!"
	@echo "🌐 Platform available at: http://localhost:5000"
	@echo "📊 Database dashboard: http://localhost:8080 (if enabled)"

# Release commands
release-check: test lint security-scan ## Pre-release checks
	@echo "✅ Release checks completed"

version: ## Show version information
	@echo "Houston Energy Market Analytics Platform"
	@echo "Version: $$(git describe --tags --always)"
	@echo "Built with: Replit AI"
	@echo "Python: $$(python --version)"
	@echo "Docker: $$(docker --version)"