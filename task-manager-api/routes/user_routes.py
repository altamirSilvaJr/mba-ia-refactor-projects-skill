from flask import Blueprint, g, request

from auth import require_auth
from errors import ApplicationError
from routes.http import respond


def build_user_blueprint(controller):
    blueprint = Blueprint("users", __name__)

    @blueprint.get("/users")
    @require_auth(("admin", "manager"))
    def get_users():
        return respond(controller.list())

    @blueprint.get("/users/<int:user_id>")
    @require_auth()
    def get_user(user_id):
        _require_self_or_privileged(user_id)
        return respond(controller.get(user_id))

    @blueprint.post("/users")
    def create_user():
        return respond(controller.create(request.get_json(silent=True)))

    @blueprint.put("/users/<int:user_id>")
    @require_auth()
    def update_user(user_id):
        _require_self_or_privileged(user_id)
        can_change_role = g.current_user.role == "admin"
        return respond(controller.update(user_id, request.get_json(silent=True), can_change_role))

    @blueprint.delete("/users/<int:user_id>")
    @require_auth(("admin",))
    def delete_user(user_id):
        return respond(controller.delete(user_id))

    @blueprint.get("/users/<int:user_id>/tasks")
    @require_auth()
    def get_user_tasks(user_id):
        _require_self_or_privileged(user_id)
        return respond(controller.tasks(user_id))

    @blueprint.post("/login")
    def login():
        return respond(controller.login(request.get_json(silent=True)))

    return blueprint


def _require_self_or_privileged(user_id):
    if g.current_user.id != user_id and g.current_user.role not in ("admin", "manager"):
        raise ApplicationError("Acesso negado", 403)
