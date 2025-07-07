from fastapi import FastAPI, UploadFile, File, Form
from agents.supervisor_agent import supervisor_graph  # Import your graph
from dotenv import load_dotenv 
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional


load_dotenv()

import shutil
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/supervisor")
async def run_supervisor(
    content: str = Form(...),                 
    file: Optional[UploadFile] = File(None),  # Make file optional
):
    file_path = None
    # FastAPI sends "" (empty string) if file field is left empty in docs UI
    if isinstance(file, UploadFile) and file.filename:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    # Build the message
    user_content = content
    if file_path:
        user_content += f" The file to process is at {file_path}."
    

    input_messages = [{"role": "user", "content": user_content}]
    final_state = supervisor_graph.invoke({"messages": input_messages})

    # Optionally remove the file after processing
    if file_path:
        os.remove(file_path)

    # Extract the final summary or relevant response
    

    return {"result": final_state}

# To run: uvicorn api_server:app --reload
