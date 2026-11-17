from fastapi.testclient import TestClient
from amazon_search_service.main import app

def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["catalog_products"] >= 9000

def test_search():
    with TestClient(app) as client:
        r = client.post(
            "/search",
            json={
                "query": "best non drying lip stain",
                "top_k": 5,
                "candidate_k": 100
            }
        )
        assert r.status_code == 200
        body = r.json()
        assert body["query"] == "best non drying lip stain"
        assert len(body["results"]) == 5
        assert body["results"][0]["rank"] == 1
        assert "ranking_score" in body["results"][0]

def test_invalid_candidate_k():
    with TestClient(app) as client:
        r = client.post(
            "/search",
            json={
                "query": "lip stain",
                "top_k": 10,
                "candidate_k": 5
            }
        )
        assert r.status_code == 422
