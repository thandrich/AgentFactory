from typing import Dict, Any, Optional
import json
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
        
    def create_agent(self, goal: str, max_retries: int = 3) -> Optional[str]:
        """
        Creates an agent based on the goal.
        Returns the generated Python code if successful, None otherwise.
        """
        logger.info(f"Starting agent creation for goal: {goal}")
        
        # Step 1: Architect
        blueprint = self.architect.design_agent(goal)
        if "error" in blueprint:
            logger.error(f"Architect failed: {blueprint['error']}")
            return None
            
        logger.info("Blueprint generated successfully.")
        
        # Step 2 & 3: Engineer & Auditor Loop
        current_code = None
        feedback = None
        
        for attempt in range(max_retries + 1):
            logger.info(f"Attempt {attempt + 1}/{max_retries + 1}")
            
            # Engineer generates code (taking feedback into account if any)
            # For MVP, we'll just pass the blueprint again, but in a real system we'd pass feedback
            if feedback:
                logger.info("Providing feedback to Engineer...")
                # In a real system: current_code = self.engineer.fix_code(blueprint, current_code, feedback)
                # For MVP mock, we'll just regenerate (which might not fix it without a smarter mock, but demonstrates the loop)
                current_code = self.engineer.build_agent(blueprint) 
            else:
                current_code = self.engineer.build_agent(blueprint)
                
            # Auditor reviews code
            review_result = self.auditor.review_code(current_code, blueprint)
            
            if review_result is True:
                logger.info("Auditor approved the code!")
                return current_code
            else:
                feedback = review_result
                logger.warning(f"Auditor rejected the code. Issues: {feedback['issues']}")
                
        logger.error("Max retries reached. Agent creation failed.")
        return None

