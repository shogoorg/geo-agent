import pytest
from app.spatial.h3_service import spatial_service


def test_enrich_a2ui_data_with_routes() -> None:
    data = [
        {
            "updateComponents": {
                "components": [
                    {
                        "component": "GoogleMap",
                        "routes": [
                            {
                                "origin": {
                                    "lat": 35.6580339,
                                    "lng": 139.7016358,
                                    "label": "渋谷駅",
                                    "placeId": "ChIJnxAAO1aLGGARJqvi8d4oczM",
                                },
                                "destination": {
                                    "lat": 35.6894807,
                                    "lng": 139.6916863,
                                    "label": "東京都庁",
                                    "placeId": "ChIJoTcat9SMGGAR6GGG8zdcZvE",
                                },
                            }
                        ],
                    }
                ]
            }
        },
        {
            "updateDataModel": {
                "value": {}
            }
        },
    ]

    enriched = spatial_service.enrich_a2ui_data(data, resolution=9)

    # Check updateComponents
    map_comp = enriched[0]["updateComponents"]["components"][0]
    route = map_comp["routes"][0]
    assert "h3Cell" in route["origin"]
    assert "h3Cell" in route["destination"]
    assert route["origin"]["h3Cell"] == spatial_service.lat_lng_to_cell(35.6580339, 139.7016358, 9)
    assert route["destination"]["h3Cell"] == spatial_service.lat_lng_to_cell(35.6894807, 139.6916863, 9)

    # Check updateDataModel
    value = enriched[1]["updateDataModel"]["value"]
    assert value["h3Resolution"] == 9
    assert value["originH3Cell"] == route["origin"]["h3Cell"]
    assert value["destinationH3Cell"] == route["destination"]["h3Cell"]
