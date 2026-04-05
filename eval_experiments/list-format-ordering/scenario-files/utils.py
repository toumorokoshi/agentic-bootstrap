"""Utility functions for the TaskFlow application."""

import re
import hashlib
import secrets
import string
from datetime import datetime, timedelta


# Password requirements
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()-_=+"

# Token settings
TOKEN_LENGTH = 32
TOKEN_EXPIRY_HOURS = 24

# File upload limits
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".doc", ".docx", ".txt", ".csv"}

# Date formatting
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DISPLAY_DATE_FORMAT = "%B %d, %Y"
DISPLAY_TIME_FORMAT = "%I:%M %p"


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def generate_token(length=TOKEN_LENGTH):
    """Generate a secure random token."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password, salt=None):
    """Hash a password with optional salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    combined = f"{salt}{password}"
    hashed = hashlib.sha256(combined.encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password, stored_hash):
    """Verify a password against a stored hash."""
    salt = stored_hash.split(":")[0]
    return hash_password(password, salt) == stored_hash


def validate_password_strength(password):
    """Check if a password meets strength requirements."""
    errors = []
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    return errors


def truncate_text(text, max_length=100, suffix="..."):
    """Truncate text to a maximum length with a suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_sort_params(sort_string, allowed_fields, default_field="created_at", default_order="desc"):
    """Parse sort parameters from a query string like 'field:order'."""
    if not sort_string:
        return default_field, default_order
    parts = sort_string.split(":")
    field = parts[0] if parts[0] in allowed_fields else default_field
    order = parts[1] if len(parts) > 1 and parts[1] in ("asc", "desc") else default_order
    return field, order


def format_file_size(size_bytes):
    """Format file size in bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def is_valid_file_extension(filename):
    """Check if a filename has an allowed extension."""
    if "." not in filename:
        return False
    ext = "." + filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def calculate_time_ago(dt):
    """Return a human-readable 'time ago' string."""
    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def paginate(items, page, per_page):
    """Paginate a list of items."""
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(items) + per_page - 1) // per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total_items": len(items),
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


def merge_dicts(base, overrides):
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def sanitize_html(text):
    """Remove HTML tags from text for safe display."""
    return re.sub(r"<[^>]+>", "", text)


def extract_mentions(text):
    """Extract @mentions from text."""
    return re.findall(r"@(\w+)", text)


def generate_color_from_string(text):
    """Generate a consistent hex color from a string."""
    hash_value = hashlib.md5(text.encode()).hexdigest()
    return f"#{hash_value[:6]}"
