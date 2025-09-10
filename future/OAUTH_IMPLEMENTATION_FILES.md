# 🔐 OAuth Implementation Files Structure

This document provides all the files needed to implement OAuth authentication for ClickUp and Notion integrations.

## 📁 Directory Structure

```
scrumy-clean/
├── integration/
│   ├── app/
│   │   ├── oauth/
│   │   │   ├── __init__.py
│   │   │   ├── oauth_handler.py
│   │   │   ├── oauth_manager.py
│   │   │   └── token_store.py
│   │   ├── integrations/
│   │   │   ├── clickup_integration_oauth.py
│   │   │   └── notion_integration_oauth.py
│   │   ├── database_migrations.py
│   │   └── callable_utility_oauth.py
│   ├── tests/
│   │   ├── oauth/
│   │   │   ├── __init__.py
│   │   │   ├── test_oauth_flow.py
│   │   │   └── test_oauth_e2e.py
│   │   └── test_oauth_integration.py
│   └── config/
│       └── oauth_config.py
├── frontend_dashboard/
│   ├── src/
│   │   ├── components/
│   │   │   ├── integrations/
│   │   │   │   ├── IntegrationsTab.jsx
│   │   │   │   ├── IntegrationCard.jsx
│   │   │   │   └── OAuthCallback.jsx
│   │   │   └── ui/
│   │   │       ├── card.jsx
│   │   │       ├── button.jsx
│   │   │       └── badge.jsx
│   │   ├── hooks/
│   │   │   └── useIntegrations.js
│   │   └── services/
│   │       └── integrationService.js
└── docs/
    ├── OAUTH_SETUP_GUIDE.md
    └── OAUTH_TESTING_GUIDE.md
```

## 🛠️ Implementation Files

### 1. Backend OAuth Handler

**File**: `integration/app/oauth/oauth_handler.py`
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
from .oauth_manager import OAuthManager
from .token_store import TokenStore

logger = logging.getLogger(__name__)
router = APIRouter()

class OAuthHandler:
    def __init__(self, db):
        self.db = db
        self.token_store = TokenStore(db)
        self.oauth_manager = OAuthManager(db)
    
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
    
    async def initiate_oauth(self, platform: str, user_id: str) -> Dict:
        """Initiate OAuth flow for ClickUp or Notion"""
        if platform not in ['clickup', 'notion']:
            raise HTTPException(status_code=400, detail="Unsupported platform")
        
        # Generate secure state token
        state_token = self.generate_state_token(user_id, platform)
        
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
    
    async def handle_callback(self, platform: str, code: str, state: str) -> RedirectResponse:
        """Handle OAuth callback and exchange code for token"""
        
        # Verify state token
        state_data = await self.verify_state_token(state)
        if not state_data:
            raise HTTPException(status_code=400, detail="Invalid or expired state token")
        
        user_id = state_data['user_id']
        
        try:
            # Exchange authorization code for access token
            token_info = await self._exchange_code_for_token(platform, code)
            
            # Save token to database
            await self.token_store.save_token(user_id, platform, token_info)
            
            # Redirect back to frontend with success
            frontend_url = f"{os.getenv('FRONTEND_BASE_URL')}/integrations?success={platform}"
            return RedirectResponse(frontend_url)
                
        except Exception as e:
            logger.error(f"OAuth callback error for {platform}: {e}")
            frontend_url = f"{os.getenv('FRONTEND_BASE_URL')}/integrations?error={platform}"
            return RedirectResponse(frontend_url)
    
    async def _exchange_code_for_token(self, platform: str, code: str) -> Dict:
        """Exchange authorization code for access token"""
        
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
                return response.json()
            else:
                logger.error(f"Token exchange failed for {platform}: {response.text}")
                raise HTTPException(status_code=400, detail=f"Token exchange failed: {response.text}")

# FastAPI router endpoints
oauth_handler = OAuthHandler(None)  # DB will be injected

@router.get("/auth/{platform}/initiate")
async def initiate_oauth_endpoint(platform: str, user_id: str):
    """Initiate OAuth flow endpoint"""
    return await oauth_handler.initiate_oauth(platform, user_id)

@router.get("/auth/{platform}/callback")
async def oauth_callback_endpoint(platform: str, code: str, state: str):
    """OAuth callback endpoint"""
    return await oauth_handler.handle_callback(platform, code, state)

@router.get("/auth/status")
async def get_auth_status_endpoint(user_id: str):
    """Get user's integration authentication status"""
    return await oauth_handler.token_store.get_auth_status(user_id)

@router.delete("/auth/{platform}/disconnect")
async def disconnect_integration_endpoint(platform: str, user_id: str):
    """Disconnect user from integration platform"""
    await oauth_handler.token_store.delete_token(user_id, platform)
    return {'success': True, 'message': f'Disconnected from {platform}'}
```

### 2. Token Store Manager

**File**: `integration/app/oauth/token_store.py`
```python
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TokenStore:
    def __init__(self, db):
        self.db = db
    
    async def save_token(self, user_id: str, platform: str, token_data: Dict):
        """Save OAuth token to database with workspace info"""
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
        
        logger.info(f"Saved OAuth token for user {user_id}, platform {platform}")
    
    async def get_token(self, user_id: str, platform: str) -> Optional[Dict]:
        """Get valid token for user and platform"""
        token = await self.db.fetch_one("""
            SELECT * FROM user_integration_tokens 
            WHERE user_id = ? AND platform = ?
        """, (user_id, platform))
        
        if not token:
            return None
        
        # Check if token is expired
        if token['expires_at'] and datetime.utcnow() > datetime.fromisoformat(token['expires_at']):
            # Try to refresh token if refresh_token exists
            if token['refresh_token']:
                return await self._refresh_token(user_id, platform, token['refresh_token'])
            else:
                # Token expired and no refresh token
                await self.delete_token(user_id, platform)
                return None
        
        return dict(token)
    
    async def delete_token(self, user_id: str, platform: str):
        """Delete OAuth token for user and platform"""
        await self.db.execute("""
            DELETE FROM user_integration_tokens 
            WHERE user_id = ? AND platform = ?
        """, (user_id, platform))
        
        logger.info(f"Deleted OAuth token for user {user_id}, platform {platform}")
    
    async def get_auth_status(self, user_id: str) -> Dict:
        """Get authentication status for all platforms"""
        clickup_token = await self.get_token(user_id, 'clickup')
        notion_token = await self.get_token(user_id, 'notion')
        
        return {
            'clickup': {
                'connected': clickup_token is not None,
                'workspace_name': clickup_token.get('workspace_name') if clickup_token else None,
                'connected_at': clickup_token.get('created_at') if clickup_token else None,
                'expires_at': clickup_token.get('expires_at') if clickup_token else None
            },
            'notion': {
                'connected': notion_token is not None,
                'workspace_name': notion_token.get('workspace_name') if notion_token else None,
                'connected_at': notion_token.get('created_at') if notion_token else None,
                'expires_at': notion_token.get('expires_at') if notion_token else None
            }
        }
    
    async def _get_workspace_info(self, platform: str, access_token: str) -> Dict:
        """Get workspace information after OAuth"""
        try:
            import httpx
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
    
    async def _refresh_token(self, user_id: str, platform: str, refresh_token: str) -> Optional[Dict]:
        """Refresh expired OAuth token"""
        try:
            import httpx
            
            if platform == 'clickup':
                # ClickUp token refresh (if supported)
                # Implementation depends on ClickUp's refresh token support
                pass
            
            elif platform == 'notion':
                # Notion doesn't typically support refresh tokens
                # User will need to re-authenticate
                pass
            
            return None
        except Exception as e:
            logger.error(f"Token refresh failed for {platform}: {e}")
            return None
```

### 3. Database Migrations

**File**: `integration/app/database_migrations.py`
```python
import sqlite3
import asyncio
from datetime import datetime

async def create_oauth_tables(db):
    """Create tables for OAuth token management"""
    
    # User integration tokens table
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
    
    # OAuth state tokens table (for security)
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
    
    # User preferences for integrations
    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_integration_preferences (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            default_platform TEXT,
            smart_routing BOOLEAN DEFAULT TRUE,
            auto_task_creation BOOLEAN DEFAULT TRUE,
            notification_settings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        )
    """)
    
    print("✅ OAuth tables created successfully")

async def migrate_existing_data(db):
    """Migrate any existing hardcoded token data"""
    
    # Check if there are any existing meetings or tasks that need user association
    existing_meetings = await db.fetch_all("SELECT * FROM meetings LIMIT 5")
    
    if existing_meetings:
        print(f"📊 Found {len(existing_meetings)} existing meetings")
        print("⚠️  Note: Existing data will need manual user association after OAuth implementation")
    
    print("✅ Data migration check completed")

def run_migrations():
    """Run all OAuth-related database migrations"""
    import asyncio
    import aiosqlite
    
    async def main():
        async with aiosqlite.connect("integration.db") as db:
            await create_oauth_tables(db)
            await migrate_existing_data(db)
            await db.commit()
    
    asyncio.run(main())

if __name__ == "__main__":
    run_migrations()
```

### 4. OAuth-Aware Integration Classes

**File**: `integration/app/integrations/clickup_integration_oauth.py`
```python
import httpx
from typing import Dict, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ClickUpIntegrationOAuth:
    """OAuth-aware ClickUp integration"""
    
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
        """Create ClickUp integration instance from user's stored OAuth token"""
        from ..oauth.token_store import TokenStore
        
        token_store = TokenStore(db)
        token_data = await token_store.get_token(user_id, 'clickup')
        
        if not token_data:
            raise ValueError(f"No ClickUp OAuth token found for user {user_id}")
        
        return cls(
            access_token=token_data['access_token'],
            workspace_id=token_data['workspace_id']
        )
    
    async def test_connection(self) -> bool:
        """Test if the OAuth token is valid"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/user", headers=self.headers)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"ClickUp connection test failed: {e}")
            return False
    
    async def get_teams(self) -> List[Dict]:
        """Get user's teams/workspaces"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/team", headers=self.headers)
                if response.status_code == 200:
                    return response.json().get('teams', [])
                return []
        except Exception as e:
            logger.error(f"Failed to get ClickUp teams: {e}")
            return []
    
    async def get_spaces(self, team_id: str) -> List[Dict]:
        """Get spaces within a team"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/team/{team_id}/space", headers=self.headers)
                if response.status_code == 200:
                    return response.json().get('spaces', [])
                return []
        except Exception as e:
            logger.error(f"Failed to get ClickUp spaces: {e}")
            return []
    
    async def get_lists(self, space_id: str) -> List[Dict]:
        """Get lists within a space"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/space/{space_id}/list", headers=self.headers)
                if response.status_code == 200:
                    return response.json().get('lists', [])
                return []
        except Exception as e:
            logger.error(f"Failed to get ClickUp lists: {e}")
            return []
    
    async def create_task(self, task_data: Dict) -> Dict:
        """Create a task in ClickUp using OAuth token"""
        try:
            list_id = task_data.get('list_id')
            if not list_id:
                # Try to find a default list
                teams = await self.get_teams()
                if teams:
                    spaces = await self.get_spaces(teams[0]['id'])
                    if spaces:
                        lists = await self.get_lists(spaces[0]['id'])
                        if lists:
                            list_id = lists[0]['id']
                
                if not list_id:
                    raise ValueError("No list_id provided and couldn't find default list")
            
            # Prepare task payload
            payload = {
                "name": task_data.get('title', 'Meeting Action Item'),
                "description": task_data.get('description', ''),
                "assignees": task_data.get('assignees', []),
                "tags": task_data.get('tags', []),
                "status": task_data.get('status', 'to do'),
                "priority": task_data.get('priority', 3),
                "due_date": task_data.get('due_date'),
                "time_estimate": task_data.get('time_estimate')
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/list/{list_id}/task",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    task_result = response.json()
                    logger.info(f"Created ClickUp task: {task_result.get('id')}")
                    return {
                        'success': True,
                        'task_id': task_result.get('id'),
                        'task_url': task_result.get('url'),
                        'platform': 'clickup',
                        'created_at': datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"ClickUp task creation failed: {response.text}")
                    return {
                        'success': False,
                        'error': f"API error: {response.status_code}",
                        'platform': 'clickup'
                    }
                    
        except Exception as e:
            logger.error(f"ClickUp task creation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'clickup'
            }
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/task/{task_id}", headers=self.headers)
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.error(f"Failed to get ClickUp task {task_id}: {e}")
            return None
    
    async def update_task(self, task_id: str, updates: Dict) -> Dict:
        """Update an existing task"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/task/{task_id}",
                    headers=self.headers,
                    json=updates
                )
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'task_id': task_id,
                        'platform': 'clickup'
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Update failed: {response.status_code}",
                        'platform': 'clickup'
                    }
        except Exception as e:
            logger.error(f"ClickUp task update error: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'clickup'
            }
```

### 5. Frontend Integrations Tab Component

**File**: `frontend_dashboard/src/components/integrations/IntegrationsTab.jsx`
```jsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { ExternalLink, CheckCircle, AlertCircle, Unplug, RefreshCw } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { integrationService } from '../../services/integrationService';

const IntegrationsTab = () => {
    const { user } = useAuth();
    const [integrationStatus, setIntegrationStatus] = useState({
        clickup: { 
            connected: false, 
            workspace_name: null, 
            connecting: false,
            connected_at: null,
            expires_at: null
        },
        notion: { 
            connected: false, 
            workspace_name: null, 
            connecting: false,
            connected_at: null,
            expires_at: null
        }
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (user?.id) {
            fetchIntegrationStatus();
        }
    }, [user]);

    useEffect(() => {
        // Listen for OAuth completion messages
        const handleMessage = (event) => {
            if (event.data.type === 'oauth_complete') {
                fetchIntegrationStatus();
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, []);

    const fetchIntegrationStatus = async () => {
        if (!user?.id) return;
        
        try {
            setError(null);
            const status = await integrationService.getAuthStatus(user.id);
            setIntegrationStatus(status);
        } catch (error) {
            console.error('Failed to fetch integration status:', error);
            setError('Failed to load integration status');
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
            const { auth_url } = await integrationService.initiateOAuth(platform, user.id);
            
            // Open OAuth flow in new window
            const authWindow = window.open(
                auth_url, 
                `${platform}_oauth`, 
                'width=600,height=700,scrollbars=yes,resizable=yes,centerscreen=yes'
            );

            // Poll for window closure
            const checkClosed = setInterval(() => {
                if (authWindow.closed) {
                    clearInterval(checkClosed);
                    // Wait a moment then refresh status
                    setTimeout(() => {
                        fetchIntegrationStatus();
                    }, 1000);
                }
            }, 1000);

            // Set timeout for OAuth process
            setTimeout(() => {
                if (!authWindow.closed) {
                    authWindow.close();
                    clearInterval(checkClosed);
                }
                setIntegrationStatus(prev => ({
                    ...prev,
                    [platform]: { ...prev[platform], connecting: false }
                }));
            }, 300000); // 5 minutes timeout

        } catch (error) {
            console.error(`Failed to initiate ${platform} OAuth:`, error);
            setError(`Failed to connect to ${platform}. Please try again.`);
            setIntegrationStatus(prev => ({
                ...prev,
                [platform]: { ...prev[platform], connecting: false }
            }));
        }
    };

    const handleDisconnect = async (platform) => {
        if (!user?.id) return;
        
        try {
            await integrationService.disconnect(platform, user.id);
            await fetchIntegrationStatus();
        } catch (error) {
            console.error(`Failed to disconnect ${platform}:`, error);
            setError(`Failed to disconnect from ${platform}. Please try again.`);
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
                            onError={(e) => {
                                e.target.src = `/icons/default-integration.png`;
                            }}
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
                        
                        {status.connected && (
                            <div className="space-y-2">
                                {status.workspace_name && (