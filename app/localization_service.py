"""Place Localization Service for GeoAgent.

Enriches A2UI response payloads by resolving localized place display names,
real-time opening hours, and Pro-tier place metadata from Google Places API (New).
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

# FieldMask for Place Details (Pro SKU tier: excludes Enterprise fields)
PRO_TIER_FIELD_MASK = (
    "displayName,formattedAddress,primaryTypeDisplayName,businessStatus,"
    "currentOpeningHours,rating,userRatingCount,priceLevel"
)


class PlaceLocalizationService:
    """Resolves localized place names and Pro-tier metadata from Google Places API (New)."""

    def __init__(self) -> None:
        # cache_key: "{language}:{place_id}" -> { ... metadata dict ... }
        self._cache: dict[str, dict[str, Any]] = {}

    def get_place_details(self, place_id: str, language: str = "ja") -> dict[str, Any]:
        """Fetches localized metadata and opening hours from Google Places API (New)."""
        cache_key = f"{language}:{place_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
        if not api_key:
            return {"name": "", "open_now": None}

        url = f"https://places.googleapis.com/v1/places/{place_id}?languageCode={language}"
        req = urllib.request.Request(
            url,
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": PRO_TIER_FIELD_MASK,
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    name = body.get("displayName", {}).get("text", "")
                    address = body.get("formattedAddress", "")
                    primary_type = body.get("primaryTypeDisplayName", {}).get(
                        "text", ""
                    )
                    business_status = body.get("businessStatus")
                    opening_hours = body.get("currentOpeningHours", {})
                    open_now = opening_hours.get("openNow")
                    next_open_time = opening_hours.get("nextOpenTime")
                    weekday_descriptions = opening_hours.get("weekdayDescriptions")
                    rating = body.get("rating")
                    user_rating_count = body.get("userRatingCount")
                    price_level = body.get("priceLevel")

                    result = {
                        "name": name,
                        "address": address,
                        "primary_type": primary_type,
                        "business_status": business_status,
                        "open_now": open_now,
                        "next_open_time": next_open_time,
                        "weekday_descriptions": weekday_descriptions,
                        "rating": rating,
                        "user_rating_count": user_rating_count,
                        "price_level": price_level,
                    }
                    if name:
                        self._cache[cache_key] = result
                        return result
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            logger.warning("Localization skipped for place %s: %s", place_id, e)

        return {"name": "", "open_now": None}

    def get_display_name(self, place_id: str, language: str = "ja") -> str:
        """Backward-compatible helper to get localized name."""
        details = self.get_place_details(place_id, language=language)
        return str(details.get("name", ""))

    @staticmethod
    def _populate_pro_metadata(target: dict[str, Any], details: dict[str, Any]) -> None:
        """Injects Pro-tier place metadata fields into the target dictionary."""
        mapping = [
            ("name", "name"),
            ("address", "address"),
            ("primary_type", "primaryType"),
            ("business_status", "businessStatus"),
            ("open_now", "openNow"),
            ("next_open_time", "nextOpenTime"),
            ("weekday_descriptions", "weekdayDescriptions"),
            ("rating", "rating"),
            ("user_rating_count", "userRatingCount"),
            ("price_level", "priceLevel"),
        ]
        for src_key, dst_key in mapping:
            val = details.get(src_key)
            if val is not None and val != "":
                target[dst_key] = val
            elif src_key == "open_now" and val is not None:
                target[dst_key] = val

    def localize_parts(self, parts: list[Any], language: str = "ja") -> list[Any]:
        """Translates place names and enriches openNow within A2A Parts."""
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

        place_details_map: dict[str, dict[str, Any]] = {}

        def _enrich_node(node: dict[str, Any]) -> dict[str, Any] | None:
            p_id = node.get("placeId")
            if not p_id:
                return None
            details = self.get_place_details(p_id, language=language)
            place_details_map[p_id] = details
            if details.get("name"):
                node["label"] = details["name"]
            return details

        # ----------------------------------------------------------------------
        # Pass 1: GoogleMap.markers および routes (origin / destination) の同期
        # ----------------------------------------------------------------------
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
                                    _enrich_node(marker)

                        routes = comp.get("routes", [])
                        if isinstance(routes, list):
                            for route in routes:
                                if isinstance(route, dict):
                                    orig = route.get("origin")
                                    if isinstance(orig, dict):
                                        _enrich_node(orig)
                                    dest = route.get("destination")
                                    if isinstance(dest, dict):
                                        _enrich_node(dest)

        # ----------------------------------------------------------------------
        # Pass 2: updateDataModel.places への Pro 枠メタデータ注入
        # ----------------------------------------------------------------------
        for action in actions:
            if not isinstance(action, dict):
                continue
            update_dm = action.get("updateDataModel", {})
            if isinstance(update_dm, dict):
                val = update_dm.get("value", {})
                if isinstance(val, dict):
                    for k, items in val.items():
                        if k in ("destinationDetails", "originDetails", "h3Clusters"):
                            continue
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    p_id = item.get("id") or item.get("placeId")
                                    if p_id:
                                        details = place_details_map.get(
                                            p_id
                                        ) or self.get_place_details(
                                            p_id, language=language
                                        )
                                        self._populate_pro_metadata(item, details)

        return parts


localization_service = PlaceLocalizationService()
