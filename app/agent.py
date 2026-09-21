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
import os


import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


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
        city: The name of the city to get the current time for.

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
    name="geo_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a helpful AI assistant designed to provide accurate and useful information.",
    tools=[get_weather, get_current_time],
)

app = App(
    root_agent=root_agent,
    name="app",
)

# ==============================================================================
# MAUI Agent Bundle Initialization (Matching agent/python/__main__.py logic)
# ==============================================================================
from agent import MAUIAgent
from agent_config import AgentConfig, FallbackMode
from agent_with_grounding import MAUIAgentWithGrounding
from agent_with_templates import MAUIAgentWithTemplates
from app.agent_executor import MAUIAgentExecutor

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

