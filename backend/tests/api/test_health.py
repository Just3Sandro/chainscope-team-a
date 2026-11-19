from uuid import UUID


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert UUID(response.headers["X-Request-ID"]).version == 4


def test_client_request_id_is_ignored(client):
    client_id = "e604f91f-d681-47e9-b3d1-0554ae14751e"
    response = client.get("/api/v1/health", headers={"X-Request-ID": client_id})
    assert response.headers["X-Request-ID"] != client_id
    assert UUID(response.headers["X-Request-ID"]).version == 4
