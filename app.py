import streamlit as st
import tempfile
import time
from backend.graph import app_graph
from backend.vector_store import initialize_milvus
from utils.document_loaders import process_file_ingestion

# Initialize DB connection for Ingestion
milvus_client, collection_name = initialize_milvus()

st.set_page_config(layout="wide", page_title="Chakravyuh AI")

# --- CSS for "Deep System Design" Look ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stSidebar { background-color: #161b22; }
    .status-box { padding: 10px; border-radius: 5px; border: 1px solid #30363d; margin-bottom: 10px; }
    .success { border-color: #238636; color: #238636; }
    .conflict { border-color: #da3633; color: #da3633; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Chakravyuh: Multimodal RAG System")
st.markdown("*Architecting the Future of Enterprise AI*")

# --- Sidebar: Multimodal Ingestion ---
with st.sidebar:
    st.header("📥 Ingestion Pipeline")

    # "Mannfile" Input
    uploaded_files = st.file_uploader(
        "Upload Documents (PDF, TXT, DOCX)",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True
    )

    # "Chubi" Input
    uploaded_images = st.file_uploader(
        "Upload Images (Diagrams, Schematics)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    # Audio Input
    uploaded_audio = st.file_uploader(
        "Upload Audio (Logs, Voice Notes)",
        type=["mp3", "wav", "mp4"],
        accept_multiple_files=True
    )

    if st.button("Process & Ingest Data"):
        if not (uploaded_files or uploaded_images or uploaded_audio):
            st.warning("Please upload at least one file.")
        else:
            with st.status("Ingesting Data into Hyper-Node Graph...", expanded=True) as status:
                count = 0
                
                # Text
                if uploaded_files:
                    st.write("📄 Processing Text Documents...")
                    for f in uploaded_files:
                        c = process_file_ingestion(f, "text", milvus_client, collection_name)
                        count += c

                # Images
                if uploaded_images:
                    st.write("🖼️ Processing Images (Visual Embedding)...")
                    for f in uploaded_images:
                        c = process_file_ingestion(f, "image", milvus_client, collection_name)
                        count += c

                # Audio
                if uploaded_audio:
                    st.write("🎙️ Processing Audio (Whisper Transcription)...")
                    for f in uploaded_audio:
                        c = process_file_ingestion(f, "audio", milvus_client, collection_name)
                        count += c
                
                status.update(label=f"Ingestion Complete! Added {count} nodes.", state="complete")

# --- Main Interface: Split Screen ---
col_chat, col_evidence = st.columns([1, 1])

if "messages" not in st.session_state:
    st.session_state.messages = []

with col_chat:
    st.subheader("💬 Query Interface")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input
    if prompt := st.chat_input("Ask about the engine, safety protocols, or conflicting data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # --- THE AGENTIC LOOP VISUALIZATION ---
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            evidence_placeholder = col_evidence.empty() # Update right panel

            # Step-by-step Execution Log
            with st.status("🧠 Chakravyuh Reasoning Engine", expanded=True) as status:
                
                # 1. Router
                st.write("Searching Intent Classifier...")
                inputs = {"query": prompt}
                # Run Graph (Streaming steps would be better, but simple invoke for now)
                
                # We emulate steps for visualization since we are running invoke() synchronously
                # ideally we stream the graph events.
                
                st.write("➡️ Routing Query...")
                time.sleep(0.5) # UI pacing
                
                # Run Backend
                final_state = app_graph.invoke(inputs)
                
                # Update Status based on State
                intent = final_state.get("intent", "TEXT")
                st.write(f"✅ Intent Detected: **{intent}**")
                
                docs = final_state.get("retrieved_docs", [])
                st.write(f"🔍 Retrieved {len(docs)} Evidence Candidates")
                
                conflict = final_state.get("conflict_detected", False)
                if conflict:
                    st.write("⚠️ **Conflict Detected in Evidence!** Triggering Judge Node.")
                else:
                    st.write("⚖️ Evidence Consistent.")

                st.write("✍️ Synthesizing Answer...")
                status.update(label="Response Generated", state="complete")

            # Show Answer
            answer = final_state.get("final_answer", "I could not generate an answer.")
            response_placeholder.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

            # --- EVIDENCE BOARD (Right Panel) ---
            with col_evidence:
                st.subheader("📂 Evidence Board")
                st.info("Live Retrieval State")
                
                if docs:
                    for i, doc in enumerate(docs):
                        entity = doc.get('entity', {})
                        modality = entity.get('modality', 'UNKNOWN')
                        content = entity.get('content_blob', '')
                        meta = entity.get('metadata', {})

                        with st.expander(f"Evidence {i+1} [{modality}]", expanded=True):
                            st.caption(f"Source: {meta.get('filename', 'Unknown')}")
                            st.markdown(f"**Content:** {content[:200]}...")
                            if modality == "IMAGE":
                                st.image("https://via.placeholder.com/150", caption="Visual Match (Placeholder)")
                else:
                    st.write("No evidence retrieved.")
