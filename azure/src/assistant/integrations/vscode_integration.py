import json
import subprocess
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class VSCodeIntegration:
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.vscode_settings_path = self.project_path / ".vscode" / "settings.json"
        self.vscode_tasks_path = self.project_path / ".vscode" / "tasks.json"
        self.vscode_launch_path = self.project_path / ".vscode" / "launch.json"
    
    async def open_project(self, project_path: str) -> bool:
        """Open a project in VSCode."""
        try:
            result = subprocess.run(
                ["code", project_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise Exception(f"Failed to open VSCode: {str(e)}")
    
    async def open_file(self, file_path: str, line_number: Optional[int] = None) -> bool:
        """Open a specific file in VSCode, optionally at a specific line."""
        try:
            cmd = ["code", file_path]
            if line_number:
                cmd.extend(["-g", f"{file_path}:{line_number}"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise Exception(f"Failed to open file in VSCode: {str(e)}")
    
    async def get_workspace_settings(self) -> Dict[str, Any]:
        """Get VSCode workspace settings."""
        try:
            if self.vscode_settings_path.exists():
                with open(self.vscode_settings_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            raise Exception(f"Failed to read VSCode settings: {str(e)}")
    
    async def update_workspace_settings(self, settings: Dict[str, Any]) -> bool:
        """Update VSCode workspace settings."""
        try:
            os.makedirs(self.vscode_settings_path.parent, exist_ok=True)
            
            existing_settings = await self.get_workspace_settings()
            existing_settings.update(settings)
            
            with open(self.vscode_settings_path, 'w') as f:
                json.dump(existing_settings, f, indent=2)
            return True
        except Exception as e:
            raise Exception(f"Failed to update VSCode settings: {str(e)}")
    
    async def create_task(self, task_config: Dict[str, Any]) -> bool:
        """Create a VSCode task configuration."""
        try:
            os.makedirs(self.vscode_tasks_path.parent, exist_ok=True)
            
            tasks = {"version": "2.0.0", "tasks": []}
            if self.vscode_tasks_path.exists():
                with open(self.vscode_tasks_path, 'r') as f:
                    tasks = json.load(f)
            
            tasks["tasks"].append(task_config)
            
            with open(self.vscode_tasks_path, 'w') as f:
                json.dump(tasks, f, indent=2)
            return True
        except Exception as e:
            raise Exception(f"Failed to create VSCode task: {str(e)}")
    
    async def create_launch_config(self, launch_config: Dict[str, Any]) -> bool:
        """Create a VSCode launch configuration."""
        try:
            os.makedirs(self.vscode_launch_path.parent, exist_ok=True)
            
            launch = {"version": "0.2.0", "configurations": []}
            if self.vscode_launch_path.exists():
                with open(self.vscode_launch_path, 'r') as f:
                    launch = json.load(f)
            
            launch["configurations"].append(launch_config)
            
            with open(self.vscode_launch_path, 'w') as f:
                json.dump(launch, f, indent=2)
            return True
        except Exception as e:
            raise Exception(f"Failed to create VSCode launch config: {str(e)}")
    
    async def install_extension(self, extension_id: str) -> bool:
        """Install a VSCode extension."""
        try:
            result = subprocess.run(
                ["code", "--install-extension", extension_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise Exception(f"Failed to install VSCode extension: {str(e)}")
    
    async def get_installed_extensions(self) -> List[str]:
        """Get list of installed VSCode extensions."""
        try:
            result = subprocess.run(
                ["code", "--list-extensions"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            return []
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise Exception(f"Failed to get VSCode extensions: {str(e)}")
    
    async def create_snippet(self, language: str, snippet_name: str, snippet_config: Dict[str, Any]) -> bool:
        """Create a VSCode snippet."""
        try:
            snippets_dir = self.project_path / ".vscode"
            os.makedirs(snippets_dir, exist_ok=True)
            
            snippet_file = snippets_dir / f"{language}.json"
            snippets = {}
            
            if snippet_file.exists():
                with open(snippet_file, 'r') as f:
                    snippets = json.load(f)
            
            snippets[snippet_name] = snippet_config
            
            with open(snippet_file, 'w') as f:
                json.dump(snippets, f, indent=2)
            return True
        except Exception as e:
            raise Exception(f"Failed to create VSCode snippet: {str(e)}")
    
    async def get_workspace_files(self, pattern: Optional[str] = None) -> List[str]:
        """Get list of files in the workspace."""
        try:
            files = []
            for file_path in self.project_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.project_path)
                    if pattern is None or pattern in str(relative_path):
                        files.append(str(relative_path))
            return files
        except Exception as e:
            raise Exception(f"Failed to get workspace files: {str(e)}")
    
    async def setup_project_structure(self, project_type: str) -> bool:
        """Setup basic project structure and configurations."""
        try:
            configs = {
                "python": {
                    "settings": {
                        "python.defaultInterpreterPath": "./venv/bin/python",
                        "python.linting.enabled": True,
                        "python.linting.pylintEnabled": True,
                        "python.formatting.provider": "black"
                    },
                    "extensions": [
                        "ms-python.python",
                        "ms-python.black-formatter",
                        "ms-python.pylint"
                    ]
                },
                "javascript": {
                    "settings": {
                        "typescript.preferences.quoteStyle": "double",
                        "editor.defaultFormatter": "esbenp.prettier-vscode"
                    },
                    "extensions": [
                        "esbenp.prettier-vscode",
                        "ms-vscode.vscode-typescript-next"
                    ]
                }
            }
            
            if project_type in configs:
                config = configs[project_type]
                await self.update_workspace_settings(config["settings"])
                
                for extension in config["extensions"]:
                    await self.install_extension(extension)
            
            return True
        except Exception as e:
            raise Exception(f"Failed to setup project structure: {str(e)}")
    
    async def run_terminal_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run a command in VSCode's integrated terminal."""
        try:
            work_dir = cwd or str(self.project_path)
            result = subprocess.run(
                command.split(),
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            raise Exception("Command timed out")
        except Exception as e:
            raise Exception(f"Failed to run terminal command: {str(e)}")
    
    async def get_git_status(self) -> Dict[str, Any]:
        """Get git status of the current workspace."""
        try:
            result = await self.run_terminal_command("git status --porcelain")
            if result["success"]:
                lines = result["stdout"].strip().split('\n') if result["stdout"].strip() else []
                return {
                    "clean": len(lines) == 0,
                    "modified_files": [line[3:] for line in lines if line.startswith(' M')],
                    "added_files": [line[3:] for line in lines if line.startswith('A ')],
                    "deleted_files": [line[3:] for line in lines if line.startswith(' D')],
                    "untracked_files": [line[3:] for line in lines if line.startswith('??')]
                }
            return {"error": result["stderr"]}
        except Exception as e:
            return {"error": str(e)}