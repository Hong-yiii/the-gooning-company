import { useState, useEffect } from 'react'
import ChatPanel from './components/ChatPanel'
import RoadmapPanel from './components/RoadmapPanel'
import GodFilesPanel from './components/GodFilesPanel'
import CascadePanel from './components/CascadePanel'
import { fetchSystemStatus, subscribeEvents } from './api/index'
import styles from './App.module.css'

export default function App() {
  const [status, setStatus] = useState({
    coordinator: 'connecting',
    agents: {},
    model: null,
  })
  const [liveRoadmap, setLiveRoadmap] = useState(null)
  const [liveGod, setLiveGod] = useState(null)
  const [liveCascade, setLiveCascade] = useState(null)
  const [streamState, setStreamState] = useState('connecting')

  useEffect(() => {
    fetchSystemStatus().then(setStatus)
    const id = setInterval(() => fetchSystemStatus().then(setStatus), 15000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    const unsubscribe = subscribeEvents({
      onOpen: () => setStreamState('live'),
      onRoadmap: (cols) => setLiveRoadmap(cols),
      onGod: (payload) => setLiveGod(payload),
      onCascade: (events) => setLiveCascade(events),
      onError: () => setStreamState('reconnecting'),
    })
    return unsubscribe
  }, [])

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.logoMark} />
          <span className={styles.companyName}>the gooning company</span>
          {status.model && (
            <span className={styles.modelBadge}>{status.model}</span>
          )}
        </div>
        <div className={styles.headerRight}>
          <StreamBadge state={streamState} />
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

        <div className={styles.centerColumn}>
          <RoadmapPanel liveColumns={liveRoadmap} />
          <CascadePanel events={liveCascade} />
        </div>

        <GodFilesPanel agentStatuses={status.agents} liveUpdate={liveGod} />
      </main>
    </div>
  )
}

function StreamBadge({ state }) {
  const isLive = state === 'live'
  return (
    <div className={styles.streamBadge} title={`event stream: ${state}`}>
      <span
        className={`${styles.streamDot} ${
          isLive ? styles.streamLive : styles.streamDown
        }`}
      />
      <span className={styles.streamLabel}>{isLive ? 'live' : state}</span>
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
