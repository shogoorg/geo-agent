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
        {"updateDataModel": {"value": {}}},
    ]

    enriched = spatial_service.enrich_a2ui_data(data, resolution=9)

    # Check updateComponents (routes should NOT have redundant h3Cell)
    map_comp = enriched[0]["updateComponents"]["components"][0]
    route = map_comp["routes"][0]
    assert "h3Cell" not in route["origin"]
    assert "h3Cell" not in route["destination"]
    orig_cell = spatial_service.lat_lng_to_cell(35.6580339, 139.7016358, 9)
    dest_cell = spatial_service.lat_lng_to_cell(35.6894807, 139.6916863, 9)

    # Check updateDataModel (route commute without places should remain empty)
    value = enriched[1]["updateDataModel"]["value"]
    assert "h3Resolution" not in value
    assert "originH3Cell" not in value
    assert "destinationH3Cell" not in value


def test_enrich_a2ui_data_with_h3_clusters() -> None:
    # 2 places in cell A, 1 place in cell B
    data = [
        {
            "updateDataModel": {
                "value": {
                    "places": [
                        {
                            "name": "Cafe A1",
                            "lat": 35.6885,
                            "lng": 139.7105,
                        },
                        {
                            "name": "Cafe A2",
                            "lat": 35.6886,
                            "lng": 139.7106,
                        },
                        {
                            "name": "Cafe B1",
                            "lat": 35.6580,
                            "lng": 139.7016,
                        },
                    ]
                }
            }
        }
    ]

    enriched = spatial_service.enrich_a2ui_data(data, resolution=9)
    value = enriched[0]["updateDataModel"]["value"]

    assert "h3Clusters" in value
    clusters = value["h3Clusters"]
    assert len(clusters) == 2

    # Cluster with 2 places should be first due to count desc sort
    assert clusters[0]["count"] == 2
    assert len(clusters[0]["places"]) == 2
    assert clusters[1]["count"] == 1
    assert len(clusters[1]["places"]) == 1
