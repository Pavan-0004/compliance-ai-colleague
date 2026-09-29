export default function TranscriptFeed({ log }) {
  if (!log || log.length === 0) {
    return <section className="transcript-feed empty">No conversation yet.</section>
  }

  return (
    <section className="transcript-feed">
      <h2>Conversation</h2>
      <ul>
        {log
          .slice()
          .reverse()
          .map((entry, i) => (
            <li key={i}>
              <div className="entry-user">You: {entry.user}</div>
              <div className="entry-assistant">Colleague: {entry.assistant}</div>
            </li>
          ))}
      </ul>
    </section>
  )
}
