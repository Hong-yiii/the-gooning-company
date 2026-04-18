import { useState, useRef, useEffect, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import { sendMessage } from '../api/index'
import styles from './ChatPanel.module.css'

const WELCOME = {
  id: 'welcome',
  role: 'assistant',
  content: `Good to have you here. I'm the coordinator for **the gooning company** — I route your intent to the Product, Marketing, and Finance agents and surface the cascade back to you.\n\nWhat are you thinking about today?`,
  timestamp: new Date(),
}

export default function ChatPanel({ liveCascade }) {
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [turnStartTs, setTurnStartTs] = useState(null)
  const [conversationId] = useState(() => crypto.randomUUID())
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || streaming) return

    const now = Date.now()
    const userMsg = { id: crypto.randomUUID(), role: 'user', content: text, timestamp: new Date(now) }
    const assistantId = crypto.randomUUID()
    const assistantMsg = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(now),
      pending: true,
      startedAt: now,
    }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setInput('')
    setStreaming(true)
    setTurnStartTs(now)

    sendMessage(
      text,
      conversationId,
      (delta) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + delta } : m))
        )
      },
      () => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, pending: false, finishedAt: Date.now() }
              : m
          )
        )
        setStreaming(false)
        setTurnStartTs(null)
        inputRef.current?.focus()
      },
      (err) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: m.content || 'Something went wrong. Try again.',
                  pending: false,
                  error: true,
                  finishedAt: Date.now(),
                }
              : m
          )
        )
        setStreaming(false)
        setTurnStartTs(null)
      }
    )
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Tool calls that happened during the current turn only.
  const turnActivity = useMemo(() => {
    if (!turnStartTs || !liveCascade) return []
    return liveCascade.filter((ev) => {
      const t = new Date(ev.ts || 0).getTime()
      return t >= turnStartTs - 250 // small slack for clock skew
    })
  }, [liveCascade, turnStartTs])

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>Coordinator</span>
        <span className={styles.panelSubtitle}>router agent</span>
        {streaming && (
          <span className={styles.headerThinking} title="router is working">
            <span className={styles.headerDot} />
            thinking
          </span>
        )}
      </div>

      <div className={styles.messages}>
        {messages.map((msg) => (
          <Message
            key={msg.id}
            message={msg}
            activity={msg.pending ? turnActivity : null}
          />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className={styles.inputArea}>
        <div className={styles.inputWrap}>
          <textarea
            ref={inputRef}
            className={styles.input}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Message the coordinator…"
            rows={1}
            disabled={streaming}
          />
          <button
            className={`${styles.sendBtn} ${streaming || !input.trim() ? styles.sendBtnDisabled : ''}`}
            onClick={handleSend}
            disabled={streaming || !input.trim()}
            aria-label="Send"
          >
            <SendIcon />
          </button>
        </div>
        <p className={styles.inputHint}>shift+enter for newline</p>
      </div>
    </div>
  )
}

function Message({ message, activity }) {
  const isUser = message.role === 'user'
  const isAssistant = !isUser

  return (
    <div className={`${styles.message} ${isUser ? styles.messageUser : styles.messageAssistant}`}>
      {isAssistant && (
        <div className={styles.agentLabel}>
          <div className={styles.agentAvatar} />
          <span>coordinator</span>
        </div>
      )}
      <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAssistant} ${message.error ? styles.bubbleError : ''}`}>
        <BubbleContent
          content={message.content}
          pending={message.pending}
          startedAt={message.startedAt}
          activity={activity}
        />
      </div>
      <span className={styles.timestamp}>{formatTime(message.timestamp)}</span>
    </div>
  )
}

function BubbleContent({ content, pending, startedAt, activity }) {
  const hasContent = Boolean(content && content.trim())

  return (
    <>
      {!hasContent && pending ? (
        <InFlightIndicator startedAt={startedAt} activity={activity} />
      ) : (
        <div className={styles.messageBody}>
          <MessageMarkdown text={content} />
          {pending && <span className={styles.cursor} />}
        </div>
      )}
      {/* Tool chips continue to show while still streaming, under the text. */}
      {hasContent && pending && activity && activity.length > 0 && (
        <ActivityStrip activity={activity} compact />
      )}
    </>
  )
}

// ─── In-flight indicator ─────────────────────────────────────────────────────

const PHASES = [
  { until: 3, label: 'routing intent' },
  { until: 8, label: 'consulting model' },
  { until: 18, label: 'calling tools' },
  { until: 45, label: 'composing reply' },
  { until: Infinity, label: 'still working' },
]

function InFlightIndicator({ startedAt, activity }) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 250)
    return () => clearInterval(id)
  }, [])

  const elapsedMs = Math.max(0, now - (startedAt || now))
  const elapsedS = elapsedMs / 1000
  const phase = PHASES.find((p) => elapsedS < p.until)?.label ?? 'working'

  return (
    <div className={styles.inflight}>
      <div className={styles.inflightHeader}>
        <Spinner />
        <span className={styles.inflightPhase}>{phase}</span>
        <span className={styles.inflightElapsed}>
          {elapsedS < 10 ? elapsedS.toFixed(1) : Math.floor(elapsedS)}s
        </span>
      </div>
      <div className={styles.inflightBar}>
        <div className={styles.inflightBarFill} />
      </div>
      {activity && activity.length > 0 && (
        <ActivityStrip activity={activity} />
      )}
    </div>
  )
}

function ActivityStrip({ activity, compact }) {
  // De-dup: show the latest event per (tool+call_id) pair so a tool_call that
  // later becomes tool_result collapses into a single row with ✓ + elapsed.
  const rows = summariseActivity(activity).slice(-4)
  if (rows.length === 0) return null

  return (
    <ul className={`${styles.activityList} ${compact ? styles.activityCompact : ''}`}>
      {rows.map((row) => (
        <li key={row.key} className={`${styles.activityRow} ${row.ok === false ? styles.activityErr : ''}`}>
          <span className={styles.activityArrow}>{row.symbol}</span>
          <span className={styles.activityTool}>{row.tool}</span>
          {row.elapsed != null && (
            <span className={styles.activityElapsed}>{row.elapsed}ms</span>
          )}
          {row.note && <span className={styles.activityNote}>{row.note}</span>}
        </li>
      ))}
    </ul>
  )
}

function summariseActivity(events) {
  const byKey = new Map()
  for (const ev of events) {
    const key = ev.call_id || `${ev.tool}|${ev.ts}`
    const prev = byKey.get(key) || { key, tool: ev.tool, note: null }
    if (ev.event === 'tool_call') {
      byKey.set(key, { ...prev, symbol: '→', ok: null })
    } else if (ev.event === 'tool_result') {
      byKey.set(key, {
        ...prev,
        symbol: '✓',
        ok: true,
        elapsed: ev.elapsed_ms ?? prev.elapsed,
        note: noteFromResult(ev.result) ?? prev.note,
      })
    } else if (ev.event === 'tool_error') {
      byKey.set(key, {
        ...prev,
        symbol: '✗',
        ok: false,
        elapsed: ev.elapsed_ms ?? prev.elapsed,
        note: truncate(ev.error, 48),
      })
    }
  }
  return Array.from(byKey.values())
}

function noteFromResult(result) {
  if (!result || typeof result !== 'object') return null
  const n = result.note || result.detail || result.message
  return n ? truncate(n, 48) : null
}

function truncate(s, n) {
  if (!s) return ''
  const str = String(s)
  return str.length > n ? str.slice(0, n - 1) + '…' : str
}

// ─── Markdown renderer for chat bubbles ──────────────────────────────────────

const MD_COMPONENTS = {
  p: ({ node, ...props }) => <p className={styles.mdPara} {...props} />,
  strong: ({ node, ...props }) => <strong className={styles.mdStrong} {...props} />,
  em: ({ node, ...props }) => <em className={styles.mdEm} {...props} />,
  code: ({ node, inline, children, ...props }) =>
    inline === false ? (
      <pre className={styles.mdPre}>
        <code className={styles.mdCodeBlock} {...props}>{children}</code>
      </pre>
    ) : (
      <code className={styles.mdCode} {...props}>{children}</code>
    ),
  ul: ({ node, ...props }) => <ul className={styles.mdUl} {...props} />,
  ol: ({ node, ...props }) => <ol className={styles.mdOl} {...props} />,
  li: ({ node, ...props }) => <li className={styles.mdLi} {...props} />,
  a: ({ node, ...props }) => (
    <a className={styles.mdLink} target="_blank" rel="noreferrer" {...props} />
  ),
  blockquote: ({ node, ...props }) => (
    <blockquote className={styles.mdQuote} {...props} />
  ),
  hr: () => <hr className={styles.mdHr} />,
}

function MessageMarkdown({ text }) {
  return <ReactMarkdown components={MD_COMPONENTS}>{text}</ReactMarkdown>
}

// ─── Small bits ──────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg
      className={styles.spinner}
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeDasharray="14 42"
      />
    </svg>
  )
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function SendIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      <path
        d="M1.5 7.5L13.5 7.5M13.5 7.5L8.5 2.5M13.5 7.5L8.5 12.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
