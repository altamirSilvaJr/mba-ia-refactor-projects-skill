from flask import Blueprint, jsonify, request


def _response(result):
    payload, status = result
    return jsonify(payload), status


def create_user_blueprint(controller):
    blueprint = Blueprint("users", __name__)

    @blueprint.get("/usuarios")
    def list_users(): return _response(controller.list_all())

    @blueprint.get("/usuarios/<int:user_id>")
    def get_user(user_id): return _response(controller.get(user_id))

    @blueprint.post("/usuarios")
    def create_user(): return _response(controller.create(request.get_json(silent=True)))

    @blueprint.post("/login")
    def login(): return _response(controller.login(request.get_json(silent=True)))

    return blueprint
