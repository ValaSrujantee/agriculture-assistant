"""Modular OpenWeather current-conditions provider with an honest fallback."""
import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen


class WeatherNotConfigured(Exception):
    pass


class WeatherProviderError(Exception):
    pass


class OpenWeatherProvider:
    endpoint = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key=None):
        self.api_key = api_key if api_key is not None else os.getenv("OPENWEATHER_API_KEY", "")

    def current(self, location: str):
        if not self.api_key:
            raise WeatherNotConfigured("Weather service is not configured. Please enter weather values manually.")
        query = urlencode({"q": location, "appid": self.api_key, "units": "metric"})
        try:
            with urlopen(f"{self.endpoint}?{query}", timeout=6) as response:
                raw = json.loads(response.read().decode("utf-8"))
            return {
                "temperature": float(raw["main"]["temp"]),
                "humidity": float(raw["main"]["humidity"]),
                "rainfall": float(raw.get("rain", {}).get("1h", 0.0)),
                "source": "weather_service", "location": location,
            }
        except Exception as exc:
            raise WeatherProviderError("Weather could not be retrieved for that location. Enter weather values manually.") from exc
