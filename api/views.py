from operator import itemgetter

from django.core.handlers.wsgi import WSGIRequest
from rest_framework.decorators import api_view  # type: ignore
from rest_framework.response import Response  # type: ignore

from .errors import WrongDate, generate_error_info
from .openweather import OpenWeather


@api_view(("GET",))
def get_weather_data(request: WSGIRequest) -> Response:
    """Getting data from openweather api."""
    country_code, city, dt = itemgetter("country_code", "city", "date")(request.GET)
    try:
        weather = OpenWeather(city, country_code, dt).get_weather()
    except WrongDate as e:
        return Response(generate_error_info(str(e)))
    return Response(weather)
