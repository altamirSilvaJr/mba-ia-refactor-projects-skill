import unittest

from app import create_app
from database import db
from models.category import Category
from models.task import Task
from models.user import User


class AppContractTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-only-secret",
            "CORS_ORIGINS": ("http://localhost",),
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            admin = User(name="Admin", email="admin@example.com", role="admin")
            admin.set_password("admin-pass")
            user = User(name="User", email="user@example.com", role="user")
            user.set_password("user-pass")
            category = Category(name="Backend")
            db.session.add_all((admin, user, category))
            db.session.commit()
            task = Task(title="Existing task", user_id=user.id, category_id=category.id)
            db.session.add(task)
            db.session.commit()

        self.admin_headers = self._login("admin@example.com", "admin-pass")
        self.user_headers = self._login("user@example.com", "user-pass")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self, email, password):
        response = self.client.post("/login", json={"email": email, "password": password})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertNotIn("password", body["user"])
        return {"Authorization": f"Bearer {body['token']}"}

    def test_original_endpoint_inventory_is_preserved(self):
        rules = {
            (method, rule.rule)
            for rule in self.app.url_map.iter_rules()
            for method in rule.methods
            if method not in {"HEAD", "OPTIONS"} and rule.endpoint != "static"
        }
        expected = {
            ("GET", "/"), ("GET", "/health"), ("POST", "/login"),
            ("GET", "/tasks"), ("POST", "/tasks"), ("GET", "/tasks/<int:task_id>"),
            ("PUT", "/tasks/<int:task_id>"), ("DELETE", "/tasks/<int:task_id>"),
            ("GET", "/tasks/search"), ("GET", "/tasks/stats"),
            ("GET", "/users"), ("POST", "/users"), ("GET", "/users/<int:user_id>"),
            ("PUT", "/users/<int:user_id>"), ("DELETE", "/users/<int:user_id>"),
            ("GET", "/users/<int:user_id>/tasks"),
            ("GET", "/reports/summary"), ("GET", "/reports/user/<int:user_id>"),
            ("GET", "/categories"), ("POST", "/categories"),
            ("PUT", "/categories/<int:category_id>"), ("DELETE", "/categories/<int:category_id>"),
        }
        self.assertEqual(rules, expected)

    def test_authentication_and_role_enforcement(self):
        self.assertEqual(self.client.get("/tasks").status_code, 401)
        self.assertEqual(self.client.get("/reports/summary", headers=self.user_headers).status_code, 403)
        self.assertEqual(self.client.get("/reports/summary", headers=self.admin_headers).status_code, 200)

    def test_public_registration_cannot_choose_admin_role(self):
        response = self.client.post("/users", json={
            "name": "Attacker", "email": "attacker@example.com", "password": "pass1234", "role": "admin"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["role"], "user")
        self.assertNotIn("password", response.get_json())

    def test_task_crud_and_invalid_input_contract(self):
        invalid = self.client.post("/tasks", headers=self.user_headers, json={"title": "x"})
        self.assertEqual(invalid.status_code, 400)
        created = self.client.post("/tasks", headers=self.user_headers, json={"title": "New task", "priority": 2})
        self.assertEqual(created.status_code, 201)
        task_id = created.get_json()["id"]
        updated = self.client.put(f"/tasks/{task_id}", headers=self.user_headers, json={"status": "done"})
        self.assertEqual(updated.status_code, 200)
        deleted = self.client.delete(f"/tasks/{task_id}", headers=self.user_headers)
        self.assertEqual(deleted.status_code, 200)

    def test_category_delete_preserves_tasks_with_null_reference(self):
        categories = self.client.get("/categories", headers=self.admin_headers).get_json()
        category_id = categories[0]["id"]
        response = self.client.delete(f"/categories/{category_id}", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            task = db.session.scalar(db.select(Task))
            self.assertIsNone(task.category_id)


if __name__ == "__main__":
    unittest.main()
