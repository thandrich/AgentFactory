
import unittest
from unittest.mock import MagicMock, patch
import asyncio
import json
import os
from src.agent_factory.factory import AgentFactory
from google.adk.models.google_llm import Gemini
from google.genai.types import GenerateContentResponse, Candidate, Content, Part

class TestFactoryParallel(unittest.TestCase):
    @patch("src.agent_factory.factory.Architect")
    @patch("src.agent_factory.factory.Engineer")
    @patch("src.agent_factory.factory.Auditor")
    def test_create_agent_parallel(self, MockAuditor, MockEngineer, MockArchitect):
        # Setup Mocks
        factory = AgentFactory()
        
        # 1. Mock Architect Blueprint
        blueprint = {
            "end_to_end_context": "Context",
            "agents": [
                {"agent_name": "AgentA", "role": "RoleA"},
                {"agent_name": "AgentB", "role": "RoleB"}
            ]
        }
        factory.architect.design_workflow.return_value = blueprint
        
        # 2. Mock Engineer Agents
        from google.adk.agents import LlmAgent
        
        # Helper to create a mocked model
        class MockGemini(Gemini):
            response_text: str = "Default"
            
            def generate_content(self, *args, **kwargs):
                return GenerateContentResponse(
                    candidates=[Candidate(content=Content(parts=[Part(text=self.response_text)]))]
                )

        agent_a = LlmAgent(name="Engineer_AgentA", model=MockGemini(model="gemini-2.5-flash", response_text="Code for AgentA"), instruction="instr")
        agent_b = LlmAgent(name="Engineer_AgentB", model=MockGemini(model="gemini-2.5-flash", response_text="Code for AgentB"), instruction="instr")

        # Mock Engineer.create_adk_agent to return these agents
        def create_engineer_side_effect(agent_def, context):
            if agent_def["agent_name"] == "AgentA": return agent_a
            if agent_def["agent_name"] == "AgentB": return agent_b
            return None
        factory.engineer.create_adk_agent.side_effect = create_engineer_side_effect

        # 3. Mock Auditor Agent
        review_json = json.dumps({
            "approved": True,
            "issues": [],
            "suggestions": []
        })
        auditor_agent = LlmAgent(name="Auditor", model=MockGemini(model="gemini-2.5-flash", response_text=review_json), instruction="instr")
        factory.auditor.create_adk_agent.return_value = auditor_agent

        # Run Factory
        try:
            # We need to mock os.makedirs and open to avoid writing files
            with patch("os.makedirs"), patch("builtins.open", unittest.mock.mock_open()) as mock_file:
                code, blueprint_result = factory.create_agent("Build a bot")
                
                # Assertions
                self.assertIsNotNone(code)
                self.assertEqual(blueprint_result, blueprint)
                
                # Check if code corresponds to one of the agents
                self.assertTrue("Code for Agent" in code)
                
                print(f"Returned code: {code}")
                
        except Exception as e:
            self.fail(f"create_agent raised exception: {e}")

if __name__ == "__main__":
    unittest.main()
