import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.factory import AgentFactory
from agent_factory.qa_lead import QALead

def demo():
    print("Starting AgentFactory Demo...")
    
    # 1. Initialize Factory and QA
    factory = AgentFactory()
    qa = QALead()
    
    # 2. Define Goal
    goal = "Build a weather bot that can tell me the weather in London"
    print(f"Goal: {goal}")
    
    # 3. Create Agent
    print("\n--- Phase 1-3: Creation ---")
    agent_code = factory.create_agent(goal)
    
    if not agent_code:
        print("Failed to create agent.")
        sys.exit(1)
        
    print("\n--- Agent Created ---")
    print(agent_code[:200] + "...")
    
    # 4. Test Agent
    print("\n--- Phase 4: Execution ---")
    test_query = "What is the weather in London?"
    result = qa.test_agent(agent_code, test_query)
    
    if result["success"]:
        print(f"SUCCESS: Agent executed successfully.")
        print(f"Result: {result['result']}")
        print(f"Trace: {result['trace']}")
    else:
        print(f"FAILED: Agent execution failed.")
        print(f"Error: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    demo()
