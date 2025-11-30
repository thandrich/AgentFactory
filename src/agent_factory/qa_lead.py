import logging
import json
import sys
import io
import contextlib
import asyncio
from typing import Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

logger = logging.getLogger("QALead")

class QALead:
    """
    The QA Lead agent is responsible for testing the generated agent
    and evaluating its performance against the criteria.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.model_config = Gemini(model=model_name)
        
        self.system_instruction = """
        You are The QA Lead, a strict quality assurance specialist.
        Your goal is to evaluate the output of an AI agent against a set of criteria.
        
        Output strictly valid JSON with the following structure:
        {
            "success": true/false,
            "score": 1-5,
            "reasoning": "Explanation of the score",
            "failures": ["List of specific criteria failures"]
        }
        """
        
        self.judge_agent = LlmAgent(
            name="QA_Judge",
            model=self.model_config,
            instruction=self.system_instruction
        )
        self.judge_runner = InMemoryRunner(agent=self.judge_agent)
        logger.info(f"QA Lead initialized with model: {model_name}")

    def test_agent(self, agent_code: str, test_query: str, evaluation_criteria: List[str] = None) -> Dict[str, Any]:
        """
        Executes the agent code and evaluates the result.
        """
        logger.info(f"QA Lead testing agent with query: {test_query}")
        
        # 1. Execute the Agent Code
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
                # Create a restricted global scope
                exec_globals = {}
                exec(agent_code, exec_globals)
                
                # Explicitly run main() if it exists
                if "main" in exec_globals:
                    main_func = exec_globals["main"]
                    if asyncio.iscoroutinefunction(main_func):
                        asyncio.run(main_func())
                    else:
                        main_func()
                
            execution_output = output_buffer.getvalue()
            execution_error = error_buffer.getvalue()
            
            logger.info(f"Agent Execution Output: {execution_output}")
            if execution_error:
                logger.warning(f"Agent Execution Error: {execution_error}")
                
        except Exception as e:
            logger.error(f"Error executing agent: {e}")
            return {
                "success": False,
                "error": f"Runtime Error: {str(e)}",
                "output": output_buffer.getvalue(),
                "logs": error_buffer.getvalue()
            }

        # 2. Evaluate with LLM Judge
        if not evaluation_criteria:
            evaluation_criteria = ["Agent should provide a helpful response."]
            
        prompt = f"""
        Test Query: {test_query}
        
        Agent Output:
        {execution_output}
        
        Evaluation Criteria:
        {json.dumps(evaluation_criteria, indent=2)}
        
        Did the agent meet the criteria?
        """
        
        async def _run_judge():
            events = await self.judge_runner.run_debug(prompt)
            for event in reversed(events):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            return part.text
            return ""

        try:
            response_text = asyncio.run(_run_judge())
            
            # Clean up markdown
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            result = json.loads(cleaned_text.strip())
            
            # Add execution logs to result
            result["execution_output"] = execution_output
            result["execution_logs"] = execution_error
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating agent: {e}")
            return {
                "success": False,
                "error": f"Evaluation Error: {str(e)}",
                "execution_output": execution_output
            }
