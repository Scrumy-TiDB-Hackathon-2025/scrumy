export default function Sidebar() {
  return (
    <aside className="w-56 bg-white border-r p-4 flex flex-col">
      <nav className="space-y-4">
        <button className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg">
          Home
        </button>
        <button className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
          Project Trackers
        </button>
        <button className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
          Meetings
        </button>
        <button className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
          Action Items
        </button>
        <button className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
          Integrate
        </button>
      </nav>
      <div className="mt-auto">
        <button className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
          Settings
        </button>
      </div>
    </aside>
  );
}
