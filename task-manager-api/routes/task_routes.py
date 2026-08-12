from flask import Blueprint, request

from auth import require_auth
from routes.http import respond


def build_task_blueprint(controller):
    blueprint = Blueprint("tasks", __name__)

    @blueprint.get("/tasks")
    @require_auth()
    def get_tasks():
        return respond(controller.list())

    @blueprint.get("/tasks/<int:task_id>")
    @require_auth()
    def get_task(task_id):
        return respond(controller.get(task_id))

    @blueprint.post("/tasks")
    @require_auth()
    def create_task():
        return respond(controller.create(request.get_json(silent=True)))

    @blueprint.put("/tasks/<int:task_id>")
    @require_auth()
    def update_task(task_id):
        return respond(controller.update(task_id, request.get_json(silent=True)))

    @blueprint.delete("/tasks/<int:task_id>")
    @require_auth()
    def delete_task(task_id):
        return respond(controller.delete(task_id))

    @blueprint.get("/tasks/search")
    @require_auth()
    def search_tasks():
        return respond(controller.search(request.args))

    @blueprint.get("/tasks/stats")
    @require_auth()
    def task_stats():
        return respond(controller.stats())

    return blueprint
