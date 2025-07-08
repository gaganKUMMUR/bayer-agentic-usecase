from fastapi import FastAPI, UploadFile, File, Form
from agents.supervisor_agent import supervisor_graph  # Import your graph
from dotenv import load_dotenv 
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid
from agents.sentiment import get_response_from_review_agent
from agents.rating_store import store_rating, get_average_rating
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel

session_histories = {}
user_session = {"id": str(uuid.uuid4())}

# Request schema (no session_id input required now)
class ReviewRequest(BaseModel):
    user_input: str

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
    print(file.filename)
    # FastAPI sends "" (empty string) if file field is left empty in docs UI
    if file:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    # Build the message
    user_content = content
    if file_path:
        user_content += f" The file to process is at {file_path}."
    
    print(user_content)
    input_messages = [{"role": "user", "content": user_content}]
    final_state = supervisor_graph.invoke({"messages": input_messages})

    # Optionally remove the file after processing
    if file_path:
        os.remove(file_path)

    # Extract the final summary or relevant response
    

    return {"result": final_state}

@app.post("/review")
async def review_endpoint(payload: ReviewRequest):
    user_input = payload.user_input.strip()
    history = session_histories.get(user_session["id"], [])

    # Append user input
    history.append(HumanMessage(content=user_input))
    # --- Handle numeric rating if last message was a rating request ---
    if len(history) >= 2 and isinstance(history[-2], AIMessage):
        last_ai_msg = history[-2].content.strip()
        if "Please rate us from 1 to 5 stars" in last_ai_msg:
            try:
                rating = int(user_input)
                if 1 <= rating <= 5:
                    store_rating(rating)
                    avg = get_average_rating()
                    response_text = f"Thanks! You rated us {rating} ⭐. Our current average rating is {avg} ⭐."
                    history.append(AIMessage(content=response_text))
                    session_histories[user_session["id"]] = history
                    print(response_text)
                    return {
                        "session_id": user_session["id"],
                        "response": response_text,
                        "history": [msg.content for msg in history],
                    }
            except ValueError:
                pass  # Not a number, continue normally

    # --- Normal agent response flow ---
    response = get_response_from_review_agent(history)
    last_message = response["messages"][-1].content.strip()

    history.append(AIMessage(content=last_message))
    session_histories[user_session["id"]] = history

    return {
        "session_id": user_session["id"],
        "response": last_message,
        "history": [msg.content for msg in history],
    }
