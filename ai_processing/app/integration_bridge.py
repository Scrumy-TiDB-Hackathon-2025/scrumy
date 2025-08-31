"""
Integration Bridge for AI Processing

This module provides a bridge between the AI processing system and the integration system.
It handles task creation across multiple platforms (Notion, Slack, ClickUp) based on 
AI-extracted tasks from meeting transcripts.

CURRENT LIMITATIONS (TODO: Update when database support is available):
- meeting_id: Not supported by current database schema
- due_date: Not supported by current database schema

The integration system code supports these fields, but they are excluded here
to prevent database errors until schema is updated.
"""

import sys
import os
import asyncio
from typing import Dict, List, Optional
import logging

# Load shared environment variables first
def load_shared_env():
    """Load shared environment variables from /shared/.tidb.env"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    shared_env_path = os.path.join(project_root, 'shared', '.tidb.env')
    
    if os.path.exists(shared_env_path):
        with open(shared_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
        logging.info(f"Loaded shared environment from {shared_env_path}")
    else:
        logging.warning(f"Shared environment file not found: {shared_env_path}")

# Global flag to track integration availability
INTEGRATION_AVAILABLE = False
ToolRegistry = None
IntegrationManager = None

def _import_integration_system():
    """Import integration system modules after path setup"""
    global INTEGRATION_AVAILABLE, ToolRegistry, IntegrationManager
    
    if INTEGRATION_AVAILABLE:
        return True
    
    # Load shared environment
    load_shared_env()
    
    # Use absolute path to integration directory
    # Get the absolute path to this file and work backwards
    current_file = os.path.abspath(__file__)
    ai_processing_dir = os.path.dirname(os.path.dirname(current_file))  # /path/to/ai_processing
    project_root = os.path.dirname(ai_processing_dir)  # /path/to/scrumy-clean
    integration_path = os.path.join(project_root, 'integration')
    
    logging.info(f"DEBUG: Current file: {current_file}")
    logging.info(f"DEBUG: AI processing dir: {ai_processing_dir}")
    logging.info(f"DEBUG: Project root: {project_root}")
    logging.info(f"DEBUG: Integration path: {integration_path}")
    logging.info(f"DEBUG: Integration path exists: {os.path.exists(integration_path)}")
    
    if not os.path.exists(integration_path):
        logging.warning(f"Integration path does not exist: {integration_path}")
        return False
    
    app_path = os.path.join(integration_path, 'app')
    tools_path = os.path.join(app_path, 'tools.py')
    logging.info(f"DEBUG: App path exists: {os.path.exists(app_path)}")
    logging.info(f"DEBUG: Tools path exists: {os.path.exists(tools_path)}")
    
    # Remove any conflicting app paths and add integration path first
    # Remove AI processing app path to avoid conflicts
    ai_app_path = os.path.join(ai_processing_dir, 'app')
    if ai_app_path in sys.path:
        sys.path.remove(ai_app_path)
        logging.info(f"DEBUG: Removed conflicting AI app path: {ai_app_path}")
    
    # Store reference to AI processing app module before clearing
    ai_app_module = sys.modules.get('app')
    ai_app_submodules = {key: sys.modules[key] for key in sys.modules.keys() if key.startswith('app.')}
    
    # Clear any cached 'app' module to avoid conflicts during integration import
    if 'app' in sys.modules:
        del sys.modules['app']
        logging.info(f"DEBUG: Temporarily cleared 'app' module from sys.modules cache")
    
    # Also clear any app.* submodules that might be cached
    modules_to_clear = [key for key in sys.modules.keys() if key.startswith('app.')]
    for module_key in modules_to_clear:
        del sys.modules[module_key]
        logging.info(f"DEBUG: Temporarily cleared '{module_key}' from sys.modules cache")
    
    # Add integration path to sys.path if not already there
    if integration_path not in sys.path:
        sys.path.insert(0, integration_path)
        logging.info(f"DEBUG: Added to sys.path: {integration_path}")
    else:
        # Move it to the front if it's already there
        sys.path.remove(integration_path)
        sys.path.insert(0, integration_path)
        logging.info(f"DEBUG: Moved integration path to front of sys.path")
    
    try:
        from app.tools import ToolRegistry as _ToolRegistry
        from app.integrations import IntegrationManager as _IntegrationManager
        ToolRegistry = _ToolRegistry
        IntegrationManager = _IntegrationManager
        INTEGRATION_AVAILABLE = True
        logging.info("Integration system imported successfully")
        
        # Restore AI processing app modules after successful integration import
        if ai_app_module:
            sys.modules['app'] = ai_app_module
            logging.info(f"DEBUG: Restored AI processing 'app' module")
        
        for module_key, module_obj in ai_app_submodules.items():
            sys.modules[module_key] = module_obj
            logging.info(f"DEBUG: Restored AI processing '{module_key}' module")
        
        return True
    except ImportError as e:
        logging.warning(f"Integration system not available: {e}")
        logging.warning(f"DEBUG: sys.path first 5 entries: {sys.path[:5]}")
        logging.warning(f"DEBUG: Current working directory: {os.getcwd()}")
        
        # Restore AI processing app modules after failed integration import
        if ai_app_module:
            sys.modules['app'] = ai_app_module
            logging.info(f"DEBUG: Restored AI processing 'app' module after failed import")
        
        for module_key, module_obj in ai_app_submodules.items():
            sys.modules[module_key] = module_obj
            logging.info(f"DEBUG: Restored AI processing '{module_key}' module after failed import")
        
        # Try to diagnose the issue further
        try:
            import app
            logging.warning(f"DEBUG: 'app' module found at: {getattr(app, '__file__', 'No __file__ attribute')}")
            logging.warning(f"DEBUG: 'app' module path: {getattr(app, '__path__', 'No __path__ attribute')}")
            logging.warning(f"DEBUG: 'app' module contents: {dir(app)}")
            
            # Check if tools module exists in this app
            try:
                import app.tools
                logging.warning(f"DEBUG: app.tools found at: {getattr(app.tools, '__file__', 'No __file__ attribute')}")
            except ImportError as tools_e:
                logging.warning(f"DEBUG: app.tools not found: {tools_e}")
                
        except Exception as app_e:
            logging.warning(f"DEBUG: Could not import 'app' module: {app_e}")
        
        INTEGRATION_AVAILABLE = False
        return False

# Import our new database task manager
try:
    from .database_task_manager import DatabaseTaskManager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Database task manager not available: {e}")
    DATABASE_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIProcessingIntegrationBridge:
    """
    Bridge between AI processing and integration system.
    
    Handles:
    - Task data transformation from AI format to integration format
    - Error handling to ensure AI processing continues even if integrations fail
    - Configuration management for integration settings
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the integration bridge.
        
        Args:
            config: Integration configuration dict with settings like:
                   {
                       "enabled": True,
                       "platforms": ["notion", "slack", "clickup"],
                       "mock_mode": False
                   }
        """
        self.config = config or {}
        self.mock_mode = self.config.get("mock_mode", False)
        
        # Initialize database task manager for two-layer architecture
        if DATABASE_MANAGER_AVAILABLE:
            self.db_manager = DatabaseTaskManager()
            logger.info("Database task manager initialized")
        else:
            self.db_manager = None
            logger.warning("Database task manager not available")
        
        # Try to import integration system and set enabled based on result
        config_enabled = self.config.get("enabled", True)
        if config_enabled and _import_integration_system():
            try:
                self.tools_registry = ToolRegistry()
                self.integration_manager = IntegrationManager()
                self.enabled = True
                logger.info("Integration bridge initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize integration components: {e}")
                self.enabled = False
        else:
            self.enabled = False
            if not config_enabled:
                logger.info("Integration bridge disabled by configuration")
            else:
                logger.info("Integration bridge disabled - import failed")
    
    def _transform_ai_task_to_integration_format(self, ai_task: Dict) -> Dict:
        """
        Transform AI-extracted task to integration system format.
        
        Current supported fields (database limitations):
        - title (required)
        - description (optional)
        - assignee (optional)
        - priority (optional, defaults to 'medium')
        
        TODO: Add when database supports:
        - meeting_id: For tracking which meeting the task came from
        - due_date: For task scheduling
        
        Args:
            ai_task: Task dict from AI processing system
            
        Returns:
            Dict formatted for integration system
        """
        # Extract and validate core fields
        title = ai_task.get("title", "").strip()
        if not title:
            raise ValueError("Task title is required")
        
        description = ai_task.get("description", "").strip()
        assignee = ai_task.get("assignee", "").strip()
        priority = ai_task.get("priority", "medium").lower()
        
        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            logger.warning(f"Invalid priority '{priority}', defaulting to 'medium'")
            priority = "medium"
        
        integration_task = {
            "title": title,
            "description": description,
            "assignee": assignee,
            "priority": priority
        }
        
        # TODO: Uncomment when database supports these fields
        # meeting_id = ai_task.get("meeting_id")
        # if meeting_id:
        #     integration_task["meeting_id"] = meeting_id
        #
        # due_date = ai_task.get("due_date")  
        # if due_date:
        #     integration_task["due_date"] = due_date
        
        return integration_task
    
    async def create_tasks_from_ai_results(self, ai_tasks: List[Dict], 
                                         meeting_context: Optional[Dict] = None) -> Dict:
        """
        Create tasks in integration platforms using two-layer architecture.
        
        Args:
            ai_tasks: List of tasks extracted by AI processing (with all fields)
            meeting_context: Optional context about the meeting
            
        Returns:
            Dict with integration results and statistics
        """
        if not self.enabled:
            return {
                "integration_enabled": False,
                "reason": "Integration system disabled or not available",
                "tasks_processed": 0,
                "tasks_created": 0,
                "successful_integrations": [],
                "failed_integrations": [],
                "errors": []
            }
        
        if not ai_tasks:
            return {
                "integration_enabled": True,
                "tasks_processed": 0,
                "tasks_created": 0,
                "successful_integrations": [],
                "failed_integrations": [],
                "errors": []
            }
        
        # Use two-layer architecture if database manager is available
        if self.db_manager:
            meeting_id = meeting_context.get('meeting_id', f"meeting_{int(asyncio.get_event_loop().time())}") if meeting_context else f"meeting_{int(asyncio.get_event_loop().time())}"
            
            # Layer 1: Store all AI fields in database
            storage_result = self.db_manager.store_comprehensive_tasks(ai_tasks, meeting_id)
            
            # Layer 2: Get filtered tasks for integration platforms
            integration_tasks = self.db_manager.get_integration_tasks(
                storage_result["stored_tasks"], 
                platform="integration"
            )
            
            logger.info(f"Two-layer architecture: {len(ai_tasks)} AI tasks → {len(storage_result['stored_tasks'])} stored → {len(integration_tasks)} filtered for integration")
        else:
            # Fallback to old method if database manager not available
            integration_tasks = [self._transform_ai_task_to_integration_format(task) for task in ai_tasks]
            logger.warning("Using fallback task transformation (database manager not available)")
        
        results = {
            "integration_enabled": True,
            "tasks_processed": len(ai_tasks),
            "tasks_created": 0,
            "successful_integrations": [],
            "failed_integrations": [],
            "task_urls": {},
            "errors": []
        }
        
        # Initialize pipeline logger if available from meeting context
        pipeline_logger = meeting_context.get('pipeline_logger') if meeting_context else None
        
        logger.info(f"Processing {len(integration_tasks)} filtered tasks for integration platforms")
        
        for i, integration_task in enumerate(integration_tasks):
            try:
                # Log task extraction if logger available
                if pipeline_logger:
                    pipeline_logger.log_task_extraction({
                        "tasks": [integration_task],
                        "summary": meeting_context.get('summary', '') if meeting_context else ''
                    })
                
                # Create task using tools registry with filtered fields
                result = await self.tools_registry.create_task_everywhere(
                    title=integration_task["title"],
                    description=integration_task["description"],
                    assignee=integration_task["assignee"],
                    priority=integration_task["priority"]
                )
                
                # Log task creation result if logger available
                if pipeline_logger:
                    for platform, url in result.get("task_urls", {}).items():
                        pipeline_logger.log_task_creation(platform, integration_task, {
                            "success": True,
                            "url": url,
                            "platform_response": result.get(f"{platform}_response", {})
                        })
                
                if result.get("task_created"):
                    results["tasks_created"] += 1
                    
                    # Track successful integrations
                    integrations_used = result.get("integrations_used", [])
                    for integration in integrations_used:
                        if integration not in results["successful_integrations"]:
                            results["successful_integrations"].append(integration)
                    
                    # Collect task URLs
                    task_urls = result.get("task_urls", {})
                    for platform, url in task_urls.items():
                        if platform not in results["task_urls"]:
                            results["task_urls"][platform] = []
                        results["task_urls"][platform].append(url)
                    
                    logger.info(f"Task {i+1} created successfully: {integration_task['title']}")
                else:
                    error_msg = f"Task {i+1} creation failed: {result.get('error', 'Unknown error')}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
                
            except Exception as e:
                error_msg = f"Task {i+1} processing failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Determine failed integrations (platforms that were attempted but failed)
        attempted_platforms = self.config.get("platforms", ["notion", "slack", "clickup"])
        results["failed_integrations"] = [
            platform for platform in attempted_platforms 
            if platform not in results["successful_integrations"]
        ]
        
        logger.info(f"Integration complete: {results['tasks_created']}/{results['tasks_processed']} tasks created")
        return results
    
    async def send_meeting_summary_notification(self, meeting_summary: str, 
                                              tasks_created: int = 0,
                                              meeting_context: Optional[Dict] = None) -> Dict:
        """
        Send meeting summary notification to configured channels.
        
        Args:
            meeting_summary: AI-generated meeting summary
            tasks_created: Number of tasks created from the meeting
            meeting_context: Optional meeting context
            
        Returns:
            Dict with notification results
        """
        if not self.enabled:
            return {
                "notification_sent": False,
                "reason": "Integration system disabled"
            }
        
        try:
            # TODO: Implement meeting summary notification
            # This would use the Slack integration to send a summary
            # For now, just log the summary
            logger.info(f"Meeting summary ready for notification: {meeting_summary[:100]}...")
            logger.info(f"Tasks created: {tasks_created}")
            
            return {
                "notification_sent": True,
                "summary_length": len(meeting_summary),
                "tasks_mentioned": tasks_created
            }
            
        except Exception as e:
            logger.error(f"Failed to send meeting summary notification: {e}")
            return {
                "notification_sent": False,
                "error": str(e)
            }

# Factory function for easy integration
def create_integration_bridge(config: Optional[Dict] = None) -> AIProcessingIntegrationBridge:
    """
    Factory function to create an integration bridge instance.
    
    Args:
        config: Optional configuration dict
        
    Returns:
        AIProcessingIntegrationBridge instance
    """
    return AIProcessingIntegrationBridge(config)

# Default configuration for AI processing
DEFAULT_INTEGRATION_CONFIG = {
    "enabled": True,
    "platforms": ["notion", "slack", "clickup"],
    "mock_mode": False,
    "timeout_seconds": 30
}