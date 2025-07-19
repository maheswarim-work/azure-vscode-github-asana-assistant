import asana
from typing import List, Dict, Any, Optional
from ..config import settings


class AsanaClient:
    def __init__(self):
        self.client = None
        self.workspace_gid = settings.asana_workspace_gid
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure the Asana client is initialized with proper credentials."""
        if not self._initialized:
            access_token = await settings.get_asana_access_token()
            if not access_token:
                raise Exception("Asana access token not found in Key Vault or environment variables")
            
            self.client = asana.Client.access_token(access_token)
            self._initialized = True
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects in the workspace."""
        await self._ensure_initialized()
        try:
            projects = list(self.client.projects.get_projects({
                'workspace': self.workspace_gid
            }))
            return projects
        except Exception as e:
            raise Exception(f"Failed to fetch Asana projects: {str(e)}")
    
    async def get_tasks(self, project_gid: str, completed: bool = False) -> List[Dict[str, Any]]:
        """Get tasks from a specific project."""
        await self._ensure_initialized()
        try:
            tasks = list(self.client.tasks.get_tasks({
                'project': project_gid,
                'completed_since': 'now' if not completed else None,
                'opt_fields': [
                    'name', 'notes', 'completed', 'assignee', 'due_on',
                    'tags', 'custom_fields', 'created_at', 'modified_at'
                ]
            }))
            return tasks
        except Exception as e:
            raise Exception(f"Failed to fetch Asana tasks: {str(e)}")
    
    async def create_task(self, project_gid: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in Asana."""
        await self._ensure_initialized()
        try:
            task = self.client.tasks.create_task({
                'name': task_data.get('name'),
                'notes': task_data.get('notes', ''),
                'projects': [project_gid],
                'assignee': task_data.get('assignee'),
                'due_on': task_data.get('due_on'),
            })
            return task
        except Exception as e:
            raise Exception(f"Failed to create Asana task: {str(e)}")
    
    async def update_task(self, task_gid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task."""
        await self._ensure_initialized()
        try:
            task = self.client.tasks.update_task(task_gid, updates)
            return task
        except Exception as e:
            raise Exception(f"Failed to update Asana task: {str(e)}")
    
    async def complete_task(self, task_gid: str) -> Dict[str, Any]:
        """Mark a task as completed."""
        return await self.update_task(task_gid, {'completed': True})
    
    async def get_task_by_gid(self, task_gid: str) -> Dict[str, Any]:
        """Get a specific task by its GID."""
        await self._ensure_initialized()
        try:
            task = self.client.tasks.get_task(task_gid, {
                'opt_fields': [
                    'name', 'notes', 'completed', 'assignee', 'due_on',
                    'tags', 'custom_fields', 'created_at', 'modified_at',
                    'projects'
                ]
            })
            return task
        except Exception as e:
            raise Exception(f"Failed to fetch Asana task: {str(e)}")
    
    async def search_tasks(self, query: str, project_gid: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for tasks by name or content."""
        await self._ensure_initialized()
        try:
            search_params = {
                'workspace': self.workspace_gid,
                'text': query,
                'resource_type': 'task'
            }
            if project_gid:
                search_params['projects.any'] = project_gid
            
            results = list(self.client.search.search_in_workspace(
                self.workspace_gid, search_params
            ))
            return results.get('data', [])
        except Exception as e:
            raise Exception(f"Failed to search Asana tasks: {str(e)}")
    
    async def get_team_members(self) -> List[Dict[str, Any]]:
        """Get all team members in the workspace."""
        await self._ensure_initialized()
        try:
            users = list(self.client.users.get_users({
                'workspace': self.workspace_gid
            }))
            return users
        except Exception as e:
            raise Exception(f"Failed to fetch team members: {str(e)}")
    
    async def add_comment_to_task(self, task_gid: str, comment: str) -> Dict[str, Any]:
        """Add a comment to a task."""
        await self._ensure_initialized()
        try:
            story = self.client.stories.create_story({
                'task': task_gid,
                'text': comment
            })
            return story
        except Exception as e:
            raise Exception(f"Failed to add comment to task: {str(e)}")