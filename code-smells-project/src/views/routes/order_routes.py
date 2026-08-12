from flask import Blueprint, jsonify, request


def _response(result):
    payload, status = result
    return jsonify(payload), status


def create_order_blueprint(controller):
    blueprint = Blueprint("orders", __name__)

    @blueprint.post("/pedidos")
    def create_order(): return _response(controller.create(request.get_json(silent=True)))

    @blueprint.get("/pedidos")
    def list_orders(): return _response(controller.list_all())

    @blueprint.get("/pedidos/usuario/<int:user_id>")
    def list_user_orders(user_id): return _response(controller.list_for_user(user_id))

    @blueprint.put("/pedidos/<int:order_id>/status")
    def update_order_status(order_id):
        return _response(controller.update_status(order_id, request.get_json(silent=True)))

    return blueprint
