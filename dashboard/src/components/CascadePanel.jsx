import { useEffect, useRef, useState } from 'react'
import { fetchCascade } from '../api/index'
import styles from './CascadePanel.module.css'

const DOMAIN_BY_TOOL_PREFIX = {
  product: 'product',
  marketing: 'marketing',
  finance: 'finance',
  roadmap: 'roadmap',
}

export default function CascadePanel({ events: liveEvents }) {
  const [events, setEvents] = useState([])
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollRef = useRef(null)

  useEffect(() => {
    fetchCascade(100)
      .then(setEvents)
      .catch(() => setEvents([]))
  }, [])

  useEffect(() => {
    if (!liveEvents) return
    // Backend pushes the last-N tail as a snapshot per change — replace.
    setEvents(liveEvents)
  }, [liveEvents])

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events, autoScroll])

  const handleScroll = () => {
    const el = scrollRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    setAutoScroll(atBottom)
  }

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <div className={styles.headerLeft}>
          <span className={styles.panelTitle}>Cascade trace</span>
          <span className={styles.itemCount}>{events.length} events</span>
        </div>
        <span className={styles.liveTag}>
          <span className={styles.liveDot} />
          live
        </span>
      </div>

      <div ref={scrollRef} onScroll={handleScroll} className={styles.feed}>
        {events.length === 0 ? (
          <div className={styles.empty}>
            No tool calls yet. Try asking the router to add a roadmap item.
          </div>
        ) : (
          events.map((ev, i) => <CascadeRow key={`${ev.ts}-${i}`} event={ev} />)
        )}
      </div>
    </div>
  )
}

function CascadeRow({ event }) {
  const tool = event.tool || ''
  const domain = domainFromTool(tool)
  const isErr = event.event === 'tool_error' || event.ok === false
  const isCall = event.event === 'tool_call'

  return (
    <div className={`${styles.row} ${isErr ? styles.rowError : ''}`}>
      <span className={styles.time}>{shortTime(event.ts)}</span>
      <span className={`${styles.chip} ${styles[`chip_${domain}`] || ''}`}>
        {domain}
      </span>
      <span className={styles.arrow}>
        {isCall ? '→' : isErr ? '✗' : '✓'}
      </span>
      <span className={styles.toolName}>{tool}</span>
      <span className={styles.meta}>
        {renderMeta(event)}
      </span>
    </div>
  )
}

function renderMeta(event) {
  if (event.event === 'tool_call') {
    const summary = summariseArgs(event.args)
    return (
      <>
        <span className={styles.metaCaller}>from {event.caller || 'unknown'}</span>
        {summary && <span className={styles.metaArgs}>{summary}</span>}
      </>
    )
  }
  if (event.event === 'tool_result') {
    const note = event.result?.note || event.result?.detail || event.result?.message
    return (
      <>
        {event.elapsed_ms != null && (
          <span className={styles.metaTime}>{event.elapsed_ms} ms</span>
        )}
        {note && <span className={styles.metaArgs}>{truncate(note, 60)}</span>}
      </>
    )
  }
  if (event.event === 'tool_error') {
    return <span className={styles.metaError}>{truncate(event.error, 80)}</span>
  }
  return null
}

function summariseArgs(args) {
  if (!args || typeof args !== 'object') return ''
  const keys = Object.keys(args)
  if (keys.length === 0) return ''
  const preview = keys
    .slice(0, 3)
    .map((k) => `${k}=${fmt(args[k])}`)
    .join(' ')
  return keys.length > 3 ? `${preview} …` : preview
}

function fmt(v) {
  if (v == null) return '∅'
  if (typeof v === 'string') return truncate(v, 24)
  if (typeof v === 'number' || typeof v === 'boolean') return String(v)
  if (Array.isArray(v)) return `[${v.length}]`
  return '{…}'
}

function truncate(s, n) {
  if (!s) return ''
  const str = String(s)
  return str.length > n ? str.slice(0, n - 1) + '…' : str
}

function domainFromTool(tool) {
  if (!tool) return 'system'
  const prefix = tool.split('.')[0]
  return DOMAIN_BY_TOOL_PREFIX[prefix] || prefix
}

function shortTime(iso) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}
