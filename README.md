# Stock Analysis

[English](README.md) | [中文](README.zh-CN.md)

Stock Analysis is a comprehensive A-share fundamental scoring agent for Chinese stock analysis. It provides data crawling from multiple sources (CNInfo, Yahoo Finance), rule-based scoring, filtering, and a RESTful API for querying results.

## Disclaimer

**This tool is for reference and educational purposes only. The data and analysis provided are for informational purposes and should not be considered as financial advice.**

I do **NOT** provide any financial, investment, or trading recommendations. Users should conduct their own research and consult with qualified financial advisors before making any investment decisions.

**Investment involves risk, including possible loss of principal.** Past performance is not indicative of future results. Use this tool at your own risk and discretion.

The crawler/downloader will automatically fetch data from third-party websites like CNInfo and Yahoo Finance on Jan 1 and Jul 1; the analyzer will compute scores based on the fetched data and user-defined rules on Feb 1 and Aug 1. The limited frequency is to reduce the traffic to the target websites and avoid being blocked. They are for testing purposes only.

Only ten annual reports are downloaded in `data` in advance. They are for testing RAG (Retrieval-Augmented Generation) capability only and I will not provide reports crawler for ethics and security reasons, as they may cause huge traffic to the target websites.

This project is developed with the assistance of AI tools:

- GitHub Copilot for code and documentation generation, and suggestions
- ChatGPT for design discussions and problem-solving

## Technologies & Tools Used

### Backend & API

- **Python 3.14** for backend development
- **FastAPI** for async REST API with auto-generated documentation
- **Uvicorn** for ASGI serving
- **FastMCP** for Model Context Protocol server implementation
- **Pydantic** for data validation, serialization, and settings management
- **SQLAlchemy** for async ORM and database operations

### Database & Storage

- **PostgreSQL 18** for relational data storage
- **pgvector** for vector embeddings and similarity search
- **Alembic** for database schema migrations and versioning
- **MinIO** for S3-compatible object storage
- **PgQueuer** for async job queue and background task processing

### Frontend (Developed with AI Assistance)

- **Svelte/SvelteKit** for interactive user interface
- **TypeScript** for type-safe frontend development
- **Vite** for builds and dev server
- **pnpm** or **npm** for package management

### DevOps & Infrastructure

- **Docker Compose** for local multi-container orchestration
- **Kubernetes** with Kustomize for production-ready deployment
- **Nginx** for reverse proxy and web server configuration
- **Minikube** for local Kubernetes development and testing

### Development & Quality Tools

- **uv** for fast Python package and project management
- **pytest** for comprehensive unit and integration testing
- **testcontainers** for containerized dependency testing
- **ruff** for fast Python linting and code formatting
- **mypy** for static type checking
- **Git** for version control

### AI & LLM

- **LangChain + LangGraph** with OpenAI-compatible endpoints for chatbot analysis

### Configuration & Data

- **YAML** for API specifications, scoring rules, and configuration
- **CSV** for bulk data import and export

## Features

### Data & Analysis

- **Stock Data Management**: Store and query Chinese A-share stock information with classifications and industries
- **Multi-source Data Crawling**: Fetch stock data from CNInfo and Yahoo Finance with automatic rate limiting and retries
- **Rule-based Scoring**: Declarative YAML rules for computing financial metrics and overall scores
- **Stock Filtering**: Filter stocks based on configurable scoring rules
- **CSV Import/Export**: Bulk import and export stock data from/to CSV files
- **Job Queue**: PgQueuer for async job processing (data crawling, analysis, and scoring)

### API & Backend Services

- **RESTful API**: FastAPI-based async API with automatic Swagger/ReDoc documentation
- **Async Database Operations**: SQLAlchemy async with PostgreSQL for high performance and persistence
- **MCP Server**: FastMCP integration for Model Context Protocol services
- **Chatbot Agent**: LLM-powered chatbot for stock analysis insights and explanations

### Frontend & User Interface

- **Interactive Dashboard**: SvelteKit UI with stock explorer and data visualization
- **Advanced Filtering**: Query stocks with filtering by classification, industry, and custom criteria with pagination
- **Internationalization (i18n) Support**: English and Chinese toggle for global accessibility
- **Floating Chat Widget**: Integrated AI chatbot for on-demand analysis assistance

### Infrastructure & Deployment

- **Docker Compose & Kubernetes**: Multi-environment deployment with Kustomize orchestration for both development and production
- **Database Migrations**: Alembic-based schema versioning for seamless database updates
- **Vector Storage**: pgvector support for semantic search and RAG capabilities

### Code Quality & Developer Experience

- **Type Safety**: Full type hints with Pylance validation across the codebase
- **Comprehensive Documentation**: Google-style docstrings throughout all modules
- **Code Quality Standards**: Enforced through ruff linting, mypy type checking
- **Automated Testing**: pytest with testcontainers for isolated integration testing

## Features Roadmap

These features are planned:

- Add session management for chatbot
- Add RAG (Retrieval-Augmented Generation) capabilities
- Add observability and monitoring with Prometheus and Grafana

These features are under consideration for future development:

- Avoid duplicate jobs in PgQueuer
- Refine frontend UI/UX design

## Setup

**Warning: all the setup methods below will drop and recreate the database, erasing any existing data.**

If you want to keep existing data, dump the database first (`./scripts/dump_db.sh`) or ensure the database schema is up to date by running Alembic migrations manually.

[Docker Compose setup](#docker-compose-setup) is **recommended** for most users due to its simplicity and ease of use.
[Local development setup](#local-development-setup) is only intended for development and testing.
[Kubernetes setup](#kubernetes-setup) is for production deployment scenarios, but due to hardware limitations, only partial modules are supported and tested.

### Local Development Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/FreeFlyingSheep/stock-analysis
    cd stock-analysis
    ```

2. Install dependencies using [uv](https://docs.astral.sh/uv/):

    ```bash
    uv sync --all-extras
    source .venv/bin/activate
    ```

3. Configure environment variables:

    ```bash
    cp .env.example .env
    # Edit .env with your database credentials and settings
    export $(grep -v '^#' .env | xargs)
    ```

4. Initialize the database (install [PostgreSQL 18+](https://www.postgresql.org/) and [pgvector](https://github.com/pgvector/pgvector) first):

    ```bash
    ./scripts/init_db.sh
    ```

    This script will:
    - Drop any existing database
    - Create a fresh database
    - Enable the pgvector extension
    - Run Alembic migrations to create tables
    - Import initial stock data from `data/stocks.csv`
    - Initialize the PgQueuer job queue

5. Start the MinIO data store:

    In a separate terminal, run MinIO for object storage:

    ```bash
    source .venv/bin/activate
    export $(grep -v '^#' .env | xargs)
    ./scripts/run_minio.sh
    ```

6. Run the Job Queue:

    In a separate terminal, run the PgQueuer to process crawl and analysis jobs:

    ```bash
    source .venv/bin/activate
    export $(grep -v '^#' .env | xargs)
    ./scripts/run_pgq.sh
    ```

    This will start the job processor that:
    - Fetches stock data from CNInfo and Yahoo Finance
    - Computes scores and metrics using configured rules
    - Stores results in the database

7. Start the MCP server:

    In another terminal, run the FastMCP server:

    ```bash
    source .venv/bin/activate
    export $(grep -v '^#' .env | xargs)
    ./scripts/run_mcp.sh
    ```

8. Start the API Server:

    ```bash
    uv run app
    ```

    By default, the API will be available at `http://127.0.0.1:8000`.
    API documentation is automatically generated by FastAPI and can be accessed at:
    - Swagger UI: `http://127.0.0.1:8000/docs`
    - ReDoc: `http://127.0.0.1:8000/redoc`

9. Start the Frontend UI:

    In another terminal, run the SvelteKit frontend:

    ```bash
    export $(grep -v '^#' .env | xargs)
    pnpm --prefix ui run dev
    # or: npm --prefix ui run dev
    ```

    The UI will be available at `http://127.0.0.1:5173`.

### Docker Compose Setup

The configurations are set in `.env` and overridden in `compose.yaml`. If you need to change them, edit these files before starting the services.

1. Ensure Docker and Docker Compose are installed.

2. Clone the repository:

    ```bash
    git clone https://github.com/FreeFlyingSheep/stock-analysis
    cd stock-analysis
    ```

3. Configure environment variables:

    ```bash
    cp .env.example .env
    # Edit .env with your database credentials and settings
    ```

4. Run the Docker Compose setup:

    ```bash
    docker compose up -d
    ```

    This will start all necessary services including PostgreSQL, MinIO, MCP, the API server, the worker, and the frontend UI (via Nginx).
    If you update the code or configuration, rebuild the images with:

    ```bash
    docker compose up -d --build --force-recreate
    ```

    You can access the services at `http://127.0.0.1:8080`.

5. Remove all local images after shutting down:

    ```bash
    docker compose down --rmi local
    ```

    If you want to remove the volumes as well, use:

    ```bash
    docker compose down -v --rmi local
    ```

If you have dumped the database, you can restore it by running `docker exec -i stock-analysis-postgres-1 psql -U postgres -d stock_analysis < data/data.sql`, ignoring the error messages about existing objects.

### Kubernetes Setup

Take Minikube as an example for local Kubernetes deployment (MCP is not supported due to hardware limitations).
The `.env` file is not used in this setup; instead, configure environment variables directly in the Kustomize files.

1. Ensure you have Minikube running and `kubectl` configured.

   Enable the Ingress addon if not already enabled:

   ```bash
   minikube addons enable ingress
   ```

2. Clone the repository:

    ```bash
    git clone https://github.com/FreeFlyingSheep/stock-analysis
    cd stock-analysis
    ```

3. Build Docker images for Minikube:

    ```bash
    ./scripts/build.sh
    ```

4. Set up the Kubernetes resources using Kustomize:

    ```bash
    kubectl apply -k configs/k8s/overlays/dev
    ```

5. Get service IP and port:

    ```bash
    minikube ip
    kubectl get svc -n ingress-nginx ingress-nginx-controller
    ```

    Access the app at `http://<MINIKUBE_IP>:<NODE_PORT>`.

    If you are using Minikube in WSL2 (not via Docker Desktop), you may need to set up port forwarding:

    ```bash
    kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80
    ```

    Then access the app at `http://localhost:8080`.

6. Remove the Kubernetes resources when done:

    ```bash
    kubectl delete -k configs/k8s/overlays/dev
    ```

## Configuration Files & Data

### API Specifications

See [configs/api/README.md](configs/api/README.md) for details on:

- Adding new API endpoints
- YAML structure and conventions
- Maintaining endpoint specifications

### Scoring Rules

See [configs/rules/README.md](configs/rules/README.md) for details on:

- Writing scoring rules
- Metric definitions
- Filter specifications
- Rule versioning

### Prompts

See [configs/prompts/README.md](configs/prompts/README.md) for details on:

- Writing prompt templates for the chatbot

### Data Sample

See [data/sample/README.md](data/sample/README.md) for details on:

- Sample data format

### Reports

See [data/reports/README.md](data/reports/README.md) for details on:

- Metadata format

## Frontend UI

See [ui/README.md](ui/README.md) for details on:

- Frontend development

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
