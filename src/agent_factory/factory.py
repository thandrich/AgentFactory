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
    
    def __init__(self):
        self.architect = Architect()
        self.engineer = Engineer()
        self.auditor = Auditor()
        
    def create_agent(self, goal: str, max_retries: int = 3) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Creates an agent based on the goal.
        Returns (generated_code, blueprint) if successful, (None, None) otherwise.
        """
        logger.info(f"Starting agent creation for goal: {goal}")
        
        # Create workspace
        slug = "".join(c if c.isalnum() else "_" for c in goal.lower())[:50]
        workspace_dir = os.path.join(os.getcwd(), "workspaces", slug)
        os.makedirs(workspace_dir, exist_ok=True)
        logger.info(f"Created workspace: {workspace_dir}")
        
        # Step 1: Architect
        blueprint = self.architect.design_agent(goal)
        if "error" in blueprint:
            logger.error(f"Architect failed: {blueprint['error']}")
            return None, None
            
        logger.info("Blueprint generated successfully.")
        
        # Step 2 & 3: Engineer & Auditor Loop
        current_code = None
        feedback = None
        
        for attempt in range(max_retries + 1):
            logger.info(f"Attempt {attempt + 1}/{max_retries + 1}")
            
            # Engineer generates code (taking feedback into account if any)
            if feedback:
                logger.info("Providing feedback to Engineer...")
                current_code = self.engineer.build_agent(blueprint) 
            else:
                current_code = self.engineer.build_agent(blueprint)
                
            # Auditor reviews code
            review_result = self.auditor.review_code(current_code, blueprint)
            
            if review_result is True:
                logger.info("Auditor approved the code!")
                
                # Save code to workspace
                file_path = os.path.join(workspace_dir, "agent.py")
                with open(file_path, "w") as f:
                    f.write(current_code)
                logger.info(f"Agent code saved to: {file_path}")
                
                return current_code, blueprint
            else:
                feedback = review_result
                logger.warning(f"Auditor rejected the code. Issues: {feedback['issues']}")
                
        logger.error("Max retries reached. Agent creation failed.")
        return None, None

