import { useState } from "react";

/**
 * The signature element of Querynetic's UI: makes the backend's actual
 * safety guarantee (every SQL query passed the firewall before running)
 * visible to the person reading the answer, instead of hiding it behind
 * a generic "thinking..." spinner like most AI chat interfaces do.
 */
export default function VerifiedQuery({ queries, validated }) {
  const [open, setOpen] = useState(false);

  if (!queries || queries.length === 0) return null;

  return (
    <div className="mt-3 border border-border rounded-md overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-muted hover:text-text transition-colors"
      >
        <span
          className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-medium ${
            validated
              ? "bg-verified/10 text-verified"
              : "bg-danger/10 text-danger"
          }`}
        >
          {validated ? "✓ Validated" : "✗ Not validated"}
        </span>
        <span>·</span>
        <span>Read-only</span>
        <span className="ml-auto">{open ? "Hide query" : "Show query"}</span>
      </button>

      {open && (
        <div className="border-t border-border divide-y divide-border">
          {queries.map((q, i) => (
            <div key={i} className="px-3 py-2">
              <p className="text-xs text-muted mb-1">{q.sub_question}</p>
              <pre className="text-xs font-mono text-query overflow-x-auto whitespace-pre-wrap">
                {q.sql}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}