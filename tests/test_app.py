import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

initial_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))


client = TestClient(app)


def test_get_activities_returns_all_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert "Chess Club" in activities
    assert "Programming Class" in activities


def test_signup_for_activity_success():
    email = "test-student@mergington.edu"
    response = client.post("/activities/Chess%20Club/signup", json={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}

    activity = client.get("/activities").json()["Chess Club"]
    assert email in activity["participants"]


def test_signup_for_activity_rejects_duplicate():
    email = "duplicate-student@mergington.edu"
    client.post("/activities/Programming%20Class/signup", json={"email": email})
    response = client.post("/activities/Programming%20Class/signup", json={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_activity_requires_valid_email():
    response = client.post("/activities/Gym%20Class/signup", json={"email": "not-an-email"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email address"


def test_signup_for_activity_returns_activity_full_error():
    activity_name = "Debate Team"
    current_participants = client.get("/activities").json()[activity_name]["participants"]
    max_participants = client.get("/activities").json()[activity_name]["max_participants"]

    for i in range(max_participants - len(current_participants)):
        client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup",
            json={"email": f"student{i}@mergington.edu"},
        )

    response = client.post(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        json={"email": "overflow-student@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_from_activity_success():
    email = "remove-student@mergington.edu"
    client.post("/activities/Soccer%20Team/signup", json={"email": email})

    response = client.request(
        "DELETE",
        "/activities/Soccer%20Team/unregister",
        json={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Soccer Team"}

    activity = client.get("/activities").json()["Soccer Team"]
    assert email not in activity["participants"]


def test_unregister_from_activity_returns_not_found_for_missing_participant():
    response = client.request(
        "DELETE",
        "/activities/Art%20Club/unregister",
        json={"email": "ghost-student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
