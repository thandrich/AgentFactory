import sys
import os
import shutil

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.factory import AgentFactory
from agent_factory.qa_lead import QALead

def test_best_practices():
    print("Testing Best Practices Integration...")
    factory = AgentFactory()
    qa = QALead()
    
    goal = "Build a weather bot following best practices"
    
    # Clean up
    slug = "".join(c if c.isalnum() else "_" for c in goal.lower())[:50]
    workspace_dir = os.path.join(os.getcwd(), "workspaces", slug)
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
        
    code, blueprint = factory.create_agent(goal)
    
    if not code or not blueprint:
        print("FAILED: Factory failed to create agent.")
        sys.exit(1)
        
    # 1. Verify Evaluation Criteria in Blueprint
    if "evaluation_criteria" in blueprint:
        print(f"SUCCESS: Blueprint contains evaluation criteria: {blueprint['evaluation_criteria']}")
    else:
        print("FAILED: Blueprint missing evaluation criteria.")
        sys.exit(1)
        
    # 2. Verify Context Compaction in Code
    if "ContextFilterPlugin" in code:
        print("SUCCESS: Code implements ContextFilterPlugin.")
    else:
        print("FAILED: Code missing ContextFilterPlugin.")
        sys.exit(1)
        
    # 3. Verify Robust Docstrings
    if "Args:" in code and "Returns:" in code:
        print("SUCCESS: Code contains detailed docstrings.")
    else:
        print("FAILED: Code missing detailed docstrings.")
        sys.exit(1)
        
    # 4. Verify LLM-as-a-Judge
    test_query = "What is the weather in London?"
    result = qa.test_agent(code, test_query, evaluation_criteria=blueprint["evaluation_criteria"])
    
    if result["success"] and result.get("score") == 5:
        print(f"SUCCESS: QA Lead used LLM-as-a-Judge. Score: {result['score']}")
        print(f"Feedback: {result['judge_feedback']}")
    else:
        print(f"FAILED: QA Lead evaluation failed. Result: {result}")
        sys.exit(1)

if __name__ == "__main__":
    test_best_practices()
