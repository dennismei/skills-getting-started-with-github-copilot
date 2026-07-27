import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient
from src import app as app_module

client = TestClient(app_module.app)

@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities = original_activities


def test_get_activities_returns_seeded_activities():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert expected_activity in data
    assert "description" in data[expected_activity]
    assert "participants" in data[expected_activity]
    assert "michael@mergington.edu" in data[expected_activity]["participants"]


def test_signup_adds_participant_to_activity():
    # Arrange
    activity_name = "Chess Club"
    encoded_activity_name = urllib.parse.quote(activity_name, safe="")
    email = "test.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}

    get_response = client.get("/activities")
    assert email in get_response.json()[activity_name]["participants"]


def test_duplicate_signup_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    encoded_activity_name = urllib.parse.quote(activity_name, safe="")
    email = "duplicate.student@mergington.edu"
    client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_from_activity():
    # Arrange
    activity_name = "Chess Club"
    encoded_activity_name = urllib.parse.quote(activity_name, safe="")
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}

    get_response = client.get("/activities")
    assert email not in get_response.json()[activity_name]["participants"]


def test_remove_missing_participant_returns_not_found():
    # Arrange
    activity_name = "Chess Club"
    encoded_activity_name = urllib.parse.quote(activity_name, safe="")
    email = "notfound@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_root_redirects_to_static_index():
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (301, 302, 307)
    assert response.headers["location"] == "/static/index.html"
