import { useAppState } from './hooks/useAppState.js'
import StatusDashboard from './components/StatusDashboard.jsx'
import TranscriptFeed from './components/TranscriptFeed.jsx'
import MemoryPanel from './components/MemoryPanel.jsx'

export default function App() {
  const { state, connected, toggleMute } = useAppState()

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-brand">
          <h1>Jarvis</h1>
          <span className="app-sub">Personal AI Companion &nbsp;·&nbsp; 100% On-Device</span>
        </div>
        <span
          className={`conn-dot ${connected ? 'connected' : 'disconnected'}`}
          title={connected ? 'Backend connected' : 'Backend disconnected'}
        />
      </header>

      {!state ? (
        <p className="waiting">Connecting to backend…</p>
      ) : (
        <main className="app-main">
          <StatusDashboard state={state} onToggleMute={toggleMute} />
          <TranscriptFeed log={state.transcript_log} />
          <MemoryPanel notesCount={state.notes_count ?? 0} />
        </main>
      )}
    </div>
  )
}
