export default function ChatSection() {
  return (
    <div className="bg-white p-4 rounded-lg border h-full flex flex-col shadow-sm">
      <h2 className="font-semibold mb-4">ScrumAI Chat</h2>

      <div className="space-y-4 flex-1 overflow-y-auto">
        <div className="self-end bg-blue-500 text-white px-4 py-2 rounded-lg w-fit">
          Can you summarize today's standup?
        </div>
        <div className="bg-gray-100 p-3 rounded-lg">
          Today's standup covered sprint progress updates...
        </div>
        <div className="self-end bg-blue-500 text-white px-4 py-2 rounded-lg w-fit">
          What are the main blockers?
        </div>
        <div className="bg-gray-100 p-3 rounded-lg">
          The main blocker is the payment API access...
        </div>
      </div>

      <div className="flex items-center mt-4">
        <input
          type="text"
          placeholder="Ask Scrum AI"
          className="flex-1 border rounded-lg px-4 py-2"
        />
        <button className="ml-2 px-4 py-2 bg-blue-500 text-white rounded-lg">
          🎤
        </button>
      </div>
    </div>
  );
}
