# Guide

This guide provides a comprehensive operational and lifecycle manual for **geo-agent**, aligned with the [Google Agents CLI Guide](https://google.github.io/agents-cli/guide/).

---

## Overview

### Getting Started

`geo-agent` is an AI agent combining Google's **Agent Development Kit (ADK)** and the **A2UI (Agentic UI) Maps Toolkit**, managed using **Agents CLI**.

```bash
# 1. Clone the repository
git clone https://github.com/shogoorg/geo-agent.git
cd geo-agent

# 2. Install dependencies
agents-cli install

# 3. Configure environment files (.env)
# Backend (.env):
cp .env.example .env
# Edit .env and configure either Vertex AI (GOOGLE_CLOUD_PROJECT) or Google AI Studio (GEMINI_API_KEY="your-key-here")

# Frontend Local Development (.env.development):
cp client/web/react/.env.development.example client/web/react/.env.development
# Edit and set your GOOGLE_MAPS_API_KEY="your-maps-api-key"

# 4. Start the development playground
agents-cli playground
```

> 💡 **Production Frontend (.env.production):**
> When deploying to Cloud Run, copy and configure `client/web/react/.env.production.example` as `client/web/react/.env.production` with your deployed Cloud Run backend URL.

---

## Development

### Development Guide

#### Local Development & Testing
```bash
# Launch ADK web playground with hot reload at http://localhost:8080
agents-cli playground

# Start the full MAUI FastAPI backend server
uv run python -m app.fast_api_app

# Start the React frontend client
cd client/web/react && npm run dev
```

#### Code Quality & Testing
```bash
# Run Ruff linting and formatting checks
agents-cli lint

# Run unit and integration test suites
uv run pytest tests/unit tests/integration
```

#### Package Management
```bash
# Add or remove dependencies using uv
uv add <package>
uv remove <package>
```

---

### Project Structure

```
geo-agent/
├── app/                       # Core agent backend (FastAPI & Google ADK)
│   ├── agent.py               # Main agent logic & MAUI bundle registration
│   ├── agent_executor.py      # MAUI Agent Executor bridge
│   ├── fast_api_app.py        # FastAPI server & A2A protocol routes
│   └── app_utils/             # Session, artifact, and route helpers
├── client/                    # Client applications
│   ├── web/react/             # React + Vite web client with A2UI renderer
│   ├── android/               # Android client
│   └── ios/                   # iOS client
├── deployment/                # Terraform infrastructure definitions
│   └── terraform/single-project/
├── docs/                      # Project documentation and operational guides
│   └── guide.md               # Complete lifecycle and operational guide
├── vendor/                    # Vendored upstream dependencies
│   └── maui-a2ui-python/      # Synced from googlemaps/a2ui
├── tests/                     # Evaluation datasets and test suites
│   └── eval_dataset.json      # Benchmark test cases
├── agents-cli-manifest.yaml   # Agents CLI project metadata
├── GEMINI.md                  # Context document for AI coding assistants
└── pyproject.toml             # Project dependencies and toolchain config
```

---

### Extensions

`geo-agent` supports tool extensions and standard protocol integrations:
* **Model Context Protocol (MCP)**: Tools such as Grounding Lite MCP connect seamlessly via standard ADK toolsets.
* **A2A (Agent-to-Agent) Protocol**: Standardized endpoints under `/a2a/app` enable multi-agent collaboration and testing via the [A2A Inspector](https://github.com/a2aproject/a2a-inspector).
* **Vendor Sync Script**: Synchronize updates from `googlemaps/a2ui` using `./scripts/sync-a2ui.sh`.

---

## Evaluation

### Evaluation Guide

Evaluation ensures that prompt iterations, model upgrades, and new tools maintain high quality:

#### 1. Evaluation Datasets
Datasets are stored in `tests/eval_dataset.json` with canned inputs and evaluation rubrics.

#### 2. Run Evaluation
```bash
agents-cli eval run
```

#### 3. Inspect Evaluation Results
Reports in `artifacts/grade_results/` analyze response accuracy, tool selection correctness, latency, and token expenditure.

---

## Deployment & Operations

### Deployment

Deploying `geo-agent` to Google Cloud Run involves infrastructure provisioning and container deployment.

#### Step 1: Provision Infrastructure via Terraform
```bash
# Set GCP project
gcloud config set project <your-project-id>

# Run Terraform single-project provisioning
agents-cli infra single-project --apply --project <your-project-id>

# Inspect provisioned resources
agents-cli infra show
```

#### Step 2: Deploy Backend Application
```bash
agents-cli deploy --project <your-project-id>
```

#### Step 3: Configure Public Invocation
Allow unauthenticated traffic for web and mobile clients:
```bash
gcloud run services add-iam-policy-binding geo-agent \
  --region <your-region> \
  --project <your-project-id> \
  --member="allUsers" \
  --role="roles/run.invoker"
```

#### Step 4: Deploy Frontend (React Web Client)
```bash
cd client/web/react

gcloud run deploy geo-agent-web \
  --source . \
  --project <your-project-id> \
  --region <your-region> \
  --allow-unauthenticated
```

---

### Observability

Dual-channel observability provides both real-time monitoring and offline data analysis.

#### 1. Cloud Trace & Raw Completions
Raw prompt-response completions are archived in GCS and queryable via BigQuery external tables:
```bash
# Check raw completion logs in GCS
gsutil ls gs://<project-id>-<project-name>-logs/completions/

# Query completion records in BigQuery
bq query --use_legacy_sql=false \
  "SELECT * FROM \`<project-id>.<project-name>_telemetry.completions\` LIMIT 10"
```

#### 2. BigQuery Agent Analytics Plugin (`agent_events`)
When `BQ_ANALYTICS_DATASET_ID` is set, structured event records stream directly to BigQuery:

##### Recent Events
```sql
SELECT
  timestamp,
  event_type,
  agent,
  user_id,
  status
FROM
  `YOUR_PROJECT_ID.YOUR_AGENT_NAME_telemetry.agent_events`
ORDER BY
  timestamp DESC
LIMIT 100;
```

##### Tool Calls and Errors
```sql
SELECT
  timestamp,
  JSON_VALUE(content, '$.tool') AS tool_name,
  JSON_VALUE(content, '$.args') AS tool_args,
  status,
  error_message
FROM
  `YOUR_PROJECT_ID.YOUR_AGENT_NAME_telemetry.agent_events`
WHERE
  event_type IN ('TOOL_COMPLETED', 'TOOL_ERROR')
ORDER BY
  timestamp DESC;
```

##### LLM Token Usage by Agent and Model
```sql
SELECT
  agent,
  JSON_VALUE(attributes, '$.model_version') AS model,
  SUM(CAST(JSON_VALUE(attributes, '$.usage_metadata.prompt_token_count') AS INT64)) AS total_prompt_tokens,
  SUM(CAST(JSON_VALUE(attributes, '$.usage_metadata.candidates_token_count') AS INT64)) AS total_completion_tokens,
  SUM(CAST(JSON_VALUE(attributes, '$.usage_metadata.total_token_count') AS INT64)) AS grand_total_tokens
FROM
  `YOUR_PROJECT_ID.YOUR_AGENT_NAME_telemetry.agent_events`
WHERE
  event_type = 'LLM_RESPONSE'
  AND JSON_VALUE(attributes, '$.usage_metadata.prompt_token_count') IS NOT NULL
GROUP BY
  agent, model;
```

