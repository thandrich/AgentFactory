import logging
import json
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
try:
    from google.adk.tools import google_search
except ImportError:
    # Fallback or placeholder if google.adk.tools.google_search is not found
    # Assuming the user has it or we can pass a dummy
    def google_search(query: str):
        """Searches Google for the query."""
        return f"Mock search result for {query}"

logger = logging.getLogger("Engineer")

# 1. Define Model Config
model_config = Gemini(
    model="gemini-2.5-flash",
    retry_options={"attempts": 3}
)

def create_engineer_agent(agent_definition: Dict[str, Any], context: str) -> Agent:
    """
    Creates an Engineer agent configured to build a specific component.
    
    Args:
        agent_definition: The blueprint definition for this agent.
        context: The full workflow context.
    """
    agent_name = agent_definition.get('agent_name', 'Unknown_Agent')
    
    instruction = f"""
    You are The Engineer, a senior Python developer.
    
    **YOUR MISSION:**
    Build the agent described below using the Google ADK.
    
    **CONTEXT:**
    {context}
    
    **TARGET AGENT:**
    {json.dumps(agent_definition, indent=2)}
    
    **PROCESS:**
    1. Research necessary libraries using `google_search`.
    2. Write the complete, production-ready Python code for this agent.
    3. Ensure the code uses `adk.core.Agent` and follows the ADK patterns.
    
    **OUTPUT:**
    Return the Python code string.
    """
    
    return Agent(
        name=f"Engineer_{agent_name}",
        model=model_config,
        instruction=instruction,
        tools=[google_search],
        output_key=f"code_{agent_name}"
    )