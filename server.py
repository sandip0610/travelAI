# server.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List

from app import parse_input, build_llm_response, MODEL_NAME, SERPAPI_KEY
from weather import get_weather
from coordinates import get_coordinates
from places import get_top_5_attractions

app = FastAPI(title="Travel Assistant API")

class ChatRequest(BaseModel):
    message: str
    last_city: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    city: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(body: ChatRequest):
    user_input = body.message
    last_city = body.last_city

    # 1. Parse intent
    city, want_weather, want_places = parse_input(user_input, last_city)

    # If no city now, reuse previous city
    if city is None and last_city is not None:
        city = last_city

    if city is None:
        return ChatResponse(
            reply="I couldn't detect any city. Please mention a city name like 'Bangalore'.",
            city=None,
        )

    # remember city for next turn
    weather_text = None
    places: Optional[List[str]] = None

    # Weather logic (same as in main.py, but without prints)
    text = user_input.lower()
    mode = None

    if want_weather or (not want_weather and not want_places):
        coords = get_coordinates(city)
        if coords is None:
            return ChatResponse(
                reply=f"I couldn't find coordinates for {city}.",
                city=city,
            )

        lat, lon = coords

        if "tomorrow" in text:
            mode = "tomorrow"
        elif "next 7" in text or "next seven" in text or "next week" in text:
            mode = "next7"
        else:
            from main import weekday_to_date
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                if day in text:
                    mode = weekday_to_date(day)
                    break

        weather_text = get_weather(lat, lon, mode)

    # Places logic
    if want_places or (not want_weather and not want_places):
        places = get_top_5_attractions(city, SERPAPI_KEY)

    # Build final answer from LLM
    reply = build_llm_response(
        user_input=user_input,
        city=city,
        want_weather=want_weather,
        want_places=want_places,
        weather_text=weather_text,
        places=places,
    )

    return ChatResponse(
        reply=reply,
        city=city,
    )
