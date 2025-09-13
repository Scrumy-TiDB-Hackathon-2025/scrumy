'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/lib/api';

const ActionItemsPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterOpen, setFilterOpen] = useState(false);
  const [showApproveAllModal, setShowApproveAllModal] = useState(false);
  const [actionItems, setActionItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Calculate stats from real data
  const statsData = {
    totalActionItems: actionItems.length,
    pendingApproval: actionItems.filter(item => item.status === 'pending').length,
    inProgress: actionItems.filter(item => item.status === 'in_progress').length,
    completionRate: actionItems.length > 0 
      ? Math.round((actionItems.filter(item => item.status === 'completed').length / actionItems.length) * 100)
      : 0
  };

  // Transform backend task data to frontend format
  const transformTaskData = (backendTasks) => {
    return backendTasks.map(task => ({
      id: task.id,
      title: task.title,
      description: task.description || 'No description provided',
      priority: task.priority ? task.priority.charAt(0).toUpperCase() + task.priority.slice(1) : 'Medium',
      priorityColor: task.priority === 'high' ? 'bg-red-600' : task.priority === 'medium' ? 'bg-blue-500' : 'bg-gray-500',
      from: `Meeting ${task.meeting_id || 'Unknown'}`,
      due: task.due_date || 'No due date',
      confidence: 95, // Default confidence
      suggestedAssignee: {
        name: task.assignee || 'Unassigned',
        avatar: task.assignee ? task.assignee.charAt(0).toUpperCase() : 'U',
        color: 'bg-blue-500'
      },
      status: task.status || 'pending',
      aiGenerated: true
    }));
  };

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true);
        const response = await apiService.getTasks();
        const transformedTasks = transformTaskData(response.data || []);
        setActionItems(transformedTasks);
        setError('');
      } catch (err) {
        console.error('Failed to fetch tasks:', err);
        setError(`Failed to load tasks: ${err.message}`);
        // Keep empty array on error
        setActionItems([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  const handleEdit = (itemId) => {
    console.log('Edit action item:', itemId);
  };

  const handleReject = (itemId) => {
    setActionItems(prev => prev.filter(item => item.id !== itemId));
  };

  const handleApprove = (itemId) => {
    setActionItems(prev => 
      prev.map(item => 
        item.id === itemId 
          ? { ...item, status: 'approved' }
          : item
      )
    );
  };

  const handleApproveAll = () => {
    setActionItems(prev => 
      prev.map(item => ({ ...item, status: 'approved' }))
    );
    setShowApproveAllModal(false);
  };

  const handleViewDetails = (itemId) => {
    console.log('View details for:', itemId);
  };

  const handleExport = () => {
    console.log('Export action items');
  };

  const handleAddActionItem = () => {
    console.log('Add new action item');
  };

  const filteredActionItems = actionItems.filter(item =>
    item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.from.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getPriorityBadge = (priority, priorityColor) => {
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${priorityColor}`}>
        {priority}
      </span>
    );
  };

  return (
    <div className="p-6 bg-gray-50 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Action Items</h1>
          <p className="text-gray-600 mt-1">AI-detected tasks and team assignments</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleExport}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            📤 Export
          </button>
          <button 
            onClick={handleAddActionItem}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            ➕ Add Action Item
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{statsData.totalActionItems}</div>
          <div className="text-gray-600 text-sm">Total Action Items</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{statsData.pendingApproval}</div>
          <div className="text-gray-600 text-sm">Pending Approval</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{statsData.inProgress}</div>
          <div className="text-gray-600 text-sm">In Progress</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{statsData.completionRate}%</div>
          <div className="text-gray-600 text-sm">Completion Rate</div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Search meetings, action items, Project..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
            🔍
          </div>
        </div>
        <button 
          onClick={() => setFilterOpen(!filterOpen)}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          🔽 Filter
        </button>
        <button 
          onClick={() => setShowApproveAllModal(true)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
        >
          ✓ Approve All
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">Loading tasks...</div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800 font-medium">Error Loading Tasks</div>
          <div className="text-red-600 text-sm mt-1">{error}</div>
        </div>
      )}

      {/* Action Items List */}
      {!loading && !error && (
        <div className="space-y-4">
          {filteredActionItems.map((item) => (
          <div key={item.id} className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{item.title}</h3>
                  {getPriorityBadge(item.priority, item.priorityColor)}
                </div>
                
                <p className="text-gray-700 mb-4">{item.description}</p>
                
                <div className="flex items-center gap-6 text-sm text-gray-600 mb-4">
                  <span><strong>From:</strong> {item.from}</span>
                  <span><strong>Due:</strong> {item.due}</span>
                  <span><strong>Confidence:</strong> {item.confidence}%</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-600">Suggested assignee:</span>
                    <div className="flex items-center gap-2">
                      <div className={`w-6 h-6 rounded-full ${item.suggestedAssignee.color} flex items-center justify-center text-white text-xs font-medium`}>
                        {item.suggestedAssignee.avatar}
                      </div>
                      <span className="text-sm text-gray-900">{item.suggestedAssignee.name}</span>
                    </div>
                  </div>
                  
                  {item.aiGenerated && (
                    <span className="text-sm text-gray-500">AI-Generated</span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-2 ml-6">
                <button 
                  onClick={() => handleReject(item.id)}
                  className="px-3 py-1 border border-red-300 text-red-600 rounded text-sm hover:bg-red-50 flex items-center gap-1"
                >
                  ✕ Reject
                </button>
                <button 
                  onClick={() => handleApprove(item.id)}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 flex items-center gap-1"
                >
                  ✓ Approve
                </button>
              </div>
            </div>
          </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && filteredActionItems.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">No action items found</div>
          <div className="text-gray-500">
            {actionItems.length === 0 
              ? 'No tasks have been created yet. Start a meeting to generate action items!' 
              : 'Try adjusting your search terms or filters'
            }
          </div>
        </div>
      )}

      {/* Approve All Modal */}
      {showApproveAllModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Approve All Action Items</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to approve all {filteredActionItems.length} action items? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setShowApproveAllModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button 
                onClick={handleApproveAll}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Approve All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActionItemsPage;