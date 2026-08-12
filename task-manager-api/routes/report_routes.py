from flask import Blueprint, request

from auth import require_auth
from routes.http import respond


def build_report_blueprint(controller):
    blueprint = Blueprint("reports", __name__)

    @blueprint.get("/reports/summary")
    @require_auth(("admin", "manager"))
    def summary_report():
        return respond(controller.summary())

    @blueprint.get("/reports/user/<int:user_id>")
    @require_auth(("admin", "manager"))
    def user_report(user_id):
        return respond(controller.user(user_id))

    @blueprint.get("/categories")
    @require_auth()
    def get_categories():
        return respond(controller.categories())

    @blueprint.post("/categories")
    @require_auth(("admin", "manager"))
    def create_category():
        return respond(controller.create_category(request.get_json(silent=True)))

    @blueprint.put("/categories/<int:category_id>")
    @require_auth(("admin", "manager"))
    def update_category(category_id):
        return respond(controller.update_category(category_id, request.get_json(silent=True)))

    @blueprint.delete("/categories/<int:category_id>")
    @require_auth(("admin",))
    def delete_category(category_id):
        return respond(controller.delete_category(category_id))

    return blueprint
