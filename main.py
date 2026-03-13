"""Layla AI Personal Assistant — FastAPI server for iOS Shortcut integration."""

import os
from contextlib import asynccontextmanager
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import process_message
from memory import bootstrap_contacts, detect_user_email, load_memory, save_memory
from session import SessionManager

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not set. Add it to .env file.")
genai.configure(api_key=api_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks: detect user email and bootstrap contacts."""
    print("[Startup] Detecting user email...")
    try:
        email = detect_user_email()
        print(f"[Startup] User email: {email}")
    except Exception as e:
        print(f"[Startup] Could not detect email: {e}")

    memory = load_memory()
    if not memory.get("contacts"):
        print("[Startup] Bootstrapping contacts from last 3 months...")
        try:
            result = bootstrap_contacts()
            print(f"[Startup] Found {result['contacts_found']} frequent contacts")
        except Exception as e:
            print(f"[Startup] Contact bootstrap failed: {e}")
    else:
        print(f"[Startup] {len(memory['contacts'])} contacts already in memory")

    yield  # Server runs


app = FastAPI(title="Layla AI Personal Assistant", lifespan=lifespan)
session_manager = SessionManager()


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    action: str = "continue"


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a voice command from the iOS Shortcut."""
    if not request.message.strip():
        return ChatResponse(reply="I didn't catch that. Could you say it again?")

    # Handle goodbye on the server side for clean shortcut exit
    words = request.message.lower().split()
    if "goodbye" in words or "bye" in words or "bye-bye" in words:
        print(f"\n[User: {request.user_id}] {request.message}")
        print("[Layla] Goodbye! (session ending)")
        # Save last session timestamp before clearing
        memory = load_memory()
        memory["last_session_timestamp"] = datetime.now().isoformat()
        save_memory(memory)
        session_manager._sessions.pop(request.user_id, None)
        return ChatResponse(reply="Goodbye! Talk to you later.", action="stop")

    try:
        history = session_manager.get_or_create(request.user_id)
        print(f"\n[User: {request.user_id}] {request.message}")

        reply = process_message(request.message, history)

        print(f"[Layla] {reply}")
        return ChatResponse(reply=reply)

    except Exception as e:
        print(f"[Error] {e}")
        raise HTTPException(
            status_code=500,
            detail="Sorry, something went wrong. Please try again.",
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "agent": "layla"}
