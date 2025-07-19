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
            
            # Use the correct Asana client initialization
            configuration = asana.Configuration()
            configuration.access_token = access_token
            api_client = asana.ApiClient(configuration)
            self.client = asana.TasksApi(api_client)
            self.projects_api = asana.ProjectsApi(api_client)
            self.workspaces_api = asana.WorkspacesApi(api_client)
            self._initialized = True
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects in the workspace."""
        await self._ensure_initialized()
        try:
            if not self.workspace_gid:
                # Get default workspace
                workspaces_response = self.workspaces_api.get_workspaces({})
                workspaces_list = list(workspaces_response.data) if hasattr(workspaces_response, 'data') else list(workspaces_response)
                if workspaces_list and len(workspaces_list) > 0:
                    workspace = workspaces_list[0]
                    # Handle workspace object format
                    if hasattr(workspace, 'gid'):
                        self.workspace_gid = workspace.gid
                    elif isinstance(workspace, dict):
                        self.workspace_gid = workspace.get('gid')
                    else:
                        raise Exception("Invalid workspace format")
                else:
                    raise Exception("No workspace found")
            
            projects_response = self.projects_api.get_projects_for_workspace(
                self.workspace_gid, {}
            )
            projects_list = list(projects_response.data) if hasattr(projects_response, 'data') else list(projects_response)
            
            # Handle different project object formats
            projects = []
            for p in projects_list:
                if hasattr(p, 'gid') and hasattr(p, 'name'):
                    # Standard API response object
                    projects.append({"gid": p.gid, "name": p.name})
                elif isinstance(p, dict):
                    # Dict response
                    projects.append({"gid": p.get('gid', 'unknown'), "name": p.get('name', 'Unknown Project')})
                else:
                    # Fallback
                    projects.append({"gid": str(p), "name": "Unknown Project"})
            
            return projects
        except Exception as e:
            raise Exception(f"Failed to fetch Asana projects: {str(e)}")
    
    async def get_tasks(self, project_gid: str, completed: bool = False) -> List[Dict[str, Any]]:
        """Get tasks from a specific project."""
        await self._ensure_initialized()
        try:
            if project_gid:
                tasks = self.client.get_tasks_for_project(
                    project_gid=project_gid,
                    opt_fields=["name", "notes", "completed", "assignee", "due_on"]
                )
            else:
                # Get tasks from all projects
                tasks = self.client.get_tasks(
                    opt_fields=["name", "notes", "completed", "assignee", "due_on"]
                )
            return [{"gid": t.gid, "name": t.name, "completed": t.completed} for t in tasks.data]
        except Exception as e:
            raise Exception(f"Failed to fetch Asana tasks: {str(e)}")
    
    async def create_task(self, project_gid: Optional[str], task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in Asana."""
        await self._ensure_initialized()
        try:
            # Ensure we have a workspace
            if not self.workspace_gid:
                workspaces_response = self.workspaces_api.get_workspaces({})
                workspaces_list = list(workspaces_response.data) if hasattr(workspaces_response, 'data') else list(workspaces_response)
                if workspaces_list and len(workspaces_list) > 0:
                    workspace = workspaces_list[0]
                    # Handle workspace object format
                    if hasattr(workspace, 'gid'):
                        self.workspace_gid = workspace.gid
                    elif isinstance(workspace, dict):
                        self.workspace_gid = workspace.get('gid')
                    else:
                        raise Exception("Invalid workspace format")
                else:
                    raise Exception("No workspace found")
            
            # Create task request body
            body = {
                "data": {
                    "name": task_data.get('name'),
                    "notes": task_data.get('notes', ''),
                }
            }
            
            # Add project if specified, otherwise use workspace
            if project_gid:
                body["data"]["projects"] = [project_gid]
            else:
                # If no project specified, create task in workspace (will go to user's My Tasks)
                body["data"]["workspace"] = self.workspace_gid
            
            # Add optional fields
            if task_data.get('assignee'):
                body["data"]["assignee"] = task_data.get('assignee')
            if task_data.get('due_on'):
                body["data"]["due_on"] = task_data.get('due_on')
            
            task_response = self.client.create_task(body, {})
            
            # Handle different response formats
            if hasattr(task_response, 'data'):
                # Standard API response with .data attribute
                task_data = task_response.data
                if hasattr(task_data, 'gid'):
                    return {"gid": task_data.gid, "name": task_data.name, "created": True}
                elif isinstance(task_data, dict):
                    return {"gid": task_data.get('gid', 'unknown'), "name": task_data.get('name', 'Task created'), "created": True}
            elif isinstance(task_response, dict):
                # Direct dict response
                if 'data' in task_response:
                    data = task_response['data']
                    return {"gid": data.get('gid', 'unknown'), "name": data.get('name', 'Task created'), "created": True}
                else:
                    return {"gid": task_response.get('gid', 'unknown'), "name": task_response.get('name', 'Task created'), "created": True}
            
            # Fallback
            return {"gid": "unknown", "name": "Task created successfully", "created": True}
        except Exception as e:
            raise Exception(f"Failed to create Asana task: {str(e)}")
    
    async def update_task(self, task_gid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task."""
        await self._ensure_initialized()
        try:
            body = {"data": updates}
            task = self.client.update_task(task_gid, body, {})
            return {"gid": task.data.gid, "name": task.data.name, "updated": True}
        except Exception as e:
            raise Exception(f"Failed to update Asana task: {str(e)}")
    
    async def complete_task(self, task_gid: str) -> Dict[str, Any]:
        """Mark a task as completed."""
        return await self.update_task(task_gid, {'completed': True})
    
    async def get_task_details(self, task_gid: str) -> Dict[str, Any]:
        """Get detailed information about a specific task."""
        await self._ensure_initialized()
        try:
            task = self.client.get_task(task_gid, {
                "opt_fields": ["name", "notes", "completed", "assignee", "due_on", "projects", "tags"]
            })
            return {
                "gid": task.data.gid,
                "name": task.data.name,
                "notes": task.data.notes,
                "completed": task.data.completed,
                "assignee": task.data.assignee,
                "due_on": task.data.due_on,
                "projects": [{"gid": p.gid, "name": p.name} for p in task.data.projects],
                "tags": [{"gid": t.gid, "name": t.name} for t in task.data.tags]
            }
        except Exception as e:
            raise Exception(f"Failed to get Asana task details: {str(e)}")
    
    async def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Search for tasks by name or description."""
        await self._ensure_initialized()
        try:
            # Get all tasks and filter by query (basic implementation)
            tasks = self.client.get_tasks(
                opt_fields=["name", "notes", "completed"]
            )
            filtered_tasks = []
            for task in tasks.data:
                if query.lower() in task.name.lower() or (task.notes and query.lower() in task.notes.lower()):
                    filtered_tasks.append({
                        "gid": task.gid,
                        "name": task.name,
                        "completed": task.completed
                    })
            return filtered_tasks
        except Exception as e:
            raise Exception(f"Failed to search Asana tasks: {str(e)}")