"use client";

import { FormEvent, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

type Message = { role: "user" | "assistant"; content: string };
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [mode, setMode] = useState<"chat" | "coding">("chat");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [teachOpen, setTeachOpen] = useState(false);
  const [knowledge, setKnowledge] = useState({ title: "", content: "", category: "general" });

  useEffect(() => { fetch(`${API}/api/session`, { method: "POST", credentials: "include" }).catch(() => setNotice("The API is unavailable. Start the FastAPI server to begin.")); }, []);

  async function send(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput(""); setNotice(""); setMessages((current) => [...current, { role: "user", content: text }]); setBusy(true);
    try {
      const response = await fetch(`${API}/api/chat`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text, mode }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Decan could not answer right now.");
      setMessages((current) => [...current, { role: "assistant", content: payload.data.content }]);
    } catch (error) { setNotice(error instanceof Error ? error.message : "Decan could not answer right now."); }
    finally { setBusy(false); }
  }

  async function teach(event: FormEvent) {
    event.preventDefault(); setBusy(true); setNotice("");
    try {
      const response = await fetch(`${API}/api/knowledge`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(knowledge) });
      const payload = await response.json(); if (!response.ok) throw new Error(payload.detail || "Knowledge could not be added.");
      setKnowledge({ title: "", content: "", category: "general" }); setTeachOpen(false); setNotice("Knowledge added to your Decan knowledge base.");
    } catch (error) { setNotice(error instanceof Error ? error.message : "Knowledge could not be added."); } finally { setBusy(false); }
  }

  return <main className="shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark">D</span><span>Decan <strong>AI</strong></span></div><div className="status"><span /> Online · anonymous session</div><button className="new-chat" onClick={() => setMessages([])}>＋ New chat</button><nav><button className="nav-active">◌ Conversations</button><button onClick={() => setTeachOpen(true)}>＋ Teach Decan</button><button onClick={() => setMode("coding")}>⌘ Decan Coding</button><button onClick={() => setNotice("Knowledge dashboard is available through the API and migration; upload controls are next in the product roadmap.")}>▦ Decan Knowledge</button></nav><div className="sidebar-foot"><span>Decan Techs</span><small>Learn. Build. Ask. Create.</small></div></aside>
    <section className="workspace"><header><div><p className="eyebrow">PERSONAL AI WORKSPACE</p><h1>{mode === "coding" ? "Decan Coding" : "Welcome to Decan AI"}</h1></div><button className="ghost" onClick={() => setTeachOpen(true)}>Teach Decan <span>↗</span></button></header>
      <div className="chat-scroll">{messages.length === 0 ? <div className="empty"><div className="empty-mark">✦</div><h2>Ask with context.</h2><p>Chat, write code, upload knowledge, and build a better answer space around what matters to you.</p><div className="prompts"><button onClick={() => setInput("Explain a complex idea clearly")}>Explain an idea <span>→</span></button><button onClick={() => setInput("Help me debug this code")}>Debug some code <span>→</span></button><button onClick={() => setTeachOpen(true)}>Add knowledge <span>→</span></button></div></div> : messages.map((message, index) => <article className={`message ${message.role}`} key={`${message.role}-${index}`}><div className="avatar">{message.role === "assistant" ? "D" : "You"}</div><div className="message-body"><span className="message-label">{message.role === "assistant" ? "DECAN AI" : "YOU"}</span>{message.role === "assistant" ? <ReactMarkdown>{message.content}</ReactMarkdown> : <p>{message.content}</p>}</div></article>)}{busy && <div className="thinking"><span /> Decan is thinking</div>}</div>
      {notice && <div className="notice">{notice}</div>}
      <form className="composer" onSubmit={send}><button type="button" className="attach" aria-label="Attachments">＋</button><input value={input} onChange={(event) => setInput(event.target.value)} placeholder={mode === "coding" ? "Describe the code you want to build..." : "Ask Decan AI anything..."} /><button className="send" disabled={busy || !input.trim()} aria-label="Send message">↑</button></form><div className="composer-meta"><span>Decan can make mistakes. Check important information.</span><span>Mode: <button type="button" onClick={() => setMode(mode === "chat" ? "coding" : "chat")}>{mode === "chat" ? "Chat" : "Coding"} ↕</button></span></div>
    </section>
    {teachOpen && <div className="modal-backdrop" onClick={() => setTeachOpen(false)}><form className="modal" onSubmit={teach} onClick={(event) => event.stopPropagation()}><button type="button" className="close" onClick={() => setTeachOpen(false)}>×</button><p className="eyebrow">DECAN KNOWLEDGE</p><h2>Teach Decan</h2><p className="modal-copy">Add information Decan can retrieve in future answers. This is knowledge storage, not model retraining.</p><label>Title<input required value={knowledge.title} onChange={(event) => setKnowledge({ ...knowledge, title: event.target.value })} placeholder="e.g. Our product principles" /></label><label>Category<input value={knowledge.category} onChange={(event) => setKnowledge({ ...knowledge, category: event.target.value })} /></label><label>Information<textarea required value={knowledge.content} onChange={(event) => setKnowledge({ ...knowledge, content: event.target.value })} placeholder="Write the useful context here..." /></label><button className="primary" disabled={busy}>{busy ? "Adding..." : "Add knowledge"}</button></form></div>}
  </main>;
}
