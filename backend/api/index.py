"""DocQA Agent — retrieve from a knowledge base then answer (demo RAG-style)."""
from __future__ import annotations
import math, re
from collections import Counter
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="DocQA Agent", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DOCS = [
    {"id": "mcp-basics", "title": "MCP & Tool-Calling Agents", "text": "Model Context Protocol (MCP) style agents register tools with a name, description, and JSON schema. The LLM decides which tool to call. Results are fed back so the model can answer in natural language. This pattern connects apps to AI chatbots safely."},
    {"id": "policy-gated", "title": "Policy-Gated LLM Applications", "text": "In policy-gated systems a deterministic rules engine decides first (approve, deny, escalate). The LLM only drafts the customer-facing message and cannot override the policy decision. Used in refund assistants for auditability."},
    {"id": "ai-skills", "title": "AI Skills", "text": "An AI skill is a package of instructions plus optional tools. Skills can be loaded at runtime so the same agent becomes a research assistant, ops helper, or domain specialist without rewriting the core loop."},
    {"id": "local-models", "title": "Local Models with LM Studio", "text": "LM Studio lets you run open models locally and expose an OpenAI-compatible API. Agents can point LLM_BASE_URL at localhost so tool-calling works offline. Useful for privacy and demos without cloud keys."},
    {"id": "vibe-coding", "title": "AI-Assisted (Vibe) Coding", "text": "Vibe coding means shipping full-stack features with AI copilots at high speed while keeping architecture intentional: clear tool registries, policy engines, tests, and deployable demos."},
    {"id": "northline", "title": "Northline Returns Example", "text": "Northline Returns is a refund assistant demo: mock CRM, hard-coded rules for return windows and final-sale items, and NVIDIA NIM only for drafting replies. Seven scenarios for reviewers."},
    {"id": "nigeria-context", "title": "Building from Abuja, Nigeria", "text": "Samuel Campbell builds AI-native products from Abuja, Nigeria, targeting remote roles. Stack focuses on React, FastAPI, MCP-style agents, and live Vercel demos."},
]

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

def _tfidf_scores(query: str):
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []
    df = Counter()
    docs_tokens = []
    for d in DOCS:
        toks = _tokenize(d["title"] + " " + d["text"])
        docs_tokens.append(toks)
        for t in set(toks):
            df[t] += 1
    n = len(DOCS)
    q_tf = Counter(q_tokens)
    scores = []
    for i, toks in enumerate(docs_tokens):
        tf = Counter(toks)
        score = 0.0
        for term, qf in q_tf.items():
            if term not in df:
                continue
            idf = math.log((n + 1) / (df[term] + 1)) + 1
            score += (tf[term] / max(len(toks), 1)) * idf * qf
        scores.append((score, DOCS[i]))
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=5)

class AskResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@app.get("/")
def root():
    return {"message": "DocQA Agent", "docs": "/api/docs", "health": "/api/health"}

@app.get("/api/health")
@app.get("/health")
def health():
    return {"status": "ok", "documents": len(DOCS)}

@app.get("/api/docs")
def list_docs():
    return {"documents": [{"id": d["id"], "title": d["title"]} for d in DOCS]}

@app.post("/api/ask")
@app.post("/ask")
def ask(req: AskRequest):
    ranked = _tfidf_scores(req.question)
    top = [(s, d) for s, d in ranked if s > 0][: req.top_k] or ranked[:1]
    sources = [{"id": d["id"], "title": d["title"], "score": round(s, 4), "excerpt": d["text"][:220] + ("…" if len(d["text"]) > 220 else "")} for s, d in top]
    chunks = [d["text"] for _, d in top]
    answer = "Based on the knowledge base:\n\n" + "\n\n".join(f"• {c}" for c in chunks[:3]) + "\n\n(Retrieved with TF-IDF — demo RAG without a paid vector DB.)"
    return AskResponse(answer=answer, sources=sources)
