import { useState, useEffect } from 'react'
import ChatPanel from './components/ChatPanel'
import RoadmapPanel from './components/RoadmapPanel'
import GodFilesPanel from './components/GodFilesPanel'
import { fetchSystemStatus } from './api/index'
import styles from './App.module.css'

export default function App() {
  const [status, setStatus] = useState({ coordinator: 'connecting', agents: {} })

  useEffect(() => {
    fetchSystemStatus().then(setStatus)
    const id = setInterval(() => fetchSystemStatus().then(setStatus), 15000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.logoMark} />
          <span className={styles.companyName}>the gooning company</span>
        </div>
        <div className={styles.headerRight}>
          <AgentPips agents={status.agents} />
          <div className={styles.coordinatorStatus}>
            <span
              className={`${styles.statusDot} ${
                status.coordinator === 'online' ? styles.dotOnline : styles.dotOffline
              }`}
            />
            <span className={styles.statusLabel}>coordinator</span>
          </div>
        </div>
      </header>

      <main className={styles.main}>
        <ChatPanel />
        <RoadmapPanel />
        <GodFilesPanel agentStatuses={status.agents} />
      </main>
    </div>
  )
}

function AgentPips({ agents }) {
  const agentList = ['product', 'marketing', 'finance']
  return (
    <div className={styles.agentPips}>
      {agentList.map((a) => (
        <div key={a} className={styles.agentPip}>
          <span
            className={`${styles.statusDot} ${
              agents[a] === 'online' ? styles.dotOnline : styles.dotOffline
            }`}
          />
          <span className={styles.agentPipLabel}>{a}</span>
        </div>
      ))}
    </div>
  )
}
