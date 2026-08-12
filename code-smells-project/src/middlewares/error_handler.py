import logging
import sqlite3

from flask import jsonify

from src.services.errors import ApplicationError


logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ApplicationError)
    def handle_application_error(error):
        return jsonify({"erro": error.message, "sucesso": False}), error.status_code

    @app.errorhandler(sqlite3.IntegrityError)
    def handle_integrity_error(error):
        logger.warning("Database integrity error", exc_info=error)
        return jsonify({"erro": "Operação viola a integridade dos dados", "sucesso": False}), 409

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unexpected application error")
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
