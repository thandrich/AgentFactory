from typing import Dict, Any
import logging
import google.generativeai as genai

logger = logging.getLogger("Engineer")

class Engineer:
    """
    The Engineer agent is responsible for writing the Python code for the agent.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Engineer initialized with model: {model_name}")

    def build_agent(self, blueprint: Dict[str, Any]) -> str:
        """
        Generates Python code for the agent based on the blueprint.
        """
        logger.info(f"Engineer received blueprint for: {blueprint.get('agent_name')}")
        
        prompt = f"""
        You are The Engineer, a senior Python developer.
        Your goal is to write a production-ready Python script for an AI agent based on the provided Blueprint.
        
        Blueprint:
        {blueprint}
        
        ### ADK Syntax Reference (Use this EXACT syntax):
        
        1. **Imports**:
           ```python
           import os
           from google.genai import types
           from google.adk.agents import LlmAgent
           from google.adk.models.google_llm import Gemini
           from google.adk.runners import InMemoryRunner
           from google.adk.tools import AgentTool, ToolContext
           ```
           
        2. **Model Config**:
           ```python
           model_config = Gemini(model="gemini-2.5-flash")
           ```
           
        3. **Tools**:
           - Must use type hints and docstrings.
           - Must return a dictionary (e.g., `return {{"status": "success", "data": ...}}`).
           ```python
           def my_tool(arg: str) -> dict:
               \"\"\"Description.\"\"\"
               return {{"result": "value"}}
           ```
           
        4. **Agent Definition**:
           ```python
           agent = LlmAgent(
               name="agent_name",
               model=model_config,
               instruction="System instruction...",
               tools=[my_tool]
           )
           ```
           
        5. **Execution (Main Block)**:
           ```python
           import asyncio
           
           async def main():
               runner = InMemoryRunner(agent=agent)
               response = await runner.run_debug("User query")
               print(response)
               
           if __name__ == "__main__":
               asyncio.run(main())
           ```

        Requirements:
        1. Follow the **ADK Syntax Reference** above strictly.
        2. Implement the tools defined in the blueprint.
        3. Use `gemini-2.5-flash` as the model.
        4. Include the `if __name__ == "__main__":` block using `asyncio.run(main())`.
        5. Ensure robust docstrings for tools.
        
        Output ONLY the Python code. Do not include markdown code blocks.
        """
        
        logger.info("Generating code...")
        
        try:
            response = self.model.generate_content(prompt)
            code = response.text.strip()
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
