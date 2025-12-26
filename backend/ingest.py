import os
import shutil
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from pydub import AudioSegment
import speech_recognition as sr
from PIL import Image
import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Assuming OPENAI_API_KEY is in env
api_key = os.getenv("OPENAI_API_KEY")

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
    # Using OpenAI Whisper API for best results
    from openai import OpenAI
    client = OpenAI()

    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

    docs = []
    for segment in transcript.segments:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text']

        minutes = int(start_time // 60)
        seconds = int(start_time % 60)
        timestamp_str = f"{minutes:02d}:{seconds:02d}"

        docs.append(Document(
            page_content=text,
            metadata={
                "source": file_name,
                "type": "audio",
                "timestamp": timestamp_str,
                "start": start_time,
                "end": end_time,
                "citation_ref": f"{file_name} at {timestamp_str}",
                "media_url": f"/static/{file_name}"
            }
        ))
    return docs

def process_image(file_path, file_name):
    client = ChatOpenAI(model="gpt-4o", max_tokens=1000)

    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    message = HumanMessage(
        content=[
            {"type": "text", "text": "Analyze this image in detail. If it's a chart or diagram, extract all data points and trends. If it's a document, read the text. Provide a comprehensive description."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
        ]
    )

    response = client.invoke([message])
    description = response.content

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
    elif suffix in [".jpg", ".jpeg", ".png"]:
        return process_image(file_path, file_name)
    else:
        return []

def ingest_file(file, file_name):
    """
    Deprecated: Use process_file_from_path instead.
    Kept for backward compatibility if needed, but updated to use the temp approach safely.
    """
    suffix = os.path.splitext(file_name)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        return process_file_from_path(tmp_path, file_name)
    finally:
        os.remove(tmp_path)
