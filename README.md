# 🏭 AgentFactory

**AgentFactory** is a collaborative multi-agent system designed to automate the creation of high-quality AI agent workflows. Powered by **Google Gemini** and the **Agent Development Kit (ADK)**, it employs a "Team of Specialists" architecture to design, build, review, and test agentic workflows based on high-level user goals.

Built entirely on **`google.adk`** and **`google.genai`**, AgentFactory demonstrates advanced ADK patterns including sequential orchestration, review loops, human-in-the-loop (HITL) execution, and comprehensive trace logging. It exemplifies the next step in the journey to Business As A Service (BAAS) in which customers provide funds and a business plan to a BAAS provider to build and run an end-to-end AI business for them.

## 🚀 Key Features

*   **Pure ADK Architecture**:
    *   Built exclusively with `google.adk` agents (`LlmAgent`, `SequentialAgent`, `LoopAgent`)
    *   Leverages `google.genai` for model configuration and retry handling
    *   Implements ADK best practices from the official coding patterns

*   **Team of Specialists Architecture**:
    *   **The Architect**: Analyzes goals and designs a comprehensive JSON Blueprint using `LlmAgent` with flowchart generation and approval tools
    *   **The Engineer**: Implements agents in Python using ADK, adhering to strict syntax from the AgentCoding.txt bible
    *   **The Auditor**: Reviews code for security, logic, and safety within a `LoopAgent` for iterative refinement
    *   **The QA Lead**: Validates agents by executing them in a sandbox environment against the original criteria

*   **Advanced Orchestration Patterns**:
    *   **Sequential Workflow**: Architect → Engineer+Auditor Loop → QA Lead pipeline
    *   **Review Loops**: Engineer and Auditor iterate in a `LoopAgent` until code is approved (max 3 iterations)
    *   **Resumability**: HITL architecture using ADK's `ResumabilityConfig` for blueprint approval
    *   **Trace Logging**: Comprehensive execution tracing via custom `TraceLoggerPlugin`

*   **Dual Operation Modes**:
    *   **🚀 YOLO Mode**: Fully automated end-to-end execution without human intervention
    *   **🐞 Debug Mode**: Human-in-the-loop at the Architect stage for blueprint review and approval. Interactive step-by-step execution with real-time feedback.

*   **Dynamic Model Selection**:
    *   Real-time fetching of available Gemini models (e.g., `gemini-2.5-flash`, `gemini-2.0-pro`)
    *   Detailed model capabilities display (Token limits, Sampling defaults, Reasoning support)
    *   Retry configuration with exponential backoff for production reliability

*   **Production-Ready Output**:
    *   Generates standalone Python files implementing ADK agents ready for deployment
    *   Includes built-in security guardrails (e.g., `max_api_calls`)
    *   Full trace logs and debug artifacts for every execution

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
    *   Generated agents are saved in the `workspaces/{project_slug}/` directory
    *   Each workspace contains:
        *   `agent_{name}.py` - Generated ADK agent implementation
        *   `blueprint.json` - Architect's workflow design
        *   `trace_*.log` - Detailed execution traces for each agent phase
        *   `debug.log` - Comprehensive factory execution log
        *   `workflow_blueprint.png` - Visual flowchart of agent dependencies

## 📂 Project Structure

```text
agent_factory/
├── app.py                      # Streamlit Web Application entry point
├── src/
│   └── agent_factory/
│       ├── factory.py          # Main orchestration using SequentialAgent & LoopAgent
│       ├── architect.py        # Architect agent (LlmAgent with HITL tools)
│       ├── engineer.py         # Engineer agent factory (dynamic agent creation)
│       ├── auditor.py          # Auditor agent (code review LlmAgent)
│       ├── qa_lead.py          # QA Lead agent factory (validation agent creation)
│       ├── trace_logger.py     # Custom TraceLoggerPlugin for execution tracing
│       ├── agent_adapter.py    # ADK-to-legacy adapter for compatibility
│       └── utils.py            # Shared utilities (logging, model fetching, resumability)
├── .papers/
│   └── AgentCoding.txt         # ADK coding bible (patterns and best practices)
├── workspaces/                 # Output directory for generated agents
│   └── {project_slug}/
│       ├── agent_{name}.py     # Generated ADK agent code
│       ├── blueprint.json      # Architect's design blueprint
│       ├── trace_*.log         # Execution traces for each phase
│       └── debug.log           # Comprehensive debug logging
├── .env                        # API Keys (not committed)
└── pyproject.toml              # Project dependencies
```

## 🏗️ Architecture

AgentFactory implements a **sequential workflow** with embedded **review loops** using ADK orchestration agents:

```
User Goal → Architect (HITL in Debug) → [Engineer ⇄ Auditor Loop] → QA Lead → Final Agent
```

### Key Architectural Components:

1. **Architect Agent** (`LlmAgent`)
   - Tools: `generate_workflow_flowchart`, `request_approval`
   - Outputs: JSON blueprint + Graphviz flowchart
   - HITL: Uses `ResumabilityConfig` + `request_confirmation` in Debug mode

2. **Engineer-Auditor Loop** (`LoopAgent`)
   - Sequential sub-agents: Engineer → Auditor
   - Engineer creates ADK agent code based on blueprint
   - Auditor reviews for security/correctness
   - Iterates max 3 times until approved

3. **QA Lead Agent** (`LlmAgent`)
   - Validates generated agents against original criteria
   - Executes agents in controlled environment
   - Produces validation report

4. **Trace Logging** (`TraceLoggerPlugin`)
   - Custom plugin implementing `BasePlugin`
   - Logs all agent turns, tool calls, and LLM interactions
   - Outputs structured logs to workspace for debugging

## 🛡️ Security & Observability

*   **API Limits**: Generated agents include `max_api_calls` parameter to prevent runaway loops
*   **Sandboxing**: QA Lead executes agents in controlled environment (expandable to Docker/Sandboxes)
*   **Code Audit**: Auditor agent checks for unsafe imports and security vulnerabilities within the review loop
*   **Retry Handling**: Exponential backoff retry configuration on all models (handles 429, 500, 503, 504 errors)
*   **Trace Logging**: Complete execution traces via `TraceLoggerPlugin` for debugging and compliance
*   **Resumability**: HITL workflows use ADK's resumability to safely pause/resume execution
