# import requests
#
# def get_weather(lat, lon):
#     url = "https://api.open-meteo.com/v1/forecast"
#     params = {
#         'latitude': lat,
#         'longitude': lon,
#         'current_weather': True,
#         'timezone': 'auto'
#     }
#     response = requests.get(url, params=params)
#     data = response.json()
#     if 'current_weather' not in data:
#         return "Weather info not available."
#     current = data['current_weather']
#     return f"Current temp: {current['temperature']}°C, Wind: {current['windspeed']} km/h"
# -------------------------------------------------------------------------------------------

import requests
from datetime import datetime, timedelta

def get_weather(lat, lon, mode=None):
    """
    Get weather info.

    mode:
      - None        -> current weather
      - "tomorrow"  -> tomorrow's forecast
      - "next7"     -> next 7 days forecast
      - "YYYY-MM-DD" (string) -> specific date forecast
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_mean",
        "forecast_days": 7,
        "timezone": "auto",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return f"Weather service error: {e}"

    # ---------- CURRENT WEATHER ----------
    if mode is None:
        if "current_weather" in data:
            current = data["current_weather"]
            return (
                f"Current Weather:\n"
                f"Temperature: {current['temperature']}°C\n"
                f"Wind Speed: {current['windspeed']} km/h"
            )
        return "Current weather not available."

    # ---------- DAILY DATA ----------
    daily = data.get("daily")
    if not daily:
        return "Forecast data not available."

    dates = daily.get("time", [])
    max_temp = daily.get("temperature_2m_max", [])
    min_temp = daily.get("temperature_2m_min", [])
    rain_prob = daily.get("precipitation_probability_mean", [])

    # safety: lengths must match
    if not (dates and len(dates) == len(max_temp) == len(min_temp) == len(rain_prob)):
        return "Incomplete forecast data received."

    # 🎯 TOMORROW WEATHER
    if isinstance(mode, str) and mode.lower() == "tomorrow":
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if tomorrow in dates:
            i = dates.index(tomorrow)
            return (
                f"Tomorrow's Weather ({tomorrow}):\n"
                f"Max: {max_temp[i]}°C\n"
                f"Min: {min_temp[i]}°C\n"
                f"Rain Chance: {rain_prob[i]}%"
            )
        return "Tomorrow's weather not available."

    # 🎯 NEXT 7 DAYS
    if isinstance(mode, str) and mode.lower() == "next7":
        result_lines = ["Next 7 Days Forecast:"]
        for i in range(len(dates)):
            result_lines.append(
                f"{dates[i]} -> "
                f"Max: {max_temp[i]}°C, "
                f"Min: {min_temp[i]}°C, "
                f"Rain: {rain_prob[i]}%"
            )
        return "\n".join(result_lines)

    # 🎯 SPECIFIC DATE (YYYY-MM-DD)
    if mode in dates:
        i = dates.index(mode)
        return (
            f"Weather on {mode}:\n"
            f"Max: {max_temp[i]}°C\n"
            f"Min: {min_temp[i]}°C\n"
            f"Rain Chance: {rain_prob[i]}%"
        )

    return "Invalid input. Use: None, 'tomorrow', 'next7', or 'YYYY-MM-DD'."
