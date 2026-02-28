# Data Pipeline Templates

Reusable templates for data extraction, transformation, and loading workflows. Built for reliability, observability, and maintainability.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/followbl/data-pipeline-templates.git
cd data-pipeline-templates
pip install -r requirements.txt
```

## Templates

| Template | Purpose | Complexity |
|----------|---------|------------|
| `scrapers/basic-http.py` | Simple HTTP scraping with retries | Beginner |
| `scrapers/dynamic-browser.py` | JavaScript-rendered content | Intermediate |
| `apis/rest-pagination.py` | Paginated API ingestion | Intermediate |
| `apis/graphql-client.py` | GraphQL query handling | Intermediate |
| `etl/csv-to-parquet.py` | Format conversion pipeline | Beginner |
| `etl/validation-schema.py` | Data quality validation | Intermediate |
| `scheduling/cron-wrapper.py` | Production cron patterns | Intermediate |

## Project Structure

```
data-pipeline-templates/
├── scrapers/           # Web extraction patterns
├── apis/              # API ingestion patterns  
├── etl/               # Transformation utilities
├── scheduling/        # Orchestration patterns
├── utils/             # Shared helpers
├── tests/             # Test examples
└── examples/          # Full working examples
```

## Core Principles

1. **Fail Fast, Retry Smart** — Exponential backoff, circuit breakers
2. **Observable** — Structured logging, metrics, tracing
3. **Resilient** — Graceful degradation, idempotent writes
4. **Tested** — Unit + integration test patterns

## License

MIT — Use freely, contribute back.
