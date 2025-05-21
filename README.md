# 🤖 NexusFlow AI Chat (Session-Based + Threat Filtering)
This is a secure, session-based chatbot API built using **FastAPI** and **HuggingFace Transformers**. It supports:
- Contextual chat history per session (in-memory only)
- Threat and prompt injection detection using:
  - 🤖 `facebook/bart-large-mnli` zero-shot classifier
  - 🧪 Regex fallback for known attack patterns
- Endpoint to view, clear, or end a session
- Beautified LLM response formatting

---

## 🚀 Features

- ✅ **Chat with session context** (no database required)
- 🔒 **Threat filtering** using zero-shot classification + keyword checks
- 💬 **One-session history memory**
- 🧼 **Manual clear or end session**
- 🎨 **Markdown-style bot response formatting**

---

## 🔧 Requirements

Install required dependencies:

```bash
pip install -r requirements.txt
🚦 Run the API
bash

uvicorn main:app --reload
📡 API Endpoints
Method	Endpoint	Description
GET	/	Health check
POST	/chat	Chat with LLM using session_id
GET	/history?session_id=xyz	Get current session history
POST	/clear-history	Clear chat history (preserve session)
POST	/end-session	Delete session data entirely

📥 Example Request
🧠 POST /chat
json

{
  "message": "How to build a chatbot?",
  "session_id": "abc123"
}
🛡 Threat Detection
If the input contains:

🚨 Harmful intents like "how to hack", "bypass login"

🤖 Prompt injection attempts

The system will block the request with:

json

{
  "status": "error",
  "message": "🚨 Input flagged as malicious and blocked.",
  "blocked": true
}
🧽 Clear or End Session
🔄 Clear History
bash

POST /clear-history
{
  "session_id": "abc123"
}
🗑 End Session
bash

POST /end-session
{
  "session_id": "abc123"
}
📦 Folder Structure
bash
.
├── main.py           # FastAPI app
├── requirements.txt  # Dependencies
├── README.md         # Project info