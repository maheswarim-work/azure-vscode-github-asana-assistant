import azure.functions as func
import json

app = func.FunctionApp()

@app.function_name(name="SimpleTest")
@app.route(route="test", methods=["GET"])
def simple_test(req: func.HttpRequest) -> func.HttpResponse:
    """Simple test endpoint."""
    return func.HttpResponse(
        json.dumps({"message": "Test successful", "status": "ok"}),
        status_code=200,
        mimetype="application/json"
    )