import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { fetchGodFile, subscribeGodFile } from '../api/index'
import styles from './GodFilesPanel.module.css'

const AGENTS = [
  { key: 'router', label: 'Router', color: styles.agentRouter },
  { key: 'product', label: 'Product', color: styles.agentProduct },
  { key: 'marketing', label: 'Marketing', color: styles.agentMarketing },
  { key: 'finance', label: 'Finance', color: styles.agentFinance },
]

const EMPTY_BY_AGENT = Object.fromEntries(AGENTS.map(({ key }) => [key, null]))
const FALSE_BY_AGENT = Object.fromEntries(AGENTS.map(({ key }) => [key, false]))
const EMPTY_DIFF = { added: new Set(), removed: [], changeId: 0 }
const EMPTY_DIFF_BY_AGENT = Object.fromEntries(AGENTS.map(({ key }) => [key, EMPTY_DIFF]))

// After this window the "just changed" CSS classes are cleared so the
// rendered view returns to normal.
const DIFF_CLEAR_MS = 15000

// ─── Line-level diff ─────────────────────────────────────────────────────────
// Not a true LCS; trimmed-text set membership is enough for short god.md files
// where additions are mostly whole-bullet writes. False-positives only happen
// when a bullet is moved unchanged; that's acceptable visual noise.
function computeDiff(prev, next) {
  const prevLines = (prev || '').split('\n')
  const nextLines = (next || '').split('\n')
  const prevSet = new Set(prevLines.map((l) => l.trim()).filter(Boolean))
  const nextSet = new Set(nextLines.map((l) => l.trim()).filter(Boolean))

  const added = new Set()
  for (const l of nextLines) {
    const t = l.trim()
    if (t && !prevSet.has(t)) added.add(t)
  }
  const removed = []
  for (const l of prevLines) {
    const t = l.trim()
    if (t && !nextSet.has(t)) removed.push(t)
  }
  return { added, removed }
}

// Context that carries the latest diff into the markdown renderer.
const DiffContext = createContext({ added: new Set(), removed: [] })

// ─── Panel ───────────────────────────────────────────────────────────────────

export default function GodFilesPanel({ agentStatuses, liveUpdate }) {
  const [activeAgent, setActiveAgent] = useState('router')
  const [godFiles, setGodFiles] = useState(EMPTY_BY_AGENT)
  const [diffs, setDiffs] = useState(EMPTY_DIFF_BY_AGENT)
  const [pulseActive, setPulseActive] = useState(FALSE_BY_AGENT)
  const changeCounter = useRef(0)
  const clearTimers = useRef({})

  // Initial fetch — diff against empty so nothing lights up on first load.
  useEffect(() => {
    AGENTS.forEach(({ key }) => {
      fetchGodFile(key).then((data) =>
        setGodFiles((prev) => ({ ...prev, [key]: data }))
      )
    })
  }, [])

  // Slow polling fallback — SSE pushes live updates via liveUpdate prop.
  useEffect(() => {
    const unsubscribers = AGENTS.map(({ key }) =>
      subscribeGodFile(
        key,
        (data) => {
          setGodFiles((prev) => {
            const prevData = prev[key]
            if (prevData && prevData.updatedAt !== data.updatedAt) {
              applyDiff(key, prevData.content, data.content)
            }
            return { ...prev, [key]: data }
          })
        },
        30000
      )
    )
    return () => unsubscribers.forEach((fn) => fn())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Real-time SSE push from /api/events.
  useEffect(() => {
    if (!liveUpdate || !liveUpdate.agent) return
    const { agent } = liveUpdate
    setGodFiles((prev) => {
      const prevData = prev[agent]
      const changed = !prevData || prevData.updatedAt !== liveUpdate.updatedAt
      if (changed) {
        applyDiff(agent, prevData?.content, liveUpdate.content)
      }
      return { ...prev, [agent]: liveUpdate }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveUpdate])

  const applyDiff = (agent, before, after) => {
    // Skip when there's no real "before" — we don't want every first fetch
    // to light up green on fresh page loads.
    if (!before) {
      setDiffs((d) => ({ ...d, [agent]: EMPTY_DIFF }))
      return
    }
    const { added, removed } = computeDiff(before, after)
    if (added.size === 0 && removed.length === 0) {
      setDiffs((d) => ({ ...d, [agent]: EMPTY_DIFF }))
      return
    }
    changeCounter.current += 1
    const changeId = changeCounter.current
    setDiffs((d) => ({ ...d, [agent]: { added, removed, changeId } }))
    setPulseActive((p) => ({ ...p, [agent]: true }))
    clearTimeout(clearTimers.current[`pulse:${agent}`])
    clearTimers.current[`pulse:${agent}`] = setTimeout(
      () => setPulseActive((p) => ({ ...p, [agent]: false })),
      2000
    )
    clearTimeout(clearTimers.current[`diff:${agent}`])
    clearTimers.current[`diff:${agent}`] = setTimeout(
      () => setDiffs((d) => ({ ...d, [agent]: EMPTY_DIFF })),
      DIFF_CLEAR_MS
    )
  }

  useEffect(() => () => {
    Object.values(clearTimers.current).forEach(clearTimeout)
  }, [])

  const active = godFiles[activeAgent]
  const activeDiff = diffs[activeAgent]

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
            <DiffBanner diff={activeDiff} />
            <DiffContext.Provider value={activeDiff}>
              {/* remount when a change arrives so CSS fade-in animates */}
              <GodFileContent
                key={`${activeAgent}-${activeDiff.changeId}`}
                content={active.content}
              />
            </DiffContext.Provider>
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

// ─── Change banner ───────────────────────────────────────────────────────────

function DiffBanner({ diff }) {
  const [showRemoved, setShowRemoved] = useState(false)
  const addedCount = diff.added?.size || 0
  const removedCount = diff.removed?.length || 0

  if (addedCount === 0 && removedCount === 0) return null

  return (
    <div className={styles.diffBanner}>
      <span className={styles.diffBannerPulse} />
      <span className={styles.diffBannerLabel}>just edited</span>
      {addedCount > 0 && (
        <span className={styles.diffBannerAdded}>+{addedCount}</span>
      )}
      {removedCount > 0 && (
        <button
          className={styles.diffBannerRemoved}
          onClick={() => setShowRemoved((s) => !s)}
          title="click to view removed lines"
        >
          −{removedCount}
        </button>
      )}
      {showRemoved && removedCount > 0 && (
        <ul className={styles.removedList}>
          {diff.removed.slice(0, 6).map((line, i) => (
            <li key={i} className={styles.removedLine}>
              {line}
            </li>
          ))}
          {removedCount > 6 && (
            <li className={styles.removedMore}>… +{removedCount - 6} more</li>
          )}
        </ul>
      )}
    </div>
  )
}

// ─── Content / sections ──────────────────────────────────────────────────────

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

// ─── Markdown renderer (with diff-aware block highlighting) ─────────────────

function extractText(node) {
  if (node == null || typeof node === 'boolean') return ''
  if (typeof node === 'string' || typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (node.props?.children) return extractText(node.props.children)
  return ''
}

function useIsAdded(children) {
  const diff = useContext(DiffContext)
  const text = useMemo(() => extractText(children).trim(), [children])
  if (!text || diff.added.size === 0) return false
  return diff.added.has(text)
}

function DiffAwareLi({ children, ...props }) {
  const isAdded = useIsAdded(children)
  return (
    <li
      className={`${styles.li} ${isAdded ? styles.liAdded : ''}`}
      {...props}
    >
      {children}
    </li>
  )
}

function DiffAwarePara({ children, ...props }) {
  const isAdded = useIsAdded(children)
  return (
    <p
      className={`${styles.para} ${isAdded ? styles.paraAdded : ''}`}
      {...props}
    >
      {children}
    </p>
  )
}

const MARKDOWN_COMPONENTS = {
  /* god.md uses ## often — that becomes <h2>; without overrides UA styles look like giant H1s. */
  h1: ({ node, ...props }) => <h1 className={styles.h1} {...props} />,
  h2: ({ node, ...props }) => <h2 className={styles.h2} {...props} />,
  p: ({ node, ...props }) => <DiffAwarePara {...props} />,
  strong: ({ node, ...props }) => <strong className={styles.strong} {...props} />,
  em: ({ node, ...props }) => <em className={styles.em} {...props} />,
  code: ({ node, inline, className, children, ...props }) =>
    inline === false ? (
      <pre className={styles.pre}>
        <code className={styles.codeBlock} {...props}>{children}</code>
      </pre>
    ) : (
      <code className={styles.code} {...props}>{children}</code>
    ),
  ul: ({ node, ...props }) => <ul className={styles.ul} {...props} />,
  ol: ({ node, ...props }) => <ol className={styles.ol} {...props} />,
  li: ({ node, ...props }) => <DiffAwareLi {...props} />,
  a: ({ node, ...props }) => (
    <a className={styles.link} target="_blank" rel="noreferrer" {...props} />
  ),
  h3: ({ node, ...props }) => <h3 className={styles.h3} {...props} />,
  h4: ({ node, ...props }) => <h4 className={styles.h4} {...props} />,
  h5: ({ node, ...props }) => <h5 className={styles.h4} {...props} />,
  h6: ({ node, ...props }) => <h6 className={styles.h4} {...props} />,
  blockquote: ({ node, ...props }) => (
    <blockquote className={styles.blockquote} {...props} />
  ),
  hr: () => <hr className={styles.hr} />,
}

function MarkdownBody({ text }) {
  return (
    <div className={styles.markdownBody}>
      <ReactMarkdown components={MARKDOWN_COMPONENTS}>{text}</ReactMarkdown>
    </div>
  )
}

// ─── misc ────────────────────────────────────────────────────────────────────

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
