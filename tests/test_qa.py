import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.qa_lead import QALead

def test_qa_lead():
    print("Testing QA Lead...")
    qa = QALead()
    
    # Mock Agent Code
    agent_code = """
class WeatherBot:
    def run(self, query):
        print(f"Thinking about {query}...")
        return "Sunny"
"""
    
    test_query = "What is the weather?"
    result = qa.test_agent(agent_code, test_query)
    
    if result["success"] and result["result"] == "Sunny":
        print("SUCCESS: QA Lead executed agent successfully.")
        print(f"Trace: {result['trace']}")
    else:
        print(f"FAILED: QA Lead failed. Result: {result}")
        sys.exit(1)

if __name__ == "__main__":
    test_qa_lead()
