import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.auditor import Auditor

def test_auditor_review():
    print("Testing Auditor Review...")
    auditor = Auditor()
    
    blueprint = {
        "agent_name": "WeatherBot",
        "tools": [{"name": "get_weather"}]
    }
    
    # Test Case 1: Good Code
    good_code = """
def get_weather(location):
    pass
"""
    result = auditor.review_code(good_code, blueprint)
    if result is True:
        print("SUCCESS: Auditor approved good code.")
    else:
        print(f"FAILED: Auditor rejected good code. Result: {result}")
        sys.exit(1)
        
    # Test Case 2: Bad Code (Missing function)
    bad_code = """
def other_function():
    pass
"""
    result = auditor.review_code(bad_code, blueprint)
    if isinstance(result, dict) and not result["approved"]:
        print("SUCCESS: Auditor rejected bad code.")
    else:
        print(f"FAILED: Auditor approved bad code. Result: {result}")
        sys.exit(1)

if __name__ == "__main__":
    test_auditor_review()
