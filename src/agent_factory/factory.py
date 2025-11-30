from typing import Dict, Any, Optional
import json
import os
from .architect import Architect
from .engineer import Engineer
from .auditor import Auditor
from .utils import setup_logging

logger = setup_logging("Factory")

class AgentFactory:
    """
    The main factory class that orchestrates the creation of agents.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.architect = Architect(model_name=model_name)
        self.engineer = Engineer(model_name=model_name)
        self.auditor = Auditor(model_name=model_name)

    def prepare_workspace(self, goal: str) -> tuple[str, Any]:
        """Prepares the workspace and logging for a new agent."""
        slug = "".join(c if c.isalnum() else "_" for c in goal.lower())[:50]
        workspace_dir = os.path.join(os.getcwd(), "workspaces", slug)
        os.makedirs(workspace_dir, exist_ok=True)
        
        log_file = os.path.join(workspace_dir, "debug.log")
        # Re-setup logger to include file handler
        global logger
        logger = setup_logging("Factory", log_file)
        
        logger.info(f"Starting agent creation for goal: {goal}")
        logger.info(f"Created workspace: {workspace_dir}")
        return workspace_dir, logger

    def save_agent(self, code: str, workspace_dir: str) -> str:
        """Saves the agent code to the workspace."""
        file_path = os.path.join(workspace_dir, "agent.py")
        with open(file_path, "w") as f:
            f.write(code)
        logger.info(f"Agent code saved to: {file_path}")
        return file_path
        
    def create_agent(self, goal: str, max_retries: int = 3, debug_callback: Optional[callable] = None) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Creates a multi-agent system based on the goal.
        Returns (generated_code, blueprint) for the LAST agent created (for now), 
        or (None, None) if failed.
        """
        workspace_dir, _ = self.prepare_workspace(goal)
        
        # Helper for debug callback
        def notify_debug(step_name: str, content: Any):
            if debug_callback:
                if not debug_callback(step_name, content):
                    logger.warning(f"Process cancelled by user at step: {step_name}")
                    raise InterruptedError("Cancelled by user")

        try:
            # Step 1: Architect
            notify_debug("Architect: Start", {"goal": goal})
            # We pass a dummy model list for now, or fetch from utils if possible. 
            # Ideally this should come from app.py or config.
            available_models = ["gemini-2.5-flash", "gemini-1.5-pro"] 
            blueprint = self.architect.design_workflow(goal, available_models)
            notify_debug("Architect: End", blueprint)
            
            if "error" in blueprint:
                logger.error(f"Architect failed: {blueprint['error']}")
                return None, None
                
            logger.info("Blueprint generated successfully.")
            
            agents_to_build = blueprint.get("agents", [])
            context = blueprint.get("end_to_end_context", "")
            
            last_code = None
            
            # Step 2 & 3: Engineer & Auditor Loop for EACH agent
            for agent_def in agents_to_build:
                agent_name = agent_def.get("agent_name", "Unknown")
                logger.info(f"Building agent: {agent_name}")
                
                current_code = None
                feedback = None
                success = False
                
                for attempt in range(max_retries + 1):
                    logger.info(f"Attempt {attempt + 1}/{max_retries + 1} for {agent_name}")
                    
                    # Engineer
                    notify_debug(f"Engineer: Start ({agent_name} - Attempt {attempt+1})", {"agent_def": agent_def})
                    # Engineer now takes agent_def and context
                    current_code = self.engineer.build_agent(agent_def, context)
                    notify_debug(f"Engineer: End ({agent_name} - Attempt {attempt+1})", {"code": current_code})
                        
                    # Auditor
                    notify_debug(f"Auditor: Start ({agent_name} - Attempt {attempt+1})", {"code": current_code})
                    # Auditor now takes code and agent_def
                    review_result = self.auditor.review_agent(current_code, agent_def)
                    notify_debug(f"Auditor: End ({agent_name} - Attempt {attempt+1})", review_result)
                    
                    if review_result["status"] == "PASS":
                        logger.info(f"Auditor approved {agent_name}!")
                        
                        # Save code to workspace with agent name
                        file_path = os.path.join(workspace_dir, f"{agent_name}.py")
                        with open(file_path, "w") as f:
                            f.write(current_code)
                        logger.info(f"Agent code saved to: {file_path}")
                        
                        last_code = current_code
                        success = True
                        break
                    else:
                        # Feedback is implicitly handled by Engineer re-generating based on prompt?
                        # The current Engineer implementation in Step 1141 does NOT take feedback explicitly.
                        # It just takes agent_def and context.
                        # To support retry with feedback, we'd need to update Engineer again or 
                        # append feedback to the context/agent_def for the next iteration.
                        # For now, we just retry, hoping the stochastic nature fixes it, 
                        # or we can append feedback to the context.
                        logger.warning(f"Auditor rejected {agent_name}. Reason: {review_result.get('reasoning')}")
                        # Append feedback to context for next attempt (hacky but works with current Engineer)
                        context += f"\n\n[Previous Attempt Feedback for {agent_name}]: {review_result.get('feedback')}"
                
                if not success:
                    logger.error(f"Failed to build agent: {agent_name}")
                    return None, None

            # Return the last agent's code for the UI to display/run (simplification)
            return last_code, blueprint
            
        except InterruptedError:
            logger.info("Process stopped by user.")
            return None, None
