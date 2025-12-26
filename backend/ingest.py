import os
import shutil
import tempfile
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from pydub import AudioSegment
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from PIL import Image

# Initialize Gemini
# Assuming GOOGLE_API_KEY is in env, but for safety in this script we rely on env var.
if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def process_pdf(file_path, file_name):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    docs = []
    for i, page in enumerate(pages):
        docs.append(Document(
            page_content=page.page_content,
            metadata={
                "source": file_name,
                "type": "pdf",
                "page": i + 1,
                "citation_ref": f"{file_name} Page {i+1}",
                "media_url": f"/static/{file_name}"
            }
        ))
    return docs

def process_audio(file_path, file_name):
    """
    Process Audio using Gemini 1.5 Flash.
    Gemini can handle audio files directly via the File API.
    """
    # 1. Upload file to Gemini
    print(f"Uploading audio {file_name} to Gemini...")
    myfile = genai.upload_file(file_path)

    # 2. Wait for processing
    while myfile.state.name == "PROCESSING":
        time.sleep(1)
        myfile = genai.get_file(myfile.name)

    if myfile.state.name == "FAILED":
        raise ValueError("Gemini failed to process audio file")

    # 3. Prompt Gemini to transcribe and segment
    # We ask for a structured output to create chunks
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = """
    Listen to this audio carefully.
    Transcribe the content.
    Break the transcription into logical segments (approx 30-60 seconds or by topic).
    For each segment, provide:
    - Start timestamp (MM:SS)
    - End timestamp (MM:SS)
    - Verbatim text

    Format the output strictly as:
    [START: 00:00] [END: 00:30]
    Text content here...
    """

    response = model.generate_content([myfile, prompt])
    text_response = response.text

    # 4. Parse the response into Documents
    docs = []
    # Simple parsing logic (robustness would need regex)
    segments = text_response.split("[START:")

    for segment in segments:
        if not segment.strip(): continue

        try:
            # Re-add tag for parsing
            full_seg = "[START:" + segment

            start_tag_end = full_seg.find("]")
            start_time = full_seg[8:start_tag_end].strip() # 00:00

            end_tag_start = full_seg.find("[END:")
            end_tag_end = full_seg.find("]", end_tag_start)
            end_time = full_seg[end_tag_start+5 : end_tag_end].strip() # 00:30

            content = full_seg[end_tag_end+1:].strip()

            if content:
                docs.append(Document(
                    page_content=content,
                    metadata={
                        "source": file_name,
                        "type": "audio",
                        "timestamp": start_time,
                        "citation_ref": f"{file_name} at {start_time}",
                        "media_url": f"/static/{file_name}"
                    }
                ))
        except Exception as e:
            print(f"Error parsing segment: {e}")
            # Fallback: just add the whole text if parsing fails
            pass

    if not docs:
        # If parsing failed completely, add whole text
        docs.append(Document(
            page_content=text_response,
            metadata={
                "source": file_name,
                "type": "audio",
                "citation_ref": f"{file_name} (Full Audio)",
                "media_url": f"/static/{file_name}"
            }
        ))

    # Clean up file from Gemini cloud storage
    # genai.delete_file(myfile.name) # Optional: keep it or delete it. Good practice to delete.

    return docs

def process_image(file_path, file_name):
    # Use Gemini 1.5 Flash/Pro for Vision
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

    message = HumanMessage(
        content=[
            {"type": "text", "text": "Analyze this image in detail. If it's a chart or diagram, extract all data points and trends. If it's a document, read the text. Provide a comprehensive description."},
            {"type": "image_url", "image_url": file_path} # langchain-google-genai supports local paths?
            # Actually, ChatGoogleGenerativeAI expects base64 or public URL usually, or we use genai directly.
            # Let's use genai directly for simpler file handling similar to audio, or base64.
        ]
    )

    # Alternative: Use standard genai model for vision
    model = genai.GenerativeModel("gemini-1.5-flash")
    sample_file = genai.upload_file(file_path, mime_type="image/jpeg") # Auto-detect mime?

    response = model.generate_content(["Describe this image in detail, extracting all text and data.", sample_file])
    description = response.text

    return [Document(
        page_content=description,
        metadata={
            "source": file_name,
            "type": "image",
            "citation_ref": f"{file_name} (Image Analysis)",
            "media_url": f"/static/{file_name}"
        }
    )]

def process_file_from_path(file_path, file_name):
    """
    Process a file that is already saved on disk.
    """
    suffix = os.path.splitext(file_name)[1].lower()

    if suffix == ".pdf":
        return process_pdf(file_path, file_name)
    elif suffix in [".mp3", ".wav", ".m4a", ".mp4"]:
        return process_audio(file_path, file_name)
    elif suffix in [".jpg", ".jpeg", ".png", ".webp"]:
        return process_image(file_path, file_name)
    else:
        return []
