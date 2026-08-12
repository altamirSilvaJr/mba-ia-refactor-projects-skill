from flask import Blueprint, jsonify, request


def _response(result):
    payload, status = result
    return jsonify(payload), status


def create_admin_blueprint(controller):
    blueprint = Blueprint("admin", __name__)

    @blueprint.post("/admin/reset-db")
    def reset_database(): return _response(controller.reset(request.headers.get("X-Admin-Token")))

    @blueprint.post("/admin/query")
    def query_disabled(): return _response(controller.query_disabled())

    return blueprint
