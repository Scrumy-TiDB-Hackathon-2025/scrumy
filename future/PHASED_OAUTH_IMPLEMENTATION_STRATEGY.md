# 🔐 OAuth Implementation Strategy for ScrumBot
## Complete Integration Authentication with User Context

### Overview

This document provides detailed implementation guidance for OAuth authentication across ClickUp and Notion integrations, building on the foundation established in the phased deployment strategy. This focuses specifically on Phase 6 implementation with user-scoped integration services.

---

## 🎯 OAuth Integration Architecture

### Current Integration Flow (No Auth)
```
Meeting → AI Processing → Integration Service (hardcoded tokens) → ClickUp/Notion
```

### Target OAuth Flow (User-Scoped)
```
User → OAuth Setup → Token Storage → Meeting → AI Processing → User Integration Service → ClickUp/Notion
```

---

## 🏗️ Implementation Components

### 1. OAuth Application Setup

#### ClickUp OAuth Configuration
```bash
# Environment variables required
CLICKUP_CLIENT_ID=your_clickup_client_id
CLICKUP_CLIENT_SECRET=your_clickup_client_secret
CLICKUP_REDIRECT_URI=http://localhost:5167/auth/clickup/callback
```

**ClickUp App Settings:**
- App Name: `ScrumBot Meeting Assistant`
- Redirect URI: `http://localhost:5167/auth/clickup/callback`
- Scopes: `read`, `write`, `task:create`, `list:read`, `workspace:read`

#### Notion OAuth Configuration
```bash
# Environment variables required
NOTION_CLIENT_ID=your_notion_client_id
NOTION_CLIENT_SECRET=your_notion_client_secret
NOTION_REDIRECT_URI=http://localhost:5167/auth/notion/callback
```

**Notion Integration Settings:**
- Integration Name: `ScrumBot Meeting Assistant`
- Redirect URI: `http://localhost:5167/auth/notion/callback`
- Capabilities: `Read content`, `Insert content`, `Update content`

### 2. Database Schema for OAuth Tokens

```sql
-- OAuth token storage (extends Phase 1 schema)
CREATE TABLE user_integration_tokens (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    platform ENUM('clickup', 'notion') NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP,
    scope TEXT,
    workspace_id VARCHAR(255),
    workspace_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_platform (user_id, platform),
    INDEX idx_user_platform (user_id, platform),
    INDEX idx_expires (expires_at)
);

-- OAuth state management for security
CREATE TABLE oauth_states (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    state_token VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_state_expires (expires_at)
);
```

### 3. OAuth Handler Implementation

```python
# integration/app/oauth/oauth_handler.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
import httpx
import os
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

router = APIRouter()

class OAuthHandler:
    def __init__(self, db):
        self.db = db
        self.jwt_secret = os.getenv('JWT_SECRET', 'dev-secret')
    
    def generate_state_token(self, user_id: str, platform: str) -> str:
        """Generate secure state token for OAuth flow"""
        payload = {
            'user_id': user_id,
            'platform': platform,
            'timestamp': datetime.utcnow().isoformat(),
            'nonce': secrets.token_urlsafe(16)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    async def verify_state_token(self, state_token: str) -> Optional[Dict]:
        """Verify and decode state token"""
        try:
            payload = jwt.decode(state_token, self.jwt_secret, algorithms=['HS256'])
            
            # Check token age (15 minutes max)
            token_time = datetime.fromisoformat(payload['timestamp'])
            if datetime.utcnow() - token_time > timedelta(minutes=15):
                return None
                
            return payload
        except jwt.InvalidTokenError:
            return None
    
    async def initiate_oauth(self, platform: str, user_id: str) -> Dict:
        """Start OAuth flow for platform"""
        if platform not in ['clickup', 'notion']:
            raise HTTPException(400, "Unsupported platform")
        
        # Generate secure state
        state_token = self.generate_state_token(user_id, platform)
        
        # Store state in database
        await self.db.execute("""
            INSERT INTO oauth_states (id, user_id, platform, state_token, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"{user_id}_{platform}_{secrets.token_urlsafe(8)}",
            user_id,
            platform,
            state_token,
            datetime.utcnow() + timedelta(minutes=15)
        ))
        
        # Build OAuth URL
        if platform == 'clickup':
            auth_url = 'https://api.clickup.com/api/v2/oauth/authorize'
            params = {
                'client_id': os.getenv('CLICKUP_CLIENT_ID'),
                'redirect_uri': os.getenv('CLICKUP_REDIRECT_URI'),
                'state': state_token
            }
        elif platform == 'notion':
            auth_url = 'https://api.notion.com/v1/oauth/authorize'
            params = {
                'client_id': os.getenv('NOTION_CLIENT_ID'),
                'redirect_uri': os.getenv('NOTION_REDIRECT_URI'),
                'response_type': 'code',
                'owner': 'user',
                'state': state_token
            }
        
        # Build full URL
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        full_auth_url = f"{auth_url}?{param_string}"
        
        return {'auth_url': full_auth_url, 'state': state_token}
    
    async def handle_callback(self, platform: str, code: str, state: str) -> RedirectResponse:
        """Handle OAuth callback"""
        # Verify state
        state_data = await self.verify_state_token(state)
        if not state_data:
            raise HTTPException(400, "Invalid or expired state")
        
        user_id = state_data['user_id']
        
        try:
            # Exchange code for token
            token_data = await self._exchange_code_for_token(platform, code)
            
            # Get workspace info
            workspace_info = await self._get_workspace_info(platform, token_data['access_token'])
            
            # Save token
            await self._save_token(user_id, platform, token_data, workspace_info)
            
            # Clean up state
            await self.db.execute("""
                DELETE FROM oauth_states 
                WHERE user_id = ? AND platform = ?
            """, (user_id, platform))
            
            # Redirect to frontend
            return RedirectResponse(f"{os.getenv('FRONTEND_BASE_URL')}/integrations?success={platform}")
            
        except Exception as e:
            return RedirectResponse(f"{os.getenv('FRONTEND_BASE_URL')}/integrations?error={platform}")
    
    async def _exchange_code_for_token(self, platform: str, code: str) -> Dict:
        """Exchange authorization code for access token"""
        if platform == 'clickup':
            url = 'https://api.clickup.com/api/v2/oauth/token'
            data = {
                'client_id': os.getenv('CLICKUP_CLIENT_ID'),
                'client_secret': os.getenv('CLICKUP_CLIENT_SECRET'),
                'code': code
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                
        elif platform == 'notion':
            url = 'https://api.notion.com/v1/oauth/token'
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': os.getenv('NOTION_REDIRECT_URI')
            }
            
            # Notion requires Basic Auth
            import base64
            auth_string = f"{os.getenv('NOTION_CLIENT_ID')}:{os.getenv('NOTION_CLIENT_SECRET')}"
            auth_b64 = base64.b64encode(auth_string.encode()).decode()
            headers = {'Authorization': f'Basic {auth_b64}'}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(400, f"Token exchange failed: {response.text}")
    
    async def _get_workspace_info(self, platform: str, access_token: str) -> Dict:
        """Get workspace information"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
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
        except Exception:
            return {}
    
    async def _save_token(self, user_id: str, platform: str, token_data: Dict, workspace_info: Dict):
        """Save OAuth token to database"""
        expires_at = None
        if token_data.get('expires_in'):
            expires_at = datetime.utcnow() + timedelta(seconds=int(token_data['expires_in']))
        
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

# FastAPI endpoints
oauth_handler = OAuthHandler(None)  # DB injected at runtime

@router.get("/auth/{platform}/initiate")
async def initiate_oauth_endpoint(platform: str, user_id: str):
    return await oauth_handler.initiate_oauth(platform, user_id)

@router.get("/auth/{platform}/callback")
async def oauth_callback_endpoint(platform: str, code: str, state: str):
    return await oauth_handler.handle_callback(platform, code, state)

@router.get("/auth/status")
async def get_auth_status_endpoint(user_id: str):
    return await oauth_handler.get_auth_status(user_id)

@router.delete("/auth/{platform}/disconnect")
async def disconnect_integration_endpoint(platform: str, user_id: str):
    await oauth_handler.disconnect_integration(user_id, platform)
    return {'success': True, 'message': f'Disconnected from {platform}'}
```

### 4. User-Scoped Integration Services

```python
# integration/app/user_integration_service.py
from typing import Dict, Optional
from .integrations.clickup_integration import ClickUpIntegration
from .integrations.notion_integration import NotionIntegration

class UserIntegrationService:
    """User-scoped integration service using OAuth tokens"""
    
    def __init__(self, user_id: str, db):
        self.user_id = user_id
        self.db = db
    
    async def get_user_token(self, platform: str) -> Optional[Dict]:
        """Get valid OAuth token for user and platform"""
        token = await self.db.fetch_one("""
            SELECT * FROM user_integration_tokens 
            WHERE user_id = ? AND platform = ?
        """, (self.user_id, platform))
        
        if not token:
            return None
        
        # Check if token is expired
        if token['expires_at'] and datetime.utcnow() > token['expires_at']:
            # Try to refresh if refresh token exists
            if token['refresh_token']:
                return await self._refresh_token(platform, token['refresh_token'])
            else:
                # Token expired, remove it
                await self.db.execute("""
                    DELETE FROM user_integration_tokens 
                    WHERE user_id = ? AND platform = ?
                """, (self.user_id, platform))
                return None
        
        return dict(token)
    
    async def create_task(self, task_data: Dict, platform_preference: str = 'smart') -> Dict:
        """Create task using user's OAuth tokens"""
        
        # Smart platform selection
        if platform_preference == 'smart':
            # Try ClickUp first, then Notion
            clickup_token = await self.get_user_token('clickup')
            notion_token = await self.get_user_token('notion')
            
            if clickup_token:
                return await self._create_clickup_task(task_data, clickup_token)
            elif notion_token:
                return await self._create_notion_task(task_data, notion_token)
            else:
                return {
                    'success': False,
                    'error': 'No connected integrations',
                    'auth_required': True
                }
        
        # Specific platform requested
        elif platform_preference == 'clickup':
            token = await self.get_user_token('clickup')
            if token:
                return await self._create_clickup_task(task_data, token)
            else:
                return {'success': False, 'error': 'ClickUp not connected', 'auth_required': True}
        
        elif platform_preference == 'notion':
            token = await self.get_user_token('notion')
            if token:
                return await self._create_notion_task(task_data, token)
            else:
                return {'success': False, 'error': 'Notion not connected', 'auth_required': True}
    
    async def _create_clickup_task(self, task_data: Dict, token_data: Dict) -> Dict:
        """Create task in ClickUp using user's token"""
        try:
            clickup = ClickUpIntegration(
                access_token=token_data['access_token'],
                workspace_id=token_data['workspace_id']
            )
            
            result = await clickup.create_task(task_data)
            return {
                'success': True,
                'platform': 'clickup',
                'task_id': result.get('id'),
                'task_url': result.get('url'),
                'workspace': token_data['workspace_name']
            }
            
        except Exception as e:
            return {
                'success': False,
                'platform': 'clickup',
                'error': str(e)
            }
    
    async def _create_notion_task(self, task_data: Dict, token_data: Dict) -> Dict:
        """Create task in Notion using user's token"""
        try:
            notion = NotionIntegration(
                access_token=token_data['access_token'],
                workspace_id=token_data['workspace_id']
            )
            
            result = await notion.create_page(task_data)
            return {
                'success': True,
                'platform': 'notion',
                'page_id': result.get('id'),
                'page_url': result.get('url'),
                'workspace': token_data['workspace_name']
            }
            
        except Exception as e:
            return {
                'success': False,
                'platform': 'notion',
                'error': str(e)
            }
    
    async def get_connected_platforms(self) -> Dict:
        """Get user's connected integration platforms"""
        tokens = await self.db.fetch_all("""
            SELECT platform, workspace_name, created_at, expires_at
            FROM user_integration_tokens 
            WHERE user_id = ?
        """, (self.user_id,))
        
        platforms = {}
        for token in tokens:
            platforms[token['platform']] = {
                'connected': True,
                'workspace_name': token['workspace_name'],
                'connected_at': token['created_at'],
                'expires_at': token['expires_at']
            }
        
        # Add disconnected platforms
        for platform in ['clickup', 'notion']:
            if platform not in platforms:
                platforms[platform] = {'connected': False}
        
        return platforms
```

### 5. Frontend Integration Component

```javascript
// frontend_dashboard/components/integrations/OAuthIntegrations.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';

const OAuthIntegrations = () => {
    const { user } = useAuth();
    const [integrations, setIntegrations] = useState({
        clickup: { connected: false, connecting: false },
        notion: { connected: false, connecting: false }
    });

    useEffect(() => {
        if (user?.id) {
            fetchIntegrationStatus();
        }
    }, [user]);

    const fetchIntegrationStatus = async () => {
        try {
            const response = await fetch(`/api/auth/status?user_id=${user.id}`);
            const data = await response.json();
            setIntegrations(data);
        } catch (error) {
            console.error('Failed to fetch integration status:', error);
        }
    };

    const handleConnect = async (platform) => {
        setIntegrations(prev => ({
            ...prev,
            [platform]: { ...prev[platform], connecting: true }
        }));

        try {
            const response = await fetch(`/api/auth/${platform}/initiate?user_id=${user.id}`);
            const { auth_url } = await response.json();
            
            // Open OAuth window
            const authWindow = window.open(auth_url, `${platform}_oauth`, 'width=600,height=700');
            
            // Poll for completion
            const checkClosed = setInterval(() => {
                if (authWindow.closed) {
                    clearInterval(checkClosed);
                    fetchIntegrationStatus();
                }
            }, 1000);

        } catch (error) {
            console.error(`Failed to connect ${platform}:`, error);
        } finally {
            setIntegrations(prev => ({
                ...prev,
                [platform]: { ...prev[platform], connecting: false }
            }));
        }
    };

    const handleDisconnect = async (platform) => {
        try {
            await fetch(`/api/auth/${platform}/disconnect`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: user.id })
            });
            
            await fetchIntegrationStatus();
        } catch (error) {
            console.error(`Failed to disconnect ${platform}:`, error);
        }
    };

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold">Integration Settings</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(integrations).map(([platform, status]) => (
                    <IntegrationCard
                        key={platform}
                        platform={platform}
                        status={status}
                        onConnect={() => handleConnect(platform)}
                        onDisconnect={() => handleDisconnect(platform)}
                    />
                ))}
            </div>
        </div>
    );
};

const IntegrationCard = ({ platform, status, onConnect, onDisconnect }) => (
    <div className="bg-white p-6 rounded-lg border">
        <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold capitalize">{platform}</h3>
            <span className={`px-2 py-1 rounded text-sm ${
                status.connected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
            }`}>
                {status.connected ? 'Connected' : 'Not Connected'}
            </span>
        </div>
        
        {status.workspace_name && (
            <p className="text-sm text-gray-600 mb-4">
                Workspace: {status.workspace_name}
            </p>
        )}
        
        <div className="flex space-x-2">
            {status.connected ? (
                <button 
                    onClick={onDisconnect}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                    Disconnect
                </button>
            ) : (
                <button 
                    onClick={onConnect}
                    disabled={status.connecting}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                    {status.connecting ? 'Connecting...' : 'Connect'}
                </button>
            )}
        </div>
    </div>
);

export default OAuthIntegrations;
```

---

## 🔧 Integration with AI Processing

### Updated Integration Adapter

```python
# ai_processing/app/integration_adapter.py
from integration.app.user_integration_service import UserIntegrationService

class AIProcessingIntegrationAdapter:
    def __init__(self, db):
        self.db = db
    
    async def process_meeting_complete(self, 
                                     meeting_id: str,
                                     user_id: str,  # Now required
                                     tasks_data: List[Dict],
                                     **kwargs) -> Dict:
        """Process meeting with user-scoped integrations"""
        
        if not user_id:
            return {'error': 'User authentication required'}
        
        # Create user-scoped integration service
        user_service = UserIntegrationService(user_id, self.db)
        
        # Get user's connected platforms
        platforms = await user_service.get_connected_platforms()
        
        if not any(p['connected'] for p in platforms.values()):
            return {
                'success': False,
                'message': 'No integrations connected',
                'auth_required': True,
                'pending_tasks': len(tasks_data)
            }
        
        # Process tasks with user's integrations
        results = []
        for task in tasks_data:
            result = await user_service.create_task(task, platform_preference='smart')
            results.append(result)
        
        successful_tasks = [r for r in results if r.get('success')]
        
        return {
            'success': True,
            'tasks_created': len(successful_tasks),
            'total_tasks': len(tasks_data),
            'results': results,
            'user_id': user_id
        }
```

---

## ✅ Testing Strategy

### OAuth Flow Testing
```python
# integration/tests/test_oauth_flow.py
import pytest
from unittest.mock import Mock, patch

class TestOAuthFlow:
    async def test_clickup_oauth_initiation(self):
        handler = OAuthHandler(Mock())
        result = await handler.initiate_oauth('clickup', 'test_user')
        
        assert 'auth_url' in result
        assert 'clickup.com' in result['auth_url']
        assert 'state' in result
    
    async def test_notion_oauth_callback(self):
        handler = OAuthHandler(Mock())
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'access_token': 'test_token',
                'token_type': 'Bearer'
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await handler.handle_callback('notion', 'test_code', 'valid_state')
            assert isinstance(result, RedirectResponse)
```

---

## 🚀 Deployment Checklist

### OAuth Setup
- [ ] Register ClickUp OAuth application
- [ ] Register Notion integration
- [ ] Configure environment variables
- [ ] Set up redirect URIs

### Database
- [ ] Create OAuth token tables
- [ ] Set up indexes for performance
- [ ] Test token storage/retrieval

### Backend
- [ ] Implement OAuth handlers
- [ ] Add user integration service
- [ ] Update AI processing adapter
- [ ] Test end-to-end flow

### Frontend
- [ ] Add OAuth integration UI
- [ ] Implement connection management
- [ ] Test user experience
- [ ] Handle error states

This OAuth implementation provides secure, user-scoped integration services while maintaining the existing ScrumBot functionality.