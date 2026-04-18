import { useState, useEffect, useRef } from 'react'
import { fetchGodFile, subscribeGodFile } from '../api/index'
import styles from './GodFilesPanel.module.css'

const AGENTS = [
  { key: 'product', label: 'Product', color: styles.agentProduct },
  { key: 'marketing', label: 'Marketing', color: styles.agentMarketing },
  { key: 'finance', label: 'Finance', color: styles.agentFinance },
]

export default function GodFilesPanel({ agentStatuses }) {
  const [activeAgent, setActiveAgent] = useState('product')
  const [godFiles, setGodFiles] = useState({ product: null, marketing: null, finance: null })
  const [lastPulse, setLastPulse] = useState({ product: null, marketing: null, finance: null })
  const [pulseActive, setPulseActive] = useState({ product: false, marketing: false, finance: false })

  useEffect(() => {
    AGENTS.forEach(({ key }) => {
      fetchGodFile(key).then((data) =>
        setGodFiles((prev) => ({ ...prev, [key]: data }))
      )
    })
  }, [])

  useEffect(() => {
    const unsubscribers = AGENTS.map(({ key }) =>
      subscribeGodFile(key, (data) => {
        setGodFiles((prev) => {
          const prevData = prev[key]
          const changed = prevData && prevData.updatedAt !== data.updatedAt
          if (changed) {
            setLastPulse((p) => ({ ...p, [key]: data.updatedAt }))
            setPulseActive((p) => ({ ...p, [key]: true }))
            setTimeout(() => setPulseActive((p) => ({ ...p, [key]: false })), 2000)
          }
          return { ...prev, [key]: data }
        })
      }, 8000)
    )
    return () => unsubscribers.forEach((fn) => fn())
  }, [])

  const active = godFiles[activeAgent]

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>Agent Files</span>
        <span className={styles.liveTag}>
          <span className={styles.liveDot} />
          live
        </span>
      </div>

      <div className={styles.tabs}>
        {AGENTS.map(({ key, label, color }) => (
          <button
            key={key}
            className={`${styles.tab} ${activeAgent === key ? styles.tabActive : ''}`}
            onClick={() => setActiveAgent(key)}
          >
            <span className={`${styles.tabDot} ${color}`} />
            <span>{label}</span>
            {pulseActive[key] && <span className={styles.updateBadge} />}
            <StatusPip status={agentStatuses?.[key]} />
          </button>
        ))}
      </div>

      <div className={styles.fileView}>
        {!active ? (
          <div className={styles.loading}>Loading…</div>
        ) : (
          <>
            <GodFileContent content={active.content} />
            <div className={styles.fileFooter}>
              <span className={styles.footerLabel}>god.md — {activeAgent}</span>
              <span className={styles.footerTime}>
                updated {formatRelativeTime(active.updatedAt)}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function GodFileContent({ content }) {
  const sections = parseMarkdownSections(content)

  return (
    <div className={styles.content}>
      {sections.map((section, i) => (
        <Section key={i} section={section} />
      ))}
    </div>
  )
}

function Section({ section }) {
  const [collapsed, setCollapsed] = useState(false)
  const isEmpty =
    !section.body ||
    section.body.trim() === '' ||
    section.body.trim().startsWith('*(no') ||
    section.body.trim().startsWith('*(none')

  return (
    <div className={`${styles.section} ${isEmpty ? styles.sectionEmpty : ''}`}>
      <button
        className={styles.sectionHeader}
        onClick={() => setCollapsed((c) => !c)}
      >
        <span className={styles.chevron}>{collapsed ? '›' : '›'}</span>
        <span
          className={`${styles.sectionTitle} ${collapsed ? styles.sectionTitleCollapsed : ''}`}
        >
          {section.heading}
        </span>
        {isEmpty && <span className={styles.emptyMark}>empty</span>}
      </button>
      {!collapsed && section.body && (
        <div className={styles.sectionBody}>
          <MarkdownBody text={section.body} />
        </div>
      )}
    </div>
  )
}

function MarkdownBody({ text }) {
  const lines = text.split('\n').filter(Boolean)
  return (
    <div className={styles.markdownBody}>
      {lines.map((line, i) => {
        if (line.startsWith('- ')) {
          return (
            <div key={i} className={styles.listItem}>
              <span className={styles.bullet}>·</span>
              <span>{line.slice(2)}</span>
            </div>
          )
        }
        if (line.startsWith('*') && line.endsWith('*')) {
          return (
            <p key={i} className={styles.italicLine}>
              {line.slice(1, -1)}
            </p>
          )
        }
        return (
          <p key={i} className={styles.para}>
            {line}
          </p>
        )
      })}
    </div>
  )
}

function StatusPip({ status }) {
  if (!status) return null
  return (
    <span
      className={`${styles.agentStatusDot} ${
        status === 'online' ? styles.agentOnline : styles.agentOffline
      }`}
    />
  )
}

function parseMarkdownSections(markdown) {
  const lines = markdown.split('\n')
  const sections = []
  let current = null

  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (current) sections.push(current)
      current = { heading: line.slice(3).trim(), body: '' }
    } else if (line.startsWith('# ')) {
      // top-level heading — skip or use as preamble
    } else if (current) {
      if (line.startsWith('<!-- ') || line.trim() === '') {
        if (current.body.trim()) current.body += '\n'
      } else {
        current.body += (current.body ? '\n' : '') + line
      }
    }
  }
  if (current) sections.push(current)
  return sections
}

function formatRelativeTime(isoString) {
  if (!isoString) return 'never'
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes === 1) return '1 minute ago'
  if (minutes < 60) return `${minutes} minutes ago`
  const hours = Math.floor(minutes / 60)
  if (hours === 1) return '1 hour ago'
  return `${hours} hours ago`
}
