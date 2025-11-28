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

def setup_logging(name: str) -> logging.Logger:
    return logging.getLogger(name)

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables or config file."""
    # Placeholder for loading config
    return {}

def save_artifact(name: str, content: Any, artifact_type: str = "json"):
    """Save an artifact to the artifacts directory."""
    # Placeholder for saving artifacts
    logger.info(f"Saving artifact: {name} ({artifact_type})")
    # In a real implementation, this would write to a file
