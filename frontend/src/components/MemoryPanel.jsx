export default function MemoryPanel({ notesCount }) {
  return (
    <section className="memory-panel">
      <h2>On-Device Memory</h2>
      <div className="memory-stats">
        <span className="memory-count">{notesCount}</span>
        <span className="memory-label">note{notesCount === 1 ? '' : 's'} stored locally</span>
      </div>
      <p className="memory-desc">All data stays on your device — no cloud, no internet required.</p>
    </section>
  )
}
