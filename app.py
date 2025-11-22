# main.py
from datetime import timedelta,datetime
import re
import ollama
from places import get_top_5_attractions
from weather import get_weather
from coordinates import get_coordinates

def weekday_to_date(day_name: str):
    days = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    today = datetime.now()
    target = days[day_name]
    diff = (target - today.weekday()) % 7
    if diff == 0:
        diff = 7  # always choose next occurrence

    return (today + timedelta(days=diff)).strftime("%Y-%m-%d")
MODEL_NAME = "llama3"       # change to your Ollama model name if needed
SERPAPI_KEY = "764f6562ac7a13291ac92c6a7759fe148a5063770000a6e20e36a6c4edee6368"  # put your real key here

import json


  # <-- change to any model you have in `ollama list`


def parse_input(user_input: str, last_city: str | None = None):
    """
    Use the LLM to understand:
    - which city the user is talking about
    - whether they want weather info
    - whether they want places to visit

    Returns: (city, want_weather, want_places)
    """

    system_prompt = """
You are an AI assistant that extracts structured information from user messages
about travel and weather.

You must ALWAYS respond in valid JSON with this exact structure:

{
  "city": "<city name or null>",
  "want_weather": true or false,
  "want_places": true or false
}

Rules:
- "city" should be the main city the user is referring to (like "Bangalore", "Mumbai", "Paris").
- If the user clearly refers to a city, extract it as a string.
- If the user does NOT clearly mention a city and a previous city is provided, reuse that previous city.
- If no city can be determined at all, set "city" to null.
- "want_weather": true if the user seems to ask about temperature, weather, climate, how hot/cold it is, etc.
- "want_places": true if the user seems to ask about places to visit, attractions, tourist spots, planning a trip, etc.
- Both can be true if the user is asking for both.
- If the user only says something like "I'm going there", assume they want places (trip planning) by default.
"""

    # Build user prompt including previous city context
    user_prompt = {
        "user_input": user_input,
        "previous_city": last_city,
    }

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt)},
        ],
    )

    content = response["message"]["content"]

    # Try to parse JSON; if something goes wrong, fall back to simple defaults
    try:
        data = json.loads(content)
        city = data.get("city")
        want_weather = bool(data.get("want_weather", False))
        want_places = bool(data.get("want_places", False))
    except Exception:
        # Fallback heuristics if LLM returned something weird
        city = last_city
        text = user_input.lower()
        want_weather = any(w in text for w in ["weather", "temperature", "climate", "hot", "cold"])
        want_places = any(w in text for w in ["visit", "places", "tourist", "spots", "trip"])

    return city, want_weather, want_places


def build_llm_response(
    user_input: str,
    city: str,
    want_weather: bool,
    want_places: bool,
    weather_text: str | None,
    places: list[str] | None,
):
    """
    Ask Ollama to generate the final response in natural language,
    following the style of your examples and using the real data.
    """

    places_bullets = ""
    if places:
        places_bullets = "\n".join(f"- {p}" for p in places)

    prompt = f"""
You are a travel assistant. Based on the user input and the data provided, 
generate a friendly answer in the same style as these examples.

Example 1
Input: I’m going to go to Bangalore, let’s plan my trip.
Output:
In Bangalore these are the places you can go,
- Lalbagh
- Sri Chamarajendra Park
- Bangalore palace
- Bannerghatta National Park
- Jawaharlal Nehru Planetarium

Example 2
Input: I’m going to go to Bangalore, what is the temperature there
Output:
In Bangalore it’s currently 24°C with a chance of 35% to rain.

Example 3
Input: I’m going to go to Bangalore, what is the temperature there? And what are the places I can visit?
Output:
In Bangalore it’s currently 24°C with a chance of 35% to rain. And these are the places you can go:
- Lalbagh
- Sri Chamarajendra Park
- Bangalore palace
- Bannerghatta National Park
- Jawaharlal Nehru Planetarium


Now use the REAL data below. Do NOT change any numbers or place names.

User input: {user_input}

City: {city}

User wants weather: {want_weather}
User wants places: {want_places}

Weather info (already fetched from API, use this text and do not change its numbers):
{weather_text if weather_text else "NO_WEATHER_DATA"}

Places (already fetched, use exactly these names as bullets if needed):
{places_bullets if places_bullets else "NO_PLACES_DATA"}

Rules:
- Do NOT add notes, explanations, or commentary.
- Do NOT mention missing data like "no places available".
- Do NOT justify why something is not shown.
- Only provide the final answer cleanly.
- Just answer naturally like a human travel assistant.

- If the weather refers to a future date, ALWAYS use future tense:
  examples: "is expected to be", "will be", "can be expected".
- Use present tense ONLY for current weather.

- If the user only asks about weather, answer only about weather like Example 2.
- If the user only asks about places to visit, answer only with the list of places like Example 1.
- If the user asks for both, answer like Example 3: weather sentence + places list.
- If the user input is vague (e.g., 'I am going to <city>, let's plan my trip'), assume they want places.
- Keep the style similar to the examples: short, friendly, clear.
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response["message"]["content"]


def chat_loop():
    print("Welcome to your Travel Assistant! (type 'exit' to quit)")
    last_city = None

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "bye"}:
            print("Assistant: Bye! Have a great trip 😄")
            break

        # Parse this turn
        city, want_weather, want_places = parse_input(user_input)

        # If no city mentioned this time, fall back to last city (context)
        if city is None and last_city is not None:
            city = last_city

        if city is None:
            print("Assistant: I couldn't detect any city. Please mention a city name like 'Bangalore'.")
            continue

        # Remember last city for follow-up questions
        last_city = city

        weather_text = None
        places = None

        # If user explicitly asked for weather, or neither intent is clear (then give both)
        if want_weather or (not want_weather and not want_places):
            coords = get_coordinates(city)
            if coords is None:
                print(f"Assistant: I couldn't find coordinates for {city}.")
                continue
            lat, lon = coords
            text = user_input.lower()

            mode = None

            # detect "tomorrow"
            if "tomorrow" in text:
                mode = "tomorrow"

            # detect "next 7" / "next seven" / "next week"
            elif "next 7" in text or "next seven" in text or "next week" in text:
                mode = "next7"
            else:
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    if day in text:
                        mode = weekday_to_date(day)
                        break

            # detect explicit date in format YYYY-MM-DD

            # Now call your upgraded weather function
            weather_text = get_weather(lat, lon, mode)
            if mode!='next7':
                print(weather_text)


        # If user explicitly asked for places, or no clear intent (then give both)

        if want_places or (not want_weather and not want_places):
            places = get_top_5_attractions(city, SERPAPI_KEY)

        # Generate final answer from Ollama
        try:
            final_answer = build_llm_response(
                user_input=user_input,
                city=city,
                want_weather=want_weather,
                want_places=want_places,
                weather_text=weather_text,
                places=places,
            )
        except Exception as e:
            print(f"Assistant: Oops, there was an error talking to the LLM: {e}")
            continue

        print(f"Assistant: {final_answer}")


if __name__ == "__main__":
    chat_loop()
