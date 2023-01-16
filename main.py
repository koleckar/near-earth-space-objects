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

MAX_DAY_SPAN = 365


def is_date_valid(date: str) -> bool:
    '''
    :param date: (str) date in format YYYY-MM-DD
    :return: true if date in format YYYY-MM-DD, false otherwise
    '''
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False
    return True


@DeprecationWarning
def clip_end_date_to_seven_days(start_date: str, end_date: str) -> str:
    datetime_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    datetime_end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    day_span = (datetime_end_date - datetime_start_date).days

    return end_date if day_span <= 7 else str((datetime_start_date + datetime.timedelta(days=7)).date())


def get_day_span(start_date: str, end_date: str) -> int:
    datetime_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    datetime_end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    day_span = (datetime_end_date - datetime_start_date).days
    assert day_span >= 0, "Negative day span!"
    return day_span


class RestController(Resource):
    def get(self, start_date: str, end_date: str):

        logging.info(f"/space_objects GET start_date={start_date}, end_date={end_date}")

        if not is_date_valid(start_date):
            return [{"error": "invalid start_date"}], 400
        if not is_date_valid(end_date):
            return [{"error": "invalid end_date"}], 400

        nasa_responses = get_nasa_responses(start_date, end_date)

        return sort_response(nasa_responses)


api.add_resource(RestController, "/space_objects/<string:start_date>/<string:end_date>")


def get_date_pairs(start_date: str, end_date: str) -> list:
    day_span = get_day_span(start_date, end_date)
    day_span = min(day_span, MAX_DAY_SPAN)  # todo: signal span clipping in GET response?

    date_pair = []
    if day_span <= 7:
        date_pair.append([start_date, end_date])
        return date_pair

    datetime_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    date_pairs = []

    i_start = 0
    in_span = True
    while in_span:
        if i_start + 7 >= day_span:
            in_span = False

        span = min(6, max(0, day_span - i_start))
        date_pairs.append([
            str((datetime_start_date + datetime.timedelta(days=i_start)).date()),
            str((datetime_start_date + datetime.timedelta(days=i_start + span)).date())
        ])
        i_start += 7

    logging.info(date_pairs)
    return date_pairs


def get_nasa_responses(start_date: str, end_date: str) -> list:
    '''
    Calls nasa rest service (multiple times if needed). Limit is set to MAX_DAY_SPAN=365

    :return: list of entries from all days, aggregated from all nasa responses.
    '''
    nasa_responses = []
    for start, end in get_date_pairs(start_date, end_date):
        logging.info(f"making nasa GET call")
        nasa_responses.append(get_nasa_response(start, end))

    entries_all_days = []
    for nasa_response in nasa_responses:
        for entries_of_one_day in nasa_response.json()['near_earth_objects'].values():
            for entry in entries_of_one_day:
                entries_all_days.append(entry)

    return entries_all_days


def get_nasa_response(start_date: str, end_date: str):
    request_url = NASA_NEOWS_BASE_URL + "?" \
                  + "start_date=" + start_date + "&end_date=" + end_date + "&api_key=" + NASA_API_KEY

    response = requests.get(request_url)
    return response


def sort_response(entries_all_days: list) -> list:
    '''
    Space objects, sorted by their closest approach distance to Earth,
    each containing object name, size estimate, time and distance of the closest encounter.

    sorting algorithm:
    1. flatten the first dictionary having just big list of all entries.
    2. get all indexes sorted by entry["close_approach_data"][0]["miss_distance"]["kilometers"]

    :param entries_all_days: Response from possible multiple GET request to "https://api.nasa.gov/neo/rest/v1/feed"
    :return: list of dicts, keys = {'name', 'size_estimate', 'closest_encounter_time', 'closest_encounter_distance'}
    '''
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
#   partial sort while waiting for nasa GET response?
