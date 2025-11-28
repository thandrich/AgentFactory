import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.factory import AgentFactory

def test_factory_loop():
    print("Testing Agent Factory Loop...")
    factory = AgentFactory()
    
    goal = "Build a weather bot"
    code = factory.create_agent(goal)
    
    if code:
        print("SUCCESS: Factory created agent code.")
        print("Code snippet:")
        print(code[:200] + "...")
    else:
        print("FAILED: Factory failed to create agent.")
        sys.exit(1)

if __name__ == "__main__":
    test_factory_loop()
