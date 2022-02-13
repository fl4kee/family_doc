import asyncio
import logging
import time
from datetime import date, datetime
from typing import Optional, Union

import pytz  # type: ignore
from aiohttp import ClientSession
from django.conf import settings
from dotenv import dotenv_values

from api.errors import (WeatherException, WrongCity, WrongDate,
                        generate_error_info)
from weather.models import WeatherInformation

from .serializers import WeatherInformationSerializer

config = dotenv_values(".env")
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class OpenWeather:
    """ Class for interacting with Openweather api.

    Attributes:
        headers(dict): headers for requests
        city(str): city
        country_code(str): country code
        local_timezone(str): current time zone
        lon(int/None): longitude
        lat(int/None): latitude
        forecast(bool: represents if data is forecast or historical
        api_key(str/None): api key, you can get it here https://openweathermap.org/
        dt_datetime(datetime) - date in datetime format
        dt_unix(int) - date in unix format
    """

    def __init__(self, city: str, country_code: str, dt: str) -> None:
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
                        Chrome/94.0.4606.61 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,\
                    */*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        }
        self.service_url: str = "https://api.openweathermap.org"
        self.city: str = self.strip_and_lower(city)
        self.country_code: str = self.strip_and_lower(country_code)
        self.local_timezone: str = settings.TIME_ZONE
        self.lon: Optional[int] = None
        self.lat: Optional[int] = None
        self.forecast: bool = False
        self.api_key: Optional[str] = config["API_KEY"]
        self.dt_datetime: datetime = self._convert_to_datetime(dt.strip())
        self.dt_unix: int = self._convert_datetime_to_unix()

    def get_weather(self) -> Union[Optional[dict], list]:
        """Launches coroutine to get weather information from Openweather API or database.
        If current date is less than dt_datetime then we get a forecast. Otherwise historical weather
        If data is present in database then we retrieve it without making a call to api

        Returns:
            (dict/list/None): weather data.
            If forecast then its list with weather on a day with 3 hours periodicy.
            If data is from db or historical then returns dictionary with weather on specified date and time
        """
        if self.dt_datetime > datetime.now().astimezone(pytz.timezone(self.local_timezone)):
            self.forecast = True
        weather: Union[Optional[dict], list] = self._get_weather_data_from_db()
        if not weather:
            try:
                weather = asyncio.run(self.gather_weather_data())
                self._insert_weather_data_to_db(weather)
            except WeatherException as e:
                return generate_error_info(str(e))
        return weather

    async def gather_weather_data(self) -> Union[list, dict]:
        """Getting data from Openweather API.

        Returns:
            (dict/list): list of weather data if its forecast
                         dictionary if its historical data
        """
        async with ClientSession(headers=self.headers) as session:
            try:
                # Getting coordinates
                await self._get_coordinates(session)
                # Getting weather in range of next 5 days
                if self.forecast:
                    weather_data: Union[dict, list] = await self._get_weather_forecast(session)
                    return weather_data
                # Getting weather in range of last 5 days
                else:
                    weather_data = await self._get_weather_data(session)
                    return weather_data
            except (WrongCity, WrongDate) as e:
                raise WeatherException(str(e))

    def _get_weather_data_from_db(self) -> Optional[dict]:
        """Getting data from database

        Returns:
            (dict/None): data from database. None if data is not found
        """
        dt: Union[date, datetime] = self.dt_datetime

        if self.forecast:
            dt = self.dt_datetime.date()
        try:
            serializer = WeatherInformationSerializer(
                WeatherInformation.objects.get(city=self.city, date=dt, country_code=self.country_code)
            )
            logger.info(f"Got data from database for {self.dt_datetime}.")
            return serializer.data["data"]
        except WeatherInformation.DoesNotExist:
            return None

    def _insert_weather_data_to_db(
        self, weather_data: Union[Optional[dict], list]
    ) -> None:
        """Inserting to database

        Args:
            weather_data(dict/list/None): data that needs to be inserted
        """
        dt: Union[date, datetime] = self.dt_datetime
        # Если это прогноз, то убираем время, так как прогноз выдается на день с интервалом в 3 часа
        if self.forecast:
            dt = self.dt_datetime.date()
        if weather_data:
            weather_obj = WeatherInformation(city=self.city, date=dt, data=weather_data, country_code=self.country_code)
            weather_obj.save()
            logger.info("Data is saved to database")

    async def _get_weather_forecast(self, session: ClientSession) -> list:
        """Getting forecast for next 5 days

        Args:
            session(ClientSession): aiohttp session

        Returns:
            (list): data that is filtered on specified day
        """
        query = f"/data/2.5/forecast?lat={self.lat}&lon={self.lon}&appid={self.api_key}"
        data = await self._get_http(session, query)
        logger.info(f"Got forecasted weather data for {self.dt_datetime}.")
        filtered_weather_data = self._filter_weather_data(data)
        if not filtered_weather_data:
            raise WrongDate("you can get weather only for last and next five days")
        return filtered_weather_data

    async def _get_weather_data(self, session: ClientSession) -> dict:
        """Getting weather data from Openweather for last 5 days

        Args:
            session(ClientSession): aiohttp session

        Returns:
            (dict): historical weather data on specified date and time
        """
        query = f"/data/2.5/onecall/timemachine?lat={self.lat}&lon={self.lon}&dt={self.dt_unix}&appid={self.api_key}"
        data = await self._get_http(session, query)
        logger.info(f"Got historical weather data for {self.dt_datetime}.")
        if "current" not in data:
            raise WrongDate("you can get weather only for last and next five days")
        return data['current']

    async def _get_http(self, session: ClientSession, query: str) -> dict:
        async with session.get(self.service_url + query) as response:
            logger.info(f'Запрос {self.service_url + query}')
            data = await response.json()
            return data

    async def _get_coordinates(self, session: ClientSession) -> None:
        """Get coordinates and set them to corresponding attrubutes.

        Args:
            session(ClientSession): aiohttp session
        """
        query = (f"/geo/1.0/direct?q={self.city},{self.country_code}&appid={self.api_key}")
        async with session.get(self.service_url + query) as response:
            try:
                data = (await response.json())[0]
                self.lon, self.lat = data["lon"], data["lat"]
                logger.info(f"Got coordinates. Longitude: {self.lon}, Latitude: {self.lat}")
            except IndexError:
                raise WrongCity("wrong city")

    def _convert_datetime_to_unix(self) -> int:
        """Convert date from datetime to unix
        Returns:
            (int): date in unix
        """
        return int(time.mktime(self.dt_datetime.timetuple()))

    def _convert_to_datetime(self, dt: str) -> datetime:
        """Convert date string to datetime

        Args:
            dt(str): date in string format

        Returns:
            (datetime): date in datetime format
        """
        format = "%d.%m.%YT%H:%M"
        try:
            local_dt = datetime.strptime(dt, format)
        except ValueError:
            raise WrongDate('wrong datetime')
        return local_dt.astimezone(pytz.timezone(self.local_timezone))

    def _filter_weather_data(self, data: dict) -> list:
        """Filtering data on passed date

        Args:
            data(dict): data that is need to be filtered

        Returns:
            (list): filtered data
        """
        format = "%Y-%m-%d %H:%M:%S"
        return list(
            filter(lambda x: datetime.strptime(x["dt_txt"], format).date() == self.dt_datetime.date(), data["list"],)
        )

    @staticmethod
    def strip_and_lower(str_: str) -> str:
        """Removes spaces and switch to lower case.
        Args:
            str_(str): string to change

        Returns:
            str: stripped and lowercased string
        """
        return str_.strip().lower()
