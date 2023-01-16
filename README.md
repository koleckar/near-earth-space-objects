# near-earth-space-objects

Offers rest GET call returning response as json list of sorted near-earth-space-objects retrieved from NASA NeoWs rest api.  

------------------------------------------------------------------------
REST Api:  

GET at 127.0.0.1:5000/space_objects/start_date/end_date  


-start_date in format YYYY-MM-DD  
-
end_date in format YYYY-MM-DD  


The Feed date limit is only 7 Days for NASA NeoWs api, so if requested day span is larger than week, multiple calls are performed to nasa rest api, aggregating results.  
There is however limit chosen for one year. Can be switched off by adding extra boolean paramater of day_limit=False.


```json
[
    {
        "name": "(2015 AE45)",
        "size_estimate": {
            "kilometers": {
                "estimated_diameter_min": 0.0231502122,
                "estimated_diameter_max": 0.0517654482
            },
            "meters": {
                "estimated_diameter_min": 23.150212221,
                "estimated_diameter_max": 51.7654482198
            },
            "miles": {
                "estimated_diameter_min": 0.0143848705,
                "estimated_diameter_max": 0.0321655483
            },
            "feet": {
                "estimated_diameter_min": 75.9521422633,
                "estimated_diameter_max": 169.8341531374
            }
        },
        "closest_encounter_time": "2023-01-01",
        "closest_encounter_distance": {
            "astronomical": "0.0569979859",
            "lunar": "22.1722165151",
            "kilometers": "8526777.284930033",
            "miles": "5298293.7197111354"
        }
    },
    .
    .
    .
]


```
