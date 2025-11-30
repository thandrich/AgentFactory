#!/usr/bin/env python3
"""
Agent Adapter for Subprocess Communication
This script is copied to each agent's workspace to enable
stdin/stdout communication for isolated execution.
"""
import sys
import json
import asyncio
from google.adk.runners import InMemoryRunner

# Import the agent from the generated agent.py
from agent import agent

async def main():
    """Main loop that reads from stdin and writes to stdout."""
    runner = InMemoryRunner(agent=agent)
    
    # Read lines from stdin
    for line in sys.stdin:
        try:
            # Parse input JSON
            request = json.loads(line)
            query = request.get("query", "")
            
            if query == "__EXIT__":
                break
                
            # Run the agent
            events = await runner.run_debug(query)
            
            # Extract response
            response_text = ""
            for event in reversed(events):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text = part.text
                            break
                    if response_text:
                        break
            
            # Write response to stdout
            response = {"response": response_text, "error": None}
            print(json.dumps(response), flush=True)
            
        except Exception as e:
            # Write error to stdout
            error_response = {"response": None, "error": str(e)}
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
