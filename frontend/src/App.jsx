import { useAppState } from './hooks/useAppState.js'
import StatusDashboard from './components/StatusDashboard.jsx'
import TranscriptFeed from './components/TranscriptFeed.jsx'
import MemoryPanel from './components/MemoryPanel.jsx'

export default function App() {
  const { state, connected, toggleMute } = useAppState()

  return (
    <div className="app">
      <header className="app-header">
        <h1>Compliance-Safe AI Colleague</h1>
        <span className={`conn-dot ${connected ? 'connected' : 'disconnected'}`} title={connected ? 'Connected to backend' : 'Disconnected'} />
      </header>

      {!state ? (
        <p className="waiting">Waiting for backend at ws://127.0.0.1:8000/ws ...</p>
      ) : (
        <main className="app-main">
          <StatusDashboard state={state} onToggleMute={toggleMute} />
          <TranscriptFeed log={state.transcript_log} />
          <MemoryPanel notesCount={state.notes_count} />
        </main>
      )}
    </div>
  )
}
