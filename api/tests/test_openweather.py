import json
import os

import pytest
from aioresponses import aioresponses

from api.openweather import OpenWeather


def read_json(filename: str) -> dict:
    with open(filename) as f:
        return json.load(f)


test_data = read_json(os.path.join(os.path.dirname(__file__), "test_data.json"))
response_data = read_json(
    os.path.join(os.path.dirname(__file__), "response_from_weather.json")
)

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
                   Chrome/94.0.4606.61 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,\
               */*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Charset": "utf-8",
}


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m


@pytest.mark.django_db
def test_func(mock_aioresponse, mocker):
    mocker.patch("api.openweather.OpenWeather._get_coordinates", return_value=200)
    mocker.patch(
        "api.openweather.OpenWeather._get_weather_data", return_value=response_data
    )
    mock_aioresponse.get(
        "http://api.openweathermap.org/geo/1.0/direct?q=Moscow,RU&appid=f0897466f7a688ef809c8746944508f8",
        headers=HEADERS,
        payload={"lat": 55.7504461, "lon": 37.6174943},
    )

    data = OpenWeather("Moscow", "RU", "08.02.2022T12:00").get_weather()
    assert data['current'] == test_data
