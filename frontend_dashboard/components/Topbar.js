export default function Topbar() {
  return (
    <header className="flex justify-between items-center px-6 py-4 border-b bg-white">
      <input
        type="text"
        placeholder="Search meetings, action items, project..."
        className="px-4 py-2 border rounded-lg w-1/3"
      />
      <div className="flex items-center space-x-4">
        <button className="relative">
          🔔
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs px-1 rounded-full">
            2
          </span>
        </button>
        <div className="flex items-center space-x-2">
          <span className="bg-gray-300 w-8 h-8 rounded-full flex items-center justify-center">
            A
          </span>
          <span>John Doe</span>
        </div>
        <button className="bg-blue-500 text-white px-4 py-2 rounded-lg">
          Add to live meeting
        </button>
      </div>
    </header>
  );
}
