from app.localization_service import PlaceLocalizationService


def test_localize_parts_enriches_pro_tier_metadata() -> None:
    service = PlaceLocalizationService()

    # Mock get_place_details with Pro-tier fields
    service._cache["ja:place_123"] = {
        "name": "ダブルトールコーヒー 新宿御苑",
        "address": "東京都新宿区新宿1-34-13",
        "primary_type": "カフェ・喫茶",
        "business_status": "OPERATIONAL",
        "open_now": False,
        "next_open_time": "2026-10-04T23:00:00Z",
        "weekday_descriptions": [
            "月曜日: 8:00 - 18:00",
            "火曜日: 8:00 - 18:00",
            "水曜日: 8:00 - 18:00",
            "木曜日: 8:00 - 18:00",
            "金曜日: 8:00 - 18:00",
            "土曜日: 10:00 - 18:00",
            "日曜日: 定休日",
        ],
        "rating": 4.7,
        "user_rating_count": 410,
        "price_level": "PRICE_LEVEL_MODERATE",
    }

    parts = [
        {
            "kind": "data",
            "data": {
                "updateComponents": {
                    "components": [
                        {
                            "component": "GoogleMap",
                            "markers": [
                                {
                                    "placeId": "place_123",
                                    "label": "Old Name",
                                }
                            ],
                        }
                    ]
                }
            },
        },
        {
            "kind": "data",
            "data": {
                "updateDataModel": {
                    "value": {
                        "places": [
                            {
                                "id": "place_123",
                                "name": "Old Name",
                            }
                        ]
                    }
                }
            },
        },
    ]

    localized = service.localize_parts(parts, language="ja")

    # Check marker enrichment (only label is updated, no redundant place metadata on pins)
    marker = localized[0]["data"]["updateComponents"]["components"][0]["markers"][0]
    assert marker["label"] == "ダブルトールコーヒー 新宿御苑"
    assert "openNow" not in marker
    assert "address" not in marker

    # Check data model Pro-tier enrichment
    place = localized[1]["data"]["updateDataModel"]["value"]["places"][0]
    assert place["name"] == "ダブルトールコーヒー 新宿御苑"
    assert place["address"] == "東京都新宿区新宿1-34-13"
    assert place["primaryType"] == "カフェ・喫茶"
    assert place["businessStatus"] == "OPERATIONAL"
    assert place["openNow"] is False
    assert place["nextOpenTime"] == "2026-10-04T23:00:00Z"
    assert len(place["weekdayDescriptions"]) == 7
    assert place["rating"] == 4.7
    assert place["userRatingCount"] == 410
    assert place["priceLevel"] == "PRICE_LEVEL_MODERATE"


def test_localize_parts_enriches_route_destination() -> None:
    service = PlaceLocalizationService()

    service._cache["ja:tokyo_gov"] = {
        "name": "東京都庁",
        "address": "東京都新宿区西新宿2-8-1",
        "primary_type": "市役所・役場",
        "business_status": "OPERATIONAL",
        "open_now": True,
        "next_open_time": "2026-10-05T00:00:00Z",
        "weekday_descriptions": ["月曜日: 8:30 - 17:45"],
        "rating": 4.5,
        "user_rating_count": 1200,
        "price_level": None,
    }

    parts = [
        {
            "kind": "data",
            "data": {
                "updateComponents": {
                    "components": [
                        {
                            "component": "GoogleMap",
                            "routes": [
                                {
                                    "origin": {
                                        "lat": 35.658,
                                        "lng": 139.701,
                                        "label": "渋谷駅",
                                    },
                                    "destination": {
                                        "lat": 35.689,
                                        "lng": 139.691,
                                        "label": "Old Dest",
                                        "placeId": "tokyo_gov",
                                    },
                                }
                            ],
                        }
                    ]
                }
            },
        },
        {
            "kind": "data",
            "data": {
                "updateDataModel": {
                    "value": {}
                }
            },
        },
    ]

    localized = service.localize_parts(parts, language="ja")

    # Check route destination enrichment in updateComponents (label only, no redundant metadata)
    route = localized[0]["data"]["updateComponents"]["components"][0]["routes"][0]
    dest = route["destination"]
    assert dest["label"] == "東京都庁"
    assert "address" not in dest
    assert "businessStatus" not in dest
    assert "openNow" not in dest

    # Check updateDataModel (destinationDetails should not be injected)
    val = localized[1]["data"]["updateDataModel"]["value"]
    assert "destinationDetails" not in val
