import { useState } from "react";
import { connectDatabase } from "../api/client";

export default function ConnectDatabaseModal({ onClose, onConnected }) {
  const [name, setName] = useState("");
  const [connectionString, setConnectionString] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await connectDatabase(name, connectionString);
      onConnected(res.database_id);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not connect. Check the connection string.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center px-4 z-50">
      <div className="bg-panel border border-border rounded-lg p-6 w-full max-w-md">
        <h2 className="font-display text-lg font-semibold text-text mb-1">
          Connect a database
        </h2>
        <p className="text-xs text-muted mb-5">
          Read-only access is strongly recommended. Your credentials are
          encrypted before storage.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-muted mb-1.5">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="e.g. sales_prod"
              className="w-full bg-ink border border-border rounded-md px-3 py-2 text-sm text-text placeholder:text-muted/60"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1.5">
              PostgreSQL connection string
            </label>
            <input
              value={connectionString}
              onChange={(e) => setConnectionString(e.target.value)}
              required
              placeholder="postgresql://user:password@host:5432/dbname"
              className="w-full bg-ink border border-border rounded-md px-3 py-2 text-sm font-mono text-text placeholder:text-muted/60"
            />
          </div>

          {error && (
            <p className="text-sm text-danger" role="alert">
              {error}
            </p>
          )}

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 text-sm py-2 rounded-md border border-border text-muted hover:text-text transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-verified text-ink font-medium text-sm py-2 rounded-md hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? "Connecting…" : "Connect"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}