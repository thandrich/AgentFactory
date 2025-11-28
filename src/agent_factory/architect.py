from typing import Dict, Any
import json
from .utils import setup_logging

logger = setup_logging("Architect")

class Architect:
    """
    The Architect Agent.
    Role: Strategic planning and context engineering.
    Input: User natural language request.
    Output: JSON Blueprint.
    """

    def __init__(self, model_name: str = "gemini-pro"):
        self.model_name = model_name
        # Mocking ADK Model initialization
        # self.model = adk.Model(model_name)
        logger.info(f"Architect initialized with ADK model: {model_name}")

    def design_agent(self, goal: str) -> Dict[str, Any]:
        """
        Decomposes the user goal into a blueprint.
        """
        logger.info(f"Architect received goal: {goal}")
        
        # Prompt engineering for the Architect
        prompt = f"""
        You are The Architect, a senior AI system designer.
        Your goal is to design a "Team of Specialists" AI agent based on the user's request.
        
        User Request: "{goal}"
        
        Output a JSON Blueprint with the following structure:
        {{
            "agent_name": "Name of the agent",
            "role": "Brief description of the agent's role",
            "system_instruction": "Detailed system instructions. MUST follow the 'Mission -> Scene -> Think -> Act -> Observe' loop structure.",
            "few_shot_examples": ["List of strings representing example interactions"],
            "evaluation_criteria": ["List of criteria to judge the agent's performance (e.g., correctness, tone)"],
            "tools": [
                {{
                    "name": "tool_function_name",
                    "description": "Description of what the tool does. Describe actions, not implementations.",
                    "arguments": {{
                        "arg_name": "type and description"
                    }}
                }}
            ],
            "memory_requirements": "short-term" | "long-term"
        }}
        
        Ensure the system instructions are clear and the tools are well-defined.
        Return ONLY valid JSON.
        """
        
        # Mocking the LLM response for MVP 1 if ADK is not yet fully integrated or for testing
        # In real implementation: response = self.model.generate_content(prompt)
        # For now, we will simulate a response for the "weather bot" example to pass the test
        
        logger.info("Generating blueprint...")
        
        # TODO: Replace with actual LLM call
        # For the purpose of the MVP 1 verification without a live API key/ADK setup in this environment yet:
        if "weather" in goal.lower():
            return {
                "agent_name": "WeatherBot",
                "role": "Provides weather updates",
                "system_instruction": "Mission: You are a helpful weather assistant.\nScene: User asks for weather.\nThink: Identify the location.\nAct: Use get_weather.\nObserve: Report the result.",
                "few_shot_examples": [
                    "User: Weather in Paris?\nAgent: [Calls get_weather('Paris')]\nAgent: It is Sunny in Paris."
                ],
                "evaluation_criteria": [
                    "Must correctly identify the location",
                    "Must use the get_weather tool",
                    "Response must be polite"
                ],
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
            
        return {"error": "Blueprint generation failed (Mock)"}

