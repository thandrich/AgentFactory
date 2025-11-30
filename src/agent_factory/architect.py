# Load environment variables
from dotenv import load_dotenv
load_dotenv()
import logging
import json
import asyncio
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

logger = logging.getLogger("Architect")

class Architect:
    """
    The Architect agent is responsible for analyzing the user's goal and designing
    a blueprint for the agent.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.model_config = Gemini(model=model_name)
        
        self.system_instruction = """
        You are The Architect, a senior AI systems designer.
        Your goal is to design a robust, secure, and efficient AI agent based on a user's high-level request.
        
        Output strictly valid JSON with the following structure:
        {
            "agent_name": "Name of the agent",
            "role": "Detailed description of the agent's role",
            "goals": ["List of specific goals"],
            "tools": [
                {
                    "name": "tool_name",
                    "description": "What the tool does",
                    "arguments": {"arg_name": "type"}
                }
            ],
            "evaluation_criteria": [
                "Criteria 1 (e.g., 'Must return valid JSON')",
                "Criteria 2 (e.g., 'Must handle API errors gracefully')"
            ],
            "few_shot_examples": [
                {"input": "User query", "output": "Expected agent response"}
            ],
            "process_loop": "Description of the agent's think-act-observe loop"
        }
        """
        
        self.agent = LlmAgent(
            name="Architect",
            model=self.model_config,
            instruction=self.system_instruction
        )
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"Architect initialized with model: {model_name}")

    def design_agent(self, goal: str) -> Dict[str, Any]:
        """
        Generates a blueprint for the agent based on the goal.
        """
        logger.info(f"Architect received goal: {goal}")
        logger.info("Generating blueprint...")
        
        prompt = f"User Goal: {goal}\n\nGenerate the JSON blueprint."

        async def _run():
            events = await self.runner.run_debug(prompt)
            # Extract text from the last event with content
            for event in reversed(events):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            return part.text
            return ""

        try:
            response_text = asyncio.run(_run())
            
            # Clean up markdown if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            blueprint = json.loads(cleaned_text.strip())
            return blueprint
            
        except Exception as e:
            logger.error(f"Error generating blueprint: {e}")
            return {"error": str(e)}
