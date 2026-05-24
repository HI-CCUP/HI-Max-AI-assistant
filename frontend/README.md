<<<<<<< HEAD
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is enabled on this template. See [this documentation](https://react.dev/learn/react-compiler) for more information.

Note: This will impact Vite dev & build performances.

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
=======
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
source ai-env/bin/activate
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
- Speech synthesis works on phone browser
>>>>>>> 4096514364bd1080e2bc9d57048592f71db2d5ca
