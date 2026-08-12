from flask import Flask, jsonify
from flask_cors import CORS

from src.config.settings import Settings
from src.controllers.admin_controller import AdminController
from src.controllers.order_controller import OrderController
from src.controllers.product_controller import ProductController
from src.controllers.report_controller import ReportController
from src.controllers.user_controller import UserController
from src.database import get_db, init_app as init_database
from src.middlewares.error_handler import register_error_handlers
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.report_repository import ReportRepository
from src.repositories.user_repository import UserRepository
from src.services.admin_service import AdminService
from src.services.order_service import OrderService
from src.services.product_service import ProductService
from src.services.report_service import ReportService
from src.services.user_service import UserService
from src.views.routes import (
    create_admin_blueprint, create_order_blueprint, create_product_blueprint,
    create_report_blueprint, create_user_blueprint,
)


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Settings)
    if config:
        app.config.update(config)

    CORS(app, origins=app.config["CORS_ORIGINS"])
    init_database(app)
    register_error_handlers(app)

    product_controller = ProductController(ProductService(ProductRepository()))
    user_controller = UserController(UserService(UserRepository()))
    order_controller = OrderController(OrderService(OrderRepository()))
    report_controller = ReportController(ReportService(ReportRepository()))
    admin_controller = AdminController(AdminService(get_db, app.config.get("ADMIN_TOKEN")))

    app.register_blueprint(create_product_blueprint(product_controller))
    app.register_blueprint(create_user_blueprint(user_controller))
    app.register_blueprint(create_order_blueprint(order_controller))
    app.register_blueprint(create_report_blueprint(report_controller))
    app.register_blueprint(create_admin_blueprint(admin_controller))

    @app.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja", "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos", "usuarios": "/usuarios", "pedidos": "/pedidos",
                "login": "/login", "relatorios": "/relatorios/vendas", "health": "/health",
            },
        })

    return app
