import sys
import os
import shutil

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.factory import AgentFactory

def test_adk_integration_and_security():
    print("Testing ADK Integration and Security...")
    factory = AgentFactory()
    
    goal = "Build a weather bot with ADK"
    
    # Clean up previous workspace if exists
    slug = "".join(c if c.isalnum() else "_" for c in goal.lower())[:50]
    workspace_dir = os.path.join(os.getcwd(), "workspaces", slug)
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
        
    code = factory.create_agent(goal)
    
    if not code:
        print("FAILED: Factory failed to create agent.")
        sys.exit(1)
        
    # 1. Verify ADK Import
    if "import google.adk" in code or "class MockADK" in code:
        print("SUCCESS: Code contains ADK import/mock.")
    else:
        print("FAILED: Code does not contain ADK import.")
        sys.exit(1)
        
    # 2. Verify Security Limit
    if "max_api_calls" in code:
        print("SUCCESS: Code contains max_api_calls security limit.")
    else:
        print("FAILED: Code does not contain max_api_calls.")
        sys.exit(1)
        
    # 3. Verify Dynamic Storage
    if os.path.exists(workspace_dir):
        print(f"SUCCESS: Workspace directory created: {workspace_dir}")
        agent_file = os.path.join(workspace_dir, "agent.py")
        if os.path.exists(agent_file):
             print(f"SUCCESS: Agent file saved: {agent_file}")
        else:
            print("FAILED: Agent file not found in workspace.")
            sys.exit(1)
    else:
        print(f"FAILED: Workspace directory not created: {workspace_dir}")
        sys.exit(1)

if __name__ == "__main__":
    test_adk_integration_and_security()
