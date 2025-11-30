import logging
import json
import os
from typing import Any, Dict, List
import google.generativeai as genai

# Configure logging

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
    """
    local_scope = {}
    try:
        exec(code, {}, local_scope)
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

