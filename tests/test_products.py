"""
Tests for the /products CRUD endpoints.
Uses FastAPI's TestClient backed by an in-memory SQLite database.
"""
from fastapi.testclient import TestClient


PRODUCT_PAYLOAD = {
    "name": "Test Widget",
    "description": "A great test widget",
    "price": "19.99",
    "stock": 50,
}


class TestListProducts:
    def test_list_empty(self, client: TestClient) -> None:
        response = client.get("/products")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_list_with_items(self, client: TestClient) -> None:
        client.post("/products", json=PRODUCT_PAYLOAD)
        response = client.get("/products")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    def test_list_pagination(self, client: TestClient) -> None:
        # Create 3 products
        for i in range(3):
            client.post("/products", json={**PRODUCT_PAYLOAD, "name": f"Widget {i}"})

        response = client.get("/products?limit=2&skip=0")
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) <= 2


class TestGetProduct:
    def test_get_existing(self, client: TestClient) -> None:
        created = client.post("/products", json=PRODUCT_PAYLOAD).json()
        product_id = created["id"]

        response = client.get(f"/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["id"] == product_id
        assert response.json()["name"] == PRODUCT_PAYLOAD["name"]

    def test_get_not_found(self, client: TestClient) -> None:
        response = client.get("/products/999999")
        assert response.status_code == 404


class TestCreateProduct:
    def test_create_success(self, client: TestClient) -> None:
        response = client.post("/products", json=PRODUCT_PAYLOAD)
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == PRODUCT_PAYLOAD["name"]
        assert "id" in body
        assert "created_at" in body

    def test_create_minimal(self, client: TestClient) -> None:
        payload = {"name": "Minimal Product", "price": "5.00"}
        response = client.post("/products", json=payload)
        assert response.status_code == 201
        body = response.json()
        assert body["stock"] == 0
        assert body["description"] is None

    def test_create_invalid_price(self, client: TestClient) -> None:
        bad_payload = {**PRODUCT_PAYLOAD, "price": "-1.00"}
        response = client.post("/products", json=bad_payload)
        assert response.status_code == 422

    def test_create_missing_name(self, client: TestClient) -> None:
        bad_payload = {"price": "10.00"}
        response = client.post("/products", json=bad_payload)
        assert response.status_code == 422


class TestUpdateProduct:
    def test_update_name(self, client: TestClient) -> None:
        created = client.post("/products", json=PRODUCT_PAYLOAD).json()
        product_id = created["id"]

        response = client.put(
            f"/products/{product_id}", json={"name": "Updated Widget"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Widget"
        # Other fields should be unchanged
        assert response.json()["stock"] == PRODUCT_PAYLOAD["stock"]

    def test_update_stock(self, client: TestClient) -> None:
        created = client.post("/products", json=PRODUCT_PAYLOAD).json()
        product_id = created["id"]

        response = client.put(f"/products/{product_id}", json={"stock": 999})
        assert response.status_code == 200
        assert response.json()["stock"] == 999

    def test_update_not_found(self, client: TestClient) -> None:
        response = client.put("/products/999999", json={"name": "Ghost"})
        assert response.status_code == 404


class TestDeleteProduct:
    def test_delete_success(self, client: TestClient) -> None:
        created = client.post("/products", json=PRODUCT_PAYLOAD).json()
        product_id = created["id"]

        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404

    def test_delete_not_found(self, client: TestClient) -> None:
        response = client.delete("/products/999999")
        assert response.status_code == 404
