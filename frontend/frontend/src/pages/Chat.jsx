import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import CitationChip from '../components/CitationChip.jsx'
import { chat, listPapers } from '../api.js'

let nextId = 1

export default function Chat() {
  const [searchParams, setSearchParams] = useSearchParams()
  const scopedPaperId = searchParams.get('paper') || ''

  const [papers, setPapers] = useState([])
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const logRef = useRef(null)

  useEffect(() => {
    listPapers().then(setPapers).catch(() => {})
  }, [])

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  function scopeLabel() {
    if (!scopedPaperId) return 'All papers'
    const match = papers.find((p) => p.id === scopedPaperId)
    return match ? match.title : 'Selected paper'
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question || sending) return

    setInput('')
    const userMsg = { id: nextId++, role: 'user', text: question }
    const pendingMsg = { id: nextId++, role: 'assistant', text: 'Thinking…', pending: true }
    setMessages((prev) => [...prev, userMsg, pendingMsg])
    setSending(true)

    try {
      const result = await chat(question, { paperId: scopedPaperId || null })
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingMsg.id
            ? { ...m, text: result.answer, citations: result.citations, pending: false }
            : m
        )
      )
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingMsg.id
            ? { ...m, role: 'error', text: err.message || 'Something went wrong.', pending: false }
            : m
        )
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Chat</h1>
          <p>Ask a question and get an answer grounded in your papers, with page citations.</p>
        </div>
      </div>

      <div className="chat-shell">
        <div className="chat-scope">
          <label htmlFor="scope" style={{ color: 'var(--ink-muted)', fontSize: '0.85rem' }}>
            Scope:
          </label>
          <select
            id="scope"
            value={scopedPaperId}
            onChange={(e) => {
              const value = e.target.value
              setSearchParams(value ? { paper: value } : {})
            }}
          >
            <option value="">All papers</option>
            {papers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
        </div>

        <div className="chat-log" ref={logRef}>
          {messages.length === 0 && (
            <div className="empty-state">
              <p>Ask something like "what dataset did they use?" — currently scoped to {scopeLabel()}.</p>
            </div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`msg ${m.role}${m.pending ? ' pending' : ''}`}>
              <p style={{ whiteSpace: 'pre-wrap' }}>{m.text}</p>
              {m.citations && m.citations.length > 0 && (
                <div className="citations">
                  {m.citations.map((c, i) => (
                    <CitationChip key={i} citation={c} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <form className="chat-input-row" onSubmit={handleSubmit}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
            placeholder="Ask a question about your papers…"
          />
          <button className="btn btn-primary" type="submit" disabled={sending || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </>
  )
}
