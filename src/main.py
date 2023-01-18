import logging
import datetime
import asyncio
import numpy as np

import requests
import httpx
from flask import Flask, request, abort

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# get_space_objects_args = reqparse.RequestParser()
# get_space_objects_args.add_argument("start_date", type=str, required=True,
#                                     help="Start date in format yyyy-mm-dd, required")
# get_space_objects_args.add_argument("end_date", type=str, required=True,
#                                     help="End date in format yyyy-mm-dd, same date as start_date or after, required.")
# get_space_objects_args.add_argument("day_limit_off", type=bool, default=False,
#                                     help="If True, turns of day-span(end_date - start_date) limit., not required.")

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
    return day_span


def end_date_before_start_date(start_date: str, end_date: str) -> bool:
    return False if get_day_span(start_date, end_date) >= 0 else True


@app.get("/space_objects")
async def get_space_objects():
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    logging.info(f"/space_objects GET start_date={start_date}, end_date={end_date}")

    if not is_date_valid(start_date):
        return {"error": "invalid start_date"}, 400
    if not is_date_valid(end_date):
        return {"error": "invalid end_date"}, 400
    if end_date_before_start_date(start_date, end_date):
        return {"error": "end_date before start_date"}, 400

    return sort_response(
        flatten_nasa_responses(
            await get_nasa_responses(start_date, end_date)))


def get_date_pairs(start_date: str, end_date: str) -> list:
    '''
    Calculates pairs of dates - dates of first and last days of consecutive weeks in the days interval
    given by start_date and end_date. The last pair can be shorter than 7 days

    :return: list of date pairs used for GET call to nasa api.
    '''
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
        if i_start + 6 >= day_span:  # count the first day too, so only +6
            in_span = False

        span = min(6, max(0, day_span - i_start))  # count the first day too, so only +6
        date_pairs.append([
            str((datetime_start_date + datetime.timedelta(days=i_start)).date()),
            str((datetime_start_date + datetime.timedelta(days=i_start + span)).date())
        ])
        i_start += 7

    logging.info(date_pairs)
    return date_pairs


async def get_nasa_responses(start_date: str, end_date: str):
    async with httpx.AsyncClient() as session:
        return await asyncio.gather(
            *[
                asyncio.create_task(get_nasa_response(session, start_date, end_date))
                for start_date, end_date in get_date_pairs(start_date, end_date)
            ]
        )


async def get_nasa_response(session: httpx.AsyncClient, start_date: str, end_date: str):
    url = NASA_NEOWS_BASE_URL + "?" \
          + "start_date=" + start_date + "&end_date=" + end_date + "&api_key=" + NASA_API_KEY

    logging.info("GET " + start_date + " " + end_date)

    return await session.get(url, timeout=httpx.Timeout(10.0, read=None))


def flatten_nasa_responses(nasa_responses: list) -> list:
    logging.info("All nasa responses received.")
    entries_all_days = []
    for nasa_response in nasa_responses:
        for entries_of_one_day in nasa_response.json()['near_earth_objects'].values():
            for entry in entries_of_one_day:
                entries_all_days.append(entry)

    return entries_all_days


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
            'closest_encounter_time': entry["close_approach_data"][0]["close_approach_date_full"],
            'closest_encounter_distance': entry["close_approach_data"][0]["miss_distance"]
        })
    return response


if __name__ == '__main__':
    app.run(debug=True)
