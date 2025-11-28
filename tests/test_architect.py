import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.architect import Architect

def test_architect_blueprint():
    print("Testing Architect Blueprint Generation...")
    architect = Architect()
    goal = "Build a weather bot"
    blueprint = architect.design_agent(goal)
    
    print(f"Blueprint received: {json.dumps(blueprint, indent=2)}")
    
    # Validation
    required_keys = ["agent_name", "role", "system_instruction", "tools", "memory_requirements"]
    missing_keys = [key for key in required_keys if key not in blueprint]
    
    if missing_keys:
        print(f"FAILED: Missing keys in blueprint: {missing_keys}")
        sys.exit(1)
        
    if blueprint["agent_name"] != "WeatherBot":
        print(f"FAILED: Unexpected agent name: {blueprint['agent_name']}")
        sys.exit(1)
        
    print("SUCCESS: Architect generated a valid blueprint.")

if __name__ == "__main__":
    test_architect_blueprint()
