import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../api/client";

export default function Login() {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await register(email, password);
      }
      await login(email, password);
      navigate("/chat");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Something went wrong. Try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="font-display text-2xl font-semibold tracking-tight text-text">
            Querynetic
          </h1>
          <p className="mt-1 text-sm text-muted">
            Ask your database a question. Get a verified answer.
          </p>
        </div>

        <div className="bg-panel border border-border rounded-lg p-6">
          <div className="flex gap-1 mb-6 bg-panelLight rounded-md p-1">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`flex-1 text-sm py-1.5 rounded transition-colors ${
                mode === "login"
                  ? "bg-verified text-ink font-medium"
                  : "text-muted hover:text-text"
              }`}
            >
              Log in
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`flex-1 text-sm py-1.5 rounded transition-colors ${
                mode === "register"
                  ? "bg-verified text-ink font-medium"
                  : "text-muted hover:text-text"
              }`}
            >
              Sign up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-muted mb-1.5" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-ink border border-border rounded-md px-3 py-2 text-sm text-text placeholder:text-muted/60"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1.5" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-ink border border-border rounded-md px-3 py-2 text-sm text-text placeholder:text-muted/60"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="text-sm text-danger" role="alert">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-verified text-ink font-medium text-sm py-2 rounded-md hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? "Working…" : mode === "login" ? "Log in" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}