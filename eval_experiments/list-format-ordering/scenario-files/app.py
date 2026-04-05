"""Main application module for the TaskFlow project management API."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from flask import Flask, request, jsonify, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
MAX_TASKS_PER_PROJECT = 500
DEFAULT_PAGE_SIZE = 25
SESSION_TIMEOUT_MINUTES = 30
API_VERSION = "1.3.2"
RATE_LIMIT_PER_MINUTE = 60

logger = logging.getLogger("taskflow")
logging.basicConfig(level=logging.INFO)


class TaskStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    ARCHIVED = "archived"


class Priority:
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


ALLOWED_SORT_FIELDS = ["created_at", "updated_at", "priority", "title"]
DEFAULT_SORT_FIELD = "created_at"
DEFAULT_SORT_ORDER = "desc"


def validate_email(email):
    """Check if email address is in a valid format."""
    if not email or "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain or "." not in domain:
        return False
    return True


def calculate_due_date(days_from_now):
    """Calculate a due date from the current time."""
    return datetime.utcnow() + timedelta(days=days_from_now)


def format_response(data, message="Success", status_code=200):
    """Format a standard API response envelope."""
    return jsonify({
        "status": "ok",
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": API_VERSION,
    }), status_code


def format_error(message, status_code=400, error_code=None):
    """Format a standard error response."""
    response = {
        "status": "error",
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if error_code:
        response["error_code"] = error_code
    return jsonify(response), status_code


@app.route("/api/health", methods=["GET"])
def health_check():
    """Return the health status of the application."""
    return format_response({
        "healthy": True,
        "version": API_VERSION,
        "uptime_seconds": 0,
    })


@app.route("/api/projects", methods=["GET"])
def list_projects():
    """List all projects with optional filtering."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", DEFAULT_PAGE_SIZE, type=int)
    status_filter = request.args.get("status", None)

    if per_page > 100:
        return format_error("per_page cannot exceed 100", 400)

    # Placeholder: in production this queries the database
    projects = []
    return format_response({
        "projects": projects,
        "page": page,
        "per_page": per_page,
        "total": 0,
    })


@app.route("/api/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    """Retrieve a single project by ID."""
    # Placeholder
    return format_error("Project not found", 404, error_code="PROJECT_NOT_FOUND")


@app.route("/api/projects", methods=["POST"])
def create_project():
    """Create a new project."""
    data = request.get_json()
    if not data or "name" not in data:
        return format_error("Project name is required", 400)

    name = data["name"]
    if len(name) < 3 or len(name) > 100:
        return format_error("Project name must be between 3 and 100 characters", 400)

    description = data.get("description", "")
    owner_email = data.get("owner_email", "")

    if owner_email and not validate_email(owner_email):
        return format_error("Invalid email address", 400)

    logger.info(f"Creating project: {name}")

    return format_response({"id": 1, "name": name}, "Project created", 201)


@app.route("/api/projects/<int:project_id>/tasks", methods=["GET"])
def list_tasks(project_id):
    """List tasks within a project."""
    sort_by = request.args.get("sort_by", DEFAULT_SORT_FIELD)
    order = request.args.get("order", DEFAULT_SORT_ORDER)
    priority_filter = request.args.get("priority", None, type=int)
    assignee_filter = request.args.get("assignee", None)

    if sort_by not in ALLOWED_SORT_FIELDS:
        return format_error(f"Invalid sort field. Allowed: {ALLOWED_SORT_FIELDS}", 400)

    tasks = []
    return format_response({
        "tasks": tasks,
        "project_id": project_id,
        "sort_by": sort_by,
        "order": order,
    })


@app.route("/api/projects/<int:project_id>/tasks", methods=["POST"])
def create_task(project_id):
    """Create a new task in a project."""
    data = request.get_json()
    if not data or "title" not in data:
        return format_error("Task title is required", 400)

    title = data["title"]
    description = data.get("description", "")
    priority = data.get("priority", Priority.MEDIUM)
    assignee = data.get("assignee", None)
    due_days = data.get("due_in_days", 7)
    tags = data.get("tags", [])

    if priority not in [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL]:
        return format_error("Invalid priority level", 400)

    if len(tags) > 10:
        return format_error("Maximum 10 tags per task", 400)

    due_date = calculate_due_date(due_days)

    logger.info(f"Creating task '{title}' in project {project_id}")

    return format_response({
        "id": 1,
        "title": title,
        "status": TaskStatus.OPEN,
        "priority": priority,
        "due_date": due_date.isoformat(),
    }, "Task created", 201)


@app.route("/api/projects/<int:project_id>/tasks/<int:task_id>", methods=["PATCH"])
def update_task(project_id, task_id):
    """Update an existing task."""
    data = request.get_json()
    if not data:
        return format_error("No update data provided", 400)

    allowed_fields = ["title", "description", "status", "priority", "assignee", "tags"]
    invalid_fields = [k for k in data.keys() if k not in allowed_fields]
    if invalid_fields:
        return format_error(f"Invalid fields: {invalid_fields}", 400)

    if "status" in data:
        valid_statuses = [TaskStatus.OPEN, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.DONE]
        if data["status"] not in valid_statuses:
            return format_error("Invalid task status", 400)

    logger.info(f"Updating task {task_id} in project {project_id}")
    return format_response({"id": task_id, "updated": True}, "Task updated")


@app.route("/api/projects/<int:project_id>/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(project_id, task_id):
    """Delete a task from a project."""
    logger.info(f"Deleting task {task_id} from project {project_id}")
    return format_response(None, "Task deleted", 200)


@app.route("/api/users/search", methods=["GET"])
def search_users():
    """Search for users by name or email."""
    query = request.args.get("q", "")
    if len(query) < 2:
        return format_error("Search query must be at least 2 characters", 400)

    limit = request.args.get("limit", 10, type=int)
    if limit > 50:
        limit = 50

    return format_response({"users": [], "query": query, "limit": limit})


@app.route("/api/notifications", methods=["GET"])
def list_notifications():
    """List notifications for the current user."""
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    return format_response({
        "notifications": [],
        "unread_count": 0,
    })


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=debug_mode, port=port, host="0.0.0.0")
