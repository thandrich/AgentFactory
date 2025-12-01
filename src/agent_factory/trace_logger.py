"""
Trace Logger Plugin for ADK Agents

This plugin extends BasePlugin to capture and log all agent interactions
(user inputs, LLM responses, tool calls) to a file for debugging and auditing.
"""

import logging
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.callback_context import CallbackContext


class TraceLoggerPlugin(BasePlugin):
    """
    Custom plugin that logs all agent traces to a file.
    
    Implements the after_agent_callback hook to extract session events
    and write them to a structured log file after each agent execution.
    """
    
    def __init__(self, log_file_path: Optional[str] = None):
        """
        Initialize the trace logger plugin.
        
        Args:
            log_file_path: Path to the log file. If None, logs to 'agent_traces.log'
        """
        super().__init__(name="trace_logger")
        self.log_file_path = log_file_path or "agent_traces.log"
        self.logger = logging.getLogger("TraceLogger")
        
        # Ensure log directory exists
        Path(self.log_file_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"TraceLoggerPlugin initialized, writing to: {self.log_file_path}")
    
    async def after_agent_callback(self, agent, callback_context: CallbackContext):
        """
        Called after each agent execution. Extracts and logs session events.
        
        Args:
            agent: The agent that just executed
            callback_context: Contains the invocation context with session data
        """
        try:
            # Access the session from the callback context
            session = callback_context._invocation_context.session
            
            # Prepare log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent.name,
                "events": []
            }
            
            # Extract all events from the session
            for event in session.events:
                event_data = {
                    "type": type(event).__name__,
                    "content": None
                }
                
                # Extract content if available
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        # Extract text from parts
                        parts_text = []
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                parts_text.append(part.text)
                            elif hasattr(part, 'function_call'):
                                # Log tool/function calls
                                parts_text.append(f"TOOL_CALL: {part.function_call}")
                            elif hasattr(part, 'function_response'):
                                # Log tool responses
                                parts_text.append(f"TOOL_RESPONSE: {part.function_response}")
                        
                        event_data["content"] = " ".join(parts_text) if parts_text else None
                
                # Add role if available
                if hasattr(event, 'role'):
                    event_data["role"] = event.role
                
                log_entry["events"].append(event_data)
            
            # Write to log file (append mode)
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, indent=2) + "\n")
                f.write("-" * 80 + "\n")
            
            self.logger.debug(f"Logged {len(log_entry['events'])} events for agent: {agent.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to log trace: {e}", exc_info=True)
