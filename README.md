# near-earth-space-objects

Exposes rest GET returning list of sorted near-earth-space-objects retrieved from NASA NeoWs rest api.  

------------------------------------------------------------------------
REST API:  

GET at localhost:5000/space_objects?start_date=2022-04-01&end_date=2022-06-01  
  
retrieving near-earth-space-objects from nasa neows api between 2022-04-01 and 2022-06-01  
App listens on localhost port 5000, GET exposed at "/space_objects", expecting two arguments 'start_date' and 'end_date'  

- start_date as string in format YYYY-MM-DD  
- end_date as string in format YYYY-MM-DD  


Feed date limit is only 7 Days for NASA NeoWs api, so if requested day span is larger than week, internally multiple asynchronous calls are performed to nasa rest api, aggregating results for final sorting. There is however limit set to 365 days, for safety reasons.


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
        "closest_encounter_time": "2023-Jan-01 00:59",
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
Response, near-earth-space-objects sorted by closest recorded distance, a list of maps, with keys 
 - "name"
 - "size_estimate"
 - "closest_encounter_time"
 - "closest_encounter_distance"   
 
----------------------------------------------------------------------------------
note on flask async routes.  
Flask(> 2.0) has async routes, it however does not have async request stack.   

"Eventhough asynchronous code can be executed in Flask, it's executed within the context of a synchronous framework.
Various async tasks can be executed in a single request, each async task must finish before a response gets sent back. 
Other Python web frameworks that support ASGI (Asynchronous Server Gateway Interface), which supports asynchronous call stacks so that routes can run concurrently:
Django >= 3.2, FastAPI, Quart. " -from https://testdriven.io/blog/flask-async/  
  
However, in this task, the taks is not stateless, we have to wait for all the async tasks to finish, because we return sorted result.  

----------------------------------------------------------------------------------

issues/TODOs:
- Switch off day limit by adding extra boolean paramater?
- implement cache?
- partial sort while waiting for nasa GET response?
- tests

