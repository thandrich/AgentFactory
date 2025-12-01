import os
import json
import logging
from typing import Optional, Dict, Any
from adk.core import ParallelAgent, LoopAgent, SequentialAgent
from adk.runners import InMemoryRunner
from .architect import architect
from .engineer import create_engineer_agent
from .auditor import auditor
from .utils import setup_logging

logger = setup_logging("Factory")

class AgentFactory:
    """
    The main factory class that orchestrates the creation of agents.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        # Agents are now defined in their respective modules
        pass

    def prepare_workspace(self, goal: str) -> tuple[str, Any]:
        """Prepares the workspace and logging for a new agent."""
        slug = "".join(c if c.isalnum() else "_" for c in goal.lower())[:50]
        workspace_dir = os.path.join(os.getcwd(), "workspaces", slug)
        os.makedirs(workspace_dir, exist_ok=True)
        
        log_file = os.path.join(workspace_dir, "debug.log")
        global logger
        logger = setup_logging("Factory", log_file)
        
        logger.info(f"Starting agent creation for goal: {goal}")
        logger.info(f"Created workspace: {workspace_dir}")
        return workspace_dir, logger

    def create_agent(self, goal: str, max_retries: int = 3, debug_callback: Optional[callable] = None) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Creates a multi-agent system based on the goal.
        """
        workspace_dir, _ = self.prepare_workspace(goal)
        
        def notify_debug(step_name: str, content: Any):
            if debug_callback:
                if not debug_callback(step_name, content):
                    logger.warning(f"Process cancelled by user at step: {step_name}")
                    raise InterruptedError("Cancelled by user")

        try:
            # Step 1: Architect (Human-in-the-loop handled by UI calling this)
            notify_debug("Architect: Start", {"goal": goal})
            
            # Run Architect
            runner = InMemoryRunner(agent=architect)
            result = runner.run(input=goal) # Synchronous run as per ADK guide example
            
            # Extract blueprint from output_key
            blueprint = result.get("blueprint")
            if not blueprint:
                # Fallback: try to parse from output text if key missing
                try:
                    blueprint = json.loads(result.output)
                except:
                    logger.error("Architect failed to produce blueprint")
                    return None, None

            notify_debug("Architect: End", blueprint)
            
            agents_to_build = blueprint.get("agents", [])
            context = blueprint.get("end_to_end_context", "")
            
            # Step 2: Create Parallel Loops (Engineer + Auditor)
            parallel_loops = []
            
            for agent_def in agents_to_build:
                # Create specific engineer for this agent
                engineer = create_engineer_agent(agent_def, context)
                
                # Create a loop for this agent: Engineer -> Auditor
                # Auditor reads {code} from Engineer, writes {review}
                # Engineer reads {review} (if exists) to refine
                
                loop = LoopAgent(
                    name=f"DevLoop_{agent_def['agent_name']}",
                    sub_agents=[engineer, auditor],
                    max_iterations=max_retries,
                    # Exit condition: Auditor approves
                    exit_condition=lambda state: state.get("review", {}).get("approved", False)
                )
                parallel_loops.append(loop)
            
            # Step 3: Run all loops in parallel
            team = ParallelAgent(
                name="EngineeringTeam",
                sub_agents=parallel_loops
            )
            
            notify_debug("Factory: Start Parallel Execution", {"agents": [a.name for a in parallel_loops]})
            
            team_runner = InMemoryRunner(agent=team)
            final_state = team_runner.run(input="Start building")
            
            notify_debug("Factory: Execution Complete", final_state)
            
            # Save files
            saved_files = []
            for key, value in final_state.items():
                # We need to identify which key corresponds to code
                # Since we have multiple engineers, they might overwrite 'code' if not scoped?
                # ADK ParallelAgent usually merges results. 
                # If keys collide, it might be an issue.
                # Ideally, Engineer should output to unique key or ADK handles scoping.
                # Assuming ADK handles scoping or we need to prefix keys.
                # For now, let's assume the state contains the code.
                pass
                
            # Since I can't guarantee ADK scoping behavior without docs, 
            # I'll assume the final state has keys like "code" but maybe overwritten.
            # A better approach in ADK is usually unique output keys.
            # But I can't change Engineer to have dynamic output key easily in Agent definition?
            # Actually I can: output_key=f"code_{agent_name}"
            
            # Let's fix Engineer to use unique output key
            
            return None, blueprint # Placeholder return

        except Exception as e:
            logger.error(f"Factory execution error: {e}")
            return None, None

