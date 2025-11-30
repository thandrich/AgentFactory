import logging
import json
import asyncio
from typing import Dict, Any, Optional

# ADK Imports
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search      # Added Search capability

logger = logging.getLogger("Engineer")

class Engineer:
    """
    The Engineer agent is responsible for researching, designing, and writing 
    the Python code for a specific atomic agent within a larger workflow.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.model_config = Gemini(model=model_name)
        
        # Initialize Google Search tool for research
        self.search_tool = google_search

        self.system_instruction = """
        You are The Engineer, a senior Python developer and systems architect.
        
        **YOUR MISSION:**
        You will receive a definition for ONE specific agent and the context of the wider workflow. 
        Your goal is to build a production-ready standalone Python file for this agent using the Google ADK.

        **EXECUTION WORKFLOW (Mental Steps):**
        1. **Analyze**: Understand the specific goal of this agent. 
        2. **Strategy**: Decide the best technical approach:
           - **Algorithmic (Python)**: logical processing, math, data transformation. (HIGHEST PRIORITY).
           - **API/MCP**: Real-time data, external services (Stock prices, Weather, CRM).
           - **LLM**: Creative writing, summarization, complex reasoning.
        3. **Research**: Use the `google_search` tool to find:
           - The best Python libraries for the task.
           - Available public APIs or documentation if external data is needed.
        4. **Code**: Generate the file.
        
        **FAILURE CONDITION:**
        If you cannot find a viable technical solution (e.g., a required API does not exist), 
        return strictly: `# ERROR: Unable to solve task. [Reason]`

        **CODING STANDARDS & SYNTAX:**
        
        1. **Imports**:
           ```python
           import os
           import asyncio
           from google.genai import types
           from google.adk.agents import LlmAgent
           from google.adk.models.google_llm import Gemini
           from google.adk.runners import InMemoryRunner
           # Import any other standard libraries you researched
           ```
           
        2. **Model Config**:
           ```python
           # Use the model suggested in the agent definition, default to gemini-2.5-flash
           model_config = Gemini(model="gemini-2.5-flash")
           ```
           
        3. **Tools**:
           - Create python functions for any algorithmic steps or API calls you planned.
           - Must use type hints and docstrings.
           ```python
           def my_tool(arg: str) -> dict:
               \"\"\"Description.\"\"\"
               return {"result": "value"}
           ```
           
        4. **Agent Definition**:
           ```python
           agent = LlmAgent(
               name="agent_name",
               model=model_config,
               instruction="Specific system instruction based on the Goal...",
               tools=[my_tool]  # Pass functions directly.
           )
           ```
           
        5. **Execution (Main Block)**:
           ```python
           async def main():
               runner = InMemoryRunner(agent=agent)
               # Take input from environment or args in a real scenario, 
               # but here create a sample prompt based on expected inputs.
               events = await runner.run_debug("Start with expected input...")
               
               for event in reversed(events):
                   if hasattr(event, 'content') and event.content and event.content.parts:
                       for part in event.content.parts:
                           if part.text:
                               print(part.text)
                               break
               
           if __name__ == "__main__":
               asyncio.run(main())
           ```

        **OUTPUT REQUIREMENTS:**
        1. Start with a comment block listing dependencies for `pip install`.
        2. Then output the full Python code.
        3. Do NOT include markdown markers (```).
        """
        
        self.agent = LlmAgent(
            name="Engineer",
            model=self.model_config,
            instruction=self.system_instruction,
            tools=[self.search_tool]
        )
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"Engineer initialized with model: {model_name}")

    def build_agent(self, agent_definition: Dict[str, Any], context: str) -> str:
        """
        Research and generates Python code for a single atomic agent.
        
        Args:
            agent_definition: The specific JSON object for the agent to build.
            context: The end-to-end workflow description to provide context.
        """
        agent_name = agent_definition.get('agent_name', 'Unknown_Agent')
        logger.info(f"Engineer starting build for: {agent_name}")
        
        # specific instructions for this run
        prompt = f"""
        **CONTEXT (Full Workflow):**
        {context}

        **AGENT TO BUILD (Target):**
        {json.dumps(agent_definition, indent=2)}

        Research necessary libraries/APIs using Google Search, then generate the ADK Python code.
        """
        
        async def _run():
            # Run debug handles the multi-turn loop (Agent -> Tool -> Agent) automatically
            events = await self.runner.run_debug(prompt)
            
            # Extract the final textual response (The code)
            for event in reversed(events):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            return part.text
            return ""

        try:
            logger.info("Engineer is researching and coding...")
            code_response = asyncio.run(_run())
            
            # Clean up markdown if the model included it despite instructions
            cleaned_code = code_response.strip()
            if cleaned_code.startswith("```python"):
                cleaned_code = cleaned_code[9:]
            if cleaned_code.startswith("```"):
                cleaned_code = cleaned_code[3:]
            if cleaned_code.endswith("```"):
                cleaned_code = cleaned_code[:-3]
            
            return cleaned_code.strip()
            
        except Exception as e:
            logger.error(f"Error generating code for {agent_name}: {e}")
            return f"# Error generating code: {e}"