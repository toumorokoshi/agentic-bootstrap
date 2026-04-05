"""Database models for the TaskFlow application."""

from datetime import datetime
from enum import Enum


class UserRole(Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    OWNER = "owner"


class NotificationType(Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    COMMENT_ADDED = "comment_added"
    PROJECT_INVITE = "project_invite"
    DEADLINE_WARNING = "deadline_warning"


class User:
    """Represents a user in the system."""

    def __init__(self, user_id, username, email, display_name=None, role=UserRole.VIEWER):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.display_name = display_name or username
        self.role = role
        self.created_at = datetime.utcnow()
        self.last_login = None
        self.is_active = True
        self.avatar_url = None
        self.timezone = "UTC"
        self.notification_preferences = {
            "email_enabled": True,
            "push_enabled": False,
            "digest_frequency": "daily",
        }

    def full_name(self):
        """Return the display name or username."""
        return self.display_name if self.display_name else self.username

    def has_permission(self, required_role):
        """Check if user has the required role or higher."""
        role_hierarchy = {
            UserRole.VIEWER: 0,
            UserRole.EDITOR: 1,
            UserRole.ADMIN: 2,
            UserRole.OWNER: 3,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def to_dict(self):
        """Serialize user to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat(),
        }


class Project:
    """Represents a project containing tasks."""

    MAX_DESCRIPTION_LENGTH = 500
    MAX_MEMBERS = 50

    def __init__(self, project_id, name, owner, description=""):
        self.project_id = project_id
        self.name = name
        self.owner = owner
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_archived = False
        self.members = []
        self.tags = []
        self.color = "#3B82F6"
        self.icon = "folder"

    def add_member(self, user, role=UserRole.EDITOR):
        """Add a member to the project."""
        if len(self.members) >= self.MAX_MEMBERS:
            raise ValueError("Project has reached maximum member limit")
        self.members.append({"user": user, "role": role, "joined_at": datetime.utcnow()})
        self.updated_at = datetime.utcnow()

    def remove_member(self, user_id):
        """Remove a member from the project."""
        self.members = [m for m in self.members if m["user"].user_id != user_id]
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Serialize project to dictionary."""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner.to_dict() if self.owner else None,
            "is_archived": self.is_archived,
            "member_count": len(self.members),
            "color": self.color,
            "icon": self.icon,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Task:
    """Represents a task within a project."""

    MAX_TITLE_LENGTH = 200
    MAX_TAGS = 10

    def __init__(self, task_id, title, project, creator, description="",
                 priority=2, due_date=None):
        self.task_id = task_id
        self.title = title
        self.project = project
        self.creator = creator
        self.description = description
        self.priority = priority
        self.status = "open"
        self.assignee = None
        self.due_date = due_date
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.completed_at = None
        self.tags = []
        self.subtasks = []
        self.comments = []
        self.attachments = []
        self.estimated_hours = None
        self.actual_hours = None

    def assign_to(self, user):
        """Assign the task to a user."""
        self.assignee = user
        self.updated_at = datetime.utcnow()

    def change_status(self, new_status):
        """Change the task status."""
        valid_transitions = {
            "open": ["in_progress"],
            "in_progress": ["review", "open"],
            "review": ["done", "in_progress"],
            "done": ["archived", "open"],
        }
        current_transitions = valid_transitions.get(self.status, [])
        if new_status not in current_transitions:
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        self.status = new_status
        if new_status == "done":
            self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_comment(self, user, text):
        """Add a comment to the task."""
        comment = {
            "id": len(self.comments) + 1,
            "user": user,
            "text": text,
            "created_at": datetime.utcnow(),
        }
        self.comments.append(comment)
        self.updated_at = datetime.utcnow()
        return comment

    def to_dict(self):
        """Serialize task to dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assignee": self.assignee.to_dict() if self.assignee else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags,
            "comment_count": len(self.comments),
            "subtask_count": len(self.subtasks),
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Comment:
    """Represents a comment on a task."""

    MAX_LENGTH = 5000

    def __init__(self, comment_id, task, author, text):
        self.comment_id = comment_id
        self.task = task
        self.author = author
        self.text = text
        self.created_at = datetime.utcnow()
        self.edited_at = None
        self.is_deleted = False
        self.reactions = {}

    def edit(self, new_text):
        """Edit the comment text."""
        if len(new_text) > self.MAX_LENGTH:
            raise ValueError(f"Comment cannot exceed {self.MAX_LENGTH} characters")
        self.text = new_text
        self.edited_at = datetime.utcnow()

    def add_reaction(self, user, emoji):
        """Add a reaction to the comment."""
        if emoji not in self.reactions:
            self.reactions[emoji] = []
        if user.user_id not in self.reactions[emoji]:
            self.reactions[emoji].append(user.user_id)

    def to_dict(self):
        """Serialize comment to dictionary."""
        return {
            "comment_id": self.comment_id,
            "author": self.author.to_dict() if self.author else None,
            "text": self.text,
            "is_deleted": self.is_deleted,
            "reactions": self.reactions,
            "created_at": self.created_at.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
        }
