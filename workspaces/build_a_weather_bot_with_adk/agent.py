
import logging
from typing import List, Any

# Mocking google.adk for demonstration if not available
try:
    import google.adk as adk
except ImportError:
    class MockADK:
        class Agent:
            def __init__(self, name, system_instruction, tools, model="gemini-pro"):
                self.name = name
                self.system_instruction = system_instruction
                self.tools = tools
                self.model = model
                self.chat_history = []
                
            def generate_response(self, prompt):
                # Mock LLM response
                return "Sunny, 25°C"
    adk = MockADK()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WeatherBot")

def get_weather(location: str) -> str:
    """
    Get the current weather for a location.
    
    Args:
        location: City name or coordinates.
        
    Returns:
        Weather information as a string.
    """
    # Mock implementation
    logger.info(f"Getting weather for {location}")
    return f"The weather in {location} is Sunny, 25°C."

class WeatherBot(adk.Agent):
    def __init__(self, max_api_calls: int = 5):
        super().__init__(
            name="WeatherBot",
            system_instruction="You are a helpful weather assistant. Use the get_weather tool to find weather information.",
            tools=[get_weather],
            model="gemini-pro"
        )
        self.max_api_calls = max_api_calls
        self.api_calls_count = 0
        
    def run(self, user_input: str) -> str:
        logger.info(f"User Input: {user_input}")
        
        if self.api_calls_count >= self.max_api_calls:
            return "Error: Maximum API calls exceeded."
            
        self.api_calls_count += 1
        
        # Simple rule-based mock for the agent logic to simulate tool usage
        if "weather" in user_input.lower():
            # Extract location (naive)
            words = user_input.split()
            location = words[-1] # Assume last word is location
            return get_weather(location)
            
        return "I can only help with weather."

if __name__ == "__main__":
    bot = WeatherBot(max_api_calls=3)
    print(bot.run("What is the weather in London"))
