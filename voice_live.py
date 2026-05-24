import json
import subprocess
import time
from urllib.parse import quote_plus
import string
import collections

import numpy as np
import pyttsx3
import requests
import sounddevice as sd
import soundfile as sf
import whisper
import webrtcvad
from fastapi import FastAPI

app = FastAPI()


SAMPLE_RATE = 16000
CHANNELS = 1

FRAME_DURATION_MS = 30
VAD_AGGRESSIVENESS = 2
PADDING_MS = 600

MAX_RECORD_SECONDS = 8
MIN_RECORD_SECONDS = 0.3

AUDIO_FILE = "temp.wav"
OLLAMA_MODEL = "qwen2.5-coder:1.5b"

INPUT_DEVICE = None

WAKE_WORDS = [
    "hi max",
    "hey max",
    "hi mex",
    "hey mex",
    "hi marks",
    "hey marks",
    "good morning max",
    "good evening max",
]


class VoiceAssistant:
    def __init__(self, log_callback=None):
        self.active = False
        self.running = True
        self.log_callback = log_callback
        self.last_reply = ""

        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", 150)

        self.stt_model = whisper.load_model("base")

    # ---------------- LOG ----------------
    def log(self, message):
        print(message)
        if self.log_callback:
            self.log_callback(message)

    # ---------------- TTS ----------------
    def speak(self, message):
        self.last_reply = message
        log_message = f"Assistant: {message}"

        print(log_message)

        if self.log_callback:
            self.log_callback(log_message)

        try:
            self.tts.say(message)
            self.tts.runAndWait()
        except Exception as e:
            self.log(f"TTS error: {e}")

    # ---------------- RECORD WITH WEBRTC VAD ----------------
    def record_audio(self):
        self.log("Listening...")

        vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

        frame_size = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
        padding_frames = int(PADDING_MS / FRAME_DURATION_MS)

        ring_buffer = collections.deque(maxlen=padding_frames)
        voiced_frames = []

        triggered = False
        start_time = time.time()

        def is_speech(frame_float32):
            frame_float32 = np.clip(frame_float32, -1.0, 1.0)
            pcm16 = (frame_float32 * 32767).astype(np.int16).tobytes()
            return vad.is_speech(pcm16, SAMPLE_RATE)

        try:
            with sd.InputStream(
                device=INPUT_DEVICE,
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                blocksize=frame_size,
            ) as stream:
                while self.running:
                    frame, overflowed = stream.read(frame_size)

                    if overflowed:
                        self.log("Audio overflow")

                    frame = frame.reshape(-1)
                    speech = is_speech(frame)

                    if not triggered:
                        ring_buffer.append((frame.copy(), speech))

                        voiced_count = sum(1 for _, is_voiced in ring_buffer if is_voiced)

                        if voiced_count > 0.6 * ring_buffer.maxlen:
                            triggered = True
                            self.log("Speech detected")

                            for buffered_frame, _ in ring_buffer:
                                voiced_frames.append(buffered_frame)

                            ring_buffer.clear()

                    else:
                        voiced_frames.append(frame.copy())
                        ring_buffer.append((frame.copy(), speech))

                        unvoiced_count = sum(
                            1 for _, is_voiced in ring_buffer if not is_voiced
                        )

                        if unvoiced_count > 0.8 * ring_buffer.maxlen:
                            break

                    if time.time() - start_time > MAX_RECORD_SECONDS:
                        break

        except Exception as e:
            self.log(f"Recording error: {e}")
            return False

        if not voiced_frames:
            self.log("No speech detected")
            return False

        audio = np.concatenate(voiced_frames)

        duration = len(audio) / SAMPLE_RATE
        if duration < MIN_RECORD_SECONDS:
            self.log("Recording too short")
            return False

        sf.write(AUDIO_FILE, audio, SAMPLE_RATE)
        self.log(f"Recorded {duration:.2f}s")
        return True

    # ---------------- STT ----------------
    def transcribe_audio(self):
        try:
            result = self.stt_model.transcribe(
                AUDIO_FILE,
                language="en",
                fp16=False,
                temperature=0,
                condition_on_previous_text=False,
            )

            text = result["text"].lower().strip()
            self.log(f"Recognized: {text}")
            return text

        except Exception as e:
            self.log(f"Whisper error: {e}")
            return ""

    # ---------------- TEXT UTILS ----------------
    def normalize_text(self, text):
        cleaned = text.lower()
        cleaned = cleaned.translate(str.maketrans("", "", string.punctuation))
        return " ".join(cleaned.split())

    def has_wake_word(self, text):
        cleaned = self.normalize_text(text)
        return any(w in cleaned for w in WAKE_WORDS)

    def clean_text(self, text):
        cleaned = self.normalize_text(text)

        for w in WAKE_WORDS:
            cleaned = cleaned.replace(w, "")

        return " ".join(cleaned.split())

    # ---------------- FAST PARSER ----------------
    def quick_parse(self, text):
        text = self.clean_text(text)

        if any(w in text for w in ["youtube", "music", "video", "song", "play"]):
            query = text

            for w in [
                "youtube",
                "video",
                "song",
                "play",
                "search",
                "find",
                "for",
                "on",
                "open",
            ]:
                query = query.replace(w, "")

            query = " ".join(query.split()).strip()

            return {
                "intent": "youtube_search",
                "query": query,
            }

        if "google" in text:
            query = text

            for w in ["google", "search", "find", "for", "on", "open"]:
                query = query.replace(w, "")

            query = " ".join(query.split()).strip()

            return {
                "intent": "google_search",
                "query": query,
            }

        if "firefox" in text or "browser" in text:
            return {
                "intent": "open_app",
                "app": "firefox",
            }

        if "terminal" in text:
            return {
                "intent": "open_app",
                "app": "terminal",
            }

        if "spotify" in text:
            return {
                "intent": "open_app",
                "app": "spotify",
            }

        if (
            "files" in text
            or "file manager" in text
            or "folder" in text
            or "folders" in text
        ):
            return {
                "intent": "open_app",
                "app": "files",
            }

        if "stop" in text or "bye" in text:
            return {
                "intent": "stop",
            }

        return None

    # ---------------- OLLAMA ----------------
    def ask_ollama(self, text):
        text = self.clean_text(text)

        prompt = f"""
Return only valid JSON.
Your name is Max
Remember previous chat messages

Available intents:

1. youtube_search:
{{"intent": "youtube_search", "query": "search text"}}

2. google_search:
{{"intent": "google_search", "query": "search text"}}

3. open_app:
{{"intent": "open_app", "app": "firefox"}}
{{"intent": "open_app", "app": "terminal"}}
{{"intent": "open_app", "app": "spotify"}}
{{"intent": "open_app", "app": "files"}}

4. stop:
{{"intent": "stop"}}

5. chat:
{{"intent": "chat", "response": "natural short answer"}}

User text:
{text}
"""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=10,
            )

            data = response.json()
            raw = data.get("response", "{}")
            return json.loads(raw)

        except Exception as e:
            self.log(f"Ollama error: {e}")
            return {"intent": "unknown"}

    # ---------------- ACTIONS ----------------
    def open_youtube(self, query):
        if not query or not query.strip():
            url = "https://www.youtube.com"
            self.speak("Opening YouTube")
        else:
            url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            self.speak(f"Searching YouTube for {query}")

        self.log(f"Opening: {url}")
        subprocess.Popen(["xdg-open", url])

    def open_google(self, query):
        if not query or not query.strip():
            url = "https://www.google.com"
            self.speak("Opening Google")
        else:
            url = f"https://www.google.com/search?q={quote_plus(query)}"
            self.speak(f"Searching Google for {query}")

        self.log(f"Opening: {url}")
        subprocess.Popen(["xdg-open", url])

    def open_app(self, app):
        self.log(f"Opening app: {app}")

        if app == "firefox":
            subprocess.Popen(["firefox"])

        elif app == "terminal":
            subprocess.Popen(["xfce4-terminal"])

        elif app == "spotify":
            subprocess.Popen(["spotify"])

        elif app == "files":
            subprocess.Popen(["thunar"])

        else:
            self.speak("Unknown app")
            return

    # ---------------- COMMAND ----------------
    def handle_command(self, text):
        command = self.quick_parse(text)

        if command is None:
            command = self.ask_ollama(text)

        self.log(f"Command: {command}")

        intent = command.get("intent")

        if intent == "youtube_search":
            query = command.get("query", "")
            self.open_youtube(query)

        elif intent == "google_search":
            query = command.get("query", "")
            self.open_google(query)

        elif intent == "open_app":
            app = command.get("app", "")
            self.speak(f"Opening {app}")
            self.open_app(app)

        elif intent == "stop":
            self.speak("Bye")
            self.running = False
        elif intent == "chat":
            response = command.get("response", "I don't know what to say.")
            self.speak(response)
        else:
            self.speak("I don't understand")

        self.active = False
        return self.last_reply

    # ---------------- LOOP ----------------
    def run(self):
        self.running = True

        while self.running:
            if not self.record_audio():
                continue

            text = self.transcribe_audio()

            if not text:
                continue

            self.log(f"ACTIVE: {self.active}")

            if not self.active:
                if self.has_wake_word(text):
                    cleaned = self.clean_text(text)

                    if cleaned:
                        self.handle_command(cleaned)
                    else:
                        self.speak("Yes?")
                        self.active = True

                continue

            self.handle_command(text)

    def stop(self):
        self.running = False