export default function MemoryPanel({ notesCount }) {
  return (
    <section className="memory-panel">
      <h2>Local Memory</h2>
      <p>
        {notesCount} note{notesCount === 1 ? '' : 's'} stored on-device
      </p>
    </section>
  )
}
