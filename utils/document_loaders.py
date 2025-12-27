import uuid
import tempfile
import os
import json
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from utils.embeddings import get_embeddings_instance
from utils.image_utils import extract_image_text
from utils.audio_utils import extract_audio_text

def generate_uuid():
    return str(uuid.uuid4())

def process_file_ingestion(uploaded_file, file_type, milvus_client, collection_name):
    """
    Main ingestion function that routes to specific processors based on file type.
    """
    embedder = get_embeddings_instance()
    nodes = []

    # Save to temp file immediately
    suffix = f".{uploaded_file.name.split('.')[-1]}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_file.read())
        temp_file_path = temp_file.name

    # Reset pointer for downstream readers if they read from file object
    uploaded_file.seek(0)

    try:
        if "pdf" in file_type or uploaded_file.name.endswith(".pdf"):
            nodes = process_pdf(temp_file_path, uploaded_file.name, embedder)
        elif "image" in file_type or uploaded_file.name.endswith(('.png', '.jpg', '.jpeg')):
            # Pass the file-like object reset to start
            uploaded_file.seek(0)
            nodes = process_image(uploaded_file, uploaded_file.name, embedder)
        elif "audio" in file_type or uploaded_file.name.endswith(('.mp3', '.wav', '.mp4')):
            uploaded_file.seek(0)
            nodes = process_audio(uploaded_file, uploaded_file.name, embedder)
        elif "text" in file_type or uploaded_file.name.endswith(".txt"):
            nodes = process_text(temp_file_path, uploaded_file.name, embedder)

        if nodes:
            res = milvus_client.insert(collection_name=collection_name, data=nodes)
            return len(nodes)
        return 0
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def process_pdf(filepath, filename, embedder):
    loader = PyPDFLoader(filepath)
    pages = loader.load()
    nodes = []
    parent_id = generate_uuid()

    for page in pages:
        text_content = page.page_content
        if not text_content.strip():
            continue

        node_id = generate_uuid()
        embedding_dense = embedder.get_text_embedding(text_content)
        embedding_clip = embedder.get_clip_embedding(None)

        nodes.append({
            "uuid": node_id,
            "modality": "TEXT",
            "content_blob": text_content,
            "embedding_dense": embedding_dense,
            "embedding_clip": embedding_clip,
            "parent_id": parent_id,
            "metadata": {"page": page.metadata.get("page", 0), "filename": filename}
        })
    return nodes

def process_image(uploaded_file, filename, embedder):
    # Use real extraction logic
    try:
        docs = extract_image_text(uploaded_file)
        caption = docs[0].page_content if docs else ""
    except Exception as e:
        print(f"OCR Failed: {e}")
        caption = "Image analysis failed."

    if not caption.strip():
        caption = "Image with no detectable text."

    node_id = generate_uuid()
    embedding_dense = embedder.get_text_embedding(caption)
    # Ideally we'd embed the raw image bytes for CLIP here
    embedding_clip = embedder.get_clip_embedding(None)

    return [{
        "uuid": node_id,
        "modality": "IMAGE",
        "content_blob": caption,
        "embedding_dense": embedding_dense,
        "embedding_clip": embedding_clip,
        "parent_id": node_id,
        "metadata": {"filename": filename, "type": "ocr_scan"}
    }]

def process_audio(uploaded_file, filename, embedder):
    # Use real extraction logic
    try:
        transcript = extract_audio_text(uploaded_file)
    except Exception as e:
        print(f"Transcription Failed: {e}")
        transcript = "Audio transcription failed."

    if not transcript.strip():
        transcript = "Audio with no speech."

    node_id = generate_uuid()
    embedding_dense = embedder.get_text_embedding(transcript)
    embedding_clip = embedder.get_clip_embedding(None)

    return [{
        "uuid": node_id,
        "modality": "AUDIO",
        "content_blob": transcript,
        "embedding_dense": embedding_dense,
        "embedding_clip": embedding_clip,
        "parent_id": node_id,
        "metadata": {"filename": filename, "timestamp": "00:00-end"}
    }]

def process_text(filepath, filename, embedder):
    loader = TextLoader(filepath)
    docs = loader.load()
    nodes = []
    parent_id = generate_uuid()

    for doc in docs:
        nodes.append({
            "uuid": generate_uuid(),
            "modality": "TEXT",
            "content_blob": doc.page_content,
            "embedding_dense": embedder.get_text_embedding(doc.page_content),
            "embedding_clip": embedder.get_clip_embedding(None),
            "parent_id": parent_id,
            "metadata": {"filename": filename}
        })
    return nodes
