'use client';

import { useState } from 'react';
import { Plus, Filter } from 'lucide-react';

export default function ProjectTracker() {
  const [tasks] = useState({
    todo: [{ id: 1, title: 'Create' }],
    inProgress: [
      { id: 2, title: 'UI/UX | Recreate the Onboarding flow Mellypay (from Opay, Monipoint, etc)', project: 'Project 1', code: 'Pro-1920' },
      { id: 3, title: 'UI/UX | Recreate the Onboarding flow Mellypay (from Opay, Monipoint, etc)', project: 'Project 1', code: 'Pro-1920' },
    ],
    blocked: [],
    review: [
      { id: 4, title: 'UI/UX | Recreate the Onboarding flow Mellypay (from Opay, Monipoint, etc)', project: 'Project 1', code: 'Pro-1920' },
    ],
    done: [
      { id: 5, title: 'UI/UX | Recreate the Onboarding flow Mellypay (from Opay, Monipoint, etc)', project: 'Project 1', code: 'Pro-1920' },
      { id: 6, title: 'UI/UX | Recreate the Onboarding flow Mellypay (from Opay, Monipoint, etc)', project: 'Project 1', code: 'Pro-1920' },
      { id: 7, title: 'UI/UX | Recreate the Onboarding flow Mellypay (from Opay, Monipoint, etc)', project: 'Project 1', code: 'Pro-1920' },
      { id: 8, title: 'UI/UX | Recreate the Onboarding flow Mellypay (from Opay, Monipoint, etc)', project: 'Project 1', code: 'Pro-1920' },
    ],
  });

  const columns = [
    { key: 'todo', title: 'To Do' },
    { key: 'inProgress', title: 'In-Progress' },
    { key: 'blocked', title: 'Blocked' },
    { key: 'review', title: 'Review' },
    { key: 'done', title: 'Done' },
  ];

  return (
    <div className="w-full px-6 py-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Project Trackers</h1>
          <p className="text-gray-500 text-sm">Monitor sprint progress and team tasks</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-gray-700 hover:bg-gray-200 text-sm font-medium">
            <Filter size={16} /> Filter
          </button>
          <button className="flex items-center gap-2 px-3 py-2 bg-blue-600 rounded-lg text-white hover:bg-blue-700 text-sm font-medium">
            <Plus size={16} /> New Task
          </button>
        </div>
      </div>

      {/* Board */}
      <div className="flex gap-4 overflow-x-auto">
        {columns.map((col) => (
          <div key={col.key} className="flex-1 bg-white border border-gray-200 rounded-lg p-3 min-w-[220px]">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-gray-800 text-sm">{col.title}</h2>
              <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">
                {tasks[col.key].length}
              </span>
            </div>

            <div className="space-y-3">
              {tasks[col.key].map((task) => (
                <div key={task.id} className="border border-gray-200 rounded-lg p-3 bg-white shadow-sm hover:shadow-md transition">
                  <p className="text-sm text-gray-800 mb-2">{task.title}</p>
                  {task.project && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-medium">
                      {task.project}
                    </span>
                  )}
                  {task.code && <p className="text-xs text-gray-500 mt-1">{task.code}</p>}
                </div>
              ))}

              {/* Special create button for To Do */}
              {col.key === 'todo' && (
                <button className="flex items-center justify-center w-full border border-dashed border-gray-300 rounded-lg py-6 text-gray-500 hover:text-gray-700 hover:border-gray-400 text-sm font-medium">
                  <Plus size={16} className="mr-2" /> Create
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
