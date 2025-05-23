from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from transformers import pipeline

import uuid
import os
import shutil
import mimetypes
import logging

from datetime import datetime, timedelta

session_expiry = {}  # session_id -> last_active_time
session_metadata = {}  # session_id -> metadata (created_at, last_active)

def update_session_activity(session_id: str):
    now = datetime.utcnow()
    if session_id not in session_metadata:
        session_metadata[session_id] = {"created_at": now}
    session_metadata[session_id]["last_active"] = now
    session_expiry[session_id] = now

def cleanup_expired_sessions():
    now = datetime.utcnow()
    for sid, last_active in list(session_expiry.items()):
        if now - last_active > timedelta(minutes=30):
            chat_memory.pop(sid, None)
            session_attachments.pop(sid, None)
            session_expiry.pop(sid)


# === FastAPI app ===
app = FastAPI()

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === In-memory stores ===
chat_memory = {}
session_attachments = {}

# === File Upload Path ===
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === Setup logging ===
logging.basicConfig(
    filename="threat_log.txt",
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Load zero-shot classifier ===
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# === Threat detection keywords fallback ===
THREAT_KEYWORDS = ["kill", "attack", "bomb", "shoot", "harm", "destroy", "threat", "explode", "murder"]

# === Models ===
class ChatInput(BaseModel):
    message: str
    session_id: str

class Attachment(BaseModel):
    type: str  # "pdf" or "image"
    name: str
    url: str
    size: str
    description: Optional[str] = ""

class LLMResponse(BaseModel):
    status: str
    response_id: str
    timestamp: str
    content: dict
    attachments: List[Attachment]
    metadata: dict

# === Helpers ===
def get_file_type(file: UploadFile) -> str:
    mime_type, _ = mimetypes.guess_type(file.filename)
    if mime_type:
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type == "application/pdf":
            return "pdf"
    return "other"

def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024**2):.1f}MB"

def save_file(file: UploadFile, session_id: str) -> Attachment:
    file_ext = os.path.splitext(file.filename)[-1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size = os.path.getsize(file_path)
    public_url = f"http://localhost:8000/uploads/{unique_name}"

    attachment = Attachment(
        type=get_file_type(file),
        name=file.filename,
        url=public_url,
        size=format_file_size(size),
        description=f"Uploaded by user in session {session_id}"
    )

    session_attachments.setdefault(session_id, []).append(attachment)
    return attachment

def is_threatening(text: str) -> bool:
    candidate_labels = ["threat", "violence", "harmless", "neutral", "friendly"]
    result = classifier(text, candidate_labels)
    scores = dict(zip(result["labels"], result["scores"]))

    if scores.get("threat", 0) > 0.6 or scores.get("violence", 0) > 0.6:
        return True

    # Fallback to keyword match if NLP fails
    return any(word in text.lower() for word in THREAT_KEYWORDS)

def log_threat(session_id: str, message: str):
    logging.warning(f"Threat detected in session {session_id}: {message}")

# === Endpoint: Upload File ===
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    attachment = save_file(file, session_id)
    return {"status": "uploaded", "attachment": attachment}

# === Endpoint: Chat ===
@app.post("/chat", response_model=LLMResponse)
async def chat(input: ChatInput):
    user_message = input.message.strip()
    session_id = input.session_id.strip()

    # Check for threat
    if is_threatening(user_message):
        log_threat(session_id, user_message)
        return JSONResponse(
            status_code=400,
            content={"status": "threat_detected", "message": "Threatening input detected and logged."}
        )

    # Store user message
    chat_memory.setdefault(session_id, []).append({"role": "user", "message": user_message})

    # Limit context to last few messages for LLM (optional)
    recent_context = chat_memory[session_id][-3:] if session_id in chat_memory else []

    # Example: Prepare prompt from recent context
    context_prompt = "\n".join([f"{msg['role'].capitalize()}: {msg['message']}" for msg in recent_context])
    context_prompt += f"\nUser: {user_message}"

    # TODO: Replace below with actual LLM call using `context_prompt`
    bot_response = f"**Answer:**\n\nBased on your query:\n\n{user_message}\n\n**Attachments available below.**"


    # Store bot message
    chat_memory[session_id].append({"role": "bot", "message": bot_response})

    attachments = session_attachments.get(session_id, [])

    response = LLMResponse(
        status="success",
        response_id=f"res_{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow().isoformat(),
        content={"LLM Response": bot_response},
        attachments=attachments,
        metadata={
            "session_id": session_id,
            "source": "LLM-v2",
            "context_used": True
        }
    )
    return response

# === Serve uploaded files ===
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# === Debug Utilities ===
@app.get("/session-history/{session_id}")
def get_history(session_id: str):
    return {
        "messages": chat_memory.get(session_id, []),
        "attachments": session_attachments.get(session_id, [])
    }

@app.delete("/session-history/{session_id}")
def clear_history(session_id: str):
    chat_memory.pop(session_id, None)
    session_attachments.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}

import asyncio

@app.on_event("startup")
async def start_cleanup_task():
    async def cleanup_loop():
        while True:
            cleanup_expired_sessions()
            await asyncio.sleep(300)  # every 5 minutes
    asyncio.create_task(cleanup_loop())

    