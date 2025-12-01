"""
QA Lead Agent

The QA Lead validates the generated agent workflow by:
1. Creating a test case based on the original user goal
2. Executing the generated code in a sandbox
3. Evaluating the results and providing a final verdict
"""

import logging
import json
import traceback
from typing import Dict, Any, Optional
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import InMemoryRunner
from google.genai import types

logger = logging.getLogger("QALead")

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
# Tools for QA Lead
# ============================================================================

def generate_test_case(
    agent_definition: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Generates a test case for validating an agent.
    
    Args:
        agent_definition: JSON string of the agent blueprint
        tool_context: ADK tool context
        
    Returns:
        dict: Test case with input and expected behavior
    """
    try:
        agent_def = json.loads(agent_definition)
        
        # Create test case based on agent's goal and inputs
        test_case = {
            "agent_name": agent_def.get('agent_name', 'unknown'),
            "goal": agent_def.get('goal', ''),
            "test_input": f"Test input for {agent_def.get('agent_name', 'agent')}",
            "expected_behavior": f"Should accomplish: {agent_def.get('goal', 'goal not specified')}"
        }
        
        logger.info(f"Generated test case for: {test_case['agent_name']}")
        return {
            "status": "success",
            "test_case": test_case
        }
    except Exception as e:
        logger.error(f"Failed to generate test case: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def execute_agent_code(
    code_filepath: str,
    test_input: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Executes agent code in a sandboxed environment.
    
    Args:
        code_filepath: Path to the agent code file
        test_input: Input to send to the agent
        tool_context: ADK tool context
        
    Returns:
        dict: Execution results with output or error
    """
    try:
        # Read the code
        code_path = Path(code_filepath)
        if not code_path.exists():
            return {
                "success": False,
                "error": f"Code file not found: {code_filepath}"
            }
        
        code = code_path.read_text(encoding='utf-8')
        
        # Create execution environment
        exec_globals = {
            '__builtins__': __builtins__,
            'os': __import__('os'),
            'json': __import__('json'),
            'logging': __import__('logging'),
        }
        
        # Add ADK imports
        try:
            exec_globals['types'] = __import__('google.genai.types', fromlist=['types'])
            exec_globals['LlmAgent'] = __import__('google.adk.agents', fromlist=['LlmAgent']).LlmAgent
            exec_globals['Gemini'] = __import__('google.adk.models.google_llm', fromlist=['Gemini']).Gemini
            exec_globals['InMemoryRunner'] = __import__('google.adk.runners', fromlist=['InMemoryRunner']).InMemoryRunner
            exec_globals['ToolContext'] = __import__('google.adk.tools.tool_context', fromlist=['ToolContext']).ToolContext
            exec_globals['SequentialAgent'] = __import__('google.adk.agents', fromlist=['SequentialAgent']).SequentialAgent
            exec_globals['LoopAgent'] = __import__('google.adk.agents', fromlist=['LoopAgent']).LoopAgent
            exec_globals['ParallelAgent'] = __import__('google.adk.agents', fromlist=['ParallelAgent']).ParallelAgent
        except ImportError as e:
            logger.warning(f"Some ADK imports failed: {e}")
        
        # Execute the code to load the agent
        exec_locals = {}
        exec(code, exec_globals, exec_locals)
        
        if 'agent' not in exec_locals:
            return {
                "success": False,
                "error": "Code does not define an 'agent' variable"
            }
        
        agent_obj = exec_locals['agent']
        
        # Run the agent with test input
        runner = InMemoryRunner(agent=agent_obj)
        result = runner.run(input=test_input)
        
        # Extract output
        output_text = ""
        if isinstance(result, dict):
            # Try to get a reasonable output representation
            output_text = json.dumps(result, indent=2)
        else:
            output_text = str(result)
        
        logger.info(f"Agent execution completed successfully")
        return {
            "success": True,
            "output": output_text
        }
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "success": False,
            "error": traceback.format_exc()
        }


def evaluate_results(
    expected_behavior: str,
    actual_output: str,
    test_input: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Evaluates the agent's output against expected behavior.
    
    This is a placeholder - in practice, the QA Lead agent itself
    will analyze the results using its LLM capabilities.
    
    Args:
        expected_behavior: What the agent should accomplish
        actual_output: What the agent actually produced
        test_input: The input that was provided
        tool_context: ADK tool context
        
    Returns:
        dict: Evaluation results
    """
    # The actual evaluation logic will be done by the QA Lead agent's LLM
    # This tool just structures the data for evaluation
    return {
        "status": "ready_for_evaluation",
        "expected": expected_behavior,
        "actual": actual_output,
        "input": test_input
    }


# ============================================================================
# QA Lead Agent Definition
# ============================================================================

def create_qa_lead_agent(
    agent_definition: Dict[str, Any],
    code_filepath: str,
    workspace_dir: str = "."
) -> LlmAgent:
    """
    Creates a QA Lead agent to validate a specific generated agent.
    
    Args:
        agent_definition: The blueprint for the agent being tested
        code_filepath: Path to the generated agent code
        workspace_dir: Working directory for the QA process
        
    Returns:
        LlmAgent: Configured QA Lead agent
    """
    agent_name = agent_definition.get('agent_name', 'Unknown')
    
    instruction = f"""
    You are The QA Lead, a rigorous software tester and quality assurance expert.
    
    **YOUR MISSION:**
    Validate that the generated agent code works correctly and meets the original requirements.
    
    **AGENT UNDER TEST:**
    ```json
    {json.dumps(agent_definition, indent=2)}
    ```
    
    **CODE LOCATION:**
    {code_filepath}
    
    **TESTING PROCESS:**
    
    1. **Generate Test Case**:
       - Call `generate_test_case` with the agent definition JSON as a string
       - This will create appropriate test input and expected behavior
    
    2. **Execute Code**:
       - Call `execute_agent_code` with:
         * code_filepath: "{code_filepath}"
         * test_input: The test input from step 1
       - This runs the agent in a sandbox and captures output
    
    3. **Evaluate Results**:
       - Analyze the execution results
       - Compare actual output against expected behavior
       - Consider:
         * Did the agent run without errors?
         * Did it produce meaningful output?
         * Does the output align with the agent's goal?
         * Are there any obvious bugs or issues?
    
    4. **Provide Verdict**:
       - **PASS**: Agent works correctly, output is appropriate
       - **FAIL**: Agent has errors, crashes, or produces incorrect output
       
       Include in your verdict:
       - Overall status (PASS/FAIL)
       - Score (1-10)
       - Reasoning for your decision
       - Specific findings (what worked, what didn't)
       - Recommendations for improvement (if any)
    
    **EVALUATION CRITERIA:**
    
    1. **Execution**: Does the code run without errors? (40%)
    2. **Functionality**: Does it accomplish the stated goal? (40%)
    3. **Output Quality**: Is the output well-formed and useful? (20%)
    
    **VERDICT FORMAT:**
    
    ```
    **QA VERDICT: [PASS/FAIL]**
    
    **Score:** [1-10]/10
    
    **Execution Status:**
    - [Success/Failure details]
    
    **Functionality Assessment:**
    - [How well it meets the goal]
    
    **Output Quality:**
    - [Quality of the output]
    
    **Reasoning:**
    [Detailed explanation of your verdict]
    
    **Recommendations:**
    - [Suggestions for improvement, or "None - production ready"]
    ```
    
    **IMPORTANT:**
    - Be fair but rigorous
    - A working agent with minor imperfections can still PASS
    - FAIL only if there are serious errors or complete failure to meet the goal
    - Provide actionable feedback in all cases
    """
    
    return LlmAgent(
        name=f"QA_Lead_{agent_name}",
        model=model_config,
        instruction=instruction,
        tools=[generate_test_case, execute_agent_code, evaluate_results]
    )