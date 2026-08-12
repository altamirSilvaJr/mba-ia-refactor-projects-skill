import re
from datetime import datetime

from errors import ApplicationError


VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
VALID_ROLES = ("user", "admin", "manager")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def require_json_object(data):
    if not isinstance(data, dict) or not data:
        raise ApplicationError("Dados inválidos", 400)
    return data


def parse_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ApplicationError(f"{field_name} inválido", 400) from error


def parse_date(value, message="Formato de data inválido"):
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError) as error:
        raise ApplicationError(message, 400) from error


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ApplicationError("Email inválido", 400)

