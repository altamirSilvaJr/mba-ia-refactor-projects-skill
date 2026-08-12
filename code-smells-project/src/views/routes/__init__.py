from .admin_routes import create_admin_blueprint
from .order_routes import create_order_blueprint
from .product_routes import create_product_blueprint
from .report_routes import create_report_blueprint
from .user_routes import create_user_blueprint

__all__ = [
    "create_admin_blueprint", "create_order_blueprint", "create_product_blueprint",
    "create_report_blueprint", "create_user_blueprint",
]
