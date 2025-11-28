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

    def test_agent(self, agent_code: str, test_query: str, evaluation_criteria: list = None) -> Dict[str, Any]:
        """
        Executes the agent code in a sandbox and runs the test query.
        Validates the result using LLM-as-a-Judge if criteria are provided.
        """
        logger.info(f"QALead testing agent with query: {test_query}")
        
        # Sandbox execution
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
                    if hasattr(agent_instance, "run"):
                        result = agent_instance.run(test_query)
                        logger.info(f"Agent returned: {result}")
                        
                        # LLM-as-a-Judge Evaluation
                        score = 5 # Default score
                        judge_feedback = "No criteria provided."
                        
                        if evaluation_criteria:
                            logger.info("Running LLM-as-a-Judge...")
                            # Mock Judge Logic
                            # In real system: score = self.llm_judge.evaluate(result, evaluation_criteria)
                            judge_feedback = f"Evaluated against: {evaluation_criteria}"
                            if "Sunny" in result:
                                score = 5
                                judge_feedback += " -> PASSED (Score: 5/5)"
                            else:
                                score = 1
                                judge_feedback += " -> FAILED (Score: 1/5)"
                        
                        return {
                            "success": True,
                            "result": result,
                            "trace": output_capture.getvalue(),
                            "score": score,
                            "judge_feedback": judge_feedback
                        }
                    else:
                        return {"success": False, "error": "Agent has no 'run' method"}
                else:
                    return {"success": False, "error": "WeatherBot class not found in executed code"}
                    
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {"success": False, "error": str(e), "trace": output_capture.getvalue()}

