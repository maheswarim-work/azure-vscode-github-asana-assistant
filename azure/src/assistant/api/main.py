from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

from ..ai.assistant_core import AIAssistant
from ..config import settings


app = FastAPI(
    title="Azure VSCode GitHub Asana Assistant",
    description="AI assistant integrating Asana, GitHub, and VSCode",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global assistant instance
assistant = AIAssistant()


class CommandRequest(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None


class AsanaTaskRequest(BaseModel):
    project_gid: str
    name: str
    notes: Optional[str] = None
    assignee: Optional[str] = None
    due_on: Optional[str] = None


class GitHubIssueRequest(BaseModel):
    repo_name: str
    title: str
    body: Optional[str] = None
    assignee: Optional[str] = None
    labels: Optional[list] = None


class SyncRequest(BaseModel):
    source_platform: str
    target_platform: str
    source_id: str
    additional_params: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "Azure VSCode GitHub Asana Assistant API",
        "version": "0.1.0",
        "status": "running"
    }


@app.post("/command")
async def process_command(request: CommandRequest):
    """Process a natural language command."""
    try:
        result = await assistant.process_command(request.command, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get status summary from all platforms."""
    try:
        status = await assistant.get_status_summary()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Asana endpoints
@app.get("/asana/projects")
async def get_asana_projects():
    """Get all Asana projects."""
    try:
        projects = await assistant.asana_client.get_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/asana/projects/{project_gid}/tasks")
async def get_asana_tasks(project_gid: str, completed: bool = False):
    """Get tasks from an Asana project."""
    try:
        tasks = await assistant.asana_client.get_tasks(project_gid, completed)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/asana/tasks")
async def create_asana_task(request: AsanaTaskRequest):
    """Create a new Asana task."""
    try:
        task_data = {
            "name": request.name,
            "notes": request.notes,
            "assignee": request.assignee,
            "due_on": request.due_on
        }
        task = await assistant.asana_client.create_task(request.project_gid, task_data)
        return {"task": task}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# GitHub endpoints
@app.get("/github/repositories")
async def get_github_repositories():
    """Get all GitHub repositories."""
    try:
        repos = await assistant.github_client.get_repositories()
        return {"repositories": repos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/repositories/{repo_name}/issues")
async def get_github_issues(repo_name: str, state: str = "open"):
    """Get issues from a GitHub repository."""
    try:
        issues = await assistant.github_client.get_issues(repo_name, state)
        return {"issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/github/issues")
async def create_github_issue(request: GitHubIssueRequest):
    """Create a new GitHub issue."""
    try:
        issue_data = {
            "title": request.title,
            "body": request.body,
            "assignee": request.assignee,
            "labels": request.labels or []
        }
        issue = await assistant.github_client.create_issue(request.repo_name, issue_data)
        return {"issue": issue}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# VSCode endpoints
@app.post("/vscode/open-project")
async def open_vscode_project(project_path: str):
    """Open a project in VSCode."""
    try:
        success = await assistant.vscode_integration.open_project(project_path)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vscode/workspace/files")
async def get_workspace_files(pattern: Optional[str] = None):
    """Get files in the current workspace."""
    try:
        files = await assistant.vscode_integration.get_workspace_files(pattern)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vscode/git/status")
async def get_git_status():
    """Get git status of the current workspace."""
    try:
        status = await assistant.vscode_integration.get_git_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sync endpoints
@app.post("/sync")
async def sync_platforms(request: SyncRequest):
    """Sync data between platforms."""
    try:
        if request.source_platform == "asana" and request.target_platform == "github":
            result = await assistant._handle_multi_platform_action(
                "sync_task_to_issue",
                {
                    "task_gid": request.source_id,
                    **request.additional_params
                },
                f"Sync Asana task {request.source_id} to GitHub"
            )
        elif request.source_platform == "github" and request.target_platform == "asana":
            result = await assistant._handle_multi_platform_action(
                "sync_issue_to_task",
                {
                    "issue_number": int(request.source_id),
                    **request.additional_params
                },
                f"Sync GitHub issue {request.source_id} to Asana"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Sync from {request.source_platform} to {request.target_platform} not supported"
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


if __name__ == "__main__":
    uvicorn.run(
        "assistant.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )