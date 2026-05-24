# Hi Max AI Assistant

Local AI desktop/mobile assistant powered by:

- React
- FastAPI
- Ollama
- Whisper
- WebSocket audio streaming

## Features

- Voice input from phone
- Local AI chat with Ollama
- Text-to-speech on phone
- WebSocket real-time communication
- System controls (terminal, browser, spotify, files)
- Tailscale remote access

---

# Requirements

- Python 3.12+
- Node.js
- Ollama
- Tailscale (optional)

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Pull model:

```bash
ollama pull llama3.2
```

---

# Backend Setup

Create venv:

```bash
python -m venv ai-env
```

Activate:

```bash
source ai-env/bin/activate (if fish, activate.fish)
```

Install dependencies:

```bash
pip install fastapi uvicorn faster-whisper requests python-multipart websockets
```

Run backend:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

---

# Frontend Setup

Install dependencies:

```bash
npm install
```

Run frontend:

```bash
npm run dev -- --host 0.0.0.0
```

---

# Phone Access (Tailscale)

Install Tailscale on:

- computer
- phone

Get PC IP:

```bash
tailscale ip -4
```

Example:

```text
100.x.x.x
```

Open on phone:

```text
http://100.x.x.x:5173
```

---

# Architecture

```text
PC microphone (Smartphone microphone soon!)
↓
React frontend
↓
WebSocket audio
↓
FastAPI backend
↓
Whisper STT
↓
Ollama
↓
AI response
↓
React TTS
↓
Phone speaker
```

---

# Notes

- Backend runs locally on your PC
- Ollama runs fully offline
