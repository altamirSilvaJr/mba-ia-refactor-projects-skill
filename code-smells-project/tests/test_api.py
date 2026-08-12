import os
import tempfile
import unittest

from src.app import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        handle, self.database_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        self.app = create_app({
            "TESTING": True, "DATABASE_PATH": self.database_path,
            "ADMIN_TOKEN": "test-admin-token", "CORS_ORIGINS": ["http://localhost"],
        })
        self.client = self.app.test_client()

    def tearDown(self):
        os.unlink(self.database_path)

    def test_read_endpoints_preserve_contract(self):
        for path in ("/", "/health", "/produtos", "/produtos/1", "/usuarios", "/usuarios/1", "/pedidos", "/pedidos/usuario/1", "/relatorios/vendas"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.is_json)

    def test_product_crud_and_search(self):
        created = self.client.post("/produtos", json={"nome": "Produto Teste", "preco": 10, "estoque": 2})
        self.assertEqual(created.status_code, 201)
        product_id = created.get_json()["dados"]["id"]
        self.assertEqual(self.client.get(f"/produtos/{product_id}").status_code, 200)
        self.assertEqual(self.client.get("/produtos/busca?q=Teste").get_json()["total"], 1)
        self.assertEqual(self.client.put(f"/produtos/{product_id}", json={"nome": "Atualizado", "preco": 12, "estoque": 3}).status_code, 200)
        self.assertEqual(self.client.delete(f"/produtos/{product_id}").status_code, 200)

    def test_invalid_product_is_rejected(self):
        response = self.client.post("/produtos", json={"nome": "x", "preco": "bad", "estoque": -1})
        self.assertEqual(response.status_code, 400)

    def test_user_password_is_hashed_and_not_serialized(self):
        response = self.client.post("/usuarios", json={"nome": "Teste", "email": "teste@example.com", "senha": "safe-pass-123"})
        self.assertEqual(response.status_code, 201)
        users = self.client.get("/usuarios").get_json()["dados"]
        self.assertNotIn("senha", users[-1])
        self.assertEqual(self.client.post("/login", json={"email": "teste@example.com", "senha": "safe-pass-123"}).status_code, 200)

    def test_order_flow(self):
        response = self.client.post("/pedidos", json={"usuario_id": 1, "itens": [{"produto_id": 1, "quantidade": 1}]})
        self.assertEqual(response.status_code, 201)
        order_id = response.get_json()["dados"]["pedido_id"]
        self.assertEqual(self.client.put(f"/pedidos/{order_id}/status", json={"status": "aprovado"}).status_code, 200)
        self.assertEqual(len(self.client.get("/pedidos").get_json()["dados"]), 1)

    def test_admin_surfaces_are_safe(self):
        self.assertEqual(self.client.post("/admin/query", json={"sql": "DROP TABLE usuarios"}).status_code, 410)
        self.assertEqual(self.client.post("/admin/reset-db").status_code, 403)


if __name__ == "__main__":
    unittest.main()
