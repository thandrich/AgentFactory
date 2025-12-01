"""
Architect Agent

The Architect analyzes user requests and designs comprehensive agent workflows.
It generates a JSON blueprint defining all agents, their tools, inputs/outputs,
and dependencies. In Debug mode, it requests human approval before proceeding.
"""

import logging
import os
from typing import List, Dict
from graphviz import Digraph

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# Configure logging
logger = logging.getLogger("Architect")

# Model Configuration with retry options
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

def generate_workflow_flowchart(
    nodes: List[Dict[str, str]], 
    edges: List[Dict[str, str]]
) -> str:
    """
    Generates a visual flowchart of the proposed agent workflow using Graphviz.
    
    Args:
        nodes: List of dicts with keys 'name', 'model', 'inputs', 'outputs'.
        edges: List of dicts with keys 'from', 'to'.
        
    Returns:
        str: Status message indicating where the flowchart was saved.
    """
    try:
        dot = Digraph(comment='Agent Workflow', format='png')
        dot.attr(rankdir='LR')  # Left to Right orientation

        for node in nodes:
            # Create a label that shows Name, Model, and IO
            label = f"<{node['name']}<BR/><FONT POINT-SIZE='10'>Model: {node.get('model', 'N/A')}</FONT><BR/><FONT POINT-SIZE='10'>In: {node.get('inputs', '[]')}</FONT><BR/><FONT POINT-SIZE='10'>Out: {node.get('outputs', '[]')}</FONT>>"
            dot.node(node['name'], label=label, shape='box', style='rounded')

        for edge in edges:
            dot.edge(edge['from'], edge['to'])

        # Save to current working directory
        output_filename = 'workflow_blueprint'
        output_path = dot.render(output_filename, cleanup=True)
        abs_path = os.path.abspath(output_path)
        
        logger.info(f"Flowchart generated at: {abs_path}")
        return f"Flowchart successfully generated and saved to {abs_path}."
    except Exception as e:
        logger.error(f"Failed to generate flowchart: {e}")
        return f"Error generating flowchart: {str(e)}"


def request_approval(blueprint: str, tool_context: ToolContext) -> Dict[str, str]:
    """
    Requests human approval for the blueprint.
    
    This tool pauses execution in Debug mode and waits for user approval.
    In YOLO mode, this tool is never called.
    
    Args:
        blueprint: The JSON blueprint as a string
        tool_context: ADK tool context for requesting confirmation
        
    Returns:
        dict: Status of the approval request
    """
    # Check if we already have a decision (resuming from pause)
    if tool_context.tool_confirmation:
        if tool_context.tool_confirmation.confirmed:
            logger.info("Blueprint approved by user")
            return {
                "status": "approved",
                "message": "User approved the blueprint. Proceeding to implementation.",
                "feedback": tool_context.tool_confirmation.feedback or ""
            }
        else:
            logger.info("Blueprint rejected by user")
            return {
                "status": "rejected",
                "message": "User rejected the blueprint. Please revise based on feedback.",
                "feedback": tool_context.tool_confirmation.feedback or "No specific feedback provided"
            }
    
    # No decision yet - request confirmation (this pauses execution)
    tool_context.request_confirmation(
        hint="Please review the blueprint and approve or reject",
        payload={"blueprint": blueprint}
    )
    
    return {
        "status": "pending",
        "message": "Waiting for user approval..."
    }


# ============================================================================
# Architect Agent Definition
# ============================================================================

architect = LlmAgent(
    name="Architect",
    model=model_config,
    instruction="""
    You are The Architect, a senior AI systems designer with expertise in multi-agent workflows.
    
    **MISSION:**
    Analyze the user's request and design a comprehensive, production-ready multi-agent workflow.
    
    **CORE PRINCIPLES:**
    1. **Granularity**: Break complex goals into atomic, single-purpose agents
    2. **Specialization**: Each agent should have ONE clear responsibility
    3. **Clarity**: Define explicit inputs, outputs, and dependencies
    4. **Efficiency**: Use the most appropriate model for each agent's task
    
    **EXECUTION PROCESS:**
    
    1. **Analyze** the user's goal deeply:
       - What is the end deliverable?
       - What are the logical sub-tasks?
       - What dependencies exist between tasks?
    
    2. **Design** the workflow:
       - Create 2-5 specialized agents (avoid monolithic designs)
       - For each agent, define:
         * Unique name (snake_case)
         * Specific role and goal
         * Required inputs (from user or other agents)
         * Expected outputs
         * Dependencies on other agents
         * Detailed instructions for implementation
    
    3. **Visualize** by calling `generate_workflow_flowchart` with:
       - nodes: Array of {name, model, inputs, outputs}
       - edges: Array of {from, to} showing data flow
    
    4. **Output** the complete JSON blueprint following this EXACT structure:
    ```json
    {
        "end_to_end_context": "Comprehensive description of the complete workflow and how agents collaborate",
        "agents": [
            {
                "agent_name": "unique_snake_case_name",
                "role": "Brief role description",
                "suggested_model": "gemini-2.5-flash or gemini-2.0-pro or...",
                "goal": "Single atomic goal this agent accomplishes",
                "inputs": [
                    {"name": "var_name", "type": "str/dict/list", "description": "What this input contains"}
                ],
                "outputs": [
                    {"name": "var_name", "type": "str/dict/list", "description": "What this output contains"}
                ],
                "dependencies": ["name_of_agent_it_depends_on"],
                "instructions": "Extremely detailed prompt that tells the Engineer exactly how to build this agent. Reference specific tools, expected behavior, edge cases, and output format."
            }
        ]
    }
    ```
    
    5. **Request Approval** (ONLY in Debug mode):
       - After generating the blueprint, call `request_approval` with the JSON blueprint as a string
       - Wait for user feedback
       - If rejected, revise the blueprint based on feedback and request approval again
    
    **IMPORTANT NOTES:**
    - The Engineer will reference the ADK Coding Bible (AgentCoding.txt) to implement your design
    - Be extremely detailed in the "instructions" field - this is what the Engineer reads
    - Suggest appropriate models: gemini-2.5-flash for fast tasks, gemini-2.0-pro for complex reasoning
    - Ensure the workflow is linear or has clear dependencies (no circular dependencies)
    
    **OUTPUT FORMAT:**
    Always output the complete JSON blueprint. Do not truncate or summarize.
    """,
    tools=[generate_workflow_flowchart, request_approval]
)