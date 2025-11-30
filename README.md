# 🏭 AgentFactory

**AgentFactory** is a collaborative multi-agent system designed to automate the creation of high-quality AI agents. Powered by **Google Gemini** and the **Agent Development Kit (ADK)**, it employs a "Team of Specialists" architecture to design, build, review, and test agents based on high-level user goals.

## 🚀 Key Features

*   **Team of Specialists Architecture**:
    *   **The Architect**: Analyzes goals and designs a comprehensive JSON Blueprint (Persona, Tools, State).
    *   **The Engineer**: Implements the agent in Python using the Google ADK, adhering to strict syntax and best practices.
    *   **The Auditor**: Reviews the code for security, logic, and safety, providing feedback for iterative refinement.
    *   **The QA Lead**: Validates the agent by executing it in a sandbox environment against the original criteria.

*   **Dual Operation Modes**:
    *   **🚀 YOLO Mode**: "You Only Look Once" - A fire-and-forget mode for rapid prototyping. Enter a goal, and the factory handles the entire pipeline automatically.
    *   **🐞 Debug Mode**: A fully interactive, step-by-step execution mode. Review the Architect's blueprint, the Engineer's code, and the Auditor's feedback in real-time. Pause, resume, or abort at any stage.

*   **Dynamic Model Selection**:
    *   Real-time fetching of available Gemini models (e.g., `gemini-2.5-flash`, `gemini-pro`, Thinking models).
    *   Detailed model capabilities display (Token limits, Sampling defaults, Reasoning support).

*   **Production-Ready Output**:
    *   Generates standalone Python files (`agent.py`) ready for deployment.
    *   Includes built-in security guardrails (e.g., `max_api_calls`).
    *   Uses the official `google-adk` library for robust agent implementation.

## 🛠️ Installation

### Prerequisites
*   Python 3.10+
*   [uv](https://github.com/astral-sh/uv) (Fast Python package installer)
*   A Google Cloud Project with the **Gemini API** enabled.

### Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd agent_factory
    ```

2.  **Install dependencies**:
    ```bash
    uv sync
    ```

3.  **Configure Environment**:
    Create a `.env` file in the root directory and add your Google API Key:
    ```env
    GOOGLE_API_KEY=your_api_key_here
    ```

## 🎮 Usage

1.  **Start the Web Interface**:
    ```bash
    uv run streamlit run app.py
    ```

2.  **Configure the Factory**:
    *   Open the **⚙️ Configuration** expander at the top.
    *   Select your desired **Model** (e.g., `Gemini 2.5 Flash`).
    *   Adjust the **Max API Calls** slider for safety.

3.  **Build an Agent**:
    *   **YOLO Mode**: Enter your prompt (e.g., "Build a weather bot for London") and click **Build Agent**.
    *   **Debug Mode**: Switch to the Debug tab, enter your prompt, and click **Start Debug Session**. Follow the interactive steps to guide the creation process.

4.  **Access Your Agent**:
    *   Generated agents are saved in the `workspaces/` directory, organized by project slug.
    *   Each workspace contains the `agent.py` code and execution logs.

## 📂 Project Structure

```text
agent_factory/
├── app.py                  # Streamlit Web Application entry point
├── src/
│   └── agent_factory/
│       ├── architect.py    # Blueprint design logic
│       ├── engineer.py     # Code generation logic
│       ├── auditor.py      # Code review and safety checks
│       ├── qa_lead.py      # Execution and validation
│       ├── factory.py      # Orchestration logic
│       └── utils.py        # Shared utilities (logging, model fetching)
├── workspaces/             # Output directory for generated agents
├── .env                    # API Keys (not committed)
└── pyproject.toml          # Project dependencies
```

## 🛡️ Security

*   **API Limits**: The generated agents include a `max_api_calls` parameter to prevent runaway loops.
*   **Sandboxing**: The QA Lead executes agents in a controlled environment (local execution in this version, expandable to Docker/Sandboxes).
*   **Audit**: The Auditor agent explicitly checks for unsafe imports and potential security vulnerabilities before code is approved.
