# 📄 PDF Data Extractor & Search API (FastAPI + LangChain)

This FastAPI application allows you to:
- Upload a PDF to extract text, tables, and images
- Chunk and embed the text using a HuggingFace model
- Store the embeddings in a FAISS vector store
- Perform semantic search over the extracted content

---

## 🔧 Requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
Contents of requirements.txt:

makefile
fastapi
uvicorn
python-multipart
PyMuPDF==1.22.5
pdfplumber
langchain
langchain-community
faiss-cpu
sentence-transformers
torch
🚀 Running the Application
Start the FastAPI server using Uvicorn:

bash
uvicorn main:app --reload
Replace main with your Python filename if different (e.g., app.py → use uvicorn app:app --reload)

The --reload flag enables auto-reloading on code changes (useful for development)

❗ Error Faced During Model Loading
While attempting to load a model using a pickle file, I encountered the following error:

pgsql
ValueError: The de-serialization relies loading a pickle file. Pickle files can be modified to deliver a malicious payload that results in execution of arbitrary code on your machine. You will need to set allow_dangerous_deserialization to True to enable deserialization. If you do this, make sure that you trust the source of the data. For example, if you are loading a file that you created, and know that no one else has modified the file, then this is safe to do. Do not set this to True if you are loading a file from an untrusted source (e.g., some random site on the internet.).

🧾 Root Cause
This error is triggered because the file I’m trying to load uses Python's pickle module for serialization, which can execute arbitrary code during deserialization. For security reasons, PyTorch (or the respective library) blocks this by default unless explicitly allowed using:

python
allow_dangerous_deserialization=True