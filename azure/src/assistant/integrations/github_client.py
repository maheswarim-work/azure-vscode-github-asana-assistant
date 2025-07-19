from github import Github, GithubException
from typing import List, Dict, Any, Optional
from ..config import settings


class GitHubClient:
    def __init__(self):
        self.client = None
        self.organization = settings.github_organization
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure the GitHub client is initialized with proper credentials."""
        if not self._initialized:
            github_token = await settings.get_github_token()
            if not github_token:
                raise Exception("GitHub token not found in Key Vault or environment variables")
            
            self.client = Github(github_token)
            self._initialized = True
    
    async def get_repositories(self, organization: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all repositories for user or organization."""
        await self._ensure_initialized()
        try:
            if organization or self.organization:
                org = self.client.get_organization(organization or self.organization)
                repos = list(org.get_repos())
            else:
                repos = list(self.client.get_user().get_repos())
            
            return [{
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'clone_url': repo.clone_url,
                'html_url': repo.html_url,
                'default_branch': repo.default_branch,
                'language': repo.language,
                'created_at': repo.created_at.isoformat(),
                'updated_at': repo.updated_at.isoformat()
            } for repo in repos]
        except GithubException as e:
            raise Exception(f"Failed to fetch GitHub repositories: {str(e)}")
    
    async def get_repository(self, repo_name: str) -> Dict[str, Any]:
        """Get a specific repository."""
        await self._ensure_initialized()
        try:
            if self.organization:
                repo = self.client.get_repo(f"{self.organization}/{repo_name}")
            else:
                repo = self.client.get_user().get_repo(repo_name)
            
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'clone_url': repo.clone_url,
                'html_url': repo.html_url,
                'default_branch': repo.default_branch,
                'language': repo.language,
                'created_at': repo.created_at.isoformat(),
                'updated_at': repo.updated_at.isoformat()
            }
        except GithubException as e:
            raise Exception(f"Failed to fetch GitHub repository: {str(e)}")
    
    async def get_issues(self, repo_name: str, state: str = "open") -> List[Dict[str, Any]]:
        """Get issues from a repository."""
        await self._ensure_initialized()
        try:
            if self.organization:
                repo = self.client.get_repo(f"{self.organization}/{repo_name}")
            else:
                repo = self.client.get_user().get_repo(repo_name)
            
            issues = list(repo.get_issues(state=state))
            
            return [{
                'number': issue.number,
                'title': issue.title,
                'body': issue.body,
                'state': issue.state,
                'labels': [label.name for label in issue.labels],
                'assignee': issue.assignee.login if issue.assignee else None,
                'created_at': issue.created_at.isoformat(),
                'updated_at': issue.updated_at.isoformat(),
                'html_url': issue.html_url
            } for issue in issues]
        except GithubException as e:
            raise Exception(f"Failed to fetch GitHub issues: {str(e)}")
    
    async def create_issue(self, repo_name: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue."""
        await self._ensure_initialized()
        try:
            if self.organization:
                repo = self.client.get_repo(f"{self.organization}/{repo_name}")
            else:
                repo = self.client.get_user().get_repo(repo_name)
            
            issue = repo.create_issue(
                title=issue_data['title'],
                body=issue_data.get('body', ''),
                assignee=issue_data.get('assignee'),
                labels=issue_data.get('labels', [])
            )
            
            return {
                'number': issue.number,
                'title': issue.title,
                'body': issue.body,
                'html_url': issue.html_url,
                'created_at': issue.created_at.isoformat()
            }
        except GithubException as e:
            raise Exception(f"Failed to create GitHub issue: {str(e)}")
    
    async def update_issue(self, repo_name: str, issue_number: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing issue."""
        await self._ensure_initialized()
        try:
            if self.organization:
                repo = self.client.get_repo(f"{self.organization}/{repo_name}")
            else:
                repo = self.client.get_user().get_repo(repo_name)
            
            issue = repo.get_issue(issue_number)
            issue.edit(
                title=updates.get('title', issue.title),
                body=updates.get('body', issue.body),
                state=updates.get('state', issue.state),
                labels=updates.get('labels', [label.name for label in issue.labels])
            )
            
            return {
                'number': issue.number,
                'title': issue.title,
                'body': issue.body,
                'state': issue.state,
                'html_url': issue.html_url,
                'updated_at': issue.updated_at.isoformat()
            }
        except GithubException as e:
            raise Exception(f"Failed to update GitHub issue: {str(e)}")
    
    async def get_pull_requests(self, repo_name: str, state: str = "open") -> List[Dict[str, Any]]:
        """Get pull requests from a repository."""
        await self._ensure_initialized()
        try:
            if self.organization:
                repo = self.client.get_repo(f"{self.organization}/{repo_name}")
            else:
                repo = self.client.get_user().get_repo(repo_name)
            
            prs = list(repo.get_pulls(state=state))
            
            return [{
                'number': pr.number,
                'title': pr.title,
                'body': pr.body,
                'state': pr.state,
                'head': pr.head.ref,
                'base': pr.base.ref,
                'user': pr.user.login,
                'created_at': pr.created_at.isoformat(),
                'updated_at': pr.updated_at.isoformat(),
                'html_url': pr.html_url
            } for pr in prs]
        except GithubException as e:
            raise Exception(f"Failed to fetch GitHub pull requests: {str(e)}")
    
    async def create_pull_request(self, repo_name: str, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pull request."""
        await self._ensure_initialized()
        try:
            if self.organization:
                repo = self.client.get_repo(f"{self.organization}/{repo_name}")
            else:
                repo = self.client.get_user().get_repo(repo_name)
            
            pr = repo.create_pull(
                title=pr_data['title'],
                body=pr_data.get('body', ''),
                head=pr_data['head'],
                base=pr_data.get('base', repo.default_branch)
            )
            
            return {
                'number': pr.number,
                'title': pr.title,
                'body': pr.body,
                'html_url': pr.html_url,
                'created_at': pr.created_at.isoformat()
            }
        except GithubException as e:
            raise Exception(f"Failed to create GitHub pull request: {str(e)}")
    
    async def get_commits(self, repo_name: str, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get commits from a repository."""
        await self._ensure_initialized()
        try:
            if self.organization:
                repo = self.client.get_repo(f"{self.organization}/{repo_name}")
            else:
                repo = self.client.get_user().get_repo(repo_name)
            
            commits = list(repo.get_commits(sha=branch) if branch else repo.get_commits())
            
            return [{
                'sha': commit.sha,
                'message': commit.commit.message,
                'author': commit.commit.author.name,
                'date': commit.commit.author.date.isoformat(),
                'html_url': commit.html_url
            } for commit in commits[:50]]  # Limit to recent 50 commits
        except GithubException as e:
            raise Exception(f"Failed to fetch GitHub commits: {str(e)}")
    
    async def search_repositories(self, query: str) -> List[Dict[str, Any]]:
        """Search for repositories."""
        await self._ensure_initialized()
        try:
            repos = self.client.search_repositories(query)
            
            return [{
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'html_url': repo.html_url,
                'language': repo.language,
                'stars': repo.stargazers_count
            } for repo in repos[:20]]  # Limit to top 20 results
        except GithubException as e:
            raise Exception(f"Failed to search GitHub repositories: {str(e)}")
    
    async def add_comment_to_issue(self, repo_name: str, issue_number: int, comment: str) -> Dict[str, Any]:
        """Add a comment to an issue."""
        await self._ensure_initialized()
        try:
            if self.organization:
                repo = self.client.get_repo(f"{self.organization}/{repo_name}")
            else:
                repo = self.client.get_user().get_repo(repo_name)
            
            issue = repo.get_issue(issue_number)
            comment_obj = issue.create_comment(comment)
            
            return {
                'id': comment_obj.id,
                'body': comment_obj.body,
                'created_at': comment_obj.created_at.isoformat(),
                'html_url': comment_obj.html_url
            }
        except GithubException as e:
            raise Exception(f"Failed to add comment to GitHub issue: {str(e)}")