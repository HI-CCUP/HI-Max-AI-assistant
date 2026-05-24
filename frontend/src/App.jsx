import { useEffect, useMemo, useState } from "react";
import {
  Mic,
  Square,
  Search,
  PlayCircle,
  Globe,
  Terminal,
  Monitor,
  Activity,
  Trash2,
  Music,
  Folder,
  Cpu,
  Volume2,
  Volume1,
  Power,
  MessageCircle,
} from "lucide-react";
import "./App.css";

const API = "http://100.116.182.11:8000";
const WS = "ws://100.116.182.11:8000/ws";

function App() {
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [youtubeQuery, setYoutubeQuery] = useState("");
  const [googleQuery, setGoogleQuery] = useState("");
  const [aiCommand, setAiCommand] = useState("");
  const [assistantReply, setAssistantReply] = useState("Waiting for assistant...");

  const latestLog = useMemo(() => logs[logs.length - 1] || "No logs yet", [logs]);

  useEffect(() => {
  const ws = new WebSocket(WS);

  ws.onopen = () => {
    console.log("WebSocket connected");
  };

  ws.onmessage = (event) => {
  const message = String(event.data);

  setLogs((prev) => [...prev, message]);

if (message.includes("Assistant:")) {
  const reply = message.split("Assistant:").pop().trim();
  setAssistantReply(reply);
  speakOnPhone(reply);
}
};

  ws.onerror = () => {
    console.warn("WebSocket error");
  };

  ws.onclose = () => {
    console.warn("WebSocket disconnected");
  };

  return () => ws.close();
}, []);

  async function post(path, body) {
    try {
      const res = await fetch(`${API}${path}`, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!res.ok) {
        setLogs((prev) => [...prev, `Error: ${path}`]);
      }
    } catch {
      setLogs((prev) => [...prev, `Backend offline: ${path}`]);
    }
  }

  async function startAssistant() {
    await post("/start");
    setRunning(true);
  }

  async function stopAssistant() {
    await post("/stop");
    setRunning(false);
  }

  function speakOnPhone(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
}

  function searchYoutube() {
    if (!youtubeQuery.trim()) {
      window.open("https://www.youtube.com", "_blank");
      return;
    }

    const query = encodeURIComponent(youtubeQuery);
    window.open(`https://www.youtube.com/results?search_query=${query}`, "_blank");
  }

  function searchGoogle() {
    if (!googleQuery.trim()) {
      window.open("https://www.google.com", "_blank");
      return;
    }

    const query = encodeURIComponent(googleQuery);
    window.open(`https://www.google.com/search?q=${query}`, "_blank");
  }

  async function sendAI() {
  if (!aiCommand.trim()) return;

  const text = aiCommand;
  setAiCommand("");
  setAssistantReply("Thinking...");
  setLogs((prev) => [...prev, `You: ${text}`]);

  try {
    const res = await fetch(`${API}/ai-command`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });

    const data = await res.json();

    if (data.reply) {
  setAssistantReply(data.reply);
  setLogs((prev) => [...prev, `Max: ${data.reply}`]);
  speakOnPhone(data.reply);
} else {
      setAssistantReply("No reply from assistant.");
      setLogs((prev) => [...prev, "No reply from assistant."]);
    }
  } catch (err) {
    setAssistantReply("Backend offline.");
    setLogs((prev) => [...prev, "Backend offline."]);
  }
}

  function clearLogs() {
    setLogs([]);
  }

  return (
    <main className="app">
      <section className="shell">
        <header className="topbar">
          <div>
            <h1>Hi Max</h1>
          </div>

          <div className={running ? "pill active" : "pill"}>
            <span />
            {running ? "Listening" : "Stopped"}
          </div>
        </header>

        <section className="hero-card">
          <div>
            <h2>AI Assistant Control</h2>
            {/*<p>{latestLog}</p>*/}
          </div>

          <div className="hero-actions">
            <button className="primary" onClick={startAssistant}>
              <Mic size={18} />
              Start
            </button>

            <button className="danger" onClick={stopAssistant}>
              <Square size={18} />
              Stop
            </button>
          </div>
        </section>

        <section className="tiles">
          <article className="tile youtube">
            <div className="tile-title">
              <PlayCircle size={22} />
              <h3>YouTube</h3>
            </div>

            <p>Search videos manually or by voice command.</p>

            <div className="input-row">
              <input
                value={youtubeQuery}
                onChange={(e) => setYoutubeQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && searchYoutube()}
                placeholder="Search..."
              />

              <button onClick={searchYoutube}>
                <Search size={17} />
              </button>
            </div>
          </article>

          <article className="tile google">
            <div className="tile-title">
              <Globe size={22} />
              <h3>Google</h3>
            </div>

            <p>Quick web search.</p>

            <div className="input-row">
              <input
                value={googleQuery}
                onChange={(e) => setGoogleQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && searchGoogle()}
                placeholder="Search..."
              />

              <button onClick={searchGoogle}>
                <Search size={17} />
              </button>
            </div>
          </article>

          <article className="tile assistant-reply-tile">
            <div className="tile-title">
              <MessageCircle size={22} />
              <h3>Assistant Reply</h3>
            </div>

            <p className="assistant-reply">{assistantReply}</p>
          </article>

          <article className="tile">
            <div className="tile-title">
              <Terminal size={22} />
              <h3>Terminal</h3>
            </div>

            <button className="wide" onClick={() => post("/open-terminal")}>
              Open Terminal
            </button>
          </article>

          <article className="tile">
            <div className="tile-title">
              <Monitor size={22} />
              <h3>Browser</h3>
            </div>

            <button className="wide" onClick={() => post("/open-browser")}>
              Open Firefox
            </button>
          </article>

          <article className="tile">
            <div className="tile-title">
              <Music size={22} />
              <h3>Spotify</h3>
            </div>

            <button className="wide" onClick={() => post("/open-spotify")}>
              Open Spotify
            </button>
          </article>

          <article className="tile">
            <div className="tile-title">
              <Folder size={22} />
              <h3>Files</h3>
            </div>

            <button className="wide" onClick={() => post("/open-files")}>
              Open Files
            </button>
          </article>

          <article className="tile ai-tile">
            <div className="tile-title">
              <Cpu size={22} />
              <h3>AI Command</h3>
            </div>

            <div className="input-row">
              <input
                value={aiCommand}
                onChange={(e) => setAiCommand(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendAI()}
                placeholder="Type command..."
              />

              <button onClick={sendAI}>
                <Search size={17} />
              </button>
            </div>
          </article>

          <article className="tile system-tile">
            <div className="tile-title">
              <Volume2 size={22} />
              <h3>System</h3>
            </div>

            <div className="buttons-row">
              <button onClick={() => post("/volume-up")}>
                <Volume2 size={17} />
              </button>

              <button onClick={() => post("/volume-down")}>
                <Volume1 size={17} />
              </button>
            </div>

            <button className="danger wide" onClick={() => post("/shutdown")}>
              <Power size={17} />
              Shutdown
            </button>
          </article>

          <article className="tile status-tile">
            <div className="tile-title">
              <Activity size={22} />
              <h3>Status</h3>
            </div>

            <div className="stats">
              <div>
                <strong>{running ? "ON" : "OFF"}</strong>
                <span>Assistant</span>
              </div>

              <div>
                <strong>{logs.length}</strong>
                <span>Logs</span>
              </div>
            </div>
          </article>

          {/* <article className="tile logs-tile">
            <div className="logs-header">
              <div className="tile-title">
                <Activity size={22} />
                <h3>Logs</h3>
              </div>

              <button className="icon-button" onClick={clearLogs}>
                <Trash2 size={17} />
              </button>
            </div>

            <div className="logs">
              {logs.length === 0 ? (
                <p className="muted">No logs</p>
              ) : (
                logs.slice(-12).map((log, i) => <p key={i}>{log}</p>)
              )}
            </div>
          </article> */}
        </section>
      </section>
    </main>
  );
}

export default App;