import os
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, ToolContext
import asyncio
from typing import List, Dict, Any

# Placeholder functions for tools. In a real scenario, these would interact with external APIs or libraries.
def generate_story_text(prompt: str, age_group: str, tone: str) -> dict:
    """
    Generates a short children's story based on a provided prompt,
    including characters, plot points, and tone.
    """
    print(f"--- Generating story text ---")
    print(f"Prompt: {prompt}")
    print(f"Age Group: {age_group}")
    print(f"Tone: {tone}")
    # Simulate a story generation
    story = f"Once upon a time, in a land of {tone} wonders, there lived a character who was {prompt}. This character was destined for an adventure, suitable for a {age_group} audience. The story unfolds with..."
    return {"status": "success", "data": {"story_text": story, "prompt": prompt, "age_group": age_group, "tone": tone}}

def generate_illustration(scene_description: str, style: str, characters: List[str]) -> dict:
    """
    Creates an illustration that visually represents a specific scene or character
    described in the story.
    """
    print(f"--- Generating illustration ---")
    print(f"Scene Description: {scene_description}")
    print(f"Style: {style}")
    print(f"Characters: {', '.join(characters)}")
    # Simulate illustration generation
    illustration_data = f"[{style} illustration of: {scene_description} featuring {', '.join(characters)}]"
    return {"status": "success", "data": {"illustration_data": illustration_data, "scene_description": scene_description, "style": style, "characters": characters}}

def compile_to_pdf(story_content: str, illustrations: List[Dict[str, Any]], page_layout: str) -> dict:
    """
    Assembles story text and associated illustrations into a printable PDF document.
    """
    print(f"--- Compiling to PDF ---")
    print(f"Story Content: {story_content[:100]}...") # Truncate for logging
    print(f"Illustrations: {len(illustrations)} found")
    print(f"Page Layout: {page_layout}")
    # Simulate PDF compilation
    pdf_output = f"PDF output generated with layout '{page_layout}' for story: '{story_content[:50]}...' and {len(illustrations)} illustrations."
    return {"status": "success", "data": {"pdf_content": pdf_output, "file_name": "childrens_story.pdf"}}

# Model Configuration
model_config = Gemini(model="gemini-2.5-flash")

# Agent Definition
agent = LlmAgent(
    name="Story Weaver AI",
    model=model_config,
    instruction="Mission: To generate engaging and age-appropriate short children's stories with accompanying illustrations, formatted into a printable PDF. Scene: A user has provided a prompt for a children's story. Think: Analyze the user's prompt to identify key themes, characters, and plot elements suitable for a children's story. Determine the appropriate tone (e.g., whimsical, adventurous, educational). Plan the narrative arc (beginning, middle, end) and brainstorm potential illustrations that complement the story. Identify necessary tools to generate text and images, and to compile the final PDF. Act: Use the story generation tool to write the narrative. Use the illustration generation tool to create visuals for key scenes. Use the PDF compilation tool to assemble the story and illustrations into a printable format. Observe: Present the generated PDF to the user for review. If the user requests revisions, revisit the 'Think' phase to adjust the story or illustrations based on feedback. Repeat the 'Act' and 'Observe' phases until the user is satisfied. Finalize and deliver the printable PDF.",
    tools=[generate_story_text, generate_illustration, compile_to_pdf]
)

async def main():
    runner = InMemoryRunner(agent=agent)
    
    # Example 1: Initial story request
    print("--- Running Example 1 ---")
    response1 = await runner.run_debug(
        "Create a story about a brave little squirrel who finds a hidden treasure. Include a grumpy badger and a wise old owl."
    )
    print("Response 1:", response1)
    print("\n" + "="*50 + "\n")

    # Example 2: Revision request based on few-shot example
    print("--- Running Example 2 (Revision) ---")
    # Assuming the agent has context of the previous interaction, we simulate a follow-up
    # In a real chat interface, this would be a direct continuation.
    # For demonstration, we'll create a new prompt that implies a revision.
    response2 = await runner.run_debug(
        "I'd like the treasure to be a giant, shiny acorn instead of gold coins. And make the age range 4-6 and the tone whimsical."
    )
    print("Response 2:", response2)
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())