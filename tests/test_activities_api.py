import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY = "Test Activity"
EXISTING_EMAIL = "existing@example.com"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            ACTIVITY: {
                "description": "An activity for API tests",
                "schedule": "Mondays",
                "max_participants": 4,
                "participants": [EXISTING_EMAIL],
            }
        },
    )

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()[ACTIVITY]["participants"] == [EXISTING_EMAIL]


def test_signup_adds_participant(client):
    email = "new@example.com"

    response = client.post(
        f"/activities/{ACTIVITY}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {ACTIVITY}"
    assert client.get("/activities").json()[ACTIVITY]["participants"] == [
        EXISTING_EMAIL,
        email,
    ]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant_without_changing_list(client):
    response = client.post(
        f"/activities/{ACTIVITY}/signup",
        params={"email": EXISTING_EMAIL},
    )

    assert response.status_code == 400
    assert client.get("/activities").json()[ACTIVITY]["participants"] == [
        EXISTING_EMAIL
    ]


def test_unregister_removes_participant(client):
    response = client.delete(
        f"/activities/{ACTIVITY}/signup",
        params={"email": EXISTING_EMAIL},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {EXISTING_EMAIL} from {ACTIVITY}"
    assert client.get("/activities").json()[ACTIVITY]["participants"] == []


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": EXISTING_EMAIL},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_nonparticipant(client):
    email = "not-registered@example.com"
    response = client.delete(
        f"/activities/{ACTIVITY}/signup",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert client.get("/activities").json()[ACTIVITY]["participants"] == [
        EXISTING_EMAIL
    ]
