import logging
import json
import os
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logging.warning("GOOGLE_API_KEY not found in environment variables.")

logger = logging.getLogger("Architect")

class Architect:
    """
    The Architect agent is responsible for understanding the user's goal
    and designing a blueprint for the agent.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Architect initialized with model: {model_name}")

    def design_agent(self, goal: str) -> Dict[str, Any]:
        """
        Generates a JSON blueprint for the requested agent.
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
        Return ONLY valid JSON. Do not include markdown code blocks.
        """
        
        logger.info("Generating blueprint...")
        
        try:
            response = self.model.generate_content(prompt)
            # Clean up response if it contains markdown code blocks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            blueprint = json.loads(text.strip())
            return blueprint
        except Exception as e:
            logger.error(f"Error generating blueprint: {e}")
            return {"error": str(e)}
