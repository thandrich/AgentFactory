"""
Agent Factory - Main Orchestration

Coordinates the entire agent creation workflow:
1. Architect designs the blueprint (with HITL in Debug mode)
2. Engineer implements each agent
3. Auditor reviews the code (loop until approved)
4. QA Lead validates the final workflow

Supports two modes:
- Debug Mode: Human-in-the-Loop at Architect stage
- YOLO Mode: Fully automated end-to-end
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from google.adk.agents import SequentialAgent, LoopAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from .architect import architect
from .engineer import create_engineer_agent
from .auditor import auditor
from .qa_lead import create_qa_lead_agent
from .trace_logger import TraceLoggerPlugin
from .utils import (
    setup_logging,
    create_resumable_app,
    find_confirmation_request,
    create_approval_response,
    extract_blueprint_from_output
)

logger = setup_logging("Factory")


class AgentFactory:
    """
    Main factory class that orchestrates agent creation.
    
    Implements a sequential workflow:
    Architect → Engineer + Auditor Loop → QA Lead
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the factory.
        
        Args:
            model_name: Default model to use (can be overridden per agent)
        """
        self.model_name = model_name
        logger.info(f"AgentFactory initialized with model: {model_name}")
    
    def prepare_workspace(self, goal: str) -> Tuple[str, logging.Logger]:
        """
        Prepares the workspace directory and logging for a new agent creation.
        
        Args:
            goal: The user's goal (used to create workspace name)
            
        Returns:
            Tuple of (workspace_dir, logger)
        """
        # Create workspace directory
        slug = "".join(c if c.isalnum() else "_" for c in goal.lower())[:50]
        workspace_dir = os.path.join(os.getcwd(), "workspaces", slug)
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Setup logging
        log_file = os.path.join(workspace_dir, "debug.log")
        workspace_logger = setup_logging("Factory", log_file)
        
        workspace_logger.info(f"=== Starting Agent Factory ===")
        workspace_logger.info(f"Goal: {goal}")
        workspace_logger.info(f"Workspace: {workspace_dir}")
        
        return workspace_dir, workspace_logger
    
    async def create_agent_async(
        self,
        goal: str,
        mode: str = "debug",
        max_review_iterations: int = 3,
        debug_callback: Optional[callable] = None
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Creates an agent workflow asynchronously.
        
        Args:
            goal: User's high-level goal
            mode: "debug" (HITL) or "yolo" (automated)
            max_review_iterations: Max iterations for Engineer-Auditor loop
            debug_callback: Callback for debug events (step_name, content) -> bool
            
        Returns:
            Tuple of (workspace_dir, results_dict) or (None, None) on failure
        """
        workspace_dir, workspace_logger = self.prepare_workspace(goal)
        
        def notify_debug(step_name: str, content: Any):
            """Helper to notify debug callbacks."""
            if debug_callback:
                if not debug_callback(step_name, content):
                    workspace_logger.warning(f"Process cancelled by user at: {step_name}")
                    raise InterruptedError("Cancelled by user")
        
        try:
            # ================================================================
            # STEP 1: ARCHITECT - Generate Blueprint
            # ================================================================
            
            notify_debug("Architect: Start", {"goal": goal})
            
            if mode == "debug":
                # Debug Mode: Use HITL with resumability
                blueprint = await self._run_architect_with_hitl(
                    goal, workspace_dir, workspace_logger, notify_debug
                )
            else:
                # YOLO Mode: No HITL, direct execution
                blueprint = await self._run_architect_yolo(
                    goal, workspace_dir, workspace_logger
                )
            
            if not blueprint:
                workspace_logger.error("Failed to get blueprint from Architect")
                return None, None
            
            notify_debug("Architect: Complete", blueprint)
            
            # Save blueprint
            blueprint_path = os.path.join(workspace_dir, "blueprint.json")
            with open(blueprint_path, 'w') as f:
                json.dump(blueprint, f, indent=2)
            
            # ================================================================
            # STEP 2: ENGINEER + AUDITOR - Implement and Review
            # ================================================================
            
            agents_to_build = blueprint.get("agents", [])
            end_to_end_context = blueprint.get("end_to_end_context", "")
            
            notify_debug("Factory: Engineer Phase Start", {
                "agent_count": len(agents_to_build)
            })
            
            generated_code_files = []
            
            for agent_def in agents_to_build:
                agent_name = agent_def.get("agent_name", "unknown")
                
                notify_debug(f"Engineer: Building {agent_name}", agent_def)
                
                # Create Engineer for this specific agent
                engineer = create_engineer_agent(
                    agent_def,
                    end_to_end_context,
                    workspace_dir
                )
                
                # Create Engineer-Auditor review loop
                review_loop = LoopAgent(
                    name=f"ReviewLoop_{agent_name}",
                    sub_agents=[engineer, auditor],
                    max_iterations=max_review_iterations
                )
                
                # Setup trace logging
                trace_log_path = os.path.join(
                    workspace_dir,
                    f"trace_{agent_name}.log"
                )
                trace_plugin = TraceLoggerPlugin(trace_log_path)
                
                # Run the review loop
                loop_runner = InMemoryRunner(
                    agent=review_loop,
                    plugins=[trace_plugin]
                )
                
                workspace_logger.info(f"Starting review loop for: {agent_name}")
                result = loop_runner.run(
                    input=f"Implement and review the agent: {agent_name}"
                )
                
                # Track generated file
                code_file = os.path.join(workspace_dir, f"agent_{agent_name}.py")
                if os.path.exists(code_file):
                    generated_code_files.append({
                        "agent_name": agent_name,
                        "filepath": code_file,
                        "definition": agent_def
                    })
                    workspace_logger.info(f"✓ Generated: {code_file}")
                else:
                    workspace_logger.warning(f"✗ Code file not found: {code_file}")
                
                notify_debug(f"Engineer: Complete {agent_name}", {
                    "code_file": code_file
                })
            
            # ================================================================
            # STEP 3: QA LEAD - Validate Generated Agents
            # ================================================================
            
            notify_debug("QA Lead: Start", {
                "files_to_test": [f["filepath"] for f in generated_code_files]
            })
            
            qa_results = []
            
            for code_info in generated_code_files:
                workspace_logger.info(f"QA testing: {code_info['agent_name']}")
                
                # Create QA Lead for this agent
                qa_agent = create_qa_lead_agent(
                    code_info['definition'],
                    code_info['filepath'],
                    workspace_dir
                )
                
                # Setup trace logging
                qa_trace_path = os.path.join(
                    workspace_dir,
                    f"qa_trace_{code_info['agent_name']}.log"
                )
                qa_trace_plugin = TraceLoggerPlugin(qa_trace_path)
                
                # Run QA
                qa_runner = InMemoryRunner(
                    agent=qa_agent,
                    plugins=[qa_trace_plugin]
                )
                
                qa_result = qa_runner.run(
                    input=f"Validate the agent: {code_info['agent_name']}"
                )
                
                qa_results.append({
                    "agent_name": code_info['agent_name'],
                    "result": qa_result
                })
                
                workspace_logger.info(f"QA completed for: {code_info['agent_name']}")
            
            notify_debug("QA Lead: Complete", qa_results)
            
            # ================================================================
            # FINAL: Summary
            # ================================================================
            
            final_results = {
                "workspace_dir": workspace_dir,
                "blueprint": blueprint,
                "generated_files": generated_code_files,
                "qa_results": qa_results,
                "status": "success"
            }
            
            workspace_logger.info("=== Agent Factory Complete ===")
            workspace_logger.info(f"Generated {len(generated_code_files)} agents")
            
            return workspace_dir, final_results
            
        except InterruptedError:
            workspace_logger.warning("Process interrupted by user")
            return None, None
        except Exception as e:
            workspace_logger.error(f"Factory error: {e}", exc_info=True)
            return None, None
    
    async def _run_architect_with_hitl(
        self,
        goal: str,
        workspace_dir: str,
        workspace_logger: logging.Logger,
        notify_debug: callable
    ) -> Optional[Dict[str, Any]]:
        """
        Runs Architect with Human-in-the-Loop approval.
        
        Returns:
            Parsed blueprint dict or None
        """
        # Wrap architect in resumable app
        architect_app = create_resumable_app(architect, "architect_app")
        
        # Create runner
        trace_log = os.path.join(workspace_dir, "trace_architect.log")
        trace_plugin = TraceLoggerPlugin(trace_log)
        runner = InMemoryRunner(
            agent=architect_app.root_agent,
            plugins=[trace_plugin]
        )
        
        # Run architect
        events = []
        async for event in runner.run_async(new_message=goal):
            events.append(event)
        
        # Check for approval request
        confirmation_req = find_confirmation_request(events)
        
        if confirmation_req:
            workspace_logger.info("Architect requesting approval...")
            
            # Extract blueprint from payload
            blueprint_data = confirmation_req.get('payload', {}).get('blueprint', '')
            
            # Notify user for approval
            notify_debug("Architect: Awaiting Approval", {
                "blueprint": blueprint_data,
                "hint": confirmation_req.get('hint', '')
            })
            
            # In a real implementation, this would wait for user input
            # For now, we'll simulate approval
            # The Streamlit app will need to handle this properly
            
            # TODO: The calling code (Streamlit) needs to:
            # 1. Display the blueprint to the user
            # 2. Get approval (true/false) and feedback
            # 3. Call runner.run_async again with create_approval_response()
            
            workspace_logger.info("Blueprint requires user approval (HITL)")
            
            # Extract blueprint for now
            try:
                blueprint = json.loads(blueprint_data) if isinstance(blueprint_data, str) else blueprint_data
                return blueprint
            except:
                workspace_logger.error("Failed to parse blueprint from approval request")
                return None
        else:
            # No approval needed or already approved
            # Extract blueprint from output
            final_output = events[-1] if events else None
            blueprint = extract_blueprint_from_output(final_output)
            return blueprint
    
    async def _run_architect_yolo(
        self,
        goal: str,
        workspace_dir: str,
        workspace_logger: logging.Logger
    ) -> Optional[Dict[str, Any]]:
        """
        Runs Architect in YOLO mode (no HITL).
        
        We achieve this by NOT wrapping in a resumable app,
        so the request_approval tool won't pause execution.
        
        Returns:
            Parsed blueprint dict or None
        """
        workspace_logger.info("Running Architect in YOLO mode (no approval needed)")
        
        # Run architect directly without resumability
        trace_log = os.path.join(workspace_dir, "trace_architect.log")
        trace_plugin = TraceLoggerPlugin(trace_log)
        runner = InMemoryRunner(
            agent=architect,
            plugins=[trace_plugin]
        )
        
        # Since request_approval checks tool_context.tool_confirmation,
        # and there's no resumability, it will just return "pending" status
        # We need to modify the Architect to skip approval in YOLO mode
        
        # For now, let's run synchronously
        result = runner.run(input=goal)
        
        # Extract blueprint
        blueprint = extract_blueprint_from_output(result)
        return blueprint
    
    def create_agent(
        self,
        goal: str,
        mode: str = "debug",
        max_review_iterations: int = 3,
        debug_callback: Optional[callable] = None
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Synchronous wrapper for create_agent_async.
        
        Args:
            goal: User's high-level goal
            mode: "debug" or "yolo"
            max_review_iterations: Max review loop iterations
            debug_callback: Debug event callback
            
        Returns:
            Tuple of (workspace_dir, results) or (None, None)
        """
        return asyncio.run(
            self.create_agent_async(
                goal, mode, max_review_iterations, debug_callback
            )
        )
