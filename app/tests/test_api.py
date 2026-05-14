import pytest
import respx
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@respx.mock
def test_get_user_gists_success():
    mock_gist = {
        "id": "abc123",
        "html_url": "https://gist.github.com/octocat/abc123",
        "description": "A test gist",
        "created_at": "2024-01-01T12:00:00Z",
        "files": {"main.py": {"filename": "main.py", "size": 150, "language": "Python"}}
    }
    respx.get("https://api.github.com/users/octocat/gists").mock(
        return_value=httpx.Response(200, json=[mock_gist])
    )
    response = client.get("/octocat")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "abc123"
    # Verify intermediate mapping (raw keys removed, structured files array)
    assert "html_url" not in data[0]
    assert data[0]["url"] == "https://gist.github.com/octocat/abc123"

@respx.mock
def test_user_not_found():
    respx.get("https://api.github.com/users/unknown_user/gists").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    response = client.get("/unknown_user")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@respx.mock
def test_rate_limit_exceeded():
    respx.get("https://api.github.com/users/octocat/gists").mock(
        return_value=httpx.Response(403, json={"message": "API rate limit exceeded"})
    )
    response = client.get("/octocat")
    assert response.status_code == 503
    assert "rate limit" in response.json()["detail"].lower()

@respx.mock
def test_github_api_server_error():
    respx.get("https://api.github.com/users/octocat/gists").mock(
        return_value=httpx.Response(500, json={"message": "Internal Server Error"})
    )
    response = client.get("/octocat")
    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"].lower()

@respx.mock
def test_pagination_handling():
    gist1 = {"id": "1", "html_url": "https://gist.github.com/1", "description": None, "created_at": "2024-01-01T00:00:00Z", "files": {"a.txt": {"filename": "a.txt", "size": 10, "language": None}}}
    gist2 = {"id": "2", "html_url": "https://gist.github.com/2", "description": None, "created_at": "2024-01-02T00:00:00Z", "files": {"b.txt": {"filename": "b.txt", "size": 20, "language": None}}}

    # Mock first page with 'next' link header
    next_url = "https://api.github.com/users/octocat/gists?page=2"
    respx.get("https://api.github.com/users/octocat/gists").mock(
        return_value=httpx.Response(200, json=[gist1], headers={"Link": f'<{next_url}>; rel="next"'})
    )
    # Mock second page (no next link)
    respx.get("https://api.github.com/users/octocat/gists", params={"page": 2}).mock(
        return_value=httpx.Response(200, json=[gist2])
    )

    response = client.get("/octocat")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == "1"
    assert response.json()[1]["id"] == "2"