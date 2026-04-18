import { useState, useEffect } from 'react'
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

export default function RoadmapPanel({ liveColumns }) {
  const [roadmap, setRoadmap] = useState({})
  const [loading, setLoading] = useState(true)
  const [expandedCard, setExpandedCard] = useState(null)

  useEffect(() => {
    fetchRoadmap()
      .then((data) => {
        setRoadmap(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))

    // Polling fallback in case SSE is down (disabled when live events arrive).
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

  const totalItems = Object.values(roadmap).reduce((acc, col) => acc + col.length, 0)

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
            />
          ))}
        </div>
      )}
    </div>
  )
}

function KanbanColumn({ column, items, expandedCard, onExpandCard }) {
  return (
    <div className={styles.column}>
      <div className={styles.columnHeader}>
        <span className={`${styles.columnDot} ${STATUS_COLORS[column.key]}`} />
        <span className={styles.columnLabel}>{column.label}</span>
        <span className={styles.columnCount}>{items.length}</span>
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
              onToggle={() => onExpandCard(expandedCard === item.id ? null : item.id)}
            />
          ))
        )}
      </div>
    </div>
  )
}

function RoadmapCard({ item, expanded, onToggle }) {
  return (
    <div
      className={`${styles.card} ${expanded ? styles.cardExpanded : ''}`}
      onClick={onToggle}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onToggle()}
    >
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
