# main.py
from datetime import timedelta, datetime
from places import get_top_50_attractions  # <-- or get_top_5_attractions if you kept that name
from weather import get_weather
from coordinates import get_coordinates

SERPAPI_KEY = "764f6562ac7a13291ac92c6a7759fe148a5063770000a6e20e36a6c4edee6368"


def format_city_name(city: str) -> str:
    """
    Converts user input city into properly capitalized form.
    Examples:
    bangalore -> Bangalore
    new delhi -> New Delhi
    LOS ANGELES -> Los Angeles
    """
    return " ".join(word.capitalize() for word in city.strip().split())


def weekday_to_date(day_name: str) -> str:
    """Return the next date (YYYY-MM-DD) for the given weekday name."""
    days = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    day_name = day_name.lower()
    if day_name not in days:
        raise ValueError("Invalid weekday name")

    today = datetime.now()
    target = days[day_name]
    diff = (target - today.weekday()) % 7
    if diff == 0:
        diff = 7  # always choose next occurrence

    return (today + timedelta(days=diff)).strftime("%Y-%m-%d")


def ask_weather_mode() -> str | None:
    """
    Ask the user which date/range they want weather for.
    Returns mode: None, "tomorrow", "next7", or date string from weekday.
    """
    print("\nTravelAI:\n Which date or range do you want the weather for?")
    print("  1. Current weather")
    print("  2. Tomorrow")
    print("  3. Next 7 days")
    print("  4. A weekday (e.g., next Monday)")
    choice = input("Choose 1/2/3/4: ").strip()

    if choice == "1":
        return None
    elif choice == "2":
        return "tomorrow"
    elif choice == "3":
        return "next7"
    elif choice == "4":
        weekday = input("Enter weekday name (monday, tuesday, ...): ").strip().lower()
        try:
            return weekday_to_date(weekday)
        except ValueError:
            print("TravelAI: Invalid weekday name. Using current weather instead.")
            return None
    else:
        print("TravelAI: Invalid choice. Using current weather.")
        return None


def ask_places_tag() -> str | None:
    """Ask the user for an optional tag to filter places."""
    tag = input(
        "\nTravelAI:\n Do you want to filter places by any tag (e.g., 'park', 'museum', 'temple')?\n"
        "If not, just press Enter: "
    ).strip()
    return tag if tag else None


def chat_loop():
    print("Welcome to your Travel TravelAI! (type 'exit' to quit)")
    last_city = None

    # cache for current city's places + index of how many shown
    city_places: list[str] | None = None
    city_places_index: int = 0

    while True:
        # Ensure we have a city selected
        if last_city is None:
            user_input = input("\nYou (enter city name or 'exit'): ").strip()
            if user_input.lower() in {"exit", "quit", "bye"}:
                print("TravelAI: Bye! Have a great trip 😄")
                break
            if not user_input:
                print("TravelAI:\n Please enter a city name.")
                continue
            last_city = format_city_name(user_input)
            # reset places cache when choosing a new city
            city_places = None
            city_places_index = 0

        city = last_city

        # Main menu for the current city
        print(f"\nTravelAI: Current city: {city}")
        print("  1. Weather")
        print("  2. Places to visit")
        print("  3. Both")
        print("  4. Change city")
        print("  5. Exit")

        # ✅ Extra option only if we have more places left to show
        if city_places is not None and city_places_index < len(city_places):
            print("  6. More places to visit")

        choice = input("Choose 1/2/3/4/5" + ("/6" if city_places is not None and city_places_index < len(city_places) else "") + ": ").strip()

        if choice == "5":
            print("TravelAI: Bye! Have a great trip 😄")
            break

        # Change city option
        if choice == "4":
            new_city = input("\nTravelAI:\n Enter new city name (or press Enter to cancel): ").strip()
            if new_city:
                last_city = format_city_name(new_city)
                city_places = None
                city_places_index = 0
            # If empty, keep same city and loop again
            continue

        # ✅ "More places" option – just show next 5 from cache
        if choice == "6" and city_places is not None and city_places_index < len(city_places):
            batch = city_places[city_places_index:city_places_index + 5]
            print(f"\nTravelAI: More places in {city}:")
            for p in batch:
                print(f"- {p}")
            city_places_index += 5
            continue  # go back to menu

        want_weather = False
        want_places = False

        if choice == "1":
            want_weather = True
        elif choice == "2":
            want_places = True
        elif choice == "3":
            want_weather = True
            want_places = True
        else:
            print("TravelAI: Invalid choice, please try again.")
            continue

        # WEATHER FLOW
        if want_weather:
            coords = get_coordinates(city)
            if coords is None:
                print(f"TravelAI: I couldn't find coordinates for {city}.")
                continue

            lat, lon = coords
            mode = ask_weather_mode()
            weather_text = get_weather(lat, lon, mode)

            if weather_text:
                print(f"\nTravelAI: {weather_text}")
            else:
                print(f"\nTravelAI: I couldn't fetch the weather for {city}.")

        # PLACES FLOW
        if want_places:
            # ask tag each time we freshly ask for places
            tag = ask_places_tag()

            # fetch up to 50 places once for this request
            raw_places = get_top_50_attractions(city, SERPAPI_KEY, tag or "tourist attractions") or []

            # store in cache and reset index
            city_places = raw_places
            city_places_index = 0

            if not city_places:
                print(f"\nTravelAI: I couldn't find places to visit in {city}.")
            else:
                # show first 5 now
                batch = city_places[0:5]
                print(f"\nTravelAI: Here are some places in {city}:")
                for p in batch:
                    print(f"- {p}")
                city_places_index = 5
                # from now on, option 6 will appear in menu for "More places"


if __name__ == "__main__":
    chat_loop()
