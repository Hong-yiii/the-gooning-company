import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { fetchRoadmap } from '../api/index'
import styles from './RoadmapPanel.module.css'

const COLUMNS = [
  { key: 'backlog', label: 'Backlog' },
  { key: 'next', label: 'Next' },
  { key: 'in-progress', label: 'In Progress' },
  { key: 'blocked', label: 'Blocked' },
  { key: 'done', label: 'Done' },
]

const DOMAIN_COLORS = {
  product: styles.domainProduct,
  marketing: styles.domainMarketing,
  finance: styles.domainFinance,
}

const STATUS_COLORS = {
  backlog: styles.statusBacklog,
  next: styles.statusNext,
  'in-progress': styles.statusInProgress,
  blocked: styles.statusBlocked,
  done: styles.statusDone,
}

// Animation durations (kept in JS so they match CSS).
const ENTER_MS = 12000
const MOVED_MS = 8000
const COLUMN_PULSE_MS = 2000
const FLIP_MS = 560

export default function RoadmapPanel({ liveColumns }) {
  const [roadmap, setRoadmap] = useState({})
  const [loading, setLoading] = useState(true)
  const [expandedCard, setExpandedCard] = useState(null)

  // Animation effect-state keyed by card id:
  //   { [id]: { kind: 'enter' | 'moved', from?, to? } }
  const [fx, setFx] = useState({})
  // Pulse timestamps per column key; presence means "pulse active".
  const [columnPulse, setColumnPulse] = useState({})

  const cardRefs = useRef(new Map())              // id -> HTMLElement
  const prevRects = useRef(new Map())             // id -> DOMRect (last paint)
  const prevColumnById = useRef(new Map())        // id -> colKey (last paint)
  const prevColumnCounts = useRef({})
  const hasMountedOnceRef = useRef(false)
  const fxTimersRef = useRef({})
  const pulseTimersRef = useRef({})

  useEffect(() => {
    fetchRoadmap()
      .then((data) => {
        setRoadmap(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))

    const id = setInterval(() => {
      fetchRoadmap().then(setRoadmap).catch(() => {})
    }, 20000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    if (liveColumns) {
      setRoadmap(liveColumns)
      setLoading(false)
    }
  }, [liveColumns])

  // ── FLIP + enter/move detection ──────────────────────────────────────────
  useLayoutEffect(() => {
    if (loading) return

    // Build id -> column map for this render.
    const currentColumnById = new Map()
    const currentCounts = {}
    for (const col of COLUMNS) {
      const items = roadmap[col.key] || []
      currentCounts[col.key] = items.length
      for (const it of items) currentColumnById.set(it.id, col.key)
    }

    // Column-count pulse — only after first mount.
    if (hasMountedOnceRef.current) {
      const pulsedCols = []
      for (const col of COLUMNS) {
        const prev = prevColumnCounts.current[col.key]
        if (prev !== undefined && prev !== currentCounts[col.key]) {
          pulsedCols.push(col.key)
        }
      }
      if (pulsedCols.length) {
        const ts = Date.now()
        setColumnPulse((p) => {
          const next = { ...p }
          for (const c of pulsedCols) next[c] = ts
          return next
        })
        for (const c of pulsedCols) {
          clearTimeout(pulseTimersRef.current[c])
          pulseTimersRef.current[c] = setTimeout(() => {
            setColumnPulse((p) => {
              if (p[c] !== ts) return p
              const next = { ...p }
              delete next[c]
              return next
            })
          }, COLUMN_PULSE_MS)
        }
      }
    }
    prevColumnCounts.current = currentCounts

    // Measure current rects + compute FLIP / enter / moved markers.
    const newRects = new Map()
    const newFx = {}

    for (const [id, el] of cardRefs.current.entries()) {
      if (!el || !currentColumnById.has(id)) continue
      const rect = el.getBoundingClientRect()
      newRects.set(id, rect)

      const oldRect = prevRects.current.get(id)
      const oldCol = prevColumnById.current.get(id)
      const newCol = currentColumnById.get(id)

      // FLIP: card existed last paint, position changed → animate from old.
      if (oldRect) {
        const dx = oldRect.left - rect.left
        const dy = oldRect.top - rect.top
        if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) {
          playFlip(el, dx, dy)
        }
      }

      if (hasMountedOnceRef.current) {
        if (!oldRect) {
          // Brand-new card this render.
          newFx[id] = { kind: 'enter' }
        } else if (oldCol && newCol && oldCol !== newCol) {
          // Card crossed columns.
          newFx[id] = { kind: 'moved', from: oldCol, to: newCol }
        }
      }
    }

    if (Object.keys(newFx).length) {
      setFx((prev) => ({ ...prev, ...newFx }))
      for (const [id, mark] of Object.entries(newFx)) {
        const duration = mark.kind === 'enter' ? ENTER_MS : MOVED_MS
        clearTimeout(fxTimersRef.current[id])
        fxTimersRef.current[id] = setTimeout(() => {
          setFx((prev) => {
            if (!prev[id]) return prev
            const next = { ...prev }
            delete next[id]
            return next
          })
        }, duration)
      }
    }

    prevRects.current = newRects
    prevColumnById.current = currentColumnById
    hasMountedOnceRef.current = true
  })

  useEffect(
    () => () => {
      Object.values(fxTimersRef.current).forEach(clearTimeout)
      Object.values(pulseTimersRef.current).forEach(clearTimeout)
    },
    []
  )

  const registerCardRef = (id) => (el) => {
    if (el) cardRefs.current.set(id, el)
    else cardRefs.current.delete(id)
  }

  const totalItems = Object.values(roadmap).reduce(
    (acc, col) => acc + col.length,
    0
  )

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <div className={styles.headerLeft}>
          <span className={styles.panelTitle}>Product Roadmap</span>
          <span className={styles.itemCount}>{totalItems} items</span>
        </div>
        <div className={styles.legend}>
          <LegendPip label="product" className={styles.domainProduct} />
          <LegendPip label="marketing" className={styles.domainMarketing} />
          <LegendPip label="finance" className={styles.domainFinance} />
        </div>
      </div>

      {loading ? (
        <div className={styles.loading}>Loading roadmap…</div>
      ) : (
        <div className={styles.kanban}>
          {COLUMNS.map((col) => (
            <KanbanColumn
              key={col.key}
              column={col}
              items={roadmap[col.key] || []}
              expandedCard={expandedCard}
              onExpandCard={setExpandedCard}
              registerRef={registerCardRef}
              fx={fx}
              pulseActive={!!columnPulse[col.key]}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function KanbanColumn({
  column,
  items,
  expandedCard,
  onExpandCard,
  registerRef,
  fx,
  pulseActive,
}) {
  return (
    <div className={styles.column}>
      <div className={styles.columnHeader}>
        <span className={`${styles.columnDot} ${STATUS_COLORS[column.key]}`} />
        <span className={styles.columnLabel}>{column.label}</span>
        <span
          className={`${styles.columnCount} ${pulseActive ? styles.columnCountPulse : ''}`}
        >
          {items.length}
        </span>
      </div>
      <div className={styles.cards}>
        {items.length === 0 ? (
          <div className={styles.emptySlot}>—</div>
        ) : (
          items.map((item) => (
            <RoadmapCard
              key={item.id}
              item={item}
              expanded={expandedCard === item.id}
              onToggle={() =>
                onExpandCard(expandedCard === item.id ? null : item.id)
              }
              registerRef={registerRef(item.id)}
              fx={fx[item.id]}
            />
          ))
        )}
      </div>
    </div>
  )
}

function RoadmapCard({ item, expanded, onToggle, registerRef, fx }) {
  const isEntering = fx?.kind === 'enter'
  const isMoved = fx?.kind === 'moved'

  return (
    <div
      ref={registerRef}
      className={`${styles.card} ${expanded ? styles.cardExpanded : ''} ${
        isEntering ? styles.cardEntering : ''
      } ${isMoved ? styles.cardMoved : ''}`}
      onClick={onToggle}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onToggle()}
    >
      {isEntering && <span className={styles.fxBadgeNew}>new</span>}
      {isMoved && (
        <span className={styles.fxBadgeMoved}>
          → {shortCol(fx.to)}
        </span>
      )}

      <div className={styles.cardTop}>
        <span className={`${styles.domainTag} ${DOMAIN_COLORS[item.domain]}`}>
          {item.domain}
        </span>
        <span className={styles.cardId}>{item.id}</span>
      </div>
      <p className={styles.cardTitle}>{item.title}</p>
      {expanded && item.notes && (
        <p className={styles.cardNotes}>{item.notes}</p>
      )}
      {expanded && (
        <div className={styles.cardMeta}>
          <span className={styles.metaLabel}>owner</span>
          <span className={styles.metaValue}>{item.owner}</span>
        </div>
      )}
    </div>
  )
}

function LegendPip({ label, className }) {
  return (
    <div className={styles.legendPip}>
      <span className={`${styles.legendDot} ${className}`} />
      <span className={styles.legendLabel}>{label}</span>
    </div>
  )
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function playFlip(el, dx, dy) {
  // Classic FLIP: apply the old-position offset instantly, then animate back.
  el.style.transition = 'none'
  el.style.transform = `translate(${dx}px, ${dy}px)`
  el.style.zIndex = '10'
  el.style.willChange = 'transform'
  // Force reflow so the next frame sees the translate.
  // eslint-disable-next-line no-unused-expressions
  el.offsetWidth
  requestAnimationFrame(() => {
    el.style.transition = `transform ${FLIP_MS}ms cubic-bezier(0.22, 1, 0.36, 1)`
    el.style.transform = ''
    const clean = (e) => {
      if (e.propertyName !== 'transform') return
      el.style.transition = ''
      el.style.zIndex = ''
      el.style.willChange = ''
      el.removeEventListener('transitionend', clean)
    }
    el.addEventListener('transitionend', clean)
  })
}

function shortCol(col) {
  if (!col) return ''
  if (col === 'in-progress') return 'in progress'
  return col
}
