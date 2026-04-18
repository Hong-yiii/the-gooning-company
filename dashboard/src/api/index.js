// Thin client against the Python dashboard backend (see dashboard_backend/app.py).
//
// Contract:
//   GET  /api/status              -> { coordinator, agents, model, mcp }
//   GET  /api/roadmap             -> { columns, total, path }
//   GET  /api/god/:agent          -> { agent, content, updatedAt }
//   GET  /api/cascade?limit=N     -> { events, path }
//   GET  /api/events  (SSE)       -> multiplexed updates on roadmap/god/cascade
//   POST /api/chat                -> SSE stream of delta/log/done/error events

const BASE_URL = '/api'

// ─── Chat ────────────────────────────────────────────────────────────────────

/**
 * POST /api/chat { message } and stream the router reply back.
 *
 * The backend spawns `ohmo --print` per message and pushes stdout chunks
 * over SSE. We translate SSE events into the same (onDelta, onDone, onError)
 * shape the UI was built against, so no component changes are needed.
 */
export async function sendMessage(message, conversationId, onDelta, onDone, onError) {
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    })

    if (!response.ok || !response.body) {
      const text = await response.text().catch(() => '')
      onError(new Error(`chat HTTP ${response.status}: ${text || 'no body'}`))
      return
    }

    await consumeSSE(response.body, (event, data) => {
      switch (event) {
        case 'start':
          // no-op — UI already pushed the optimistic assistant bubble
          break
        case 'delta':
          onDelta(typeof data === 'string' ? data : String(data))
          break
        case 'log':
          // Surface stderr/log lines quietly — noisy but useful.
          // Keep in console so founders don't see tool chatter inline.
          // eslint-disable-next-line no-console
          console.debug('[router]', typeof data === 'string' ? data.trim() : data)
          break
        case 'done':
          onDone()
          break
        case 'error':
          onError(new Error(data?.error || 'unknown chat error'))
          break
        default:
          break
      }
    })
  } catch (err) {
    onError(err)
  }
}

/**
 * Not implemented server-side yet: the backend does not persist chat
 * history. Each turn is a fresh `ohmo --print`, so reload => empty chat.
 * Leaving the signature stable for future upgrade.
 */
export async function fetchChatHistory(_conversationId) {
  return []
}

// ─── Roadmap ─────────────────────────────────────────────────────────────────

export async function fetchRoadmap() {
  const response = await fetch(`${BASE_URL}/roadmap`)
  if (!response.ok) throw new Error(`roadmap HTTP ${response.status}`)
  const data = await response.json()
  return data.columns
}

// ─── God files ───────────────────────────────────────────────────────────────

export async function fetchGodFile(agent) {
  const response = await fetch(`${BASE_URL}/god/${agent}`)
  if (!response.ok) throw new Error(`god/${agent} HTTP ${response.status}`)
  return response.json()
}

/**
 * Poll god file on an interval. When the SSE stream is healthy,
 * RoadmapPanel / GodFilesPanel will also receive push updates via
 * subscribeEvents(); this polling fallback keeps things correct if
 * the SSE socket drops.
 */
export function subscribeGodFile(agent, onUpdate, intervalMs = 5000) {
  const id = setInterval(async () => {
    try {
      const data = await fetchGodFile(agent)
      onUpdate(data)
    } catch {
      // swallow — next tick will retry
    }
  }, intervalMs)
  return () => clearInterval(id)
}

// ─── Cascade trace ──────────────────────────────────────────────────────────

export async function fetchCascade(limit = 200) {
  const response = await fetch(`${BASE_URL}/cascade?limit=${limit}`)
  if (!response.ok) throw new Error(`cascade HTTP ${response.status}`)
  const data = await response.json()
  return data.events
}

// ─── Status ─────────────────────────────────────────────────────────────────

export async function fetchSystemStatus() {
  try {
    const response = await fetch(`${BASE_URL}/status`)
    if (!response.ok) throw new Error(`status HTTP ${response.status}`)
    return response.json()
  } catch {
    return {
      coordinator: 'offline',
      agents: { product: 'offline', marketing: 'offline', finance: 'offline' },
    }
  }
}

// ─── Multiplexed live events ─────────────────────────────────────────────────

/**
 * Subscribe to the multiplexed SSE stream at /api/events.
 *
 * The backend emits:
 *   event: ready        — handshake
 *   event: roadmap      — { columns, ... } (full snapshot)
 *   event: god          — { agent, content, updatedAt }
 *   event: cascade      — [ ... trace events ] (tail)
 *
 * Returns an unsubscribe fn. EventSource handles reconnect automatically.
 */
export function subscribeEvents(handlers) {
  const es = new EventSource(`${BASE_URL}/events`)
  if (handlers.onRoadmap) {
    es.addEventListener('roadmap', (e) => {
      try {
        const payload = JSON.parse(e.data)
        handlers.onRoadmap(payload.backlog ? payload : payload.columns ?? payload)
      } catch {}
    })
  }
  if (handlers.onGod) {
    es.addEventListener('god', (e) => {
      try {
        handlers.onGod(JSON.parse(e.data))
      } catch {}
    })
  }
  if (handlers.onCascade) {
    es.addEventListener('cascade', (e) => {
      try {
        handlers.onCascade(JSON.parse(e.data))
      } catch {}
    })
  }
  if (handlers.onOpen) {
    es.addEventListener('ready', () => handlers.onOpen())
  }
  if (handlers.onError) {
    es.onerror = (err) => handlers.onError(err)
  }
  return () => es.close()
}

// ─── SSE helper ─────────────────────────────────────────────────────────────

/**
 * Consume an SSE body from a fetch POST response. EventSource only
 * supports GET; for POST we parse the stream manually. Handles the
 * canonical "event: X\ndata: Y\n\n" framing.
 */
async function consumeSSE(body, onEvent) {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let sep
    while ((sep = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      parseFrame(frame, onEvent)
    }
  }
  if (buffer.trim()) parseFrame(buffer, onEvent)
}

function parseFrame(frame, onEvent) {
  let event = 'message'
  const dataLines = []
  for (const line of frame.split('\n')) {
    if (!line || line.startsWith(':')) continue
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''))
  }
  const raw = dataLines.join('\n')
  let parsed = raw
  try {
    parsed = JSON.parse(raw)
  } catch {
    // leave as string (delta chunks are plain text)
  }
  onEvent(event, parsed)
}
