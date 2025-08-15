export default function MeetingCard({ title, date, description }) {
  return (
    <div className="bg-white p-4 rounded-lg border mb-3 shadow-sm">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold">{title}</h3>
        <span className="text-gray-400 text-sm">{date}</span>
      </div>
      <p className="text-gray-500 text-sm mb-2">{description}</p>
      <div className="flex space-x-2">
        <button className="px-3 py-1 text-blue-500 border border-blue-500 rounded-full text-sm">
          3 Action Items
        </button>
        <button className="px-3 py-1 text-gray-500 border rounded-full text-sm">
          Transcript
        </button>
      </div>
    </div>
  );
}
