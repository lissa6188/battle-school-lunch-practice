from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_search_schools_min_length():
    r = client.get("/api/schools?query=a")
    assert r.status_code == 422


def test_search_schools_success():
    r = client.get("/api/schools?query=서울")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any("서울" in s["name"] for s in data)


def test_meals_validation_start_after_end():
    r = client.get("/api/meals?school_code=1001&start_date=2026-08-10&end_date=2026-08-01")
    assert r.status_code == 400


def test_meals_range_too_large():
    r = client.get("/api/meals?school_code=1001&start_date=2026-01-01&end_date=2026-04-01")
    assert r.status_code == 400


def test_meals_school_not_found():
    r = client.get("/api/meals?school_code=9999&start_date=2026-08-01&end_date=2026-08-02")
    assert r.status_code == 404


def test_meals_returns_list():
    r = client.get("/api/meals?school_code=1001&start_date=2026-08-17&end_date=2026-08-18")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert all("date" in item for item in data)
