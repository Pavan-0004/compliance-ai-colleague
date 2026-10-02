// Linear pipeline — 5 steps for the common flow
// online_lookup is a rare sub-step shown only in the header, not the pipeline
const STAGES = [
  { key: 'waiting_for_wake', label: 'Wake Word',  icon: '👂' },
  { key: 'listening',        label: 'Listening',  icon: '🎙️' },
  { key: 'transcribing',     label: 'Transcribe', icon: '📝' },
  { key: 'thinking',         label: 'Reasoning',  icon: '🧠' },
  { key: 'speaking',         label: 'Speaking',   icon: '🔊' },
]

// Maps any backend stage to its pipeline position
const STAGE_POS = {
  waiting_for_wake: 0,
  listening:        1,
  transcribing:     2,
  thinking:         3,
  online_lookup:    3,   // treat as same position as thinking
  speaking:         4,
  follow_up:        -1,  // not in linear flow
  muted:            -1,
  idle:             -1,
}

const STAGE_COLORS = {
  waiting_for_wake: '#2980b9',
  listening:        '#2ecc71',
  transcribing:     '#3498db',
  thinking:         '#9b59b6',
  online_lookup:    '#e67e22',
  speaking:         '#1abc9c',
  follow_up:        '#27ae60',
  muted:            '#e74c3c',
}

const STAGE_DESC = {
  waiting_for_wake: 'Say "Hey Jarvis"',
  listening:        'Listening…',
  transcribing:     'Transcribing your speech…',
  thinking:         'On-device reasoning…',
  online_lookup:    'Fetching live data…',
  speaking:         'Playing response…',
  follow_up:        'Ask a follow-up question…',
  muted:            'Microphone muted',
}

const BAR_COUNT = 14

function AudioBars({ energy }) {
  const level = Math.min(energy * 40, 1)
  return (
    <div className="audio-bars">
      {Array.from({ length: BAR_COUNT }).map((_, i) => {
        const threshold = (i + 1) / BAR_COUNT
        const active = level >= threshold
        const mid = BAR_COUNT / 2
        const heightPct = 25 + 75 * (1 - Math.abs(i - mid) / mid)
        return (
          <div
            key={i}
            className={`audio-bar ${active ? 'active' : ''}`}
            style={{ height: `${active ? heightPct : 15}%` }}
          />
        )
      })}
    </div>
  )
}

export default function StatusDashboard({ state, onToggleMute }) {
  const stage = state.stage ?? 'idle'
  const isMuted = state.muted || stage === 'muted'
  const isFollowUp = stage === 'follow_up'
  const isOnline = stage === 'online_lookup'
  const isListening = stage === 'listening' || stage === 'follow_up'

  const activePos = STAGE_POS[stage] ?? -1
  const color = STAGE_COLORS[stage] ?? '#555'
  const desc = isMuted ? '🔇 Microphone Muted' : (STAGE_DESC[stage] ?? stage)

  return (
    <div className="dashboard">

      {/* ── Header ── */}
      <div className="dash-header">
        <div className="dash-title">
          <div className={`big-dot stage-${stage}`} />
          <div>
            <div className="big-stage-label">{desc}</div>
            {isOnline && state.last_online_query && (
              <div className="online-badge">🌐 Querying: "{state.last_online_query}"</div>
            )}
          </div>
        </div>
        <button className={`mute-btn ${isMuted ? 'muted' : ''}`} onClick={onToggleMute}>
          {isMuted ? '🔈 Unmute' : '🔇 Mute (F9)'}
        </button>
      </div>

      {/* ── Pipeline ── */}
      {!isMuted && (
        <div className="pipeline-row">
          {STAGES.map((s, i) => {
            const pos = STAGE_POS[s.key]
            const isActive = activePos === pos && !isFollowUp
            const isDone  = activePos > pos && !isFollowUp
            const c = STAGE_COLORS[s.key]
            return (
              <div className="pipeline-step-wrap" key={s.key}>
                <div
                  className={`pipeline-step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}
                  style={isActive ? { borderColor: c, background: c + '22' } : isDone ? { borderColor: c + '55' } : {}}
                >
                  <span className="step-icon">{s.icon}</span>
                  <span className="step-label" style={isDone ? { color: c } : {}}>{s.label}</span>
                  {isActive && <span className="step-dot" style={{ background: c }} />}
                  {isDone  && <span className="step-check">✓</span>}
                </div>
                {i < STAGES.length - 1 && (
                  <div
                    className={`pipeline-arrow ${isDone || isActive ? 'lit' : ''}`}
                    style={isDone || isActive ? { color: c } : {}}
                  >→</div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* ── Follow-up banner ── */}
      {isFollowUp && !isMuted && (
        <div className="followup-banner">
          <span className="followup-icon">💬</span>
          <span className="followup-text">Conversation continues — ask a follow-up, no wake word needed</span>
        </div>
      )}

      {/* ── Live mic bars ── */}
      {isListening && !isMuted && (
        <div className="live-mic-row">
          <span className="live-mic-label">🎙️ Live mic</span>
          <AudioBars energy={state.mic_energy ?? 0} />
        </div>
      )}

      {/* ── What you said ── */}
      {state.last_transcript && (
        <div className="transcript-box">
          <span className="transcript-label">You said</span>
          <span className="transcript-text">"{state.last_transcript}"</span>
        </div>
      )}

      {/* ── Transcribing hint ── */}
      {stage === 'transcribing' && !state.last_transcript && (
        <div className="transcript-box transcribing-hint">
          <span className="transcript-label">Transcribing</span>
          <span className="transcript-text">Processing your speech<span className="dot-anim">…</span></span>
        </div>
      )}

      {/* ── Jarvis reply ── */}
      {state.last_reply && (
        <div className="reply-box">
          <span className="reply-label-tag">Jarvis replied</span>
          <span className="reply-text">{state.last_reply}</span>
        </div>
      )}
    </div>
  )
}
