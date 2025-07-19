import azure.functions as func
import json
import asyncio
from typing import Dict, Any
import logging

app = func.FunctionApp()

# Simple test - will add imports later
try:
    from src.assistant.ai.assistant_core import AIAssistant
    from src.assistant.config import settings
    assistant = AIAssistant()
    ASSISTANT_AVAILABLE = True
except Exception as e:
    logging.error(f"Failed to initialize assistant: {e}")
    assistant = None
    ASSISTANT_AVAILABLE = False

@app.function_name(name="ProcessCommand")
@app.route(route="command", methods=["POST"])
async def process_command(req: func.HttpRequest) -> func.HttpResponse:
    """Process a command through the AI assistant."""
    try:
        # Parse request body
        request_body = req.get_json()
        if not request_body:
            return func.HttpResponse(
                json.dumps({"error": "No request body provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        command = request_body.get("command")
        context = request_body.get("context", {})
        
        if not command:
            return func.HttpResponse(
                json.dumps({"error": "No command provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Process the command
        result = await assistant.process_command(command, context)
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error processing command: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="GetStatus")
@app.route(route="status", methods=["GET"])
async def get_status(req: func.HttpRequest) -> func.HttpResponse:
    """Get status summary from all platforms."""
    try:
        if not ASSISTANT_AVAILABLE:
            return func.HttpResponse(
                json.dumps({"error": "Assistant not available", "assistant_loaded": False}),
                status_code=500,
                mimetype="application/json"
            )
        
        status = await assistant.get_status_summary()
        
        return func.HttpResponse(
            json.dumps(status),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error getting status: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e), "assistant_loaded": ASSISTANT_AVAILABLE}),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="SyncPlatforms")
@app.route(route="sync", methods=["POST"])
async def sync_platforms(req: func.HttpRequest) -> func.HttpResponse:
    """Sync data between platforms."""
    try:
        request_body = req.get_json()
        if not request_body:
            return func.HttpResponse(
                json.dumps({"error": "No request body provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        source_platform = request_body.get("source_platform")
        target_platform = request_body.get("target_platform")
        source_id = request_body.get("source_id")
        additional_params = request_body.get("additional_params", {})
        
        if not all([source_platform, target_platform, source_id]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameters"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Determine sync action
        if source_platform == "asana" and target_platform == "github":
            action = "sync_task_to_issue"
            parameters = {
                "task_gid": source_id,
                **additional_params
            }
        elif source_platform == "github" and target_platform == "asana":
            action = "sync_issue_to_task"
            parameters = {
                "issue_number": int(source_id),
                **additional_params
            }
        else:
            return func.HttpResponse(
                json.dumps({
                    "error": f"Sync from {source_platform} to {target_platform} not supported"
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Execute sync
        result = await assistant._handle_multi_platform_action(
            action,
            parameters,
            f"Sync {source_platform} {source_id} to {target_platform}"
        )
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error syncing platforms: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="AsanaWebhook")
@app.route(route="webhooks/asana", methods=["POST"])
async def asana_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Handle Asana webhooks for real-time updates."""
    try:
        request_body = req.get_json()
        
        # Verify webhook signature (implement based on Asana's requirements)
        # For now, we'll just log the event
        logging.info(f"Asana webhook received: {json.dumps(request_body)}")
        
        # Process the webhook event
        events = request_body.get("events", [])
        for event in events:
            event_type = event.get("action")
            resource = event.get("resource", {})
            
            if event_type in ["added", "changed"] and resource.get("resource_type") == "task":
                # Task was created or updated
                logging.info(f"Task {event_type}: {resource.get('gid')}")
                
                # You could implement automatic syncing here
                # For example, sync new tasks to GitHub issues
        
        return func.HttpResponse(
            json.dumps({"status": "received"}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error processing Asana webhook: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="GitHubWebhook")
@app.route(route="webhooks/github", methods=["POST"])
async def github_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Handle GitHub webhooks for real-time updates."""
    try:
        request_body = req.get_json()
        
        # Get the event type from headers
        event_type = req.headers.get("X-GitHub-Event")
        
        logging.info(f"GitHub webhook received: {event_type}")
        
        if event_type == "issues":
            action = request_body.get("action")
            issue = request_body.get("issue", {})
            
            if action in ["opened", "edited"]:
                logging.info(f"Issue {action}: {issue.get('number')}")
                
                # You could implement automatic syncing here
                # For example, sync new issues to Asana tasks
        
        elif event_type == "pull_request":
            action = request_body.get("action")
            pr = request_body.get("pull_request", {})
            
            if action in ["opened", "closed"]:
                logging.info(f"Pull request {action}: {pr.get('number')}")
        
        return func.HttpResponse(
            json.dumps({"status": "received"}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error processing GitHub webhook: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="HealthCheck")
@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }),
        status_code=200,
        mimetype="application/json"
    )