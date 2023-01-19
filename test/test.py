import time

import requests

BASE = "http://127.0.0.1:5000"
start_date = "2022-04-01"
end_date = "2022-04-01"

t1 = time.time()
response = requests.get(BASE + "/space_objects", {"start_date": start_date, "end_date": end_date})
t2 = time.time()

print("response time:", t2 - t1, " seconds")

print("response status code=", response.status_code)
if response.status_code == 400:
    print(response.json())
if response.status_code == 200:
    for entry in response.json():
        for key, value in entry.items():
            if key == "name":
                print(f"{key}: {value}", end=" ")
            if key == "closest_encounter_time":
                print(f"| {value}")

# test invalid start, end date
# test start date > end date
# test span(start_date, end_date) > 7
# test span(start_date, end_date) > MAX_DAY_SPAN
