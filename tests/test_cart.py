"""
Tests for the /cart endpoints.
Uses FastAPI's TestClient backed by an in-memory SQLite database.
"""
from fastapi.testclient import TestClient

USER_ID = "test-user-cart"
PRODUCT_PAYLOAD = {"name": "Cart Widget", "price": "9.99", "stock": 20}


def create_product(client: TestClient) -> dict:
    return client.post("/products", json=PRODUCT_PAYLOAD).json()


class TestGetCart:
    def test_get_empty_cart_creates_on_first_access(
        self, client: TestClient
    ) -> None:
        response = client.get(f"/cart/{USER_ID}")
        assert response.status_code == 200
        body = response.json()
        assert body["user_id"] == USER_ID
        assert body["items"] == []

    def test_get_cart_idempotent(self, client: TestClient) -> None:
        resp1 = client.get(f"/cart/{USER_ID}")
        resp2 = client.get(f"/cart/{USER_ID}")
        assert resp1.json()["id"] == resp2.json()["id"]


class TestAddItem:
    def test_add_item_success(self, client: TestClient) -> None:
        product = create_product(client)
        payload = {"product_id": product["id"], "quantity": 2}

        response = client.post(f"/cart/{USER_ID}/items", json=payload)
        assert response.status_code == 201
        body = response.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["product_id"] == product["id"]
        assert body["items"][0]["quantity"] == 2

    def test_add_same_item_twice_increments_quantity(
        self, client: TestClient
    ) -> None:
        product = create_product(client)
        payload = {"product_id": product["id"], "quantity": 1}

        client.post(f"/cart/{USER_ID}/items", json=payload)
        response = client.post(f"/cart/{USER_ID}/items", json=payload)

        assert response.status_code == 201
        items = response.json()["items"]
        # There should be exactly one item with qty=2
        matching = [i for i in items if i["product_id"] == product["id"]]
        assert len(matching) == 1
        assert matching[0]["quantity"] == 2

    def test_add_nonexistent_product(self, client: TestClient) -> None:
        payload = {"product_id": 999999, "quantity": 1}
        response = client.post(f"/cart/{USER_ID}/items", json=payload)
        assert response.status_code == 404

    def test_add_exceeds_stock(self, client: TestClient) -> None:
        product = create_product(client)
        payload = {"product_id": product["id"], "quantity": 9999}
        response = client.post(f"/cart/{USER_ID}/items", json=payload)
        assert response.status_code == 400


class TestUpdateItem:
    def test_update_quantity(self, client: TestClient) -> None:
        product = create_product(client)
        add_resp = client.post(
            f"/cart/{USER_ID}/items",
            json={"product_id": product["id"], "quantity": 1},
        )
        item_id = add_resp.json()["items"][0]["id"]

        response = client.put(
            f"/cart/{USER_ID}/items/{item_id}", json={"quantity": 5}
        )
        assert response.status_code == 200
        items = response.json()["items"]
        matching = [i for i in items if i["id"] == item_id]
        assert matching[0]["quantity"] == 5

    def test_update_nonexistent_item(self, client: TestClient) -> None:
        response = client.put(
            f"/cart/{USER_ID}/items/999999", json={"quantity": 1}
        )
        assert response.status_code == 404


class TestRemoveItem:
    def test_remove_item(self, client: TestClient) -> None:
        product = create_product(client)
        add_resp = client.post(
            f"/cart/{USER_ID}/items",
            json={"product_id": product["id"], "quantity": 1},
        )
        item_id = add_resp.json()["items"][0]["id"]

        response = client.delete(f"/cart/{USER_ID}/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_remove_nonexistent_item(self, client: TestClient) -> None:
        response = client.delete(f"/cart/{USER_ID}/items/999999")
        assert response.status_code == 404


class TestClearCart:
    def test_clear_cart(self, client: TestClient) -> None:
        product = create_product(client)
        client.post(
            f"/cart/{USER_ID}/items",
            json={"product_id": product["id"], "quantity": 2},
        )

        response = client.delete(f"/cart/{USER_ID}")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_clear_empty_cart(self, client: TestClient) -> None:
        # Clearing an already empty cart should succeed
        response = client.delete("/cart/empty-cart-user-42")
        assert response.status_code == 200
        assert response.json()["items"] == []
