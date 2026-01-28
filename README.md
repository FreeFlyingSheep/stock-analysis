# Stock Analysis

Stock Analysis is a comprehensive A-share fundamental scoring agent for Chinese stock analysis. It provides data crawling from multiple sources (CNInfo, Yahoo Finance), rule-based scoring, filtering, and a RESTful API for querying results.

This project is developed with the assistance of AI tools:

- GitHub Copilot for code and documentation generation, and suggestions
- ChatGPT for design discussions and problem-solving

## Disclaimer

**This tool is for reference and educational purposes only. The data and analysis provided are for informational purposes and should not be considered as financial advice.**

I do **NOT** provide any financial, investment, or trading recommendations. Users should conduct their own research and consult with qualified financial advisors before making any investment decisions.

**Investment involves risk, including possible loss of principal.** Past performance is not indicative of future results. Use this tool at your own risk and discretion.

## Features

- **Stock Data Management**: Store and query Chinese A-share stock information with classifications and industries
- **Multi-source Data Crawling**: Fetch data from CNInfo and Yahoo Finance with automatic rate limiting and retries
- **Rule-based Scoring**: Declarative YAML rules for computing financial metrics and overall scores
- **Stock Filtering**: Filter stocks based on configurable scoring rules
- **Analysis Results Storage**: Persist computed metrics and scores to database
- **RESTful API**: FastAPI-based async API with automatic Swagger/ReDoc documentation
- **Job Queue**: PgQueuer for async job processing (data crawling and analysis)
- **Async Database Operations**: SQLAlchemy async with PostgreSQL for high performance
- **CSV Import**: Bulk import stock data from CSV files
- **Pagination & Filtering**: Query stocks with filtering by classification/industry and pagination
- **Frontend Dashboard**: SvelteKit UI with stock explorer, floating chat widget, bilingual (EN/中文) toggle, and data explorer parsing configs/api + data/api samples
- **Database Migrations**: Alembic integration for schema versioning
- **Type Safety**: Full type hints with Pylance validation
- **Google Docstrings**: Comprehensive documentation throughout the codebase
- **Code Quality**: Type checking and formatting standards
- **Docker Compose and Kubernetes Deployment**: Containerized deployment for easy setup
- **MCP Server**: FastMCP integration for FastAPI services

## Features TODO List

High priority:

- Integrate LLM for advanced stock analysis and explanations
- Add a chatbot interface for querying stock information

Medium priority:

- Expand data source integrations
- Add RAG (Retrieval-Augmented Generation) capabilities

Low priority:

- Avoid duplicate jobs in PgQueuer
- Add observability and monitoring with logging aggregation
- Deploy with Docker and Kubernetes
- Refine frontend UI/UX design
- Map stock industry sectors to classifications correctly

## Requirements

- Python 3.14+
- PostgreSQL 18+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

**Warning: all the setup methods below will drop and recreate the database, erasing any existing data.**

If you want to keep existing data, skip the database initialization step (``./scripts/init.sh``) and ensure the database schema is up to date by running Alembic migrations manually.

[Docker Compose setup](#docker-compose-setup) is **recommended** for most users due to its simplicity and ease of use.
[Local development setup](#local-development-setup) is only intended for development and testing.
[Kubernetes setup](#kubernetes-setup) is for production deployment scenarios, but due to hardware limitations, only partial modules are supported and tested.

### Local Development Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/FreeFlyingSheep/stock-analysis
    cd stock-analysis
    ```

2. Install dependencies using uv:

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

4. Initialize the database (install PostgreSQL and [pgvector](https://github.com/pgvector/pgvector) first):

    ```bash
    ./scripts/init.sh
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

    This will start all necessary services including PostgreSQL, the vLLM server, the API server, and the frontend UI.
    If you update the code or configuration, rebuild the images with:

    ```bash
    docker compose up -d --build --force-recreate
    ```

    You can access the services at `http://127.0.0.1`.

5. Remove all local images after shutting down:

    ```bash
    docker compose down --rmi local
    ```

    If you want to remove the volumes as well, use:

    ```bash
    docker compose down -v --rmi local
    ```

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

## Architecture

### Data Flow

1. **Data Crawling**: PgQueuer jobs fetch data from CNInfo and Yahoo Finance
2. **API Adapters**: Validate parameters and handle HTTP requests with retries
3. **Database Storage**: Raw API responses stored in dedicated tables
4. **Rule Engine**: Computes metrics from raw data using YAML rules
5. **Analysis**: Generates scores and stores analysis results
6. **API Access**: RESTful endpoints provide access to stocks and analysis

### Key Components

- **Adapters**: Handle external API integrations (CNInfo, Yahoo Finance)
- **Services**: Implement business logic (stock queries, analysis)
- **Jobs**: Async tasks for data processing (crawling, analysis)
- **Routers**: FastAPI endpoints for HTTP API
- **Models**: SQLAlchemy ORM models for database
- **Schemas**: Pydantic models for request/response validation

## Configuration Files

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

### Sample Data

See [data/api/README.md](data/api/README.md) for details on:

- API response samples
- Adding new response examples
- Maintaining sample data

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
