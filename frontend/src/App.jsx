import { useEffect, useState } from 'react'
const API = import.meta.env.VITE_API_URL || ''
const SUGGESTIONS = [
  'What is MCP and tool calling?',
  'How do policy-gated LLM apps work?',
  'What are AI skills?',
  'How does local LM Studio fit in?',
  'Tell me about Northline Returns',
]

export default function App() {
  const [docs, setDocs] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [log, setLog] = useState([])

  useEffect(() => {
    fetch(`${API}/api/docs`).then(r => r.json()).then(d => setDocs(d.documents || [])).catch(() => {})
  }, [])

  async function ask(q) {
    const question = (q || input).trim()
    if (!question || loading) return
    setInput('')
    setLog(l => [...l, { role: 'user', text: question }])
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 3 }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed')
      setLog(l => [...l, { role: 'bot', text: data.answer, sources: data.sources || [] }])
    } catch (e) {
      setLog(l => [...l, { role: 'bot', text: `Error: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="logo">D</div>
          <div>
            <h1>DocQA Agent</h1>
            <p className="tag">Retrieve → answer over a fixed knowledge base (demo RAG)</p>
          </div>
        </div>
        <span className="badge">Live demo</span>
      </header>
      <div className="docs">
        {(docs.length ? docs : [{ title: 'Loading corpus…' }]).map((d, i) => (
          <span key={i} className="doc-chip">{d.title}</span>
        ))}
      </div>
      <div className="chat">
        {log.length === 0 && (
          <p className="msg" style={{ color: 'var(--muted)' }}>
            Ask about MCP, policy-gated agents, AI skills, local models, or the Northline demo.
          </p>
        )}
        {log.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.text}
            {m.sources?.length > 0 && (
              <div className="sources">
                {m.sources.map((s, j) => (
                  <div key={j} className="src">
                    <strong>{s.title}</strong> (score {s.score}) — {s.excerpt}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="suggestions">
        {SUGGESTIONS.map(s => (
          <button key={s} type="button" onClick={() => ask(s)} disabled={loading}>{s}</button>
        ))}
      </div>
      <form className="composer" onSubmit={e => { e.preventDefault(); ask() }}>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask the knowledge base…" disabled={loading} />
        <button type="submit" disabled={loading || !input.trim()}>Ask</button>
      </form>
      <p className="footer">Sammy-t3ch/docqa-agent · TF-IDF retrieval · no paid vector DB required</p>
    </div>
  )
}
