from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from database import db
from errors import ApplicationError
from models.user import User


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="task-manager-auth")


def issue_token(user):
    return _serializer().dumps({"sub": user.id, "role": user.role})


def require_auth(roles=None):
    allowed_roles = set(roles or ())

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                raise ApplicationError("Autenticação obrigatória", 401)
            try:
                payload = _serializer().loads(
                    header[7:], max_age=current_app.config["AUTH_TOKEN_MAX_AGE"]
                )
            except SignatureExpired as error:
                raise ApplicationError("Token expirado", 401) from error
            except BadSignature as error:
                raise ApplicationError("Token inválido", 401) from error

            user = db.session.get(User, payload.get("sub"))
            if not user or not user.active:
                raise ApplicationError("Token inválido", 401)
            if allowed_roles and user.role not in allowed_roles:
                raise ApplicationError("Acesso negado", 403)
            g.current_user = user
            return view(*args, **kwargs)

        return wrapped

    return decorator

