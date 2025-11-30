# Dependencies for pip install:
# google-generativeai
# google-adk

import os
import asyncio
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

# Use the model suggested in the agent definition.
model_config = Gemini(model="gemini-2.0-flash")

# Define the location_identifier agent.
agent = LlmAgent(
    name="location_identifier",
    model=model_config,
    instruction=(
        "From the given user_request, identify and extract *only* the name of the city "
        "for which weather information is requested. For example, if the request is "
        "'Build a weather bot that can tell me the weather in London', the output should be 'London'. "
        "Your response must contain only the city name as a string, with no additional text or punctuation."
    ),
    # No specific tools are needed as the LLM directly performs the extraction.
    tools=[]
)

async def main():
    """
    Main function to run the location_identifier agent with a sample input.
    """
    runner = InMemoryRunner(agent=agent)
    
    # Sample input based on the expected user request format.
    sample_user_request = "Build a weather bot that can tell me the weather in London"
    print(f"Running agent with input: '{sample_user_request}'")
    
    events = await runner.run_debug(sample_user_request)
    
    city_name_found = None
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    city_name_found = part.text.strip()
                    print(f"\nIdentified City: {city_name_found}")
                    break
            if city_name_found:
                break
    
    if not city_name_found:
        print("No city name could be identified.")

if __name__ == "__main__":
    asyncio.run(main())