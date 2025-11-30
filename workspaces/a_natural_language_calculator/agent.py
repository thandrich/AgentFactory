# DEPENDENCIES:
# google-adk
# python-dotenv
# math (built-in)
# re (built-in)

import os
import asyncio
import math
import re
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

# Model Configuration
model_config = Gemini(model="gemini-2.5-flash")

def calculate_expression(expression_string: str) -> dict:
    """
    Calculates the result of a given mathematical expression string.
    Supports basic arithmetic operators (+, -, *, /, **, sqrt), parentheses, and numerical values.

    Args:
        expression_string: A string representing the mathematical expression (e.g., "10 + 5 * 2", "sqrt(81) - 3**2").

    Returns:
        A dictionary containing either the 'result' of the calculation or an 'error' message.
    """
    # Basic input validation to prevent common injection attempts or invalid characters.
    # This regex ensures the expression only contains digits, common operators, parentheses,
    # decimal points, whitespace, and the literal string "sqrt".
    # It explicitly disallows other alphabetical characters or semicolons.
    
    # Check for disallowed characters like letters (unless part of 'sqrt') or semicolons.
    if re.search(r"[a-df-zA-DF-Z_]", expression_string) or ";" in expression_string:
        return {"error": "Expression contains invalid characters or constructs (only numbers, operators, 'sqrt', and parentheses are allowed)."}

    # Replace 'sqrt' with 'math.sqrt' for evaluation, allowing for natural use by the LLM.
    processed_expression = expression_string.replace('sqrt', 'math.sqrt')

    # Define a restricted environment for eval to enhance security.
    # We provide an empty dictionary for '__builtins__', which removes access to most dangerous built-in functions.
    # We explicitly provide the 'math' module, allowing access to `math.sqrt`.
    safe_globals = {
        "__builtins__": {}, # No access to unsafe built-in functions like open(), exec(), etc.
        "math": math,       # Allow access to the math module (e.g., math.sqrt)
    }
    
    # No local variables are needed for evaluating simple mathematical expressions.
    safe_locals = {}

    try:
        # Evaluate the expression using the restricted environment.
        result = eval(processed_expression, safe_globals, safe_locals)
        return {"result": result}
    except ZeroDivisionError:
        return {"error": "Cannot divide by zero. Please provide a different calculation."}
    except (SyntaxError, TypeError, NameError, AttributeError) as e:
        # Catch various types of errors that indicate an invalid or malformed expression.
        return {"error": f"Invalid mathematical expression: {e}. Please check your input."}
    except Exception as e:
        # Catch any other unexpected errors during evaluation.
        return {"error": f"An unexpected error occurred during calculation: {e}. Please try again or rephrase."}

# Agent Definition
agent = LlmAgent(
    name="NaturalLanguageCalculator",
    model=model_config,
    instruction="""You are NaturalLanguageCalculator, an AI agent designed to understand and compute mathematical expressions provided in natural language.
Your primary goal is to accurately parse and interpret diverse natural language mathematical queries, perform standard arithmetic operations (addition, subtraction, multiplication, division), correctly apply the order of operations (e.g., PEMDAS/BODMAS), and support common mathematical functions (e.g., powers, square roots).
You will return precise numerical results for valid expressions. For ambiguous, malformed, or uncomputable mathematical expressions (e.g., division by zero), you will gracefully handle them, providing helpful feedback or asking for clarification.
When asked to compute, you MUST call the `calculate_expression` tool with a valid Python mathematical string.
For example, for "What is 100 divided by 4, plus 5 times 2?", you should call `calculate_expression("100 / 4 + 5 * 2")`.
For "Square root of 81 minus three squared", you should call `calculate_expression("sqrt(81) - 3**2")`.
""",
    tools=[calculate_expression]
)

# Main Execution Block
async def main():
    runner = InMemoryRunner(agent=agent)
    
    print("Agent: NaturalLanguageCalculator ready.")
    
    # Test case 1: Basic addition from blueprint
    print("\nUser: What is 15 plus 7?")
    events = await runner.run_debug("What is 15 plus 7?")
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
                    break
    
    # Test case 2: Product and subtraction from blueprint
    print("\nUser: Calculate the product of 12 and 5, then subtract 10.")
    events = await runner.run_debug("Calculate the product of 12 and 5, then subtract 10.")
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
                    break

    # Test case 3: Precedence from blueprint
    print("\nUser: What is 100 divided by 4, plus 5 times 2?")
    events = await runner.run_debug("What is 100 divided by 4, plus 5 times 2?")
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
                    break

    # Test case 4: Square root and power from blueprint
    print("\nUser: Square root of 81 minus three squared.")
    events = await runner.run_debug("Square root of 81 minus three squared.")
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
                    break
                    
    # Test case 5: Division by zero from blueprint
    print("\nUser: Divide forty-two by zero.")
    events = await runner.run_debug("Divide forty-two by zero.")
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
                    break
                    
    # Test case 6: Invalid expression (malformed syntax)
    print("\nUser: Calculate 5 plus (3 times.")
    events = await runner.run_debug("Calculate 5 plus (3 times.")
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
                    break
    
    # Test case 7: Attempted injection (should be caught by tool's validation or sandbox)
    print("\nUser: What is 1+1; print('hello')?")
    events = await runner.run_debug("What is 1+1; print('hello')?")
    for event in reversed(events):
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
                    break

if __name__ == "__main__":
    asyncio.run(main())