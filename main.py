import logging
import numpy as np
import datetime

import requests
from flask import Flask
from flask_restful import Api, Resource

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
api = Api(app)

NASA_API_KEY = "v9IuYe5UNjJUikdhNfapmn8HhRYJvATWCCSQIYhQ"
NASA_NEOWS_BASE_URL = "https://api.nasa.gov/neo/rest/v1/feed"


def is_date_valid(date: str) -> bool:
    '''
    :param start_date: date in format YYYY-MM-DD
    :param end_date: date in format YYYY-MM-DD
    :return: true if date in format YYYY-MM-DD, false otherwise
    '''
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False
    return True


def clip_end_date_to_seven_days(start_date: str, end_date: str) -> str:
    datetime_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    datetime_end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    day_span = (datetime_end_date - datetime_start_date).days

    return end_date if day_span <= 7 else str((datetime_start_date + datetime.timedelta(days=7)).date())


class RestController(Resource):
    def get(self, start_date: str, end_date: str):
        logging.info(f"/space_objects GET start_date={start_date}, end_date={end_date}")

        if not is_date_valid(start_date):
            return [{"error": "invalid start_date"}], 400
        if not is_date_valid(end_date):
            return [{"error": "invalid end_date"}], 400

        end_date = clip_end_date_to_seven_days(start_date, end_date)
        print(start_date)
        print(end_date)

        return sort_response(get_nasa_neows_rest_api_response(start_date, end_date))


api.add_resource(RestController, "/space_objects/<string:start_date>/<string:end_date>")


def get_nasa_neows_rest_api_response(start_date: str, end_date: str):
    request_url = NASA_NEOWS_BASE_URL + "?" \
                  + "start_date=" + start_date + "&end_date=" + end_date + "&api_key=" + NASA_API_KEY

    response = requests.get(request_url)
    return response


def sort_response(nasa_api_response) -> list:
    '''
    Space objects, sorted by their closest approach distance to Earth,
    each containing object name, size estimate, time and distance of the closest encounter.

    sorting algorithm:
    1. flatten the first dictionary having just big list of all entries.
    2. get all indexes sorted by entry["close_approach_data"][0]["miss_distance"]["kilometers"]

    :param nasa_api_response: Response from GET request to "https://api.nasa.gov/neo/rest/v1/feed"
    :return: list of dicts, keys = {name', 'size_estimate', closest_encounter_time', closest_encounter_distance'}
    '''
    near_earth_objects = nasa_api_response.json()['near_earth_objects']

    entries_all_days = []
    for entries_of_one_day in near_earth_objects.values():
        for entry in entries_of_one_day:
            entries_all_days.append(entry)

    miss_distances_in_km = np.zeros(len(entries_all_days))
    for i in range(len(entries_all_days)):
        miss_distances_in_km[i] = entries_all_days[i]["close_approach_data"][0]["miss_distance"]["kilometers"]

    indices = np.argsort(miss_distances_in_km)

    response = []
    for i in range(len(indices)):
        entry = entries_all_days[indices[i]]

        response.append({
            'name': entry['name'],
            'size_estimate': entry['estimated_diameter'],
            'closest_encounter_time': entry["close_approach_data"][0]["close_approach_date"],
            'closest_encounter_distance': entry["close_approach_data"][0]["miss_distance"]
        })
    return response


if __name__ == '__main__':
    app.run(debug=True)

# Todo:
#   !handle missing values during sorting and outputting object values!
#   implement cache?

"""
Nasa NeoWs REST api response structure:

near_earth_objects (dict): keys=consecutive days
consecutive day(list) of space objects
space object (dict): dict_keys([
    'links', 
    'id', 
    'neo_reference_id', 
    'name', 
    'nasa_jpl_url', 
    'absolute_magnitude_h', 
    'estimated_diameter', 
    'is_potentially_hazardous_asteroid', 
    'close_approach_data', 
    'is_sentry_object'
    ])
    
close_approach_data is our value for sorting entries

close_approach_data list of 1 element = (dict) : dict_keys([
    'close_approach_date', 
    'close_approach_date_full', 
    'epoch_date_close_approach',
    'relative_velocity', 
    'miss_distance', 
    'orbiting_body'
    ])
     
We sort by 'miss_distance' (dict) : dict_keys([
    'astronomical',
    'lunar',
    'kilometers',
    'miles'
    ]) 
    
we will use kilometers

entry_dist_km = near_earth_objects["2023-01-01"][entry]["close_approach_data"][0]["miss_distance"]["kilometers"])
"""
