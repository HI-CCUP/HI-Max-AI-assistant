import asyncio
import threading
import subprocess
from pydantic import BaseModel

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from voice_live import VoiceAssistant

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://100.116.182.11:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

assistant = None
thread = None
clients = []
loop = None


# ---------------- WS ----------------
async def broadcast(message):
    disconnected = []

    for ws in clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        if ws in clients:
            clients.remove(ws)


def log_callback(message):
    if loop:
        asyncio.run_coroutine_threadsafe(broadcast(message), loop)


@app.on_event("startup")
async def startup():
    global loop
    loop = asyncio.get_running_loop()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            await asyncio.sleep(1)
    except Exception:
        pass
    finally:
        if websocket in clients:
            clients.remove(websocket)


# ---------------- AI COMMAND ----------------
class AICommand(BaseModel):
    text: str


@app.post("/ai-command")
def ai_command(cmd: AICommand):
    global assistant

    if assistant is None:
        assistant = VoiceAssistant(log_callback=log_callback)

    reply = assistant.handle_command(cmd.text)

    return {
        "status": "ok",
        "reply": reply,
    }


# ---------------- VOICE CONTROL ----------------
@app.post("/start")
def start():
    global assistant, thread

    if thread and thread.is_alive():
        return {"status": "already running"}

    assistant = VoiceAssistant(log_callback=log_callback)

    thread = threading.Thread(target=assistant.run, daemon=True)
    thread.start()

    return {"status": "started"}


@app.post("/stop")
def stop():
    global assistant

    if assistant:
        assistant.stop()

    return {"status": "stopped"}


# ---------------- SYSTEM ACTIONS ----------------
@app.post("/open-terminal")
def open_terminal():
    subprocess.Popen(["xfce4-terminal"])
    return {"status": "ok"}


@app.post("/open-browser")
def open_browser():
    subprocess.Popen(["firefox"])
    return {"status": "ok"}


@app.post("/open-spotify")
def open_spotify():
    subprocess.Popen(["spotify"])
    return {"status": "spotify opened"}


@app.post("/open-files")
def open_files():
    subprocess.Popen(["thunar"])
    return {"status": "files opened"}


@app.post("/volume-up")
def volume_up():
    subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%+"])
    return {"status": "volume up"}

@app.post("/volume-down")
def volume_down():
    subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%-"])
    return {"status": "volume down"}


@app.post("/shutdown")
def shutdown():
    subprocess.Popen(["shutdown", "now"])
    return {"status": "shutting down"}