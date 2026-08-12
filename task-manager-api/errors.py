import logging

from flask import jsonify


logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_error_handlers(app):
    @app.errorhandler(ApplicationError)
    def handle_application_error(error):
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": "Recurso não encontrado"}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unexpected request failure", exc_info=error)
        return jsonify({"error": "Erro interno"}), 500

