# geo-agent

Built with agents-cli, googlemaps/a2ui, and googlemaps-samples/a2ui:
- **[agents-cli](https://github.com/google/agents-cli)**: The CLI and skills that turn any coding assistant into an expert at creating, evaluating, and deploying AI agents on Google Cloud.
- **[googlemaps/a2ui](https://github.com/googlemaps/a2ui)**: The A2UI implementation for the Maps Agentic UI Toolkit.
- **[googlemaps-samples/a2ui](https://github.com/googlemaps-samples/a2ui)**: Samples for the A2UI implementation for the Maps Agentic UI Toolkit.

Simple ReAct agent
Agent generated with `agents-cli` version `1.5.0`

## Project Structure

```
geo-agent/
├── app/                       # Core agent backend (FastAPI & Google ADK)
│   ├── agent.py               # Main agent logic & MAUI bundle definition
│   ├── agent_executor.py      # MAUI agent executor integration
│   ├── fast_api_app.py        # FastAPI Backend server with A2A routes
│   └── app_utils/             # App utilities, A2A endpoints, and services
├── client/                    # Client applications
│   ├── web/react/             # React web client with A2UI renderer
│   ├── android/               # Android client
│   └── ios/                   # iOS client
├── deployment/                # Deployment infrastructure (Terraform)
├── scripts/                   # Utility scripts (e.g., sync-a2ui.sh)
├── tests/                     # Unit, integration, and evaluation datasets
├── vendor/                    # Vendored dependencies (maui-a2ui-python)
├── Dockerfile                 # Backend container definition for Cloud Run
├── GEMINI.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies and packaging
```

### Upstream References
* **`app/`**: Implements the agent backend referencing **[googlemaps-samples/a2ui](https://github.com/googlemaps-samples/a2ui)** (`agent/python/agent_executor.py`, etc.).
* **`vendor/`**: Contains `maui-a2ui-python` synced directly from **[googlemaps/a2ui](https://github.com/googlemaps/a2ui)** (`agent/python_agent/`).

> 💡 **Tip:** Use [Antigravity CLI](https://antigravity.google/) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

Evaluate agent behavior:

```bash
agents-cli eval run
```

### Agent Configuration & Local Development

#### 1. Configure the Default Agent (`.env`)

Set `A2UI_DEFAULT_AGENT` in `.env` to choose your default agent mode:

```bash
# Option 1: Template Agent (Recommended for low-latency local search & directions)
A2UI_DEFAULT_AGENT=TEMPLATE

# Option 2: Grounding Agent (Vertex AI Maps Grounding)
# A2UI_DEFAULT_AGENT=GROUNDING

# Option 3: Base Agent (Dynamic A2UI component generation via Grounding Lite MCP)
# A2UI_DEFAULT_AGENT=BASE
```

> 💡 **Tip (Per-Query Switching without restart):**
> You can test different agent implementations against the running server by prefixing your prompt:
> * `[GROUNDING] <query>` ➔ Routes directly to `MAUIAgentWithGrounding`
> * `[TEMPLATE] <query>` ➔ Routes directly to `MAUIAgentWithTemplates`
> * `<query>` (no prefix) ➔ Routes to your configured default agent

#### 2. Start the MAUI Agent Backend

```bash
uv run python -m app.fast_api_app
```

#### 3. Start the React Web Client

```bash
cd client/web/react
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

> 💡 **Syncing Vendor Code (Optional):**
> If you need to re-sync or update the vendored `a2ui` package with `./scripts/sync-a2ui.sh [tag]`, ensure the [a2ui repository](https://github.com/googlemaps/a2ui) is cloned at `../a2ui` (or specify the path via `A2UI_REPO_DIR`).


## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |
| `agents-cli deploy`  | Deploy agent to Cloud Run                                                                   || [A2A Inspector](https://github.com/a2aproject/a2a-inspector) | Launch A2A Protocol Inspector                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

## Deployment

#### 1. Configure the Production Agent (`.env` or Deploy Flag)

Cloud Run automatically inherits `A2UI_DEFAULT_AGENT` from your root `.env` file during deployment:

```bash
# Option 1: Template Agent (Recommended for low-latency local search & directions)
A2UI_DEFAULT_AGENT=TEMPLATE

# Option 2: Grounding Agent (Vertex AI Maps Grounding)
# A2UI_DEFAULT_AGENT=GROUNDING

# Option 3: Base Agent (Dynamic A2UI component generation via Grounding Lite MCP)
# A2UI_DEFAULT_AGENT=BASE
```

> 💡 **Tip (Overriding Agent Mode at Deploy Time):**
> You can override the agent mode at deploy time without modifying `.env` using `--update-env-vars`:
> * `agents-cli deploy ... --update-env-vars A2UI_DEFAULT_AGENT=GROUNDING` ➔ Deploy as Grounding Agent
> * `agents-cli deploy ... --update-env-vars A2UI_DEFAULT_AGENT=TEMPLATE` ➔ Deploy as Template Agent

#### 2. Deploy the MAUI Agent Backend (`geo-agent`)

##### 2.1 Set Up Infrastructure (Terraform)

Provision the Google Cloud infrastructure (Cloud Run, GCS telemetry logs bucket, BigQuery dataset/views, and IAM roles) using Terraform via `agents-cli`:

```bash
# Set your GCP project
gcloud config set project <your-project-id>

# Provision single-project infrastructure (Terraform)
agents-cli infra single-project --apply --project <your-project-id>
```

To view the provisioned infrastructure status:

```bash
agents-cli infra show
```

##### 2.2 Deploy Agent Application

Deploy the application container and code:

```bash
# Deploy using agents-cli (inherits .env settings automatically)
agents-cli deploy --project <your-project-id>
```

##### 2.3 Allow Public Invocation

Allow public invocation (required for client access):

```bash
gcloud run services add-iam-policy-binding geo-agent \
  --region <your-region> \
  --project <your-project-id> \
  --member="allUsers" \
  --role="roles/run.invoker"
```

> 💡 Take note of the deployed Service URL (e.g. `https://geo-agent-xxxx.run.app`). The backend endpoint will be `https://geo-agent-xxxx.run.app/a2a/app`.

#### 3. Deploy the React Web Client (`geo-agent-web`)

Configure `client/web/react/.env.production` with your deployed backend URL and Maps API Key:

```properties
GOOGLE_MAPS_API_KEY=<your-google-maps-api-key>
VITE_A2A_SERVER_URL=https://<your-backend-url>.run.app/a2a/app
SERVER_URL=https://<your-backend-url>.run.app/a2a/app
```

Deploy the web client to Cloud Run:

```bash
cd client/web/react

gcloud run deploy geo-agent-web \
  --source . \
  --project <your-project-id> \
  --region <your-region> \
  --allow-unauthenticated
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

### 1. Cloud Trace & Prompt-Response Logging (`completions`)

Prompt-response completions are exported via OpenTelemetry to Cloud Storage and exposed as external tables in BigQuery:

```bash
PROJECT_ID="your-dev-project-id"
PROJECT_NAME="your-project-name"

# Check for telemetry files in GCS
gsutil ls gs://${PROJECT_ID}-${PROJECT_NAME}-logs/completions/

# Query completions telemetry in BigQuery
bq query --use_legacy_sql=false \
  "SELECT * FROM \`${PROJECT_ID}.${PROJECT_NAME}_telemetry.completions\` LIMIT 10"
```

### 2. BigQuery Agent Analytics (`agent_events`)

When `BQ_ANALYTICS_DATASET_ID` is configured, structured ADK agent events, tool calls, and token usage are streamed directly via `BigQueryAgentAnalyticsPlugin`.

#### 1. Recent Events
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

#### 2. Tool Calls and Errors
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

#### 3. LLM Token Usage by Agent and Model
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

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/). Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability.
See the [A2A Inspector docs](https://github.com/a2aproject/a2a-inspector) for details.
