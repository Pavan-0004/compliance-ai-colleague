const STAGE_LABELS = {
  idle: 'Idle',
  listening: 'Listening',
  muted: 'Muted',
  transcribing: 'Transcribing audio to text',
  thinking: 'Reasoning on-device',
  online_lookup: 'Online factual lookup',
  speaking: 'Replying',
}

export default function StatusDashboard({ state, onToggleMute }) {
  const stage = state.stage

  return (
    <section className="status-card">
      <div className={`indicator-light stage-${stage}`} />
      <div className="status-text">
        <div className="stage-label">{STAGE_LABELS[stage] || stage}</div>
        {stage === 'online_lookup' && state.last_online_query && (
          <div className="online-badge">Network call for: &quot;{state.last_online_query}&quot;</div>
        )}
        {state.last_transcript && <div className="last-transcript">Heard: &quot;{state.last_transcript}&quot;</div>}
      </div>
      <button className={`mute-btn ${state.muted ? 'muted' : ''}`} onClick={onToggleMute}>
        {state.muted ? 'Unmute' : 'Mute'}
      </button>
    </section>
  )
}
