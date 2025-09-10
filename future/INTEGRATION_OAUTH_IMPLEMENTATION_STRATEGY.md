# 🔐 Integration OAuth Implementation Strategy

## Overview
This document provides an end-to-end strategy for implementing OAuth authentication for ClickUp and Notion integrations, moving from hardcoded tokens to user-owned OAuth tokens through the frontend dashboard.

## 🎯 User Journey Flow

### Current State (Hardcoded Tokens)
```
User → Meeting → AI Processing → Integration Service (with .env tokens) → ClickUp/Notion
```

### Target State (OAuth Flow)
```
User → Frontend Dashboard → OAuth Sign-in → Token Storage → Meeting → AI Processing → User-Scoped Integration → ClickUp/Notion
```

## 🏗️ Implementation Architecture

### Phase 1: OAuth Infrastructure Setup
**Timeline: Day 1-2**

#### 1.1 OAuth App Registration
**ClickUp OAuth App Setup:**
- App Name: `ScrumBot Meeting Assistant`
- Redirect URI: `http://localhost:5167/auth/clickup/callback`
- Scopes: `read`, `write`, `task:create`, `list:read`, `workspace:read`

**Notion OAuth App Setup:**
- App Name: `ScrumBot Meeting Assistant`
- Redirect URI: `http://localhost:5167/auth/notion/callback`
- Scopes: `read`, `insert`, `update`

#### 1.2 Environment Variables
**File**: `.env.integration`
```bash
# OAuth Client Credentials
CLICKUP_CLIENT_ID=your_clickup_client_id
CLICKUP_CLIENT_SECRET=your_clickup_client_secret
NOTION_CLIENT_ID=your_notion_client_id
NOTION_CLIENT_SECRET=your_notion_client_secret

# OAuth Callback URLs
APP_BASE_URL=http://localhost:5167
FRONTEND_BASE_URL=http://localhost:3000

# JWT Secret for state management
JWT_SECRET=your_jwt_secret_here
```

#### 1.3 Database Schema Updates
**File**: `integration/app/database_migrations.py`
```python
async def create_oauth_tables(db):
    """Create tables for OAuth token management"""
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_integration_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            token_type TEXT DEFAULT 'Bearer',
            expires_at TIMESTAMP,
            scope TEXT,
            workspace_id TEXT,
            workspace_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, platform)
        )
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS oauth_states (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            state_token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    """)
```

### Phase 2: OAuth Endpoints Implementation
**Timeline: Day 2-3**

#### 2.1 OAuth Handler Service
**File**: `integration/app/oauth_handler.py`
```python
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
import httpx
import os
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class OAuthManager:
    def __init__(self, db):
        self.db = db
    
    def generate_state_token(self, user_id: str, platform: str) -> str:
        """Generate secure state token for OAuth flow"""
        payload = {
            'user_id': user_id,
            'platform': platform,
            'timestamp': datetime.utcnow().isoformat(),
            'nonce': secrets.token_urlsafe(16)
        }
        return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')
    
    async def verify_state_token(self, state_token: str) -> Optional[Dict]:
        """Verify and decode state token"""
        try:
            payload = jwt.decode(state_token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            
            # Check if token is not too old (15 minutes max)
            token_time = datetime.fromisoformat(payload['timestamp'])
            if datetime.utcnow() - token_time > timedelta(minutes=15):
                return None
                
            return payload
        except jwt.InvalidTokenError:
            return None
    
    async def save_oauth_token(self, user_id: str, platform: str, token_data: Dict):
        """Save OAuth token to database"""
        expires_at = None
        if token_data.get('expires_in'):
            expires_at = datetime.utcnow() + timedelta(seconds=int(token_data['expires_in']))
        
        # Get workspace info for better UX
        workspace_info = await self._get_workspace_info(platform, token_data['access_token'])
        
        await self.db.execute("""
            INSERT OR REPLACE INTO user_integration_tokens 
            (id, user_id, platform, access_token, refresh_token, token_type,
             expires_at, scope, workspace_id, workspace_name, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"{user_id}_{platform}",
            user_id,
            platform,
            token_data['access_token'],
            token_data.get('refresh_token'),
            token_data.get('token_type', 'Bearer'),
            expires_at,
            token_data.get('scope'),
            workspace_info.get('id'),
            workspace_info.get('name'),
            datetime.utcnow()
        ))
    
    async def _get_workspace_info(self, platform: str, access_token: str) -> Dict:
        """Get workspace information after OAuth"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            if platform == 'clickup':
                async with httpx.AsyncClient() as client:
                    response = await client.get('https://api.clickup.com/api/v2/team', headers=headers)
                    if response.status_code == 200:
                        teams = response.json().get('teams', [])
                        if teams:
                            return {'id': teams[0]['id'], 'name': teams[0]['name']}
            
            elif platform == 'notion':
                headers['Notion-Version'] = '2022-06-28'
                async with httpx.AsyncClient() as client:
                    response = await client.get('https://api.notion.com/v1/users/me', headers=headers)
                    if response.status_code == 200:
                        user_info = response.json()
                        return {'id': user_info.get('id'), 'name': user_info.get('name', 'Notion Workspace')}
            
            return {}
        except Exception as e:
            logger.warning(f"Could not fetch workspace info for {platform}: {e}")
            return {}

oauth_manager = OAuthManager(None)  # Will be injected

@router.get("/auth/{platform}/initiate")
async def initiate_oauth(platform: str, user_id: str):
    """Initiate OAuth flow for ClickUp or Notion"""
    if platform not in ['clickup', 'notion']:
        raise HTTPException(status_code=400, detail="Unsupported platform")
    
    # Generate secure state token
    state_token = oauth_manager.generate_state_token(user_id, platform)
    
    # Build OAuth URL
    if platform == 'clickup':
        auth_url = 'https://api.clickup.com/api/v2/oauth/authorize'
        params = {
            'client_id': os.getenv('CLICKUP_CLIENT_ID'),
            'redirect_uri': f"{os.getenv('APP_BASE_URL')}/auth/clickup/callback",
            'state': state_token
        }
    
    elif platform == 'notion':
        auth_url = 'https://api.notion.com/v1/oauth/authorize'
        params = {
            'client_id': os.getenv('NOTION_CLIENT_ID'),
            'redirect_uri': f"{os.getenv('APP_BASE_URL')}/auth/notion/callback",
            'response_type': 'code',
            'owner': 'user',
            'state': state_token
        }
    
    # Build full auth URL
    param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    full_auth_url = f"{auth_url}?{param_string}"
    
    logger.info(f"Initiating OAuth for {platform}, user {user_id}")
    return {'auth_url': full_auth_url, 'state': state_token}

@router.get("/auth/{platform}/callback")
async def oauth_callback(platform: str, code: str, state: str, background_tasks: BackgroundTasks):
    """Handle OAuth callback and exchange code for token"""
    
    # Verify state token
    state_data = await oauth_manager.verify_state_token(state)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state token")
    
    user_id = state_data['user_id']
    
    try:
        # Exchange authorization code for access token
        if platform == 'clickup':
            token_url = 'https://api.clickup.com/api/v2/oauth/token'
            token_data = {
                'client_id': os.getenv('CLICKUP_CLIENT_ID'),
                'client_secret': os.getenv('CLICKUP_CLIENT_SECRET'),
                'code': code
            }
        
        elif platform == 'notion':
            token_url = 'https://api.notion.com/v1/oauth/token'
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': f"{os.getenv('APP_BASE_URL')}/auth/notion/callback",
                'client_id': os.getenv('NOTION_CLIENT_ID'),
                'client_secret': os.getenv('NOTION_CLIENT_SECRET')
            }
        
        # Make token exchange request
        async with httpx.AsyncClient() as client:
            if platform == 'notion':
                # Notion requires Basic Auth for token endpoint
                import base64
                auth_string = f"{os.getenv('NOTION_CLIENT_ID')}:{os.getenv('NOTION_CLIENT_SECRET')}"
                auth_bytes = auth_string.encode('ascii')
                auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
                
                headers = {'Authorization': f'Basic {auth_b64}'}
                response = await client.post(token_url, json=token_data, headers=headers)
            else:
                response = await client.post(token_url, json=token_data)
            
            if response.status_code == 200:
                token_info = response.json()
                
                # Save token to database
                await oauth_manager.save_oauth_token(user_id, platform, token_info)
                
                # Process any pending tasks for this user
                background_tasks.add_task(process_pending_tasks, user_id)
                
                # Redirect back to frontend with success
                frontend_url = f"{os.getenv('FRONTEND_BASE_URL')}/integrations?success={platform}"
                return RedirectResponse(frontend_url)
            
            else:
                logger.error(f"Token exchange failed for {platform}: {response.text}")
                raise HTTPException(status_code=400, detail=f"Token exchange failed: {response.text}")
                
    except Exception as e:
        logger.error(f"OAuth callback error for {platform}: {e}")
        frontend_url = f"{os.getenv('FRONTEND_BASE_URL')}/integrations?error={platform}"
        return RedirectResponse(frontend_url)

@router.get("/auth/status")
async def get_auth_status(user_id: str):
    """Get user's integration authentication status"""
    
    clickup_token = await oauth_manager.db.fetch_one("""
        SELECT platform, workspace_name, created_at, expires_at
        FROM user_integration_tokens 
        WHERE user_id = ? AND platform = 'clickup'
    """, (user_id,))
    
    notion_token = await oauth_manager.db.fetch_one("""
        SELECT platform, workspace_name, created_at, expires_at  
        FROM user_integration_tokens
        WHERE user_id = ? AND platform = 'notion'
    """, (user_id,))
    
    return {
        'clickup': {
            'connected': clickup_token is not None,
            'workspace_name': clickup_token['workspace_name'] if clickup_token else None,
            'connected_at': clickup_token['created_at'] if clickup_token else None,
            'expires_at': clickup_token['expires_at'] if clickup_token else None
        },
        'notion': {
            'connected': notion_token is not None,
            'workspace_name': notion_token['workspace_name'] if notion_token else None,
            'connected_at': notion_token['created_at'] if notion_token else None,
            'expires_at': notion_token['expires_at'] if notion_token else None
        }
    }

@router.delete("/auth/{platform}/disconnect")
async def disconnect_integration(platform: str, user_id: str):
    """Disconnect user from integration platform"""
    
    await oauth_manager.db.execute("""
        DELETE FROM user_integration_tokens 
        WHERE user_id = ? AND platform = ?
    """, (user_id, platform))
    
    return {'success': True, 'message': f'Disconnected from {platform}'}

async def process_pending_tasks(user_id: str):
    """Background task to process any pending tasks after OAuth completion"""
    # This would integrate with the existing task processing system
    logger.info(f"Processing pending tasks for user {user_id}")
    pass
```

### Phase 3: Frontend Dashboard Integration
**Timeline: Day 3-4**

#### 3.1 Integrations Tab Component
**File**: `frontend_dashboard/src/components/IntegrationsTab.jsx`
```javascript
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ExternalLink, CheckCircle, AlertCircle, Unplug } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const IntegrationsTab = () => {
    const { user } = useAuth();
    const [integrationStatus, setIntegrationStatus] = useState({
        clickup: { connected: false, workspace_name: null, connecting: false },
        notion: { connected: false, workspace_name: null, connecting: false }
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchIntegrationStatus();
    }, [user]);

    const fetchIntegrationStatus = async () => {
        if (!user?.id) return;
        
        try {
            const response = await fetch(`/api/auth/status?user_id=${user.id}`);
            const data = await response.json();
            setIntegrationStatus(data);
        } catch (error) {
            console.error('Failed to fetch integration status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleConnect = async (platform) => {
        if (!user?.id) return;
        
        setIntegrationStatus(prev => ({
            ...prev,
            [platform]: { ...prev[platform], connecting: true }
        }));

        try {
            const response = await fetch(`/api/auth/${platform}/initiate?user_id=${user.id}`);
            const data = await response.json();
            
            // Open OAuth flow in new tab
            const authWindow = window.open(
                data.auth_url, 
                `${platform}_oauth`, 
                'width=600,height=700,scrollbars=yes,resizable=yes'
            );

            // Poll for completion
            const checkAuth = setInterval(async () => {
                try {
                    if (authWindow.closed) {
                        clearInterval(checkAuth);
                        // Refresh status after OAuth completion
                        await fetchIntegrationStatus();
                        setIntegrationStatus(prev => ({
                            ...prev,
                            [platform]: { ...prev[platform], connecting: false }
                        }));
                    }
                } catch (error) {
                    clearInterval(checkAuth);
                    setIntegrationStatus(prev => ({
                        ...prev,
                        [platform]: { ...prev[platform], connecting: false }
                    }));
                }
            }, 1000);

        } catch (error) {
            console.error(`Failed to initiate ${platform} OAuth:`, error);
            setIntegrationStatus(prev => ({
                ...prev,
                [platform]: { ...prev[platform], connecting: false }
            }));
        }
    };

    const handleDisconnect = async (platform) => {
        if (!user?.id) return;
        
        try {
            const response = await fetch(`/api/auth/${platform}/disconnect`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: user.id })
            });
            
            if (response.ok) {
                await fetchIntegrationStatus();
            }
        } catch (error) {
            console.error(`Failed to disconnect ${platform}:`, error);
        }
    };

    const IntegrationCard = ({ platform, config }) => {
        const status = integrationStatus[platform];
        
        return (
            <Card className="w-full">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center space-x-2">
                        <img 
                            src={`/icons/${platform}-logo.png`} 
                            alt={config.name}
                            className="w-8 h-8"
                        />
                        <CardTitle className="text-lg">{config.name}</CardTitle>
                    </div>
                    <Badge 
                        variant={status.connected ? "default" : "secondary"}
                        className={status.connected ? "bg-green-100 text-green-800" : ""}
                    >
                        {status.connected ? (
                            <>
                                <CheckCircle className="w-3 h-3 mr-1" />
                                Connected
                            </>
                        ) : (
                            <>
                                <AlertCircle className="w-3 h-3 mr-1" />
                                Not Connected
                            </>
                        )}
                    </Badge>
                </CardHeader>
                
                <CardContent>
                    <div className="space-y-3">
                        <p className="text-sm text-gray-600">{config.description}</p>
                        
                        {status.connected && status.workspace_name && (
                            <div className="text-sm">
                                <span className="font-medium">Workspace: </span>
                                <span className="text-gray-700">{status.workspace_name}</span>
                            </div>
                        )}
                        
                        <div className="flex space-x-2">
                            {status.connected ? (
                                <Button 
                                    variant="outline" 
                                    size="sm"
                                    onClick={() => handleDisconnect(platform)}
                                >
                                    <Unplug className="w-4 h-4 mr-2" />
                                    Disconnect
                                </Button>
                            ) : (
                                <Button 
                                    onClick={() => handleConnect(platform)}
                                    disabled={status.connecting}
                                    className="bg-blue-600 hover:bg-blue-700"
                                >
                                    <ExternalLink className="w-4 h-4 mr-2" />
                                    {status.connecting ? 'Connecting...' : 'Connect'}
                                </Button>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        );
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Integrations</h2>
                <p className="text-gray-600">
                    Connect your productivity tools to automatically create tasks from meeting insights.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <IntegrationCard 
                    platform="clickup"
                    config={{
                        name: "ClickUp",
                        description: "Create tasks, assign team members, and organize projects directly from meeting summaries."
                    }}
                />
                
                <IntegrationCard 
                    platform="notion"
                    config={{
                        name: "Notion", 
                        description: "Generate meeting notes, action items, and project documentation in your Notion workspace."
                    }}
                />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">How it works</h3>
                <ol className="text-sm text-blue-800 space-y-1">
                    <li>1. Connect your ClickUp and/or Notion accounts using OAuth</li>
                    <li>2. Install the Chrome extension and start recording meetings</li>
                    <li>3. AI will automatically create tasks and notes in your connected tools</li>
                    <li>4. Review and manage everything from your integrated workspace</li>
                </ol>
            </div>
        </div>
    );
};

export default IntegrationsTab;
```

### Phase 4: Integration Service Updates
**Timeline: Day 4-5**

#### 4.1 Token-Aware Integration Classes
**File**: `integration/app/integrations/clickup_integration.py`
```python
class ClickUpIntegration:
    def __init__(self, access_token: str, workspace_id: str = None):
        self.access_token = access_token
        self.workspace_id = workspace_id
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    async def from_user(cls, db, user_id: str):
        """Create ClickUp integration instance from user's stored token"""
        token_record = await db.fetch_one("""
            SELECT access_token, workspace_id FROM user_integration_tokens 
            WHERE user_id = ? AND platform = 'clickup'
        """, (user_id,))
        
        if not token_record:
            raise ValueError(f"No ClickUp token found for user {user_id}")
        
        return cls(
            access_token=token_record['access_token'],
            workspace_id=token_record['workspace_id']
        )
    
    async def create_task(self, task_data: Dict) -> Dict:
        """Create task with user's authenticated account"""
        # Implementation using self.access_token
        # ... rest of existing implementation
```

#### 4.2 Updated Callable Utility
**File**: `integration/app/callable_utility.py`
```python
from typing import Dict, List, Optional
from .integrations import NotionIntegration, ClickUpIntegration
from .oauth_handler import oauth_manager

class IntegrationUtility:
    """OAuth-aware callable utility for integration operations"""
    
    def __init__(self, db):
        self.db = db
        self.oauth_manager = oauth_manager
        
    async def create_task(self, user_id: str, task_data: Dict, 
                         platform_preference: str = 'smart') -> Dict:
        """Create task using user's authenticated providers"""
        
        # Check authentication status
        auth_status = await self.oauth_manager.get_auth_status(user_id)
        
        # Determine which platform to use
        if platform_preference == 'clickup' and auth_status['clickup']:
            return await self._create_clickup_task(user_id, task_data)
        elif platform_preference == 'notion' and auth_status['notion']:
            return await self._create_notion_task(user_id, task_data)
        elif platform_preference == 'smart':
            # Smart routing based on task type and available integrations
            if auth_status['clickup']:
                return await self._create_clickup_task(user_id, task_data)
            elif auth_status['notion']:
                return await self._create_notion_task(user_id, task_data)
            else:
                raise ValueError("No authenticated integrations available")
        else:
            raise ValueError(f"Platform {platform_preference} not available for user")
    
    async def _create_clickup_task(self, user_id: str, task_data: Dict) -> Dict:
        """Create task in ClickUp using user's token"""
        clickup = await ClickUpIntegration.from_user(self.db, user_id)
        return await clickup.create_task(task_data)
    
    async def _create_notion_task(self, user_id: str, task_data: Dict) -> Dict:
        """Create task in Notion using user's token"""
        notion = await NotionIntegration.from_user(self.db, user_id)
        return await notion.create_task(task_data)
    
    async def get_user_integrations(self, user_id: str) -> Dict:
        """Get user's connected integrations and capabilities"""
        auth_status = await self.oauth_manager.get_auth_status(user_id)
        
        capabilities = []
        if auth_status['clickup']:
            capabilities.append({
                'platform': 'clickup',
                'features': ['task_creation', 'list_management', 'team_assignment']
            })
        if auth_status['notion']:
            capabilities.append({
                'platform': 'notion', 
                'features': ['page_creation', 'database_updates', 'meeting_notes']
            })
        
        return {
            'connected_platforms': capabilities,
            'total_connections': len(capabilities)
        }

# Global utility instance
integration_utility = IntegrationUtility(None)  # DB will be injected
```

### Phase 5: Testing & Deployment
**Timeline: Day 5-6**

#### 5.1 Integration Tests
**File**: `integration/tests/test_oauth_flow.py`
```python
import pytest
import asyncio
from unittest.mock import Mock, patch
from ..app.oauth_handler import OAuthManager
from ..app.callable_utility import IntegrationUtility

class TestOAuthFlow:
    
    @pytest.fixture
    async def oauth_manager(self):
        db_mock = Mock()
        return OAuthManager(db_mock)
    
    async def test_state_token_generation_and_verification(self, oauth_manager):
        """Test OAuth state token security"""
        user_id = "test_user_123"
        platform = "clickup"
        
        # Generate state token
        state_token = oauth_manager.generate_state_token(user_id, platform)
        assert state_token is not None
        
        # Verify state token
        payload = await oauth_manager.verify_state_token(state_token)
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['platform'] == platform
    
    @patch('httpx.AsyncClient')
    async def test_clickup_oauth_callback(self, mock_client, oauth_manager):
        """Test ClickUp OAuth token exchange"""
        # Mock successful token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'token_type': 'Bearer'
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Mock database save
        oauth_manager.db.execute = Mock()
        
        # Test token exchange
        token_data = {'access_token': 'test_access_token', 'token_type': 'Bearer'}
        await oauth_manager.save_oauth_token('test_user', 'clickup', token_data)
        
        # Verify database call
        oauth_manager.db.execute.assert_called_once()
    
    async def test_integration_utility_with_auth(self):
        """Test integration utility with OAuth tokens"""
        # Mock authenticated user
        db_mock = Mock()
        db_mock.fetch_one.return_value = {
            'access_token': 'test_token',
            'workspace_id': 'test_workspace'
        }
        
        utility = IntegrationUtility(db_mock)
        
        # Test user integration status
        with patch.object(utility.oauth_manager, 'get_auth_status') as mock_auth:
            mock_auth.return_value = {'clickup': True, 'notion': False}
            
            integrations = await utility.get_user_integrations('test_user')
            assert len(integrations['connected_platforms']) == 1
            assert integrations['connected_platforms'][0]['platform'] == 'clickup'
```

#### 5.2 End-to-End Test Script
**File**: `integration/test_oauth_e2e.py`
```python
#!/usr/bin/env python3
"""
End-to-end OAuth integration test
Simulates the complete user journey from dashboard to task creation
"""

import asyncio
import httpx
import json
from datetime import datetime

class E2ETestRunner:
    def __init__(self):
        self.base_url = "http://localhost:5167"
        self.test_user_id = "test_user_e2e"
    
    async def run_complete_flow(self):
        """Run complete OAuth integration flow"""
        print("🚀 Starting E2E OAuth Integration Test")
        
        # Step 1: Check initial auth status
        print("\n1. Checking initial auth status...")
        status = await self.check_auth_status()
        print(f"   Initial status: {status}")
        
        # Step 2: Initiate OAuth (would require manual intervention)
        print("\n2. OAuth initiation test...")
        auth_urls = await self.get_oauth_urls()
        print(f"   ClickUp OAuth URL: {auth_urls.get('clickup', 'Not available')}")
        print(f"   Notion OAuth URL: {auth_urls.get('notion', 'Not available')}")
        
        # Step 3: Test integration utility (assuming tokens exist)
        print("\n3. Testing integration utility...")
        await self.test_integration_capabilities()
        
        print("\n✅ E2E Test Complete!")
    
    async def check_auth_status(self):
        """Check user's current authentication status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/auth/status?user_id={self.test_user_id}")
            return response.json()
    
    async def get_oauth_urls(self):
        """Get OAuth initiation URLs"""
        urls = {}
        
        for platform in ['clickup', 'notion']:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get