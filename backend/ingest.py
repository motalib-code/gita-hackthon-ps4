import os
import shutil
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from openai import OpenAI
import traceback
import cv2  # For video frame extraction
# Update for moviepy 2.0+
from moviepy import VideoFileClip

def process_pdf(file_path, file_name):
    try:
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
    except Exception as e:
        print(f"Error processing PDF {file_name}: {e}")
        return []

def process_audio(file_path, file_name):
    try:
        # Using OpenAI Whisper API for best results
        if not os.getenv("OPENAI_API_KEY"):
             raise ValueError("OPENAI_API_KEY not set for Audio Processing")

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
            start_time = segment.start
            end_time = segment.end
            text = segment.text

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
    except Exception as e:
        print(f"Error processing Audio {file_name}: {e}")
        return []

def process_image(file_path, file_name):
    try:
        if not os.getenv("OPENAI_API_KEY"):
             raise ValueError("OPENAI_API_KEY not set for Image Processing")

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
    except Exception as e:
        print(f"Error processing Image {file_name}: {e}")
        return []

def process_video(file_path, file_name):
    """
    Process Video:
    1. Extract Audio -> Transcribe (Whisper)
    2. Extract Key Frames (e.g., every 10s) -> Analyze (GPT-4o)
    """
    docs = []

    # 1. Audio Processing
    try:
        print(f"Extracting audio from {file_name}...")
        clip = VideoFileClip(file_path)

        # Temp audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name

        # MoviePy 2.0+ audio write
        # .audio is an AudioClip
        if clip.audio:
            clip.audio.write_audiofile(temp_audio_path, verbose=False, logger=None)

            # Transcribe
            audio_docs = process_audio(temp_audio_path, file_name)
            # Update metadata to reflect it's from video
            for doc in audio_docs:
                doc.metadata["type"] = "video_audio"
                doc.metadata["citation_ref"] = f"{file_name} (Audio) at {doc.metadata.get('timestamp')}"

            docs.extend(audio_docs)
        else:
            print("No audio track found in video.")

        os.remove(temp_audio_path)
        clip.close()

    except Exception as e:
        print(f"Error extracting/processing audio from video {file_name}: {e}")
        # traceback.print_exc()

    # 2. Visual Processing (Sample frames)
    try:
        print(f"Extracting frames from {file_name}...")
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
             print(f"Could not open video {file_path}")
             return docs

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 24 # Fallback

        frame_interval = int(fps * 10) # Every 10 seconds
        if frame_interval == 0: frame_interval = 1

        frame_count = 0
        success = True

        while success:
            success, frame = cap.read()
            if not success:
                break

            if frame_count % frame_interval == 0:
                # Save frame to temp
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_frame:
                    cv2.imwrite(temp_frame.name, frame)
                    temp_frame_path = temp_frame.name

                # Process as image
                image_docs = process_image(temp_frame_path, file_name)

                # Update metadata
                timestamp_sec = frame_count / fps
                minutes = int(timestamp_sec // 60)
                seconds = int(timestamp_sec % 60)
                timestamp_str = f"{minutes:02d}:{seconds:02d}"

                for doc in image_docs:
                    doc.metadata["type"] = "video_frame"
                    doc.metadata["timestamp"] = timestamp_str
                    doc.metadata["citation_ref"] = f"{file_name} (Visual) at {timestamp_str}"

                docs.extend(image_docs)
                os.remove(temp_frame_path)

            frame_count += 1

        cap.release()

    except Exception as e:
        print(f"Error processing video frames for {file_name}: {e}")

    return docs

def process_file_from_path(file_path, file_name):
    """
    Process a file that is already saved on disk.
    """
    try:
        suffix = os.path.splitext(file_name)[1].lower()

        if suffix == ".pdf":
            return process_pdf(file_path, file_name)
        elif suffix in [".mp3", ".wav", ".m4a", ".mpga", ".webm"]: # Pure Audio
            return process_audio(file_path, file_name)
        elif suffix in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            return process_image(file_path, file_name)
        elif suffix in [".mp4", ".mpeg", ".mov", ".avi"]: # Video
            return process_video(file_path, file_name)
        else:
            # Fallback for text files
            if suffix in [".txt", ".md"]:
                 with open(file_path, "r", encoding="utf-8") as f:
                     content = f.read()
                 return [Document(page_content=content, metadata={"source": file_name, "citation_ref": file_name})]
            return []
    except Exception as e:
        print(f"Error in main processing loop for {file_name}: {e}")
        return []

def ingest_file(file, file_name):
    """
    Deprecated: Use process_file_from_path instead.
    """
    suffix = os.path.splitext(file_name)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        return process_file_from_path(tmp_path, file_name)
    finally:
        os.remove(tmp_path)
