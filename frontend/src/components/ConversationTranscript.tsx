import type { MessageOut } from "../api/client";

export default function ConversationTranscript({ messages }: { messages: MessageOut[] }) {
  if (messages.length === 0) {
    return <p className="empty-state">Nessun messaggio.</p>;
  }

  return (
    <div className="transcript">
      {messages.map((message, index) => (
        <div key={index} className={`bubble bubble-${message.role}`}>
          <div className="bubble-content">{message.content}</div>
          <div className="bubble-time">
            {new Date(message.created_at).toLocaleString("it-IT")}
          </div>
        </div>
      ))}
    </div>
  );
}
