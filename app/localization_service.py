"""Place Localization Service for GeoAgent.

Enriches A2UI response payloads by resolving localized place display names
from Google Places API (New) based on user-selected language for Template mode.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


class PlaceLocalizationService:
    """Resolves localized place names from Google Places API (New) using standard library."""

    def __init__(self) -> None:
        # In-memory cache: "{language}:{place_id}" -> "ダブルトールコーヒー 新宿御苑"
        self._cache: dict[str, str] = {}

    def get_display_name(self, place_id: str, language: str = "ja") -> str:
        """Fetches localized place display name from Google Places API (New) with caching."""
        cache_key = f"{language}:{place_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
        if not api_key:
            return ""

        url = f"https://places.googleapis.com/v1/places/{place_id}?languageCode={language}"
        req = urllib.request.Request(
            url,
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "displayName",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    name = body.get("displayName", {}).get("text", "")
                    if name:
                        self._cache[cache_key] = name
                        return name
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            logger.warning("Localization skipped for place %s: %s", place_id, e)

        return ""

    def localize_parts(self, parts: list[Any], language: str = "ja") -> list[Any]:
        """Translates place names within A2A Parts to the requested language in memory."""
        actions: list[dict[str, Any]] = []
        for part in parts:
            data = None
            if hasattr(part, "root") and hasattr(part.root, "data"):
                data = part.root.data
            elif hasattr(part, "data"):
                data = part.data
            elif isinstance(part, dict) and part.get("kind") == "data":
                data = part.get("data")

            if isinstance(data, dict):
                actions.append(data)
            elif isinstance(data, list):
                actions.extend([item for item in data if isinstance(item, dict)])

        # 1. Update GoogleMap.markers labels with localized place names
        place_to_name: dict[str, str] = {}
        for action in actions:
            if not isinstance(action, dict):
                continue
            update_comps = action.get("updateComponents", {})
            if isinstance(update_comps, dict):
                for comp in update_comps.get("components", []):
                    if isinstance(comp, dict) and comp.get("component") == "GoogleMap":
                        markers = comp.get("markers", [])
                        if isinstance(markers, list):
                            for marker in markers:
                                if isinstance(marker, dict):
                                    p_id = marker.get("placeId")
                                    if p_id:
                                        localized_name = self.get_display_name(
                                            p_id, language=language
                                        )
                                        if localized_name:
                                            marker["label"] = localized_name
                                            place_to_name[p_id] = localized_name

        # 2. Update updateDataModel places with localized place names
        for action in actions:
            if not isinstance(action, dict):
                continue
            update_dm = action.get("updateDataModel", {})
            if isinstance(update_dm, dict):
                val = update_dm.get("value", {})
                if isinstance(val, dict):
                    for _k, items in val.items():
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    p_id = item.get("id") or item.get("placeId")
                                    if p_id:
                                        localized_name = place_to_name.get(
                                            p_id
                                        ) or self.get_display_name(
                                            p_id, language=language
                                        )
                                        if localized_name:
                                            item["name"] = localized_name

        return parts


localization_service = PlaceLocalizationService()
