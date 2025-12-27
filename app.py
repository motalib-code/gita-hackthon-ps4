import streamlit as st
import os
import shutil
import time
import pandas as pd

# Set page config FIRST
st.set_page_config(page_title="Chakravyuh-AI: Multimodal RAG", layout="wide", page_icon="☸️")

# Custom CSS for "Chakravyuh" styling
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stChatInput {
        position: fixed;
        bottom: 30px;
    }
    .stStatus {
        background-color: #e6f3ff;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #2196F3;
    }
    .evidence-card {
        background-color: white;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #4CAF50;
    }
    .conflict-card {
        background-color: #fff3f3;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #F44336;
    }
    .citation {
        font-size: 0.8em;
        color: #666;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions for imports (Lazy loading to allow API Key input first)
def get_backend_modules():
    try:
        from backend.rag import answer_query
        from backend.ingest import process_file_from_path
        from backend.vector_store import add_documents
        return answer_query, process_file_from_path, add_documents
    except Exception as e:
        return None, None, None

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "evidence_log" not in st.session_state:
    st.session_state.evidence_log = []
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False

# Sidebar: System Configuration & Ingestion
with st.sidebar:
    st.title("☸️ Chakravyuh Control")

    # 1. API Key Setup
    api_key = st.text_input("OpenAI API Key", type="password", help="Required for GPT-4o & Whisper")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.session_state.api_key_set = True
        st.success("System Online")

    st.divider()

    # 2. Multimodal Ingestion
    st.header("📥 Ingestion Pipeline")

    uploaded_file = st.file_uploader(
        "Upload Evidence (PDF, Audio, Image)",
        type=["pdf", "mp3", "wav", "jpg", "png", "jpeg", "txt"],
        help="Supports Multimodal Data"
    )

    if uploaded_file and st.session_state.api_key_set:
        if st.button("Ingest & Index"):
            with st.spinner("Running Ingestion Pipeline..."):
                # Save locally
                os.makedirs("backend/data_store", exist_ok=True)
                file_path = os.path.join("backend/data_store", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Import Backend
                answer_query, process_file_from_path, add_documents = get_backend_modules()
                
                # Process
                status_container = st.status("Processing Data Streams...", expanded=True)
                
                status_container.write("🔍 Identifying Modality...")
                time.sleep(0.5)
                
                try:
                    status_container.write("🧠 Extracting Semantics (Whisper/GPT-4o)...")
                    docs = process_file_from_path(file_path, uploaded_file.name)

                    status_container.write("🕸️ Generating Hyper-Node Embeddings...")
                    count = add_documents(docs)

                    status_container.update(label="Ingestion Complete!", state="complete", expanded=False)
                    st.success(f"Successfully indexed {count} chunks from {uploaded_file.name}")

                except Exception as e:
                    status_container.update(label="Ingestion Failed", state="error")
                    st.error(f"Error: {str(e)}")

    elif uploaded_file and not st.session_state.api_key_set:
        st.warning("Please enter OpenAI API Key first.")

# Main Layout: Split Screen
col1, col2 = st.columns([1, 1])

# Left Column: Chat Interface
with col1:
    st.subheader("💬 Investigation Console")

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about the evidence..."):
        if not st.session_state.api_key_set:
            st.error("System Offline: API Key Missing")
        else:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate Response
            with st.chat_message("assistant"):
                answer_query, _, _ = get_backend_modules()
                
                # Animated Thinking Process
                with st.status("Architecting Reasoning...", expanded=True) as status:
                    status.write("🧠 Intent Classification: Factual Inquiry")
                    time.sleep(0.5)

                    status.write("🔍 Retrieving Evidence (Vector Search)...")
                    # This logic is actually inside `answer_query` but we simulate the feedback here
                    # or better yet, `answer_query` runs fast.

                    status.write("⚖️ Detecting Conflicts & Judging...")
                    time.sleep(0.5)

                    try:
                        result = answer_query(prompt)
                        response_text = result["answer"]
                        sources = result["sources"]

                        status.update(label="Response Generated", state="complete", expanded=False)

                        st.markdown(response_text)

                        # Save to history
                        st.session_state.messages.append({"role": "assistant", "content": response_text})

                        # Update Evidence Log
                        st.session_state.evidence_log = sources

                    except Exception as e:
                        status.update(label="System Failure", state="error")
                        st.error(f"Error: {str(e)}")

# Right Column: Evidence Board (Explainability)
with col2:
    st.subheader("🕵️ Evidence Board (Explainable AI)")

    if st.session_state.evidence_log:
        st.markdown("### Retrieved Context")

        # Check for Conflicts (Simple heuristic based on "CONFLICT DETECTED" string in answer)
        last_msg = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
        if "CONFLICT DETECTED" in last_msg:
            st.markdown("""
            <div class="conflict-card">
                <b>⚠️ CONFLICT ALERT</b><br>
                The system detected contradictions in the retrieved evidence. See the breakdown below.
            </div>
            """, unsafe_allow_html=True)

        # Display Sources
        for i, source in enumerate(st.session_state.evidence_log):
            source_type = source.get("type", "text")
            ref = source.get("citation_ref", "Unknown")

            with st.container():
                st.markdown(f"""
                <div class="evidence-card">
                    <b>Source {i+1}: {ref}</b> <span style='float:right; font-size:0.8em; background:#ddd; padding:2px 5px; border-radius:4px;'>{source_type.upper()}</span>
                    <br>
                    <span class="citation">Metadata: {source}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # If image, show it
                if source_type == "image":
                    media_url = source.get("media_url", "")
                    # In a real app, serve this file. Here we just assume it's in backend/data_store
                    # Since we are local, we can try to find it.
                    filename = source.get("source", "")
                    if filename:
                        filepath = os.path.join("backend/data_store", filename)
                        if os.path.exists(filepath):
                            st.image(filepath, caption="Visual Evidence", width=300)
    else:
        st.info("Waiting for query... Evidence will appear here.")

        st.markdown("### Architecture Diagram")
        st.code("""
        [User Input]
             ⬇
        [Intent Router] ➡ [Visual Search (CLIP)]
             ⬇                  ⬇
        [Text Search]      [Image Captioning]
             ⬇                  ⬇
        [Conflict Judge (NLI Logic)]
             ⬇
        [Generator (GPT-4o)] ➡ [Frontend]
        """, language="text")
