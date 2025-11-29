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

st.set_page_config(page_title="AgentFactory", layout="wide")

st.title("🏭 AgentFactory")
st.markdown("### Collaborative Multi-Agent System for AI Agent Creation")

# Sidebar for configuration
st.sidebar.header("Configuration")
model_name = st.sidebar.selectbox("Model", ["gemini-pro", "gemini-1.5-flash"])
max_retries = st.sidebar.slider("Max API Calls", 1, 50, 10)

# Tabs
tab1, tab2 = st.tabs(["🚀 YOLO Mode", "🐞 Debug Mode"])

# --- YOLO MODE ---
with tab1:
    st.header("YOLO Mode")
    st.markdown("Fire-and-forget agent creation.")
    
    yolo_goal = st.text_area("What agent do you want to build?", "Build a weather bot that can tell me the weather in London")
    yolo_max_api_calls = st.number_input("Max API Calls (Security)", 1, 20, 5, key="yolo_max")
    
    if st.button("Build Agent (YOLO)"):
        with st.status("Building Agent...", expanded=True) as status:
            factory = AgentFactory()
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
                
                if result["success"]:
                    st.success(f"Agent Execution Successful! Score: {result.get('score', 'N/A')}/5")
                    st.json(result)
                else:
                    st.error(f"Agent Execution Failed: {result.get('error')}")
                    
                status.update(label="Build Complete!", state="complete", expanded=False)
            else:
                st.error("Failed to build agent.")
                status.update(label="Build Failed", state="error")

# --- DEBUG MODE ---
with tab2:
    st.header("Debug Mode")
    st.markdown("Interactive step-by-step execution.")
    
    debug_goal = st.text_area("What agent do you want to build?", "Build a weather bot that can tell me the weather in London", key="debug_goal")
    debug_max_retries = st.slider("Max API Calls", 1, 50, 10, key="debug_retries")
    
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
            factory = AgentFactory()
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
            factory = AgentFactory()
            # Re-setup logging
            factory.prepare_workspace(debug_goal) 
            
            with st.spinner("Architect is thinking..."):
                blueprint = factory.architect.design_agent(debug_goal)
                st.session_state.blueprint = blueprint
                add_log("Architect generated blueprint.")
                st.session_state.debug_state = "ARCHITECT_DONE"
                st.rerun()
                
        if col2.button("⏹️ Abort"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "ARCHITECT_DONE":
        st.success("Architect Complete")
        st.json(st.session_state.blueprint)
        
        col1, col2 = st.columns(2)
        if col1.button("Example: Continue to Engineer"):
            st.session_state.debug_state = "ENGINEER_READY"
            st.session_state.attempt = 1
            st.rerun()
        if col2.button("⏹️ Abort"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "ENGINEER_READY":
        st.info(f"Step 2: Engineer (Attempt {st.session_state.attempt})")
        st.write("Ready to generate code.")
        if st.session_state.feedback:
            st.warning(f"Addressing Feedback: {st.session_state.feedback}")
            
        col1, col2 = st.columns(2)
        if col1.button("▶️ Run Engineer"):
            factory = AgentFactory()
            factory.prepare_workspace(debug_goal)
            
            with st.spinner("Engineer is coding..."):
                if st.session_state.feedback:
                    code = factory.engineer.build_agent(st.session_state.blueprint) # In real impl, pass feedback
                else:
                    code = factory.engineer.build_agent(st.session_state.blueprint)
                
                st.session_state.code = code
                add_log(f"Engineer generated code (Attempt {st.session_state.attempt})")
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
            factory = AgentFactory()
            factory.prepare_workspace(debug_goal)
            
            with st.spinner("Auditor is reviewing..."):
                result = factory.auditor.review_code(st.session_state.code, st.session_state.blueprint)
                add_log(f"Auditor review complete: {result}")
                
                if result is True:
                    st.session_state.debug_state = "SUCCESS"
                    # Save
                    factory.save_agent(st.session_state.code, st.session_state.workspace_dir)
                else:
                    st.session_state.feedback = result
                    if st.session_state.attempt < debug_max_retries:
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
        if st.button("Start Over"):
            st.session_state.debug_state = "IDLE"
            st.rerun()

    elif st.session_state.debug_state == "FAILED":
        st.error("❌ Agent Creation Failed (Max Retries Reached)")
        if st.button("Start Over"):
            st.session_state.debug_state = "IDLE"
            st.rerun()
