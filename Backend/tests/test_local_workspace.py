from fastapi.testclient import TestClient

from app.main import app
from app.services.projects import project_service
from app.storage.repository import JSONDocumentRepository


def test_anonymous_workspace_project_crud(monkeypatch, tmp_path):
    projects_repo = JSONDocumentRepository("projects", data_dir=str(tmp_path))
    monkeypatch.setattr(project_service, "get_repository", lambda _: projects_repo)
    client = TestClient(app)

    created = client.post(
        "/api/projects",
        json={"id": "local-workspace-test", "name": "Local Workspace Test"},
    )

    assert created.status_code == 201
    assert created.json()["userId"] == "local-workspace"

    listed = client.get("/api/projects")
    assert listed.status_code == 200
    assert any(project["id"] == "local-workspace-test" for project in listed.json())

    deleted = client.delete("/api/projects/local-workspace-test")
    assert deleted.status_code == 200
    assert client.get("/api/me").status_code == 404
    assert client.post("/api/auth/sync").status_code == 404