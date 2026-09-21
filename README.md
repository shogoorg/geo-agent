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

Start the MAUI agent backend:

```bash
cd agent/python
A2UI_DEFAULT_AGENT=TEMPLATE uv run . --host 127.0.0.1
```

Start the React web client:

```bash
cd client/web/react
npm run dev
```

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

```bash
gcloud config set project <your-project-id>
agents-cli deploy --project <your-project-id>
```

```bash
gcloud run services add-iam-policy-binding geo-agent \
  --region  <your-region> \
  --project  <your-project-id> \
  --member="allUsers" \
  --role="roles/run.invoker"
```

```bash
cd client/web/react
gcloud run deploy geo-agent-web \
  --source . \
  --project  <your-project-id> \
  --region  <your-region> \
  --allow-unauthenticated
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

```bash
agents-cli infra single-project --apply -project YOUR_DEV_PROJECT_ID
```
```bash
agents-cli infra show
```

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/). Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability.
See the [A2A Inspector docs](https://github.com/a2aproject/a2a-inspector) for details.
