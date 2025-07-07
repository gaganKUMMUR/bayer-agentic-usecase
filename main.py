from fastapi import FastAPI, UploadFile, File, Form
from supervisor_agent import supervisor_graph  # Import your graph

import shutil
import os

app = FastAPI()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/supervisor")
async def run_supervisor(
    content: str = Form(...),                 # user's instruction (text command)
    file: UploadFile = File(None),            # optional file
):
    # Handle file if present (save it temporarily)
    file_path = None
    if file:
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
