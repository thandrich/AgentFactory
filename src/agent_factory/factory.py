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
        Creates an agent based on the goal.
        Returns (generated_code, blueprint) if successful, (None, None) otherwise.
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
            blueprint = self.architect.design_agent(goal)
            notify_debug("Architect: End", blueprint)
            
            if "error" in blueprint:
                logger.error(f"Architect failed: {blueprint['error']}")
                return None, None
                
            logger.info("Blueprint generated successfully.")
            
            # Step 2 & 3: Engineer & Auditor Loop
            current_code = None
            feedback = None
            
            for attempt in range(max_retries + 1):
                logger.info(f"Attempt {attempt + 1}/{max_retries + 1}")
                
                # Engineer
                notify_debug(f"Engineer: Start (Attempt {attempt+1})", {"blueprint": blueprint, "feedback": feedback})
                if feedback:
                    logger.info("Providing feedback to Engineer...")
                    current_code = self.engineer.build_agent(blueprint) 
                else:
                    current_code = self.engineer.build_agent(blueprint)
                notify_debug(f"Engineer: End (Attempt {attempt+1})", {"code": current_code})
                    
                # Auditor
                notify_debug(f"Auditor: Start (Attempt {attempt+1})", {"code": current_code})
                review_result = self.auditor.review_code(current_code, blueprint)
                notify_debug(f"Auditor: End (Attempt {attempt+1})", review_result)
                
                if review_result is True:
                    logger.info("Auditor approved the code!")
                    
                    # Save code to workspace
                    self.save_agent(current_code, workspace_dir)
                    
                    return current_code, blueprint
                else:
                    feedback = review_result
                    logger.warning(f"Auditor rejected the code. Issues: {feedback['issues']}")
                    
            logger.error("Max retries reached. Agent creation failed.")
            return None, None
            
        except InterruptedError:
            logger.info("Process stopped by user.")
            return None, None
