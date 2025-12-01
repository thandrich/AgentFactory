
import asyncio
import logging
from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing ParallelAgent and SequentialAgent...")

    # Mock agents using LlmAgent with simple instructions
    # We use a simple model or even a mock if possible, but let's try with Gemini flash
    model = Gemini(model="gemini-2.5-flash")

    agent1 = LlmAgent(
        name="Agent1",
        model=model,
        instruction="You are Agent 1. Output 'Hello from Agent 1'."
    )

    agent2 = LlmAgent(
        name="Agent2",
        model=model,
        instruction="You are Agent 2. Output 'Hello from Agent 2'."
    )

    # Parallel Agent
    parallel_team = ParallelAgent(
        name="ParallelTeam",
        sub_agents=[agent1, agent2]
    )

    # Auditor Agent
    auditor = LlmAgent(
        name="Auditor",
        model=model,
        instruction="You are an Auditor. You receive inputs from multiple agents. Summarize them."
    )

    # Sequential Agent
    root_agent = SequentialAgent(
        name="RootAgent",
        sub_agents=[parallel_team, auditor]
    )

    runner = InMemoryRunner(agent=root_agent)
    
    print("Running RootAgent...")
    events = await runner.run_debug("Start the process.")
    
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Final Output: {part.text}")
                    return

if __name__ == "__main__":
    asyncio.run(main())
