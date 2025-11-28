from typing import Dict, Any
import json
import sys
import io
import contextlib
from .utils import setup_logging

logger = setup_logging("QALead")

class QALead:
    """
    The QA Lead Agent.
    Role: Execution and validation.
    Input: Approved Python code.
    Output: Execution trace and success status.
    """

    def __init__(self):
        logger.info("QALead initialized")

    def test_agent(self, agent_code: str, test_query: str) -> Dict[str, Any]:
        """
        Executes the agent code in a sandbox and runs the test query.
        """
        logger.info(f"QALead testing agent with query: {test_query}")
        
        # Sandbox execution
        # We need to execute the code to get the agent class
        # Then instantiate it and run it
        
        # Capture stdout
        output_capture = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(output_capture):
                # Create a local scope for execution
                # Use the same dictionary for globals and locals to ensure functions can see each other
                execution_scope = {}
                exec(agent_code, execution_scope)
                
                # Find the agent class (assuming it's the one with 'Bot' or 'Agent' in name, or just the last class)
                # For MVP, we know it's WeatherBot
                if "WeatherBot" in execution_scope:
                    agent_class = execution_scope["WeatherBot"]
                    agent_instance = agent_class()
                    
                    # Run the agent
                    # Assuming the agent has a 'run' method as per Engineer prompt
                    if hasattr(agent_instance, "run"):
                        result = agent_instance.run(test_query)
                        logger.info(f"Agent returned: {result}")
                        
                        return {
                            "success": True,
                            "result": result,
                            "trace": output_capture.getvalue()
                        }
                    else:
                        return {"success": False, "error": "Agent has no 'run' method"}
                else:
                    return {"success": False, "error": "WeatherBot class not found in executed code"}
                    
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {"success": False, "error": str(e), "trace": output_capture.getvalue()}

