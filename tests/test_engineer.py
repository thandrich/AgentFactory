import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.engineer import Engineer

def test_engineer_code_generation():
    print("Testing Engineer Code Generation...")
    engineer = Engineer()
    
    blueprint = {
        "agent_name": "WeatherBot",
        "role": "Provides weather updates",
        "system_instruction": "You are a helpful weather assistant. Use the get_weather tool to find weather information.",
        "tools": [
            {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "arguments": {
                    "location": "str: City name or coordinates"
                }
            }
        ],
        "memory_requirements": "short-term"
    }
    
    code = engineer.build_agent(blueprint)
    
    print("Code received:")
    print(code[:200] + "...") # Print first 200 chars
    
    # Validation
    if "class WeatherBot" not in code:
        print("FAILED: 'class WeatherBot' not found in generated code.")
        sys.exit(1)
        
    if "def get_weather" not in code:
        print("FAILED: 'def get_weather' not found in generated code.")
        sys.exit(1)
        
    print("SUCCESS: Engineer generated valid-looking Python code.")

if __name__ == "__main__":
    test_engineer_code_generation()
