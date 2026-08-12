from flask import Blueprint, jsonify, request


def _response(result):
    payload, status = result
    return jsonify(payload), status


def create_product_blueprint(controller):
    blueprint = Blueprint("products", __name__)

    @blueprint.get("/produtos")
    def list_products(): return _response(controller.list_all())

    @blueprint.get("/produtos/busca")
    def search_products(): return _response(controller.search(request.args))

    @blueprint.get("/produtos/<int:product_id>")
    def get_product(product_id): return _response(controller.get(product_id))

    @blueprint.post("/produtos")
    def create_product(): return _response(controller.create(request.get_json(silent=True)))

    @blueprint.put("/produtos/<int:product_id>")
    def update_product(product_id): return _response(controller.update(product_id, request.get_json(silent=True)))

    @blueprint.delete("/produtos/<int:product_id>")
    def delete_product(product_id): return _response(controller.delete(product_id))

    return blueprint
