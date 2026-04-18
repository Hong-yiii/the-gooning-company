import { useState, useRef, useEffect } from 'react'
import { sendMessage } from '../api/index'
import styles from './ChatPanel.module.css'

const WELCOME = {
  id: 'welcome',
  role: 'assistant',
  content: `Good to have you here. I'm the coordinator for **the gooning company** — I route your intent to the Product, Marketing, and Finance agents and surface the cascade back to you.\n\nWhat are you thinking about today?`,
  timestamp: new Date(),
}

export default function ChatPanel() {
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [conversationId] = useState(() => crypto.randomUUID())
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || streaming) return

    const userMsg = { id: crypto.randomUUID(), role: 'user', content: text, timestamp: new Date() }
    const assistantId = crypto.randomUUID()
    const assistantMsg = { id: assistantId, role: 'assistant', content: '', timestamp: new Date(), pending: true }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setInput('')
    setStreaming(true)

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
          prev.map((m) => (m.id === assistantId ? { ...m, pending: false } : m))
        )
        setStreaming(false)
        inputRef.current?.focus()
      },
      (err) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: 'Something went wrong. Try again.', pending: false, error: true }
              : m
          )
        )
        setStreaming(false)
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

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>Coordinator</span>
        <span className={styles.panelSubtitle}>router agent</span>
      </div>

      <div className={styles.messages}>
        {messages.map((msg) => (
          <Message key={msg.id} message={msg} />
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

function Message({ message }) {
  const isUser = message.role === 'user'
  const lines = message.content.split('\n')

  return (
    <div className={`${styles.message} ${isUser ? styles.messageUser : styles.messageAssistant}`}>
      {!isUser && (
        <div className={styles.agentLabel}>
          <div className={styles.agentAvatar} />
          <span>coordinator</span>
        </div>
      )}
      <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAssistant}`}>
        <FormattedContent content={message.content} pending={message.pending} />
      </div>
      <span className={styles.timestamp}>{formatTime(message.timestamp)}</span>
    </div>
  )
}

function FormattedContent({ content, pending }) {
  if (!content && pending) {
    return (
      <span className={styles.thinkingDots}>
        <span />
        <span />
        <span />
      </span>
    )
  }

  const segments = parseInlineMarkdown(content)
  return (
    <p className={styles.messageText}>
      {segments}
      {pending && <span className={styles.cursor} />}
    </p>
  )
}

function parseInlineMarkdown(text) {
  const parts = []
  const regex = /\*\*(.+?)\*\*|_(.+?)_|\*(.+?)\*/g
  let last = 0
  let match
  let key = 0

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) {
      parts.push(<span key={key++}>{text.slice(last, match.index)}</span>)
    }
    if (match[1]) parts.push(<strong key={key++}>{match[1]}</strong>)
    else if (match[2]) parts.push(<em key={key++}>{match[2]}</em>)
    else if (match[3]) parts.push(<em key={key++}>{match[3]}</em>)
    last = regex.lastIndex
  }

  if (last < text.length) {
    parts.push(<span key={key++}>{text.slice(last)}</span>)
  }

  return parts.length ? parts : text
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
