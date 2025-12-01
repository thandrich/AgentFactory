import streamlit as st
import sys
import os
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent_factory.factory import AgentFactory
from agent_factory.qa_lead import QALead
# ... (Previous imports)
from google.adk.runners import InMemoryRunner
from agent_factory.utils import get_available_models, SubprocessAgentRunner
import asyncio

# Helper for Chat Interface
def render_chat_interface(agent_code, key_prefix, workspace_dir):
    st.markdown("### 💬 Chat with your Agent")
    
    # Initialize chat state
    if f"{key_prefix}_messages" not in st.session_state:
        st.session_state[f"{key_prefix}_messages"] = []
    if f"{key_prefix}_agent" not in st.session_state:
        try:
            # Use direct loading instead of subprocess for now to avoid Windows issues
            from agent_factory.utils import load_agent_from_code
            agent = load_agent_from_code(agent_code)
            st.session_state[f"{key_prefix}_agent"] = agent
            st.session_state[f"{key_prefix}_runner"] = InMemoryRunner(agent=agent)
        except Exception as e:
            st.error(f"Failed to load agent: {e}")
            return

    # Display chat history
    for msg in st.session_state[f"{key_prefix}_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Say something to your agent..."):
        # Add user message
        st.session_state[f"{key_prefix}_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            runner = st.session_state[f"{key_prefix}_runner"]
            with st.spinner("Agent is thinking..."):
                try:
                    # Run the agent async
                    async def _run():
                        events = await runner.run_debug(prompt)
                        for event in reversed(events):
                            if hasattr(event, 'content') and event.content and event.content.parts:
                                for part in event.content.parts:
                                    if part.text:
                                        return part.text
                        return "No response from agent."
                    
                    response_text = asyncio.run(_run())
                    
                    st.markdown(response_text)
                    st.session_state[f"{key_prefix}_messages"].append({"role": "assistant", "content": response_text})
                    
                except Exception as e:
                    st.error(f"Error during chat: {e}")

st.set_page_config(
    page_title="AgentFactory - Autonomous Agentic Workflow Creation",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
def load_css():
    css_file = os.path.join(os.getcwd(), "style.css")
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Display Logo and Title
col1, col2 = st.columns([1, 5])
with col1:
    logo_path = os.path.join(os.getcwd(), "assets", "logo.jpg")
    if os.path.exists(logo_path):
        st.image(logo_path, width=300)
    else:
        st.write("🏭")

with col2:
    st.title("AGENTFACTORY")
    st.caption("Autonomous Agentic Workflow Creation powered by Google Gemini & ADK")

# Configuration Section (Sidebar)
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Dynamic Model Selection
    if "available_models" not in st.session_state:
        with st.spinner("Fetching available models..."):
            st.session_state.available_models = get_available_models()
    
    models = st.session_state.available_models
    
    # Sort by Display Name (ASC) then Version (DESC)
    models.sort(key=lambda x: (x["display_name"], x.get("version", "")), reverse=False)
    models.sort(key=lambda x: x.get("version", ""), reverse=True)
    models.sort(key=lambda x: x["display_name"])
    
    # Format function for dropdown
    def format_model_option(model):
        thinking_tag = " 🧠" if model.get("thinking") else ""
        version = model.get("version", "")
        return f"{model['display_name']} - {version}{thinking_tag}"
    
    # Create a mapping for easy lookup
    model_map = {format_model_option(m): m for m in models}
    model_options = list(model_map.keys())
    
    # Default selection logic
    default_index = 0
    for i, opt in enumerate(model_options):
        if "Gemini 2.5 Flash" in opt:
            default_index = i
            break
            
    selected_option = st.selectbox("Select Model", model_options, index=default_index)
    selected_model_info = model_map[selected_option]
    selected_model_name = selected_model_info["name"]
    
    # Model Details
    with st.expander("Model Details", expanded=False):
        st.caption(selected_model_info.get('description'))
        st.metric("Input Limit", f"{selected_model_info.get('input_token_limit'):,}")
        st.metric("Output Limit", f"{selected_model_info.get('output_token_limit'):,}")
        
        st.markdown("**Capabilities**")
        methods = selected_model_info.get('supported_generation_methods', [])
        for method in methods:
            st.markdown(f"- `{method}`")
        if selected_model_info.get('thinking'):
            st.markdown("- `🧠 Thinking / Reasoning`")

    max_retries = st.slider("Max API Calls", 1, 50, 10)

model_name = selected_model_name # Alias for compatibility

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["🚀 YOLO Mode", "🐞 Debug Mode"])

# --- YOLO MODE ---
with tab1:
    st.header("YOLO Mode")
    st.markdown("Fire-and-forget agent creation.")
    
    yolo_goal = st.text_area("What agent do you want to build?", "Build a weather bot that can tell me the weather in London")
    # yolo_max_api_calls removed, using global max_retries
    
    if st.button("Build Agent (YOLO)"):
        with st.status("Building Agent...", expanded=True) as status:
            factory = AgentFactory(model_name=model_name)
            qa = QALead()
            
            st.write("🏗️ Architect designing blueprint...")
            code, blueprint = factory.create_agent(yolo_goal, max_retries=max_retries)
            
            if code and blueprint:
                st.write("✅ Agent built successfully!")
                st.code(code, language="python")
                
                st.write("🧪 QA Lead testing agent...")
                # Extract evaluation criteria
                criteria = blueprint.get("evaluation_criteria", [])
                
                # Run test
                result = qa.test_agent(code, "Test Query (Auto)", evaluation_criteria=criteria)
# --- DEBUG MODE ---
with tab2:
    st.header("Debug Mode")
    st.markdown("Interactive step-by-step execution.")
    
    debug_goal = st.text_area("What agent do you want to build?", "Build a weather bot that can tell me the weather in London", key="debug_goal")
    
    # State Management
    if "debug_state" not in st.session_state:
        st.session_state.debug_state = "IDLE"
        st.session_state.workspace_dir = None
        st.session_state.blueprint = None
        st.session_state.code = None
        st.session_state.feedback = None
        st.session_state.attempt = 0
        st.session_state.logs = []

    # Helper to add log
    def add_log(msg, level="INFO"):
        st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] [{level}] {msg}")

    # Start Button
    if st.session_state.debug_state == "IDLE":
        if st.button("Start Debug Session", type="primary"):
            factory = AgentFactory(model_name=model_name)
            workspace_dir, logger = factory.prepare_workspace(debug_goal)
            st.session_state.workspace_dir = workspace_dir
            st.session_state.debug_state = "ARCHITECT_READY"
            st.session_state.logs = [] # Clear logs
            
            # Check API Key
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                add_log(f"API Key found: {api_key[:5]}...{api_key[-5:]}")
            else:
                add_log("ERROR: GOOGLE_API_KEY not found in environment!")
                
            add_log(f"Initialized workspace: {workspace_dir}")
            st.rerun()

    # Display Logs (Collapsed by default to save space)
    if st.session_state.logs:
        with st.expander("Execution Logs", expanded=False):
            for log in st.session_state.logs:
                st.text(log)

    # State Machine Container
    if st.session_state.debug_state != "IDLE":
        with st.container(border=True):
            # Architect Phase
            if st.session_state.debug_state == "ARCHITECT_READY":
                st.info("Step 1: Architect")
                st.write("Ready to design the agent blueprint.")
                
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("▶️ Run Architect"):
                        factory = AgentFactory(model_name=model_name)
                        factory.prepare_workspace(debug_goal) 
                        
                        with st.spinner("Architect is thinking..."):
                            available_models = [m["name"] for m in st.session_state.available_models]
                            feedback = st.session_state.get("architect_feedback", None)
                            blueprint = factory.architect.design_workflow(debug_goal, available_models, feedback=feedback)
                            st.session_state.blueprint = blueprint
                            add_log(f"Architect - {model_name}: Generated blueprint.")
                            st.session_state.debug_state = "ARCHITECT_DONE"
                            st.rerun()
                with col2:
                    if st.button("⏹️ Abort", type="secondary"):
                        st.session_state.debug_state = "IDLE"
                        st.rerun()

            elif st.session_state.debug_state == "ARCHITECT_DONE":
                st.success("Architect Complete")
                
                # Display Flowchart
                if os.path.exists("workflow_blueprint.png"):
                    st.image("workflow_blueprint.png", caption="Workflow Blueprint")
                    
                with st.expander("View Blueprint JSON"):
                    st.json(st.session_state.blueprint)
                
                # Feedback UI
                st.markdown("### Refine Design")
                feedback_input = st.text_area("Feedback", key="architect_feedback_input")
                
                c1, c2, c3 = st.columns([1, 1, 4])
                with c1:
                    if st.button("🔄 Refine"):
                        if not feedback_input.strip():
                            st.warning("Please enter feedback before refining.")
                        else:
                            with st.spinner("Refining design..."):
                                factory = AgentFactory(model_name=model_name)
                                factory.prepare_workspace(debug_goal)
                                available_models = [m["name"] for m in st.session_state.available_models]
                                blueprint = factory.architect.design_workflow(
                                    debug_goal, 
                                    available_models, 
                                    feedback=feedback_input
                                )
                                st.session_state.blueprint = blueprint
                                add_log(f"Architect - {model_name}: Refined blueprint based on feedback.")
                                st.rerun()
                with c2:
                    if st.button("Continue ➡️", type="primary"):
                        if "agents" not in st.session_state.blueprint or not st.session_state.blueprint.get("agents"):
                            st.error("❌ Invalid blueprint - no agents defined!")
                        else:
                            st.session_state.debug_state = "ENGINEER_READY"
                            st.session_state.attempt = 1
                            st.rerun()
                with c3:
                    if st.button("⏹️ Abort", type="secondary"):
                        st.session_state.debug_state = "IDLE"
                        st.rerun()

            # Engineer Phase
            elif st.session_state.debug_state == "ENGINEER_READY":
                st.info(f"Step 2: Engineer (Attempt {st.session_state.attempt})")
                st.write("Ready to generate code.")
                if st.session_state.feedback:
                    st.warning(f"Addressing Feedback: {st.session_state.feedback}")
                    
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("▶️ Run Engineer"):
                        factory = AgentFactory(model_name=model_name)
                        factory.prepare_workspace(debug_goal)
                        
                        with st.spinner("Engineer is coding..."):
                            agents = st.session_state.blueprint.get("agents", [])
                            if not agents:
                                st.error("No agents found in blueprint!")
                                st.stop()
                                
                            target_agent = agents[0]
                            context = st.session_state.blueprint.get("end_to_end_context", "")
                            
                            code = factory.engineer.build_agent(target_agent, context)
                            
                            st.session_state.code = code
                            add_log(f"Engineer - {model_name}: Generated code for {target_agent.get('agent_name')} (Attempt {st.session_state.attempt})")
                            st.session_state.debug_state = "ENGINEER_DONE"
                            st.rerun()
                with col2:
                    if st.button("⏹️ Abort", type="secondary"):
                        st.session_state.debug_state = "IDLE"
                        st.rerun()

            elif st.session_state.debug_state == "ENGINEER_DONE":
                st.success("Engineer Complete")
                with st.expander("View Generated Code"):
                    st.code(st.session_state.code, language="python")
                
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Continue to Auditor ➡️", type="primary"):
                        st.session_state.debug_state = "AUDITOR_READY"
                        st.rerun()
                with col2:
                    if st.button("⏹️ Abort", type="secondary"):
                        st.session_state.debug_state = "IDLE"
                        st.rerun()

            # Auditor Phase
            elif st.session_state.debug_state == "AUDITOR_READY":
                st.info(f"Step 3: Auditor (Attempt {st.session_state.attempt})")
                st.write("Ready to review code.")
                
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("▶️ Run Auditor"):
                        factory = AgentFactory(model_name=model_name)
                        factory.prepare_workspace(debug_goal)
                        
                        with st.spinner("Auditor is reviewing..."):
                            agents = st.session_state.blueprint.get("agents", [])
                            target_agent = agents[0]
                            
                            result = factory.auditor.review_agent(st.session_state.code, target_agent)
                            add_log(f"Auditor - {model_name}: Review complete: {result}")
                            
                            if result["status"] == "PASS":
                                st.session_state.debug_state = "SUCCESS"
                                factory.save_agent(st.session_state.code, st.session_state.workspace_dir)
                            else:
                                st.session_state.feedback = result.get("feedback") or result.get("reasoning")
                                if st.session_state.attempt < max_retries:
                                    st.session_state.debug_state = "RETRY_NEEDED"
                                else:
                                    st.session_state.debug_state = "FAILED"
                            st.rerun()
                with col2:
                    if st.button("⏹️ Abort", type="secondary"):
                        st.session_state.debug_state = "IDLE"
                        st.rerun()

            elif st.session_state.debug_state == "RETRY_NEEDED":
                st.warning("Auditor Rejected Code")
                st.json(st.session_state.feedback)
                
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("🔄 Retry (Back to Engineer)"):
                        st.session_state.attempt += 1
                        st.session_state.debug_state = "ENGINEER_READY"
                        st.rerun()
                with col2:
                    if st.button("⏹️ Abort", type="secondary"):
                        st.session_state.debug_state = "IDLE"
                        st.rerun()

            elif st.session_state.debug_state == "SUCCESS":
                st.success("🎉 Agent Created Successfully!")
                st.write(f"Saved to: {st.session_state.workspace_dir}")
                
                render_chat_interface(st.session_state.code, "debug", st.session_state.workspace_dir)
                
                if st.button("Start Over", type="secondary"):
                    st.session_state.debug_state = "IDLE"
                    st.rerun()

            elif st.session_state.debug_state == "FAILED":
                st.error("❌ Agent Creation Failed (Max Retries Reached)")
                if st.button("Start Over", type="secondary"):
                    st.session_state.debug_state = "IDLE"
                    st.rerun()
