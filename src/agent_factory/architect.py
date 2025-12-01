import logging
import os
from typing import List, Dict
from graphviz import Digraph
from adk.core import Agent
from adk.models import Gemini

# Configure logging
logger = logging.getLogger("Architect")
logging.basicConfig(level=logging.INFO)

# 1. Define Model Config
model_config = Gemini(
    model="gemini-2.5-flash",
    retry_options={"max_retries": 3}
)

# 2. Define Tools
def generate_workflow_flowchart(nodes: List[Dict[str, str]], edges: List[Dict[str, str]]) -> str:
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

        # Save to current working directory (project root or workspace)
        output_filename = 'workflow_blueprint'
        output_path = dot.render(output_filename, cleanup=True)
        abs_path = os.path.abspath(output_path)
        
        logger.info(f"Flowchart generated at: {abs_path}")
        return f"Flowchart successfully generated and saved to {abs_path}. Please present this to the user."
    except Exception as e:
        logger.error(f"Failed to generate flowchart: {e}")
        return f"Error generating flowchart: {str(e)}"

# 3. Define the Agent
architect = Agent(
    name="Architect",
    model=model_config,
    instruction="""
    You are The Architect, a senior AI systems designer.
    
    **CORE RESPONSIBILITIES:**
    1. Analyze the User's Request.
    2. Break it down into atomic, granular steps. Prioritize multiple specialist agents over single complex agents.
    3. Assign the most suitable model for each agent.
    4. Define clear Inputs and Outputs for every agent.
    5. **Visualise** the workflow by calling the `generate_workflow_flowchart` tool.

    **PROCESS:**
    1. Think: Break down the user's goal.
    2. Call `generate_workflow_flowchart`.
    3. Output the complete JSON blueprint.

    **FINAL JSON STRUCTURE (Required in output):**
    ```json
    {
        "end_to_end_context": "Full description of the complete workflow",
        "agents": [
            {
                "agent_name": "unique_snake_case_name",
                "role": "Specific role description",
                "suggested_model": "model_name",
                "goal": "Atomic goal of this agent",
                "inputs": [{"name": "var_name", "type": "type", "description": "desc"}],
                "outputs": [{"name": "var_name", "type": "type", "description": "desc"}],
                "dependencies": ["name_of_agent_it_depends_on"],
                "instructions": "Detailed prompt instructions for the Engineer to build this agent."
            }
        ]
    }
    ```
    """,
    tools=[generate_workflow_flowchart],
    output_key="blueprint"
)