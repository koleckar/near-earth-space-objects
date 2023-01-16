import requests

BASE = "http://127.0.0.1:5000"
start_date = "2023-01-01"
end_date = "2023-01-30"

#response = requests.get(BASE + "/space_objects?" + "start_date=" + start_date + "&end_date=" + end_date)
response = requests.get(BASE + "/space_objects" + "/" + start_date + "/" + end_date)
print(response.status_code)
for entry in response.json():
    for key, value in entry.items():
        print(f"{key}: {value}")

