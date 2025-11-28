import logging
import json
import os
from typing import Any, Dict

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
