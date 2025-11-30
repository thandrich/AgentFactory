# Load environment variables
from dotenv import load_dotenv
load_dotenv()
import logging
import json
import asyncio
import os
from typing import Dict, Any, List, Optional
from graphviz import Digraph
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

logger = logging.getLogger("Architect")
logging.basicConfig(level=logging.INFO)

class Architect:
    """
    The Architect agent is responsible for decomposing high-level user requests into 
    atomic, production-ready specialist agents. It visualizes the workflow and 
    iterates based on user feedback before generating a comprehensive JSON blueprint 
    for the Engineer agents.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the Architect.
        
        Args:
            model_name: The model to use for the Architect itself.
        """
        self.model_name = model_name
        self.model_config = Gemini(model=model_name)
        
        # Define the tool for flowchart generation
        self.tools = [self.generate_workflow_flowchart]

        self.system_instruction = """
        You are The Architect, a senior AI systems designer.
        
        **CORE RESPONSIBILITIES:**
        1. Analyze the User's Request.
        2. Break it down into atomic, granular steps. prioritize multiple specialist agents over single complex agents.
        3. Assign the most suitable model for each agent from the provided list; prioritise latest versions, flash models for simpler tasks, pro models for complex reasoning.
        4. Define clear Inputs and Outputs for every agent to ensure they can be chained.
        5. **Visualise** the workflow by calling the `generate_workflow_flowchart` tool.

        **CONSTRAINTS:**
        - **NO** test cases.
        - **NO** mock implementations. All designs must be for production-ready builds.

        **PROCESS (DO ALL IN ONE RESPONSE):**
        1. Think: Break down the user's goal into atomic agents.
        2. **IMMEDIATELY** call `generate_workflow_flowchart` with the proposed nodes and edges.
        3. Provide a brief textual description of the workflow.
        4. **IMMEDIATELY** output the complete JSON blueprint below.
        
        **CRITICAL RULES:**
        - Do NOT ask the user if the plan sounds good or wait for approval
        - Do NOT say "let me know if you'd like adjustments"
        - Output the flowchart tool call AND the complete JSON blueprint in THIS response
        - If refinement feedback is provided, incorporate it and output the NEW flowchart + JSON

        **FINAL JSON STRUCTURE (Required in every response):**
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
        """

        self.agent = LlmAgent(
            name="Architect",
            model=self.model_config,
            instruction=self.system_instruction,
            tools=self.tools
        )
        self.runner = InMemoryRunner(agent=self.agent)
        logger.info(f"Architect initialized with model: {model_name}")

    def generate_workflow_flowchart(self, nodes: List[Dict[str, str]], edges: List[Dict[str, str]]) -> str:
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

    def _clean_json_response(self, text: str) -> str:
        """Helper to clean markdown code blocks from LLM response with multiple strategies."""
        cleaned = text.strip()
        
        # Strategy 1: Look for JSON code blocks
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0]
        elif "```" in cleaned:
            # Try to extract content between first pair of backticks
            parts = cleaned.split("```")
            if len(parts) >= 3:
                cleaned = parts[1]
        
        # Strategy 2: Look for JSON object markers
        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            # Find the matching closing brace
            brace_count = 0
            end = -1
            for i in range(start, len(cleaned)):
                if cleaned[i] == "{":
                    brace_count += 1
                elif cleaned[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            if end > start:
                cleaned = cleaned[start:end]
                
        return cleaned.strip()

    def design_workflow(self, user_request: str, available_models: List[str], feedback: str = None) -> Dict[str, Any]:
        """
        Designs the workflow. If feedback is provided, iterates on the previous design.
        Returns the blueprint dictionary.
        """
        logger.info(f"Starting Architect session for: {user_request}")
        
        # Construct prompt
        prompt = f"""
        User Request: {user_request}
        Available Models: {', '.join(available_models)}
        
        Design the workflow, visualize it, and output the JSON blueprint.
        """
        
        if feedback:
            prompt += f"\n\nUser Feedback on previous design: {feedback}\nPlease refine the design."

        async def _run_with_retry():
            """Single async function that handles both initial attempt and retry to avoid event loop issues"""
            # First attempt
            events = await self.runner.run_debug(prompt)
            response_text = ""
            for event in reversed(events):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text = part.text
                            break
                            
            logger.info(f"Architect raw response length: {len(response_text)} chars")
            
            # Try to parse JSON from first response
            potential_json = self._clean_json_response(response_text)
            
            try:
                data = json.loads(potential_json)
                if "agents" in data and data["agents"]:
                    logger.info(f"✅ Successfully parsed blueprint with {len(data['agents'])} agents")
                    return data
                else:
                    logger.warning("Parsed JSON but missing 'agents' key or empty agents list")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed on first attempt: {e}")
                
            # Retry with explicit JSON-only request (still in same async context)
            logger.info("🔄 Retrying with explicit JSON request...")
            retry_prompt = f"""
            You previously provided a workflow design, but it was not in valid JSON format.
            
            Please output ONLY the JSON blueprint in this exact structure (no additional text):
            
            {{
                "end_to_end_context": "description",
                "agents": [
                    {{
                        "agent_name": "name",
                        "role": "role",
                        "suggested_model": "model",
                        "goal": "goal",
                        "inputs": [],
                        "outputs": [],
                        "dependencies": [],
                        "instructions": "instructions"
                    }}
                ]
            }}
            
            For the original request: {user_request}
            """
            
            # Second attempt (still in same async context - no new asyncio.run())
            retry_events = await self.runner.run_debug(retry_prompt)
            retry_response = ""
            for event in reversed(retry_events):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            retry_response = part.text
                            break
                            
            retry_json = self._clean_json_response(retry_response)
            
            try:
                data = json.loads(retry_json)
                if "agents" in data:
                    logger.info(f"✅ Retry successful! Parsed blueprint with {len(data.get('agents', []))} agents")
                    return data
            except json.JSONDecodeError as e2:
                logger.error(f"JSON parsing failed on retry: {e2}")
                
            # If still failing, return error
            return {
                "error": "Architect did not return valid JSON after retry",
                "raw_response": response_text[:500]
            }

        try:
            # Single asyncio.run() call for entire process
            return asyncio.run(_run_with_retry())
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            return {"error": str(e)}