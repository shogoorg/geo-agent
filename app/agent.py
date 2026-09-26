# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
# Standard ADK Agent & BigQuery Analytics Setup
# Reference: https://google.github.io/agents-cli/guide/observability/bq-agent-analytics/
#
# Core ADK agent definition including tools, Gemini model configuration, and
# BigQuery telemetry streaming. Kept as the standard base reference for rebuilding
# custom agent logic and tool implementations from scratch.
# ==============================================================================
import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
import logging
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.cloud import bigquery


MODEL = "gemini-3.7-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


root_agent = Agent(
    # Keep in sync with agents-cli-manifest.yaml: agents-cli derives this name
    # from the project `name:` recorded there, and telemetry reports it as
    # gen_ai.agent.name. Renaming the agent only here makes the two disagree,
    # and anything selecting traces by name stops finding this agent's.
    # name="my_agent",
    name="geo_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a helpful AI assistant designed to provide accurate and useful information.",
    tools=[get_weather, get_current_time],
)
import os

# Initialize BigQuery Analytics
_plugins = []
_project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
_dataset_id = os.environ.get("BQ_ANALYTICS_DATASET_ID", "adk_agent_analytics")
_location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east1")

if _project_id:
    try:
        bq = bigquery.Client(project=_project_id)
        bq.create_dataset(f"{_project_id}.{_dataset_id}", exists_ok=True)

        _plugins.append(
            BigQueryAgentAnalyticsPlugin(
                project_id=_project_id,
                dataset_id=_dataset_id,
                location=_location,
                config=BigQueryLoggerConfig(
                    gcs_bucket_name=os.environ.get("BQ_ANALYTICS_GCS_BUCKET"),
                    connection_id=os.environ.get("BQ_ANALYTICS_CONNECTION_ID"),
                ),
            )
        )
    except Exception as e:
        logging.warning(f"Failed to initialize BigQuery Analytics: {e}")

app = App(
    root_agent=root_agent,
    name="app",
    plugins=_plugins,
)

# ==============================================================================
# MAUI Agent Bundle Initialization (Matching agent/python/__main__.py logic)
# ==============================================================================
from google.adk.models.llm_request import LlmRequest
import agent
from agent import MAUIAgent
import agent_config
from agent_config import AgentConfig, FallbackMode
import agent_with_grounding
from agent_with_grounding import MAUIAgentWithGrounding
import agent_with_templates
from agent_with_templates import MAUIAgentWithTemplates
from app.agent_executor import MAUIAgentExecutor


class GeminiAdapter(Gemini):
    """Adapter to route LiteLlm calls through ADK's native Gemini model (google.genai.Client)
    using MODEL ('gemini-3.7-flash') so that OpenTelemetry Prompt-Response logging
    (GoogleGenAiSdkInstrumentor) instruments all client/A2A calls."""

    def __init__(self, model: str = MODEL, **kwargs):
        kwargs.pop("model", None)
        super().__init__(
            model=MODEL,
            retry_options=types.HttpRetryOptions(attempts=3),
            **kwargs,
        )

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ):
        if llm_request.model is None:
            llm_request.model = self.model
        async for item in super().generate_content_async(llm_request, stream=stream):
            yield item


# Replace LiteLlm in upstream MAUI agent modules with GeminiAdapter
agent.LiteLlm = GeminiAdapter
agent_with_templates.LiteLlm = GeminiAdapter
agent_with_grounding.LiteLlm = GeminiAdapter

# Inject analytics plugin into MAUIAgent's Runner factory without modifying upstream package
# Note: uses _plugins list from the BigQuery analytics initialization block above
if _plugins:
    analytics_plugin = _plugins[0]
    _original_build_runner = MAUIAgent._build_runner

    def _build_runner_with_analytics(self, agent):
        runner = _original_build_runner(self, agent)
        if hasattr(runner, "plugin_manager"):
            runner.plugin_manager.register_plugin(analytics_plugin)
        return runner

    MAUIAgent._build_runner = _build_runner_with_analytics

def create_maui_bundle(base_url: str | None = None):
    """Initializes and returns the MAUI agents and executor matching a2ui-samples."""
    default_app_url = os.getenv("APP_URL", "http://127.0.0.1:8000")
    if not default_app_url.endswith("/a2a/app"):
        default_app_url = f"{default_app_url.rstrip('/')}/a2a/app"
    resolved_base_url = base_url or default_app_url
    default_agent_name = os.getenv("A2UI_DEFAULT_AGENT", "TEMPLATE")
    fallback_mode_env = os.getenv("A2UI_FALLBACK_MODE")
    if fallback_mode_env:
        config = AgentConfig(fallback_mode=FallbackMode(fallback_mode_env))
    else:
        config = AgentConfig()

    ui_agent = MAUIAgent(base_url=resolved_base_url)
    grounding_agent = MAUIAgentWithGrounding(base_url=resolved_base_url)
    template_agent = MAUIAgentWithTemplates(base_url=resolved_base_url, config=config)

    agent_map = {
        "MAUIAGENT": ui_agent,
        "BASE": ui_agent,
        "MAUIAGENTWITHGROUNDING": grounding_agent,
        "GROUNDING": grounding_agent,
        "MAUIAGENTWITHTEMPLATES": template_agent,
        "TEMPLATE": template_agent,
    }

    normalized_agent = default_agent_name.upper()
    if normalized_agent not in agent_map:
        raise ValueError(
            f"Unknown agent: {default_agent_name}. Expected one of {list(agent_map.keys())}"
        )

    default_agent = agent_map[normalized_agent]

    agent_executor = MAUIAgentExecutor(
        default_agent=default_agent,
        grounding_agent=grounding_agent,
        template_agent=template_agent,
    )

    return {
        "default_agent": default_agent,
        "ui_agent": ui_agent,
        "grounding_agent": grounding_agent,
        "template_agent": template_agent,
        "agent_executor": agent_executor,
    }

