import logging
import json
import asyncio
from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

logger = logging.getLogger("Engineer")

class Engineer:
    """
    The Engineer agent is responsible for writing the Python code for the agent.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.model_config = Gemini(model=model_name)
        
        self.system_instruction = """
        You are The Engineer, a senior Python developer.
        Your goal is to write a production-ready Python script for an AI agent based on the provided Blueprint.
        
        ### ADK Syntax Reference (Use this EXACT syntax):
        
        1. **Imports**:
           ```python
           import os
           import asyncio
           from google.genai import types
           from google.adk.agents import LlmAgent
           from google.adk.models.google_llm import Gemini
           from google.adk.runners import InMemoryRunner
           ```
           
        2. **Model Config**:
           ```python
           model_config = Gemini(model="gemini-2.5-flash")
           ```
           
        3. **Tools**:
           - Must use type hints and docstrings.
           - Must return a dictionary (e.g., `return {"status": "success", "data": ...}`).
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
               instruction="System instruction...",
               tools=[my_tool]  # Pass functions directly! DO NOT wrap in AgentTool.
           )
           ```
           
        5. **Execution (Main Block)**:
           ```python
           async def main():
               runner = InMemoryRunner(agent=agent)
               # Example interaction
               events = await runner.run_debug("Start")
               # Print the last event's text
               for event in reversed(events):
                   if hasattr(event, 'content') and event.content and event.content.parts:
                       for part in event.content.parts:
                           if part.text:
                               print(part.text)
                               break
               
           if __name__ == "__main__":
               asyncio.run(main())
           ```

        Requirements:
        1. Follow the **ADK Syntax Reference** above strictly.
        2. Implement the tools defined in the blueprint.
        3. Use `gemini-2.5-flash` as the model.
        4. Include the `if __name__ == "__main__":` block using `asyncio.run(main())`.
        5. Ensure robust docstrings for tools.
        6. **CRITICAL**: At the TOP of your output, include a comment block listing all required dependencies:
           ```python
           # DEPENDENCIES:
           # google-adk
           # python-dotenv
           # <any other packages needed by tools>
           ```
        
        Output format:
        - Start with the DEPENDENCIES comment block
        - Then output the Python code
        - Do NOT include markdown code blocks (no ``` markers)
        """
        
        self.agent = LlmAgent(
            name="Engineer",
            model=self.model_config,
            instruction=self.system_instruction
        )
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"Engineer initialized with model: {model_name}")

    def build_agent(self, blueprint: Dict[str, Any], feedback: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates Python code for the agent based on the blueprint.
        If feedback is provided (from Auditor), incorporates it into the prompt.
        """
        if not blueprint or not isinstance(blueprint, dict):
            logger.error("Engineer received invalid blueprint")
            return "# Error: Invalid blueprint"
            
        logger.info(f"Engineer received blueprint for: {blueprint.get('agent_name', 'Unknown')}")
        
        # Build the prompt with optional feedback
        prompt = f"Blueprint:\n{json.dumps(blueprint, indent=2)}\n\n"
        
        if feedback:
            logger.info("Incorporating Auditor feedback into generation...")
            prompt += f"""
PREVIOUS CODE REVIEW FEEDBACK:
The code you previously generated was reviewed and needs improvements.

Issues Found:
{json.dumps(feedback.get('issues', []), indent=2)}

Suggestions:
{json.dumps(feedback.get('suggestions', []), indent=2)}

Please generate IMPROVED code that addresses all the issues and suggestions above.
"""
        else:
            prompt += "Generate the Python code."
        
        logger.info("Generating code...")
        
        async def _run():
            events = await self.runner.run_debug(prompt)
            for event in reversed(events):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            return part.text
            return ""

        try:
            code = asyncio.run(_run())
            code = code.strip()
            
            # Clean up markdown
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            return code.strip()
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return f"# Error generating code: {e}"
