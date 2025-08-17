"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { FiHome, FiClipboard, FiUsers, FiCheckSquare, FiLink, FiSettings, FiChevronLeft, FiChevronRight } from "react-icons/fi";

const navItems = [
  { label: "Home", icon: <FiHome />, path: "/" },
  { label: "Project Trackers", icon: <FiClipboard />, path: "/project_tracker" },
  { label: "Meetings", icon: <FiUsers />, path: "/meetings" },
  { label: "Action Items", icon: <FiCheckSquare />, path: "/action_items" },
  { label: "Integrate", icon: <FiLink />, path: "/integrations" },
];

export default function Sidebar() {
  const [selected, setSelected] = useState("Home");
  const [collapsed, setCollapsed] = useState(false);
  const router = useRouter();
  
  const handleNav = (item) => {
    setSelected(item.label);
    router.push(item.path);
  };

  const handleSettings = () => {
    setSelected("Settings");
    router.push("/settings");
  };

  return (
    <aside
      className={`bg-white border-r p-3 flex flex-col h-full transition-all duration-200 ${
        collapsed ? "w-20" : "w-56"
      }`}
    >
      {/* Logo Section */}
      <div className={`mb-4 flex items-center justify-center h-16 ${collapsed ? "px-0" : "px-2"}`}>
        {!collapsed ? (
          <span className="font-bold text-xl text-blue-600">LOGO</span>
        ) : (
          <span className="font-bold text-xl text-blue-600">L</span>
        )}
      </div>

      {/* Collapse Button */}
      <button
        className="mb-2 self-end text-gray-400 hover:text-blue-500 transition"
        onClick={() => setCollapsed((c) => !c)}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? <FiChevronRight size={20} /> : <FiChevronLeft size={20} />}
      </button>

      {/* Navigation - This will take up available space */}
      <nav className="space-y-2 flex-1">
        {navItems.map((item) => (
          <button
            key={item.label}
            className={`flex items-center w-full px-3 py-2 rounded-md text-sm transition
              ${selected === item.label ? "bg-blue-500 text-white" : "text-gray-700 hover:bg-gray-100"}
              ${collapsed ? "justify-center" : ""}
            `}
            onClick={() => handleNav(item)}
          >
            <span className="mr-2 text-lg">{item.icon}</span>
            {!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Settings at the bottom - This will stick to the bottom */}
      <div className="mt-auto border-t border-gray-200 pt-3">
        <button
          className={`flex items-center w-full px-3 py-2 rounded-md text-sm transition
            ${selected === "Settings" ? "bg-blue-500 text-white" : "text-gray-700 hover:bg-gray-100"}
            ${collapsed ? "justify-center" : ""}
          `}
          onClick={handleSettings}
        >
          <span className="mr-2 text-lg">
            <FiSettings />
          </span>
          {!collapsed && <span>Settings</span>}
        </button>
      </div>
    </aside>
  );
}