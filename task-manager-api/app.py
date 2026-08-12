import os
from datetime import datetime

from flask import Flask
from flask_cors import CORS

from auth import issue_token
from config import Config
from controllers import ReportController, TaskController, UserController
from database import db
from errors import register_error_handlers
from repositories import CategoryRepository, TaskRepository, UserRepository
from routes import build_report_blueprint, build_task_blueprint, build_user_blueprint
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService


def create_app(config=None):
    application = Flask(__name__)
    application.config.from_object(Config)
    if config:
        application.config.update(config)

    CORS(application, origins=application.config["CORS_ORIGINS"])
    db.init_app(application)
    register_error_handlers(application)

    task_repository = TaskRepository()
    user_repository = UserRepository()
    category_repository = CategoryRepository()

    task_controller = TaskController(
        TaskService(task_repository, user_repository, category_repository)
    )
    user_controller = UserController(
        UserService(user_repository, task_repository, issue_token)
    )
    report_controller = ReportController(
        ReportService(task_repository, user_repository, category_repository)
    )

    application.register_blueprint(build_task_blueprint(task_controller))
    application.register_blueprint(build_user_blueprint(user_controller))
    application.register_blueprint(build_report_blueprint(report_controller))

    @application.get("/health")
    def health():
        return {"status": "ok", "timestamp": str(datetime.now())}

    @application.get("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    return application


# Adapter de compatibilidade para `from app import app` e servidores WSGI.
app = create_app()


if __name__ == "__main__":
    app.run(
        debug=app.config["DEBUG"],
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
    )
