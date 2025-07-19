import openai
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..config import settings
from ..integrations.asana_client import AsanaClient
from ..integrations.github_client import GitHubClient
from ..integrations.vscode_integration import VSCodeIntegration


class AIAssistant:
    def __init__(self):
        self.asana_client = AsanaClient()
        self.github_client = GitHubClient()
        self.vscode_integration = VSCodeIntegration()
        self._openai_initialized = False
    
    async def _ensure_openai_initialized(self):
        """Ensure OpenAI is initialized with proper API key."""
        if not self._openai_initialized:
            api_key = await settings.get_openai_api_key()
            if not api_key:
                raise Exception("OpenAI API key not found in Key Vault or environment variables")
            
            openai.api_key = api_key
            self._openai_initialized = True
        
        self.system_prompt = """
        You are an AI assistant that helps developers integrate their workflow between Asana, GitHub, and VSCode.
        
        Your capabilities include:
        1. Managing Asana tasks and projects
        2. Creating and managing GitHub issues and pull requests
        3. Setting up VSCode workspaces and configurations
        4. Syncing information between all three platforms
        5. Providing intelligent suggestions for project management
        
        Always provide clear, actionable responses and ask for clarification when needed.
        """
    
    async def process_command(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user command and execute appropriate actions."""
        try:
            # Analyze the user input to determine intent
            intent = await self._analyze_intent(user_input, context)
            
            # Execute the appropriate action based on intent
            result = await self._execute_action(intent, user_input, context)
            
            return {
                "success": True,
                "intent": intent,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_intent(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze user input to determine intent and required actions."""
        await self._ensure_openai_initialized()
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"""
                    Analyze this user request and determine the intent and required actions:
                    
                    User Input: {user_input}
                    Context: {json.dumps(context or {}, indent=2)}
                    
                    Respond with a JSON object containing:
                    - intent: The main intent (e.g., "create_task", "sync_issue", "setup_project")
                    - platform: Primary platform involved ("asana", "github", "vscode", "multi")
                    - action: Specific action to take
                    - parameters: Required parameters for the action
                    - confidence: Confidence level (0-1)
                    """
                }
            ]
            
            response = openai.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=settings.max_tokens,
                temperature=0.3
            )
            
            intent_text = response.choices[0].message.content
            return json.loads(intent_text)
        except Exception as e:
            raise Exception(f"Failed to analyze intent: {str(e)}")
    
    async def _execute_action(self, intent: Dict[str, Any], user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the determined action."""
        action = intent.get("action")
        platform = intent.get("platform")
        parameters = intent.get("parameters", {})
        
        if platform == "asana":
            return await self._handle_asana_action(action, parameters, user_input)
        elif platform == "github":
            return await self._handle_github_action(action, parameters, user_input)
        elif platform == "vscode":
            return await self._handle_vscode_action(action, parameters, user_input)
        elif platform == "multi":
            return await self._handle_multi_platform_action(action, parameters, user_input)
        else:
            return await self._generate_response(user_input, context)
    
    async def _handle_asana_action(self, action: str, parameters: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Handle Asana-specific actions."""
        try:
            if action in ["create_task", "create_new_task"]:
                # Extract task name from parameters or user input
                task_name = parameters.get("task_name") or parameters.get("name")
                if not task_name:
                    # Extract from user input as fallback
                    task_name = user_input.replace("Create a task for", "").replace("Create task", "").strip()
                
                task_data = {
                    "name": task_name,
                    "notes": parameters.get("notes", f"Task created via AI assistant: {user_input}")
                }
                
                task = await self.asana_client.create_task(
                    parameters.get("project_gid"),
                    task_data
                )
                return {"action": "task_created", "data": task}
            
            elif action == "get_tasks":
                tasks = await self.asana_client.get_tasks(
                    parameters.get("project_gid"),
                    parameters.get("completed", False)
                )
                return {"action": "tasks_retrieved", "data": tasks}
            
            elif action == "update_task":
                task = await self.asana_client.update_task(
                    parameters.get("task_gid"),
                    parameters.get("updates")
                )
                return {"action": "task_updated", "data": task}
            
            elif action == "search_tasks":
                tasks = await self.asana_client.search_tasks(
                    parameters.get("query"),
                    parameters.get("project_gid")
                )
                return {"action": "tasks_found", "data": tasks}
            
            else:
                return {"error": f"Unknown Asana action: {action}"}
        except Exception as e:
            return {"error": f"Asana action failed: {str(e)}"}
    
    async def _handle_github_action(self, action: str, parameters: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Handle GitHub-specific actions."""
        try:
            if action == "create_issue":
                issue = await self.github_client.create_issue(
                    parameters.get("repo_name"),
                    parameters.get("issue_data")
                )
                return {"action": "issue_created", "data": issue}
            
            elif action == "get_issues":
                issues = await self.github_client.get_issues(
                    parameters.get("repo_name"),
                    parameters.get("state", "open")
                )
                return {"action": "issues_retrieved", "data": issues}
            
            elif action == "create_pr":
                pr = await self.github_client.create_pull_request(
                    parameters.get("repo_name"),
                    parameters.get("pr_data")
                )
                return {"action": "pr_created", "data": pr}
            
            elif action == "get_repositories":
                repos = await self.github_client.get_repositories()
                return {"action": "repositories_retrieved", "data": repos}
            
            else:
                return {"error": f"Unknown GitHub action: {action}"}
        except Exception as e:
            return {"error": f"GitHub action failed: {str(e)}"}
    
    async def _handle_vscode_action(self, action: str, parameters: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Handle VSCode-specific actions."""
        try:
            if action == "open_project":
                success = await self.vscode_integration.open_project(
                    parameters.get("project_path")
                )
                return {"action": "project_opened", "success": success}
            
            elif action == "setup_project":
                success = await self.vscode_integration.setup_project_structure(
                    parameters.get("project_type")
                )
                return {"action": "project_setup", "success": success}
            
            elif action == "create_task":
                success = await self.vscode_integration.create_task(
                    parameters.get("task_config")
                )
                return {"action": "vscode_task_created", "success": success}
            
            elif action == "install_extension":
                success = await self.vscode_integration.install_extension(
                    parameters.get("extension_id")
                )
                return {"action": "extension_installed", "success": success}
            
            else:
                return {"error": f"Unknown VSCode action: {action}"}
        except Exception as e:
            return {"error": f"VSCode action failed: {str(e)}"}
    
    async def _handle_multi_platform_action(self, action: str, parameters: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Handle actions that involve multiple platforms."""
        try:
            if action == "sync_task_to_issue":
                # Get Asana task
                task = await self.asana_client.get_task_by_gid(parameters.get("task_gid"))
                
                # Create GitHub issue
                issue_data = {
                    "title": task["name"],
                    "body": f"Synced from Asana task: {task.get('notes', '')}\n\nTask ID: {task['gid']}",
                    "labels": ["asana-sync"]
                }
                issue = await self.github_client.create_issue(
                    parameters.get("repo_name"),
                    issue_data
                )
                
                # Update Asana task with GitHub link
                await self.asana_client.add_comment_to_task(
                    parameters.get("task_gid"),
                    f"GitHub issue created: {issue['html_url']}"
                )
                
                return {
                    "action": "task_synced_to_issue",
                    "asana_task": task,
                    "github_issue": issue
                }
            
            elif action == "sync_issue_to_task":
                # Get GitHub issue
                issues = await self.github_client.get_issues(
                    parameters.get("repo_name"),
                    "open"
                )
                issue = next((i for i in issues if i["number"] == parameters.get("issue_number")), None)
                
                if not issue:
                    return {"error": "Issue not found"}
                
                # Create Asana task
                task_data = {
                    "name": issue["title"],
                    "notes": f"Synced from GitHub issue: {issue['body']}\n\nIssue URL: {issue['html_url']}"
                }
                task = await self.asana_client.create_task(
                    parameters.get("project_gid"),
                    task_data
                )
                
                # Add comment to GitHub issue
                await self.github_client.add_comment_to_issue(
                    parameters.get("repo_name"),
                    parameters.get("issue_number"),
                    f"Asana task created for tracking this issue."
                )
                
                return {
                    "action": "issue_synced_to_task",
                    "github_issue": issue,
                    "asana_task": task
                }
            
            else:
                return {"error": f"Unknown multi-platform action: {action}"}
        except Exception as e:
            return {"error": f"Multi-platform action failed: {str(e)}"}
    
    async def _generate_response(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a conversational response using OpenAI."""
        await self._ensure_openai_initialized()
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            if context:
                messages.insert(1, {
                    "role": "assistant",
                    "content": f"Context: {json.dumps(context, indent=2)}"
                })
            
            response = openai.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            return {
                "action": "conversational_response",
                "response": response.choices[0].message.content
            }
        except Exception as e:
            return {"error": f"Failed to generate response: {str(e)}"}
    
    async def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current status across all platforms."""
        try:
            # Get Asana projects and tasks
            asana_projects = await self.asana_client.get_projects()
            
            # Get GitHub repositories
            github_repos = await self.github_client.get_repositories()
            
            # Get VSCode workspace info
            vscode_files = await self.vscode_integration.get_workspace_files()
            git_status = await self.vscode_integration.get_git_status()
            
            return {
                "asana": {
                    "projects_count": len(asana_projects),
                    "projects": asana_projects[:5]  # Limit to first 5
                },
                "github": {
                    "repositories_count": len(github_repos),
                    "repositories": github_repos[:5]  # Limit to first 5
                },
                "vscode": {
                    "workspace_files_count": len(vscode_files),
                    "git_status": git_status
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to get status summary: {str(e)}"}