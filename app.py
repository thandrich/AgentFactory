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

st.set_page_config(page_title="AgentFactory", layout="wide")

st.title("🏭 AgentFactory")
st.markdown("### Collaborative Multi-Agent System for AI Agent Creation")

# Configuration Section (Main Page for Width)
with st.expander("⚙️ Configuration", expanded=True):
    # Dynamic Model Selection
    if "available_models" not in st.session_state:
        with st.spinner("Fetching available models..."):
            st.session_state.available_models = get_available_models()
    
    models = st.session_state.available_models
    
    # Sort by Display Name (ASC) then Version (DESC)
    models.sort(key=lambda x: (x["display_name"], x.get("version", "")), reverse=False)
    # To get Version DESC, we can't easily use a single lambda with mixed sort orders for strings.
    # So let's sort by Version DESC first, then Display Name ASC (Python sort is stable)
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
    
    # Comprehensive Details Display
    st.markdown("---")
    st.markdown(f"### {selected_model_info['display_name']}")
    st.caption(selected_model_info.get('description'))
    
    # Row 1: Key Specs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Version", selected_model_info.get('version'))
    c2.metric("Type", selected_model_info.get('type'))
    c3.metric("Input Limit", f"{selected_model_info.get('input_token_limit'):,}")
    c4.metric("Output Limit", f"{selected_model_info.get('output_token_limit'):,}")
    
    # Row 2: Sampling Parameters & Capabilities
    st.markdown("**Model Parameters & Capabilities**")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("🎛️ **Sampling Defaults**")
        params = {
            "Temperature": selected_model_info.get('temperature'),
            "Max Temp": selected_model_info.get('max_temperature'),
            "Top P": selected_model_info.get('top_p'),
            "Top K": selected_model_info.get('top_k')
        }
        st.json({k: v for k, v in params.items() if v is not None})
        
    with c2:
        st.write("⚡ **Capabilities**")
        methods = selected_model_info.get('supported_generation_methods', [])
        for method in methods:
            st.markdown(f"- `{method}`")
        if selected_model_info.get('thinking'):
            st.markdown("- `🧠 Thinking / Reasoning`")

    max_retries = st.slider("Max API Calls", 1, 50, 10)

model_name = selected_model_name # Alias for compatibility

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
    # debug_max_retries removed, using global max_retries
    
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
        if st.button("Start Debug Session"):
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

    # Display Logs
    with st.expander("Execution Logs", expanded=True):
        for log in st.session_state.logs:
            st.text(log)

    # State Machine
    if st.session_state.debug_state == "ARCHITECT_READY":
        st.info("Step 1: Architect")
        st.write("Ready to design the agent blueprint.")
        
        col1, col2 = st.columns(2)
        if col1.button("▶️ Run Architect"):
            factory = AgentFactory(model_name=model_name)
            # Re-setup logging
            factory.prepare_workspace(debug_goal) 
            
            with st.spinner("Architect is thinking..."):
                # Use new design_workflow method
                available_models = [m["name"] for m in st.session_state.available_models]
                feedback = st.session_state.get("architect_feedback", None)
                blueprint = factory.architect.design_workflow(debug_goal, available_models, feedback=feedback)
                st.session_state.blueprint = blueprint
                add_log(f"Architect - {model_name}: Generated blueprint.")
                st.session_state.debug_state = "ARCHITECT_DONE"
                st.rerun()
                
        if col2.button("⏹️ Abort"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "ARCHITECT_DONE":
        st.success("Architect Complete")
        
        # Display Flowchart
        if os.path.exists("workflow_blueprint.png"):
            st.image("workflow_blueprint.png", caption="Workflow Blueprint")
            
        st.json(st.session_state.blueprint)
        
        # Feedback UI
        st.markdown("### Refine Design")
        feedback_input = st.text_area("Feedback", key="architect_feedback_input")
        
        col1, col2, col3 = st.columns(3)
        if col1.button("🔄 Refine Design"):
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
                    st.rerun()  # Stay in ARCHITECT_DONE state
            
        if col2.button("Continue to Engineer"):
            # Validate blueprint before proceeding
            if "agents" not in st.session_state.blueprint:
                st.error("❌ Invalid blueprint - no agents defined! Please refine the design.")
            elif not st.session_state.blueprint.get("agents"):
                st.error("❌ Blueprint has empty agents list! Please refine the design.")
            else:
                st.session_state.debug_state = "ENGINEER_READY"
                st.session_state.attempt = 1
                st.rerun()
        if col3.button("⏹️ Abort"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "ENGINEER_READY":
        st.info(f"Step 2: Engineer (Attempt {st.session_state.attempt})")
        st.write("Ready to generate code.")
        if st.session_state.feedback:
            st.warning(f"Addressing Feedback: {st.session_state.feedback}")
            
        col1, col2 = st.columns(2)
        if col1.button("▶️ Run Engineer"):
            factory = AgentFactory(model_name=model_name)
            factory.prepare_workspace(debug_goal)
            
            with st.spinner("Engineer is coding..."):
                # Pick the first agent for debug mode simplicity
                agents = st.session_state.blueprint.get("agents", [])
                if not agents:
                    st.error("No agents found in blueprint!")
                    st.stop()
                    
                target_agent = agents[0]
                context = st.session_state.blueprint.get("end_to_end_context", "")
                
                # Engineer now takes agent_def and context
                code = factory.engineer.build_agent(target_agent, context)
                
                st.session_state.code = code
                add_log(f"Engineer - {model_name}: Generated code for {target_agent.get('agent_name')} (Attempt {st.session_state.attempt})")
                st.session_state.debug_state = "ENGINEER_DONE"
                st.rerun()
                
        if col2.button("⏹️ Abort"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "ENGINEER_DONE":
        st.success("Engineer Complete")
        st.code(st.session_state.code, language="python")
        
        col1, col2 = st.columns(2)
        if col1.button("Continue to Auditor"):
            st.session_state.debug_state = "AUDITOR_READY"
            st.rerun()
        if col2.button("⏹️ Abort"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "AUDITOR_READY":
        st.info(f"Step 3: Auditor (Attempt {st.session_state.attempt})")
        st.write("Ready to review code.")
        
        col1, col2 = st.columns(2)
        if col1.button("▶️ Run Auditor"):
            factory = AgentFactory(model_name=model_name)
            factory.prepare_workspace(debug_goal)
            
            with st.spinner("Auditor is reviewing..."):
                agents = st.session_state.blueprint.get("agents", [])
                target_agent = agents[0]
                
                # Auditor now takes code and agent_def
                result = factory.auditor.review_agent(st.session_state.code, target_agent)
                add_log(f"Auditor - {model_name}: Review complete: {result}")
                
                if result["status"] == "PASS":
                    st.session_state.debug_state = "SUCCESS"
                    # Save
                    factory.save_agent(st.session_state.code, st.session_state.workspace_dir)
                else:
                    st.session_state.feedback = result.get("feedback") or result.get("reasoning")
                    if st.session_state.attempt < max_retries:
                        st.session_state.debug_state = "RETRY_NEEDED"
                    else:
                        st.session_state.debug_state = "FAILED"
                st.rerun()
                
        if col2.button("⏹️ Abort"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "RETRY_NEEDED":
        st.warning("Auditor Rejected Code")
        st.json(st.session_state.feedback)
        
        col1, col2 = st.columns(2)
        if col1.button("🔄 Retry (Back to Engineer)"):
            st.session_state.attempt += 1
            st.session_state.debug_state = "ENGINEER_READY"
            st.rerun()
        if col2.button("⏹️ Abort"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "SUCCESS":
        st.success("🎉 Agent Created Successfully!")
        st.write(f"Saved to: {st.session_state.workspace_dir}")
        
        render_chat_interface(st.session_state.code, "debug", st.session_state.workspace_dir)
        
        if st.button("Start Over"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "FAILED":
        st.error("❌ Agent Creation Failed (Max Retries Reached)")
        if st.button("Start Over"):
            st.session_state.debug_state = "IDLE"
            st.rerun()
