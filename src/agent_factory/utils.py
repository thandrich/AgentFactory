import logging
import json
import os
from typing import Any, Dict, List, Optional
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("AgentFactory")

def setup_logging(name: str, log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # Capture everything
    
    # Check if handlers already exist to avoid duplicates
    if not logger.handlers:
        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    # File Handler (if requested)
    if log_file:
        # Check if file handler already exists
        has_file_handler = any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(log_file) for h in logger.handlers)
        if not has_file_handler:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            
    return logger

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables or config file."""
    # Placeholder for loading config
    return {}

def save_artifact(name: str, content: Any, artifact_type: str = "json"):
    """Save an artifact to the artifacts directory."""
    # Placeholder for saving artifacts
    logger.info(f"Saving artifact: {name} ({artifact_type})")
    # In a real implementation, this would write to a file

def get_available_models() -> List[Dict[str, Any]]:
    """
    Retrieves a list of available Gemini models that support content generation.
    Returns a list of dictionaries with model details.
    """
    try:
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Check for attributes safely
                is_thinking = getattr(m, 'thinking', False)
                version = getattr(m, 'version', 'unknown')
                
                model_info = {
                    "name": m.name,
                    "display_name": m.display_name,
                    "description": m.description,
                    "version": version,
                    "input_token_limit": m.input_token_limit,
                    "output_token_limit": m.output_token_limit,
                    "supported_generation_methods": m.supported_generation_methods,
                    "thinking": is_thinking,
                    "temperature": getattr(m, 'temperature', None),
                    "max_temperature": getattr(m, 'max_temperature', None),
                    "top_p": getattr(m, 'top_p', None),
                    "top_k": getattr(m, 'top_k', None)
                }
                
                # Determine type
                if is_thinking:
                    model_info["type"] = "Thinking / Agentic"
                elif "flash" in m.name.lower():
                    model_info["type"] = "Fast / Flash"
                elif "pro" in m.name.lower():
                    model_info["type"] = "Standard / Pro"
                else:
                    model_info["type"] = "Other"
                    
                models.append(model_info)
        return models
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return []

def load_agent_from_code(code: str):
    """
    Executes the provided code string and returns the 'agent' object defined within it.
    Pre-loads common imports to prevent "name not defined" errors.
    """
    # Pre-load common imports into global scope
    global_scope = {
        '__builtins__': __builtins__,
        'os': __import__('os'),
        'sys': __import__('sys'),
        'json': __import__('json'),
        'asyncio': __import__('asyncio'),
        'logging': __import__('logging'),
    }
    
    # Add ADK imports
    try:
        global_scope['types'] = __import__('google.genai.types', fromlist=['types'])
        global_scope['LlmAgent'] = __import__('google.adk.agents', fromlist=['LlmAgent']).LlmAgent
        global_scope['Gemini'] = __import__('google.adk.models.google_llm', fromlist=['Gemini']).Gemini
        global_scope['InMemoryRunner'] = __import__('google.adk.runners', fromlist=['InMemoryRunner']).InMemoryRunner
    except ImportError as e:
        logger.warning(f"Could not preload ADK modules: {e}")
    
    local_scope = {}
    try:
        exec(code, global_scope, local_scope)
    except Exception as e:
        raise ValueError(f"Failed to execute agent code: {e}")
        
    if "agent" not in local_scope:
        raise ValueError("The generated code does not define an 'agent' variable.")
        
    return local_scope["agent"]

class SubprocessAgentRunner:
    """
    Runs a generated agent in a subprocess with isolated dependencies.
    """
    def __init__(self, workspace_dir: str):
        """
        Initialize the subprocess runner.
        
        Args:
            workspace_dir: Path to the workspace containing agent.py
        """
        self.workspace_dir = workspace_dir
        self.process = None
        self.dependencies = []
        
    def _extract_dependencies(self, code: str) -> list:
        """Extract dependencies from the DEPENDENCIES comment block."""
        deps = []
        in_deps_block = False
        for line in code.split('\n'):
            if line.strip().startswith('# DEPENDENCIES:'):
                in_deps_block = True
                continue
            if in_deps_block:
                if line.strip().startswith('#'):
                    dep = line.strip()[1:].strip()
                    if dep:
                        deps.append(dep)
                else:
                    break
        return deps
        
    def start(self, code: str):
        """
        Start the agent subprocess.
        
        Args:
            code: The generated agent code
        """
        import subprocess
        import shutil
        
        # Extract dependencies
        self.dependencies = self._extract_dependencies(code)
        
        # Copy agent_adapter.py to workspace
        adapter_src = os.path.join(os.path.dirname(__file__), "agent_adapter.py")
        adapter_dst = os.path.join(self.workspace_dir, "agent_adapter.py")
        shutil.copy(adapter_src, adapter_dst)
        
        # Build the command with dependencies
        cmd = ["uv", "run"]
        for dep in self.dependencies:
            cmd.extend(["--with", dep])
        cmd.extend(["python", "agent_adapter.py"])
        
        # Start the subprocess
        self.process = subprocess.Popen(
            cmd,
            cwd=self.workspace_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        logger.info(f"Started agent subprocess with dependencies: {self.dependencies}")
        
    def send_message(self, query: str) -> dict:
        """
        Send a message to the agent and get the response.
        
        Args:
            query: The user's query
            
        Returns:
            dict with {"response": str, "error": str or None}
        """
        if not self.process:
            raise RuntimeError("Subprocess not started. Call start() first.")
            
        # Send query as JSON
        request = json.dumps({"query": query}) + "\n"
        self.process.stdin.write(request)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if response_line:
            return json.loads(response_line)
        else:
            return {"response": None, "error": "No response from agent"}
            
    def stop(self):
        """Stop the agent subprocess."""
        if self.process:
            try:
                # Send exit signal
                self.process.stdin.write(json.dumps({"query": "__EXIT__"}) + "\n")
                self.process.stdin.flush()
                self.process.wait(timeout=5)
            except:
                self.process.terminate()
                self.process.wait(timeout=5)
            finally:
                self.process = None
                logger.info("Stopped agent subprocess")


# ============================================================================
# ADK Resumability Helpers (for Human-in-the-Loop)
# ============================================================================

def create_resumable_app(agent, app_name: str = "resumable_agent"):
    """
    Wraps an agent in an App with ResumabilityConfig for Human-in-the-Loop support.
    
    Args:
        agent: The ADK agent to wrap
        app_name: Name for the app
        
    Returns:
        App: Configured app with resumability enabled
    """
    from google.adk.apps.app import App, ResumabilityConfig
    
    return App(
        name=app_name,
        root_agent=agent,
        resumability_config=ResumabilityConfig(is_resumable=True)
    )


def find_confirmation_request(events: List[Any]) -> Optional[Dict[str, Any]]:
    """
    Searches through ADK events to find a confirmation request event.
    
    This is used to detect when an agent has paused for human approval.
    
    Args:
        events: List of events from runner execution
        
    Returns:
        dict with confirmation request details, or None if not found
    """
    for event in events:
        # Check if this is a function call event
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    # Look for adk_request_confirmation function call
                    if hasattr(part, 'function_call'):
                        func_call = part.function_call
                        if func_call.name == 'adk_request_confirmation':
                            # Extract the confirmation details
                            return {
                                'event_id': id(event),
                                'function_call': func_call,
                                'hint': func_call.args.get('hint', ''),
                                'payload': func_call.args.get('payload', {})
                            }
    return None


def create_approval_response(approved: bool, feedback: str = "") -> Dict[str, Any]:
    """
    Creates a properly formatted approval response message for ADK resumability.
    
    Args:
        approved: Whether the user approved (True) or rejected (False)
        feedback: Optional feedback message from the user
        
    Returns:
        dict: Message object to pass to runner.run_async() for resuming
    """
    from google.genai import types
    
    # Create the confirmation response
    return types.Content(
        role='user',
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    name='adk_request_confirmation',
                    response={
                        'confirmed': approved,
                        'feedback': feedback
                    }
                )
            )
        ]
    )


def extract_blueprint_from_output(output: Any) -> Optional[Dict[str, Any]]:
    """
    Extracts and parses the JSON blueprint from agent output.
    
    Args:
        output: Output from agent execution (could be dict, string, or other)
        
    Returns:
        Parsed blueprint as dict, or None if extraction fails
    """
    import re
    
    # If it's already a dict with 'blueprint' key, return it
    if isinstance(output, dict):
        if 'blueprint' in output:
            bp = output['blueprint']
            if isinstance(bp, str):
                try:
                    return json.loads(bp)
                except:
                    pass
            return bp
        
        # Maybe the whole dict IS the blueprint
        if 'agents' in output and 'end_to_end_context' in output:
            return output
    
    # If it's a string, try to extract JSON
    if isinstance(output, str):
        # Try to find JSON block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try parsing the whole string as JSON
        try:
            return json.loads(output)
        except:
            pass
    
    logger.warning("Could not extract blueprint from output")
    return None
