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
