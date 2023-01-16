import requests

BASE = "http://127.0.0.1:5000"
start_date = "2023-01-01"
end_date = "2023-03-01"

# response = requests.get(BASE + "/space_objects?" + "start_date=" + start_date + "&end_date=" + end_date)
response = requests.get(BASE + "/space_objects" + "/" + start_date + "/" + end_date)
print(response.status_code)
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
