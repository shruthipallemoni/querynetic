# Querynetic

**An autonomous AI data analyst — not a Text-to-SQL wrapper, not a RAG demo, not a chatbot.**

Querynetic lets a user connect their own database and ask business questions in
plain English. Behind the scenes, a multi-agent pipeline plans the query, retrieves
only the relevant schema, generates SQL, **validates and firewalls it before
execution**, runs it safely, and returns a summarized, explained answer.

The core design principle: **the LLM is never trusted with raw database access,
the full schema, or raw query results.** Every stage exists to enforce that.

---

## Why this exists

Most student "chat with your database" projects execute whatever SQL the model
writes and hope for the best. Querynetic treats that as unacceptable in
production, and is built around three questions a real engineering team asks
before shipping anything like this:

1. What happens when the AI writes a wrong or dangerous query?
2. What's the smallest amount of information we actually need to send to the LLM?
3. How do we know, with evidence, that the system's answers are correct?

---

## Architecture

```
User question
     │
     ▼
┌─────────────┐
│   Planner    │  decides what needs to happen (single query? comparison?)
└─────┬───────┘
      ▼
┌─────────────────┐
│ Schema Retrieval │  finds only relevant tables/columns via embeddings
└─────┬───────────┘
      ▼
┌─────────────────┐
│  SQL Generation  │  writes the SQL query
└─────┬───────────┘
      ▼
┌───────────────────────┐
│ SQL Validation/Firewall│  blocks destructive ops, injection, unauthorized tables
└─────┬─────────────────┘
      │  (fails → repair loop)
      ▼
┌─────────────┐
│  Execution   │  runs query via a READ-ONLY connection to the user's DB
└─────┬───────┘
      ▼
┌───────────────────┐
│ Result Summarization│  computes stats/summary — never sends raw rows to the LLM
└─────┬───────────────┘
      ▼
Final answer + chart shown to user
```

Each agent has exactly one job. This means when something goes wrong, the
failure is traceable to a single stage instead of buried inside one giant prompt.

---

## Tech stack

| Layer          | Choice                                   |
|----------------|-------------------------------------------|
| Frontend       | React + Vite + Tailwind CSS              |
| Backend        | FastAPI (Python)                          |
| Orchestration  | LangGraph                                 |
| App database   | PostgreSQL + SQLAlchemy                   |
| Vector store   | Chroma (schema embeddings)                |
| Caching        | Redis                                     |
| Auth           | JWT (OAuth planned)                       |
| Visualization  | Plotly / Recharts                         |
| Deployment     | Docker + Docker Compose                   |
| Testing        | Pytest                                    |

---

## Project structure

```
querynetic/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── core/                # config + Querynetic's own DB connection
│   │   ├── agents/               # one file per pipeline stage
│   │   ├── graph.py              # wires agents into a LangGraph pipeline
│   │   ├── api/                  # HTTP endpoints the frontend calls
│   │   └── db_connectors/        # connections to the USER'S connected database
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       └── pages/
└── docs/
```

`db_connectors/` (the user's business database) and `core/db.py` (Querynetic's
own app database) are kept deliberately separate — mixing these up is one of
the easiest and most dangerous mistakes to make in a system like this.

---

## Getting started

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your own values
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Roadmap / current status

- [ ] Core pipeline: Planner → Schema Retrieval → SQL Generation → Validation → Execution → Summarization
- [ ] SQL Repair Agent + Verification Agent (auto-fix failed queries)
- [ ] Conversation memory (follow-up questions without repeating context)
- [ ] Auth (JWT) + basic RBAC (Owner / Analyst / Viewer)
- [ ] Observability logging per pipeline stage (latency, token usage, retries)
- [ ] Visualization + export (Plotly, PDF)
- [ ] Multi-tenant organizations, business glossary, admin panel *(post-MVP)*

---

## Security notes

- Database credentials are encrypted at rest and only decrypted at the moment
  of connection.
- All connections to user-provided databases use a **read-only** role wherever
  possible.
- All generated SQL passes through validation and a firewall before execution —
  destructive statements (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`) and
  multi-statement queries are rejected outright.
