"""
Engineer Agent

The Engineer implements agents based on the Architect's blueprint.
It references the ADK Coding Bible and creates production-ready Python code
using google.adk and google.genai exclusively.
"""

import logging
import json
import os
from typing import Dict, Any
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types

logger = logging.getLogger("Engineer")

# Model Configuration
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

model_config = Gemini(
    model="gemini-2.5-flash",
    retry_options=retry_config
)


# ============================================================================
# Tools
# ============================================================================

def write_code_to_file(
    filename: str, 
    code: str, 
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Writes the generated agent code to a file in the workspace.
    
    Args:
        filename: Name of the file (e.g., 'agent.py')
        code: The Python code string
        tool_context: ADK tool context
        
    Returns:
        dict: Status of the write operation
    """
    try:
        # Write to current directory (workspace will be set by factory)
        filepath = Path(filename)
        filepath.write_text(code, encoding='utf-8')
        
        logger.info(f"Wrote code to: {filepath.absolute()}")
        return {
            "status": "success",
            "file": str(filepath.absolute()),
            "lines": len(code.split('\n'))
        }
    except Exception as e:
        logger.error(f"Failed to write code: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def read_coding_bible(tool_context: ToolContext) -> str:
    """
    Reads the ADK Coding Bible (AgentCoding.txt) for reference.
    
    Returns:
        str: Contents of the coding bible
    """
    try:
        # Locate the coding bible
        bible_path = Path(__file__).parent.parent.parent / ".papers" / "AgentCoding.txt"
        
        if bible_path.exists():
            content = bible_path.read_text(encoding='utf-8')
            logger.info(f"Read coding bible: {len(content)} characters")
            return content
        else:
            logger.warning(f"Coding bible not found at: {bible_path}")
            return "ERROR: Coding bible not found. Using best practices from memory."
    except Exception as e:
        logger.error(f"Failed to read coding bible: {e}")
        return f"ERROR: Could not read coding bible: {str(e)}"


# ============================================================================
# Engineer Agent Factory
# ============================================================================

def create_engineer_agent(
    agent_definition: Dict[str, Any], 
    context: str,
    workspace_dir: str = "."
) -> LlmAgent:
    """
    Creates an Engineer agent configured to build a specific component.
    
    Args:
        agent_definition: The blueprint definition for this agent from Architect
        context: The full workflow context from Architect's end_to_end_context
        workspace_dir: Directory where the code will be saved
        
    Returns:
        LlmAgent: Configured engineer agent
    """
    agent_name = agent_definition.get('agent_name', 'Unknown_Agent')
    
    # Change to workspace directory for file writing
    original_dir = os.getcwd()
    if workspace_dir and workspace_dir != ".":
        os.makedirs(workspace_dir, exist_ok=True)
        os.chdir(workspace_dir)
    
    instruction = f"""
    You are The Engineer, a senior Python developer specializing in agent development with Google ADK.
    
    **YOUR MISSION:**
    Implement the agent described in the blueprint below using ONLY google.adk and google.genai libraries.
    
    **CRITICAL RULES:**
    1. **EXCLUSIVE LIBRARY USE**: You MUST use ONLY:
       - google.adk (for agents, runners, tools)
       - google.genai (for types, models)
       - Standard library (os, json, logging, etc.)
    
    2. **REFERENCE THE CODING BIBLE**: 
       - Call `read_coding_bible` tool FIRST to review ADK patterns
       - Follow the patterns EXACTLY as documented
       - DO NOT improvise - replicate the examples
    
    3. **CODE STRUCTURE**:
       - Import from google.adk.agents (LlmAgent, SequentialAgent, LoopAgent, etc.)
       - Import from google.adk.models.google_llm (Gemini)
       - Import from google.adk.runners (InMemoryRunner)
       - Define custom tools as Python functions with proper type hints and docstrings
       - Create the agent using LlmAgent with clear instructions
       - Name the final agent object as 'agent' so it can be executed
    
    4. **TOOL CREATION**:
       - Define tools as regular Python functions
       - Use ToolContext parameter if the tool needs state access
       - Include comprehensive docstrings
       - Return dictionaries with clear status/data
    
    **FULL WORKFLOW CONTEXT:**
    {context}
    
    **YOUR TARGET AGENT BLUEPRINT:**
    ```json
    {json.dumps(agent_definition, indent=2)}
    ```
    
    **IMPLEMENTATION PROCESS:**
    
    1. **Study**: Call `read_coding_bible` to review ADK patterns
    
    2. **Plan**: Based on the blueprint:
       - What tools does this agent need?
       - What inputs will it receive (from state or previous agents)?
       - What outputs should it produce?
       - What ADK pattern fits best (simple LlmAgent, SequentialAgent, LoopAgent)?
    
    3. **Implement**: Write complete, production-ready Python code:
       ```python
       # Standard imports
       import os
       import json
       import logging
       from typing import Dict, Any, List
       
       # ADK imports
       from google.adk.agents import LlmAgent
       from google.adk.models.google_llm import Gemini
       from google.adk.runners import InMemoryRunner
       from google.adk.tools.tool_context import ToolContext
       from google.genai import types
       
       # Configure model
       model = Gemini(model="{agent_definition.get('suggested_model', 'gemini-2.5-flash')}")
       
       # Define custom tools
       def my_tool(param: str, tool_context: ToolContext) -> Dict[str, Any]:
           \"\"\"Tool docstring.\"\"\"
           # Implementation
           return {{"status": "success", "result": "..."}}
       
       # Create agent
       agent = LlmAgent(
           name="{agent_name}",
           model=model,
           instruction=\"\"\"
           Clear, detailed instructions for what this agent does.
           Use {{input_variable}} syntax to reference inputs from state.
           \"\"\",
           tools=[my_tool]
       )
       ```
    
    4. **Save**: Call `write_code_to_file` with:
       - filename: "agent_{agent_name}.py"
       - code: Your complete implementation
    
    5. **Verify**: Output a summary of:
       - What tools you created
       - What the agent does
       - How it should be executed
    
    **KEY REQUIREMENTS:**
    - Agent name must be "{agent_name}"
    - Follow the role: {agent_definition.get('role', 'Not specified')}
    - Achieve the goal: {agent_definition.get('goal', 'Not specified')}
    - Handle inputs: {json.dumps(agent_definition.get('inputs', []))}
    - Produce outputs: {json.dumps(agent_definition.get('outputs', []))}
    
    **ARCHITECT'S DETAILED INSTRUCTIONS:**
    {agent_definition.get('instructions', 'No additional instructions provided')}
    
    **OUTPUT:**
    First call read_coding_bible, then implement the agent, then save it.
    Finally, provide a brief summary of what you built.
    """
    
    engineer = LlmAgent(
        name=f"Engineer_{agent_name}",
        model=model_config,
        instruction=instruction,
        tools=[read_coding_bible, write_code_to_file]
    )
    
    # Restore original directory
    os.chdir(original_dir)
    
    return engineer