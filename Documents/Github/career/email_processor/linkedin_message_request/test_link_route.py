import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_link_page():
    response = client.get("/link")
    assert response.status_code == 200
    assert "Submit Career Job Link" in response.text

def test_post_link_route():
    payload = {
        "url": "https://careers.google.com/jobs/results/test12345",
        "status": "Pending"
    }
    response = client.post("/link", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Career page job link saved successfully"
    assert "saved_date" in data
    print("Test passed! Saved date:", data["saved_date"])

if __name__ == "__main__":
    test_get_link_page()
    test_post_link_route()
    print("ALL TESTS PASSED SUCCESSFULLY!")
