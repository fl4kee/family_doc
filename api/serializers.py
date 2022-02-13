from rest_framework import serializers  # type: ignore

from weather.models import WeatherInformation


class WeatherInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherInformation
        fields = "__all__"
