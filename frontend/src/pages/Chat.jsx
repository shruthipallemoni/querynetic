import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { askQuestion, listDatabases, logout } from "../api/client";
import VerifiedQuery from "../components/VerifiedQuery";
import ConnectDatabaseModal from "../components/ConnectDatabaseModal";

const THREAD_ID = "web-session-1";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [databases, setDatabases] = useState([]);
  const [selectedDb, setSelectedDb] = useState("");
  const [showModal, setShowModal] = useState(false);
  const bottomRef = useRef(null);
  const navigate = useNavigate();

  async function refreshDatabases(preferredId) {
    const list = await listDatabases();
    setDatabases(list);
    if (preferredId) {
      setSelectedDb(preferredId);
    } else if (list.length > 0 && !selectedDb) {
      setSelectedDb(list[0].database_id);
    }
  }

  useEffect(() => {
    refreshDatabases();
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading || !selectedDb) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await askQuestion(question, selectedDb, THREAD_ID);
      setMessages((prev) => [
        ...prev,
        res.error
          ? { role: "error", text: res.error }
          : {
              role: "assistant",
              text: res.answer,
              queries: res.queries,
              validated: res.validated,
            },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "error",
          text: err.response?.data?.detail || "Request failed. Try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border px-6 py-3 flex items-center justify-between gap-4">
        <h1 className="font-display text-lg font-semibold text-text">
          Querynetic
        </h1>

        <div className="flex items-center gap-3">
          {databases.length > 0 && (
            <select
              value={selectedDb}
              onChange={(e) => setSelectedDb(e.target.value)}
              className="bg-panel border border-border rounded-md px-2 py-1.5 text-xs text-text"
            >
              {databases.map((d) => (
                <option key={d.database_id} value={d.database_id}>
                  {d.database_id}
                </option>
              ))}
            </select>
          )}
          <button
            onClick={() => setShowModal(true)}
            className="text-xs bg-panel border border-border text-text px-3 py-1.5 rounded-md hover:border-verified transition-colors"
          >
            + Connect database
          </button>
          <button
            onClick={handleLogout}
            className="text-xs text-muted hover:text-text transition-colors"
          >
            Log out
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl mx-auto space-y-4">
          {messages.length === 0 && (
            <p className="text-sm text-muted text-center mt-16">
              {selectedDb
                ? `Ask a question about "${selectedDb}" — e.g. "Compare total revenue between Europe and North America."`
                : 'No database connected yet — click "+ Connect database" to get started.'}
            </p>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              <div
                className={`max-w-[85%] rounded-lg px-4 py-3 text-sm ${
                  m.role === "user"
                    ? "bg-verified text-ink"
                    : m.role === "error"
                    ? "bg-danger/10 border border-danger/30 text-danger"
                    : "bg-panel border border-border text-text"
                }`}
              >
                <p className="whitespace-pre-wrap">{m.text}</p>
                {m.role === "assistant" && (
                  <VerifiedQuery queries={m.queries} validated={m.validated} />
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-panel border border-border rounded-lg px-4 py-3 text-sm text-muted">
                Thinking…
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </main>

      <form onSubmit={handleSend} className="border-t border-border px-6 py-4">
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={selectedDb ? "Ask about your data…" : "Connect a database first…"}
            disabled={!selectedDb}
            className="flex-1 bg-panel border border-border rounded-md px-3 py-2 text-sm text-text placeholder:text-muted/60 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !selectedDb}
            className="bg-verified text-ink text-sm font-medium px-4 py-2 rounded-md hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            Ask
          </button>
        </div>
      </form>

      {showModal && (
        <ConnectDatabaseModal
          onClose={() => setShowModal(false)}
          onConnected={(newId) => {
            setShowModal(false);
            refreshDatabases(newId);
          }}
        />
      )}
    </div>
  );
}