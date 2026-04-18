// TODO(backend): replace mock data + endpoints once backend is live

const BASE_URL = '/api'

// ─── Chat ────────────────────────────────────────────────────────────────────

/**
 * Send a message to the coordinator (router) agent and stream the response.
 * TODO(backend): POST /api/chat { message, conversation_id }
 * Expected SSE stream: { type: 'delta'|'done'|'error', content: string }
 */
export async function sendMessage(message, conversationId, onDelta, onDone, onError) {
  // TODO(backend): implement real SSE streaming from coordinator
  const mockReply = await mockCoordinatorReply(message)
  simulateStream(mockReply, onDelta, onDone)
}

/**
 * TODO(backend): GET /api/chat/history?conversation_id=...
 */
export async function fetchChatHistory(conversationId) {
  // TODO(backend): return persisted conversation history
  return []
}

// ─── Roadmap ─────────────────────────────────────────────────────────────────

/**
 * TODO(backend): GET /api/roadmap
 * Returns parsed roadmap items grouped by status column.
 */
export async function fetchRoadmap() {
  // TODO(backend): parse state/roadmap.md and return structured data
  return MOCK_ROADMAP
}

// ─── God Files ───────────────────────────────────────────────────────────────

/**
 * TODO(backend): GET /api/god/:agent
 * agent: 'product' | 'marketing' | 'finance'
 * Returns { content: string (raw markdown), updatedAt: ISO string }
 */
export async function fetchGodFile(agent) {
  // TODO(backend): read workspaces/<agent>/memory/god.md and return
  return MOCK_GOD_FILES[agent]
}

/**
 * TODO(backend): GET /api/god/:agent/stream (SSE)
 * Real-time updates when god.md changes (file watch on backend).
 * For now, poll fetchGodFile on an interval.
 */
export function subscribeGodFile(agent, onUpdate, intervalMs = 5000) {
  // TODO(backend): replace polling with SSE subscription
  const id = setInterval(async () => {
    const data = await fetchGodFile(agent)
    onUpdate(data)
  }, intervalMs)
  return () => clearInterval(id)
}

// ─── Coordinator status ───────────────────────────────────────────────────────

/**
 * TODO(backend): GET /api/status
 * Returns { coordinator: 'online'|'offline', agents: { product, marketing, finance } }
 */
export async function fetchSystemStatus() {
  // TODO(backend): return live agent status from orchestrator
  return {
    coordinator: 'online',
    agents: {
      product: 'online',
      marketing: 'online',
      finance: 'online',
    },
  }
}

// ─── Mock helpers (remove when backend is live) ───────────────────────────────

async function mockCoordinatorReply(message) {
  const lower = message.toLowerCase()
  if (lower.includes('roadmap')) {
    return `I've checked in with the **Product** agent about the roadmap. Currently everything is in the planning stage — no items have been promoted to *in-progress* yet.\n\nWould you like me to ask Product to draft the first items based on your priorities?`
  }
  if (lower.includes('market') || lower.includes('campaign')) {
    return `I'll loop in **Marketing**. Based on the current roadmap state, there isn't a live campaign yet. Marketing is ready to draft positioning once the core product decisions are locked.\n\nShall I ask Marketing to sketch an initial campaign brief?`
  }
  if (lower.includes('financ') || lower.includes('runway') || lower.includes('money')) {
    return `Reaching out to **Finance** now. Projections depend on the roadmap scope — once Product finalises the next sprint, Finance can model burn and runway.\n\nDo you want a rough projection based on assumptions, or wait for the roadmap to stabilise first?`
  }
  return `Understood. I'm the coordinator for the gooning company — I route your intent to **Product**, **Marketing**, and **Finance** and broker the cascades between them.\n\nWhat would you like to work on today?`
}

function simulateStream(text, onDelta, onDone) {
  const words = text.split(' ')
  let i = 0
  const tick = () => {
    if (i >= words.length) {
      onDone()
      return
    }
    const chunk = (i === 0 ? '' : ' ') + words[i]
    onDelta(chunk)
    i++
    setTimeout(tick, 30 + Math.random() * 40)
  }
  setTimeout(tick, 200)
}

// ─── Mock data ────────────────────────────────────────────────────────────────

const MOCK_ROADMAP = {
  backlog: [
    { id: 'P-001', title: 'Define core user persona', domain: 'product', owner: 'product', notes: 'Who hurts most without this?' },
    { id: 'M-001', title: 'Brand positioning document', domain: 'marketing', owner: 'marketing', notes: 'Depends on P-001 persona' },
    { id: 'F-001', title: 'Unit economics baseline', domain: 'finance', owner: 'finance', notes: 'Need pricing model input from product' },
  ],
  next: [
    { id: 'P-002', title: 'MVP feature scope', domain: 'product', owner: 'product', notes: 'Freeze scope before marketing drafts campaign' },
  ],
  'in-progress': [],
  blocked: [],
  done: [],
}

const MOCK_GOD_FILES = {
  product: {
    content: `# god.md — product

## Current worldview
No active user research sessions yet. The company is pre-launch — founder is the primary signal source. Next 30 days shape: lock MVP scope, identify one high-pain persona, draft the first roadmap items.

## Open product questions
- Who is the primary user? Founder-first or end-customer-first?
- What is the smallest thing that proves value?
- Should the roadmap be public or internal-only?

## Roadmap reasoning log
- *(no entries yet — roadmap is blank)*

## Signals from other functions
- Finance is waiting on pricing model before running projections.
- Marketing is ready to draft positioning once persona is confirmed.`,
    updatedAt: new Date(Date.now() - 4 * 60 * 1000).toISOString(),
  },
  marketing: {
    content: `# god.md — marketing

## Positioning (current)
No positioning drafted yet. Waiting for the product persona to be confirmed by the Product agent before writing the core promise.

## Campaigns in flight
*(none — pre-launch)*

## Signals from other functions
- Product has flagged that persona definition is in backlog (P-001).
- Will draft initial positioning once P-001 is resolved.

## Open questions for the founder
- What channels are you most comfortable with? (Content, paid, community, cold outreach?)
- Do we have a budget ceiling for the first campaign?`,
    updatedAt: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
  },
  finance: {
    content: `# god.md — finance

## Projection assumptions (current)
- Revenue model: TBD (waiting on product pricing decision)
- Cost structure: minimal — founder-run, no employees
- Hiring plan: none in the next 90 days

## Last projection snapshot
*(no snapshot yet — awaiting product scope and pricing model)*

## Signals from other functions
- Product: MVP scope not finalised; cannot model revenue until then.
- Marketing: no campaign spend planned yet; burn is currently near-zero.

## Open questions for the founder
- What is your current runway (months)?
- Is there a target MRR milestone that changes hiring intent?`,
    updatedAt: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
  },
}
