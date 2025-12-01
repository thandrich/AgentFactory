"""
Basic integration test for the rewritten backend.

Tests the basic workflow without full execution to verify structure.
"""

import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent_factory.factory import AgentFactory
from src.agent_factory.architect import architect
from src.agent_factory.engineer import create_engineer_agent
from src.agent_factory.auditor import auditor
from src.agent_factory.qa_lead import create_qa_lead_agent
from src.agent_factory.trace_logger import TraceLoggerPlugin
from src.agent_factory.utils import (
    create_resumable_app,
    find_confirmation_request,
    create_approval_response,
    extract_blueprint_from_output
)


def test_imports():
    """Test that all modules can be imported."""
    assert AgentFactory is not None
    assert architect is not None
    assert create_engineer_agent is not None
    assert auditor is not None
    assert create_qa_lead_agent is not None
    assert TraceLoggerPlugin is not None
    assert create_resumable_app is not None
    assert find_confirmation_request is not None
    assert create_approval_response is not None
    assert extract_blueprint_from_output is not None


def test_factory_initialization():
    """Test factory can be initialized."""
    factory = AgentFactory(model_name="gemini-2.5-flash")
    assert factory is not None
    assert factory.model_name == "gemini-2.5-flash"


def test_workspace_preparation():
    """Test workspace directory creation."""
    factory = AgentFactory()
    workspace_dir, logger = factory.prepare_workspace("test goal unique")
    
    assert workspace_dir is not None
    assert os.path.exists(workspace_dir)
    assert "test_goal_unique" in workspace_dir
    
    # Don't cleanup - may be locked by logger
    # The workspace will be cleaned up manually or on next run


def test_architect_agent_structure():
    """Test architect agent is properly configured."""
    assert architect.name == "Architect"
    assert architect.model is not None
    assert len(architect.tools) == 2  # generate_workflow_flowchart, request_approval


def test_auditor_agent_structure():
    """Test auditor agent is properly configured."""
    assert auditor.name == "Auditor"
    assert auditor.model is not None
    assert len(auditor.tools) == 1  # approve_code


def test_engineer_creation():
    """Test engineer agent can be created."""
    agent_def = {
        "agent_name": "test_agent",
        "role": "Test role",
        "suggested_model": "gemini-2.5-flash",
        "goal": "Test goal",
        "inputs": [],
        "outputs": [],
        "dependencies": [],
        "instructions": "Test instructions"
    }
    
    engineer = create_engineer_agent(agent_def, "Test context")
    
    assert engineer is not None
    assert engineer.name == "Engineer_test_agent"
    assert len(engineer.tools) == 2  # read_coding_bible, write_code_to_file


def test_qa_lead_creation():
    """Test QA lead agent can be created."""
    agent_def = {
        "agent_name": "test_agent",
        "goal": "Test goal"
    }
    
    qa_lead = create_qa_lead_agent(agent_def, "test_code.py", ".")
    
    assert qa_lead is not None
    assert "QA_Lead" in qa_lead.name
    assert len(qa_lead.tools) == 3  # generate_test_case, execute_agent_code, evaluate_results


def test_trace_logger_plugin():
    """Test trace logger plugin can be created."""
    plugin = TraceLoggerPlugin("test_trace.log")
    
    assert plugin is not None
    assert plugin.name == "trace_logger"
    assert plugin.log_file_path == "test_trace.log"
    
    # Cleanup
    if os.path.exists("test_trace.log"):
        os.remove("test_trace.log")


def test_extract_blueprint_from_output():
    """Test blueprint extraction from various output formats."""
    # Test dict with blueprint key
    output1 = {
        "blueprint": {
            "agents": [],
            "end_to_end_context": "test"
        }
    }
    result1 = extract_blueprint_from_output(output1)
    assert result1 is not None
    assert "agents" in result1
    
    # Test dict that IS the blueprint
    output2 = {
        "agents": [],
        "end_to_end_context": "test"
    }
    result2 = extract_blueprint_from_output(output2)
    assert result2 is not None
    assert result2 == output2
    
    # Test JSON string
    output3 = '{"agents": [], "end_to_end_context": "test"}'
    result3 = extract_blueprint_from_output(output3)
    assert result3 is not None
    assert "agents" in result3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
