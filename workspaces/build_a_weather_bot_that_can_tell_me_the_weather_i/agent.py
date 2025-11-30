# Dependencies:
# pip install google-generative-ai
# pip install google-generative-ai-adk
# pip install requests

import os
import asyncio
import requests
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

# Use the model suggested in the agent definition
model_config = Gemini(model="gemini-2.5-flash")

def get_current_weather(location: str) -> str:
    """
    Retrieves current weather information for a specified location using OpenWeatherMap API.

    Args:
        location: The city for which to retrieve weather information.

    Returns:
        A formatted string containing the current weather conditions, or an error message.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OpenWeatherMap API key not found. Please set the OPENWEATHER_API_KEY environment variable."

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric"  # For temperature in Celsius
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if data.get("cod") == 200:
            main_data = data.get("main", {})
            weather_data = data.get("weather", []) if data.get("weather") else {}
            wind_data = data.get("wind", {})
            city_name = data.get("name", location)

            temperature = main_data.get("temp")
            humidity = main_data.get("humidity")
            description = weather_data.get("description", "N/A").capitalize()
            wind_speed = wind_data.get("speed") # m/s by default for metric units

            report = (
                f"Current weather in {city_name}:\n"
                f"Description: {description}.\n"
                f"Temperature: {temperature}°C.\n"
                f"Humidity: {humidity}%.\n"
                f"Wind Speed: {wind_speed} m/s."
            )
            return report
        else:
            return f"Could not retrieve weather for {location}. Reason: {data.get('message', 'Unknown error')}"

    except requests.exceptions.RequestException as e:
        return f"Network error or invalid API request: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

agent = LlmAgent(
    name="WeatherTeller",
    model=model_config,
    instruction=(
        "You are a helpful AI assistant specialized in providing real-time weather information. "
        "Your task is to respond to user queries about the weather. "
        "For this specific request, the user wants the weather in 'London'. "
        "You will use an internal weather tool (`get_current_weather(location='London')`) to fetch "
        "the current weather for 'London' and then present the information clearly and concisely to the user "
        "in a readable format. Always specify the units (e.g., °C, m/s)."
    ),
    tools=[get_current_weather]
)

async def main():
    """
    Main function to run the WeatherTeller agent.
    It simulates a user asking for weather in London.
    """
    runner = InMemoryRunner(agent=agent)
    # The agent's instruction specifically targets 'London', so the prompt can be generic.
    events = await runner.run_debug("What is the current weather?")

    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)
                    break

if __name__ == "__main__":
    # Ensure OPENWEATHER_API_KEY is set in your environment
    # For testing, you can temporarily set it like this:
    # os.environ["OPENWEATHER_API_KEY"] = "YOUR_OPENWEATHER_API_KEY"
    # Remember to replace "YOUR_OPENWEATHER_API_KEY" with your actual key.
    
    # You will need to obtain a free API key from OpenWeatherMap (openweathermap.org)
    # and set it as an environment variable or directly here for testing.
    if "OPENWEATHER_API_KEY" not in os.environ:
        print("WARNING: OPENWEATHER_API_KEY environment variable is not set.")
        print("Please obtain a free API key from openweathermap.org and set it.")
        print("Example: export OPENWEATHER_API_KEY='your_key_here'")
        # Exit or provide a dummy key for testing without actual API calls
        # For this example, we'll proceed but the tool call will return an error message.

    asyncio.run(main())