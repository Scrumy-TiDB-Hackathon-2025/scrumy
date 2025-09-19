import { FiSearch } from 'react-icons/fi';
import { IoMdNotificationsOutline } from 'react-icons/io';
import { FaUserCircle } from 'react-icons/fa';

export default function Topbar() {
  return (
    <header className="flex justify-between items-center px-6 py-4 border-b bg-white">
      {/* Transparent rounded search bar with icon */}
      <div className="relative w-1/3">
        <input
          type="text"
          placeholder="Search meetings, action items, project..."
          className="pl-10 pr-4 py-2 w-full rounded-full bg-transparent border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-200"
        />
        <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-lg" />
        </div>   
        <div className="flex items-center space-x-6">
        {/* Notification icon */}
        <button className="relative">
          <IoMdNotificationsOutline className="text-2xl text-gray-600" />
          <span className="absolute -top-1 -right-2 bg-red-500 text-white text-xs px-1 rounded-full">
            2
          </span>
        </button>
        {/* Profile icon and name */}
        <div className="flex items-center space-x-2">
          <FaUserCircle className="text-3xl text-gray-400" />
          <span className="text-gray-700 font-medium">John Doe</span>
        </div>
      </div>
    </header>
  );
}