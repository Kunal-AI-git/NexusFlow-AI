## AI-Powered Chat and File Analysis API
This is a FastAPI backend application for secure and session-based user chat with threat detection, file uploads (PDFs and images), attachment tracking, and contextual AI-powered responses.

## Features
1. Session-based chat memory with history

2. Threat detection using a zero-shot classifier (facebook/bart-large-mnli)

3. File upload and storage with public URL generation (PDFs & Images)

4. Attachment metadata and chat response formatting

5. Contextual response simulation (customizable with any LLM)

6. Auto-cleanup of inactive sessions every 30 minutes

7. Session history inspection & deletion endpoints

8. CORS enabled for cross-origin access

## Project Structure
bash
.
├── main.py             # FastAPI backend code
├── uploads/            # Folder to store uploaded files
├── threat_log.txt      # Log file for flagged threats
└── README.md           # Project documentation

## Setup & Run
1. Clone the Repository
bash
git clone https://github.com/yourusername/ai-chat-analyzer.git
cd ai-chat-analyzer

2. Create a Virtual Environment
bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Dependencies
bash
pip install -r requirements.txt
If requirements.txt is not available, install manually:
bash
pip install fastapi uvicorn python-multipart transformers torch aiofiles

4. Run the App
bash
uvicorn main:app --reload
Visit http://localhost:8000/docs for the Swagger UI.

## API Endpoints
## POST /upload
Upload an image or PDF file.

Form Data:

file: UploadFile (image/pdf)

session_id: string

## POST /chat
Submit a chat message. Detects threats and uses recent chat context for response.

Body:

json

{
  "message": "Tell me about the uploaded file",
  "session_id": "session_1"
}

## GET /session-history/{session_id}
Returns chat and uploaded attachments history for the session.

## DELETE /session-history/{session_id}
Clears messages and attachments for a session.

## Threat Detection
Uses zero-shot classification (facebook/bart-large-mnli) to flag potentially violent or threatening input. Logs all detected threats in threat_log.txt.

## Uploaded File Access
Uploaded files are publicly accessible via:

bash
http://localhost:8000/uploads/<filename>

## License
MIT License