"""Uber H3 Spatial Indexing Service tailored to A2UI v0.9 schema (Template & Grounding)."""

from __future__ import annotations

import time
from typing import Any

import h3


class H3SpatialService:
    """Uber H3 (Hexagonal Hierarchical Spatial Index) service."""

    def __init__(self, default_resolution: int = 9, ttl_seconds: int = 3600) -> None:
        self.default_resolution = default_resolution
        self.ttl_seconds = ttl_seconds
        # key: "{res}:{h3_cell}" -> { "expires_at": float, "place": dict }
        self._cache: dict[str, dict[str, Any]] = {}

    def lat_lng_to_cell(
        self, lat: float, lng: float, resolution: int | None = None
    ) -> str:
        """Converts latitude and longitude coordinates to an H3 cell ID string."""
        res = resolution if resolution is not None else self.default_resolution
        return str(h3.latlng_to_cell(lat, lng, res))

    def get_k_ring(self, center_cell: str, ring_size: int = 1) -> list[str]:
        """Returns the center cell plus surrounding k layers of hexagonal cells."""
        return [str(cell) for cell in h3.grid_disk(center_cell, ring_size)]

    def set_cached_place(self, cell_key: str, place: dict[str, Any]) -> None:
        """Saves place information into an in-memory spatial cache keyed by H3 cell."""
        self._cache[cell_key] = {
            "expires_at": time.time() + self.ttl_seconds,
            "place": place,
        }

    def enrich_a2ui_data(self, data: Any, resolution: int = 9) -> Any:
        """Traverses A2UI v0.9 payload and injects h3Cell attributes for both TEMPLATE and GROUNDING modes."""
        if not isinstance(data, list):
            return data

        place_id_to_h3: dict[str, str] = {}

        # ----------------------------------------------------------------------
        # Pass 1: Traverse GoogleMap.markers in updateComponents
        # (Coordinates exist here for both TEMPLATE and GROUNDING modes)
        # ----------------------------------------------------------------------
        for action in data:
            if not isinstance(action, dict):
                continue

            if "updateComponents" in action:
                components = action["updateComponents"].get("components", [])
                if isinstance(components, list):
                    for comp in components:
                        if (
                            isinstance(comp, dict)
                            and comp.get("component") == "GoogleMap"
                        ):
                            markers = comp.get("markers", [])
                            if isinstance(markers, list):
                                for marker in markers:
                                    if (
                                        isinstance(marker, dict)
                                        and "lat" in marker
                                        and "lng" in marker
                                    ):
                                        m_lat = float(marker["lat"])
                                        m_lng = float(marker["lng"])
                                        cell_id = self.lat_lng_to_cell(
                                            m_lat, m_lng, resolution
                                        )
                                        marker["h3Cell"] = cell_id

                                        p_id = marker.get("placeId")
                                        if p_id:
                                            place_id_to_h3[p_id] = cell_id
                                            cell_key = f"{resolution}:{cell_id}"
                                            self.set_cached_place(cell_key, marker)

        # ----------------------------------------------------------------------
        # Pass 2: Traverse updateDataModel (supports places, cafes, or any list key)
        # ----------------------------------------------------------------------
        for action in data:
            if not isinstance(action, dict):
                continue

            if "updateDataModel" in action:
                value = action["updateDataModel"].get("value", {})
                if isinstance(value, dict):
                    value["h3Resolution"] = resolution

                    for _key, items in value.items():
                        if isinstance(items, list):
                            for item in items:
                                if not isinstance(item, dict):
                                    continue

                                # Case A: item contains direct lat/lng (TEMPLATE mode)
                                if "lat" in item and "lng" in item:
                                    lat = float(item["lat"])
                                    lng = float(item["lng"])
                                    item["h3Cell"] = self.lat_lng_to_cell(
                                        lat, lng, resolution
                                    )
                                # Case B: item only contains id/placeId (GROUNDING mode)
                                else:
                                    p_id = item.get("id") or item.get("placeId")
                                    if p_id and p_id in place_id_to_h3:
                                        item["h3Cell"] = place_id_to_h3[p_id]

        return data

    def query_nearby(
        self, lat: float, lng: float, resolution: int | None = None
    ) -> dict[str, Any]:
        """Queries the center hexagonal cell plus surrounding 6 neighbors (7 cells total)."""
        res = resolution if resolution is not None else self.default_resolution
        center_cell = self.lat_lng_to_cell(lat, lng, res)
        target_cells = self.get_k_ring(center_cell, ring_size=1)
        return {
            "resolution": res,
            "center_cell": center_cell,
            "target_cells_count": len(target_cells),
            "k_ring_cells": target_cells,
        }


spatial_service = H3SpatialService(default_resolution=9)
