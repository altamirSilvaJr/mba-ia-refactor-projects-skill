from flask import Blueprint, jsonify


def _response(result):
    payload, status = result
    return jsonify(payload), status


def create_report_blueprint(controller):
    blueprint = Blueprint("reports", __name__)

    @blueprint.get("/relatorios/vendas")
    def sales_report(): return _response(controller.sales())

    @blueprint.get("/health")
    def health(): return _response(controller.health())

    return blueprint
