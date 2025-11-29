import contextlib
import io
import logging
from typing import Dict, Any
import json
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

logger = logging.getLogger("QALead")

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
                # For MVP, we know it's WeatherBot (or whatever the Architect named it, but we'll try to find a class that inherits from Agent or just any class)
                # A robust way is to look for a class that has a 'run' method
                agent_instance = None
                for name, obj in execution_scope.items():
                    if isinstance(obj, type) and hasattr(obj, 'run'):
                        # Try to instantiate
                        try:
                            # Try with max_api_calls arg if it accepts it, or no args
                            try:
                                agent_instance = obj(max_api_calls=5)
                            except TypeError:
                                agent_instance = obj()
                            break
                        except Exception:
                            continue
                
                if agent_instance:
                    # Run the agent
                    result = agent_instance.run(test_query)
                    logger.info(f"Agent returned: {result}")
                    
                    # LLM-as-a-Judge Evaluation
                    score = 5 # Default score
                    judge_feedback = "No criteria provided."
                    if evaluation_criteria:
                        logger.info("Running LLM-as-a-Judge...")
                        
                        # Real LLM Judge
                        try:
                            model = genai.GenerativeModel("gemini-2.5-flash")
                            judge_prompt = f"""
                            Compare the AGENT RESPONSE to the EVALUATION CRITERIA for the query: "{test_query}"
                            
                            Evaluation Criteria:
                            {evaluation_criteria}
                            
                            Agent Response: {result}
                            
                            Score 1-5 based on how well the response meets the criteria.
                            Output a JSON object:
                            {{
                                "score": int,
                                "feedback": "string explaining the score"
                            }}
                            """
                            response = model.generate_content(judge_prompt)
                            text = response.text.strip()
                            if text.startswith("```json"):
                                text = text[7:]
                            if text.startswith("```"):
                                text = text[3:]
                            if text.endswith("```"):
                                text = text[:-3]
                                
                            judge_result = json.loads(text.strip())
                            score = judge_result.get("score", 1)
                            judge_feedback = judge_result.get("feedback", "No feedback provided.")
                            
                        except Exception as e:
                            logger.error(f"Judge failed: {e}")
                            score = 1
                            judge_feedback = f"Judge failed: {e}"
                    
                    return {
                        "success": True,
                        "result": result,
                        "trace": output_capture.getvalue(),
                        "score": score,
                        "judge_feedback": judge_feedback
                    }
                else:
                    return {"success": False, "error": "No suitable Agent class found in executed code"}
                    
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {"success": False, "error": str(e), "trace": output_capture.getvalue()}
