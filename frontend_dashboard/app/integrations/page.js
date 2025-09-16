'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/lib/api';

const IntegrationsPage = () => {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchIntegrations = async () => {
      try {
        setLoading(true);
        const response = await apiService.getIntegrations();
        setIntegrations(response.data || []);
        setError('');
      } catch (err) {
        console.error('Failed to fetch integrations:', err);
        setError(`Failed to load integrations: ${err.message}`);
        // Fallback to mock data
        setIntegrations([
    {
      id: 1,
      name: 'Google Calendar',
      description: 'Sync meeting schedules and automatically detect when to start recording',
      status: 'Connected',
      icon: '📅',
      features: ['Meeting reminder', 'Auto-detect meetings', 'Schedule sync'],
      lastSync: '2 minutes ago',
      category: 'Calendar'
    },
    {
      id: 2,
      name: 'Google Meet',
      description: 'Automatically join and record Google Meet sessions with AI transcription',
      status: 'Connected',
      icon: '📹',
      features: ['Meeting remainder', 'Auto-detect meetings', 'Schedule sync'],
      lastSync: '2 minutes ago',
      category: 'Video Conferencing'
    },
    {
      id: 3,
      name: 'Google Meet',
      description: 'Automatically join and record Google Meet sessions with AI transcription',
      status: 'Connected',
      icon: '📹',
      features: ['Meeting remainder', 'Auto-detect meetings', 'Schedule sync'],
      lastSync: '2 minutes ago',
      category: 'Video Conferencing'
    },
    {
      id: 4,
      name: 'Google Meet',
      description: 'Automatically join and record Google Meet sessions with AI transcription',
      status: 'Connected',
      icon: '📹',
      features: ['Meeting remainder', 'Auto-detect meetings', 'Schedule sync'],
      lastSync: '2 minutes ago',
      category: 'Video Conferencing'
    },
    {
      id: 5,
      name: 'Google Meet',
      description: 'Automatically join and record Google Meet sessions with AI transcription',
      status: 'Connected',
      icon: '📹',
      features: ['Meeting remainder', 'Auto-detect meetings', 'Schedule sync'],
      lastSync: '2 minutes ago',
      category: 'Video Conferencing'
    },
    {
      id: 6,
      name: 'Google Meet',
      description: 'Automatically join and record Google Meet sessions with AI transcription',
      status: 'Connected',
      icon: '📹',
      features: ['Meeting remainder', 'Auto-detect meetings', 'Schedule sync'],
      lastSync: '2 minutes ago',
      category: 'Video Conferencing'
    },
    {
      id: 7,
      name: 'Slack',
      description: 'Send meeting summaries and action items to Slack channels',
      status: 'Available',
      icon: '💬',
      features: ['Channel notifications', 'Summary sharing', 'Action item alerts'],
      lastSync: null,
      category: 'Communication'
    },
    {
      id: 8,
      name: 'Microsoft Teams',
      description: 'Join and record Microsoft Teams meetings automatically',
      status: 'Available',
      icon: '👥',
      features: ['Auto-join meetings', 'Recording', 'Transcription'],
      lastSync: null,
      category: 'Video Conferencing'
    },
    {
      id: 9,
      name: 'Zoom',
      description: 'Record and transcribe Zoom meetings with AI-powered insights',
      status: 'Available',
      icon: '🎥',
      features: ['Auto-recording', 'Transcription', 'Meeting insights'],
      lastSync: null,
      category: 'Video Conferencing'
    },
    {
      id: 10,
      name: 'Notion',
      description: 'Automatically create meeting notes and action items in Notion',
      status: 'Available',
      icon: '📝',
      features: ['Note creation', 'Action items sync', 'Database integration'],
      lastSync: null,
      category: 'Productivity'
    },
    {
      id: 11,
      name: 'Jira',
      description: 'Create tickets and tasks from meeting action items',
      status: 'Available',
      icon: '🎯',
      features: ['Ticket creation', 'Task management', 'Sprint integration'],
      lastSync: null,
      category: 'Project Management'
    }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchIntegrations();
  }, []);

  // Calculate stats
  const integrationsArray = Array.isArray(integrations) ? integrations : [];
  const connectedCount = integrationsArray.filter(i => i.status === 'Connected').length;
  const availableCount = integrationsArray.filter(i => i.status === 'Available').length;
  const autoEnabledCount = integrationsArray.filter(i => i.status === 'Connected' && i.features.includes('Auto-detect meetings')).length;

  const handleConfigure = (integrationId) => {
    console.log('Configure integration:', integrationId);
    // Here you would typically open a configuration modal or navigate to a config page
  };

  const handleConnect = (integrationId) => {
    setIntegrations(prev => 
      prev.map(integration => 
        integration.id === integrationId 
          ? { ...integration, status: 'Connected', lastSync: 'Just now' }
          : integration
      )
    );
  };

  const handleDisconnect = (integrationId) => {
    setIntegrations(prev => 
      prev.map(integration => 
        integration.id === integrationId 
          ? { ...integration, status: 'Available', lastSync: null }
          : integration
      )
    );
  };

  const getStatusBadge = (status) => {
    if (status === 'Connected') {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          Connected
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        Available
      </span>
    );
  };

  const renderIntegrationCard = (integration) => (
    <div key={integration.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-2xl">{integration.icon}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{integration.name}</h3>
            {getStatusBadge(integration.status)}
          </div>
        </div>
        <button 
          onClick={() => handleConfigure(integration.id)}
          className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 flex items-center gap-2"
        >
          ⚙️ Configure
        </button>
      </div>
      
      <p className="text-gray-600 mb-4">{integration.description}</p>
      
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">Features</p>
        <div className="flex flex-wrap gap-2">
          {integration.features.map((feature, index) => (
            <span 
              key={index}
              className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs"
            >
              {feature}
            </span>
          ))}
        </div>
      </div>
      
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          {integration.lastSync ? `Last sync: ${integration.lastSync}` : 'Not connected'}
        </div>
        <div className="flex items-center gap-2">
          {integration.lastSync && (
            <button className="text-blue-600 hover:text-blue-700 text-sm">
              🔗
            </button>
          )}
          {integration.status === 'Connected' ? (
            <button 
              onClick={() => handleDisconnect(integration.id)}
              className="px-3 py-1 border border-red-300 text-red-600 rounded text-sm hover:bg-red-50"
            >
              Disconnect
            </button>
          ) : (
            <button 
              onClick={() => handleConnect(integration.id)}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Connect
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6 bg-gray-50 h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-600 mt-1">Connect ScrumAI with your favourite tools and platforms</p>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">Loading integrations...</div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800 font-medium">Error Loading Integrations</div>
          <div className="text-red-600 text-sm mt-1">{error}</div>
        </div>
      )}

      {/* Stats Cards */}
      {!loading && (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{connectedCount}</div>
          <div className="text-gray-600 text-sm">Connected</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{availableCount}</div>
          <div className="text-gray-600 text-sm">Available</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{autoEnabledCount}</div>
          <div className="text-gray-600 text-sm">Auto-enabled</div>
        </div>
      </div>
      )}

      {/* Available Integrations Section */}
      {!loading && (
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Available Integrations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {integrationsArray.map(integration => renderIntegrationCard(integration))}
        </div>
      </div>
      )}

      {/* Empty state for when no integrations are available */}
      {!loading && !error && integrationsArray.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">No integrations available</div>
          <div className="text-gray-500">Check back later for new integrations</div>
        </div>
      )}
    </div>
  );
};

export default IntegrationsPage;