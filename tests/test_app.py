import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# keep a pristine snapshot of the starting data so each test runs against
# the same state
_original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict before every test."""
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))
    yield


# client can be shared by all tests once the fixture resets state
client = TestClient(app)


def test_root_redirect():
    # Arrange: fixture has already reset state
    # Act
    response = client.get("/", follow_redirects=False)
    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    # Arrange
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # some known keys should be present
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_success():
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    assert email not in activities[activity]["participants"]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    assert response.json()["message"] == f"Signed up {email} for {activity}"


def test_signup_already_signed():
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_activity_not_found():
    # Arrange
    activity = "Nonexistent"
    email = "someone@example.com"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unregister_success():
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    assert email in activities[activity]["participants"]

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]
    assert response.json()["message"] == f"Unregistered {email} from {activity}"


def test_unregister_not_signed():
    # Arrange
    activity = "Chess Club"
    email = "absent@mergington.edu"
    assert email not in activities[activity]["participants"]

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert "participant not found" in response.json()["detail"].lower()


def test_unregister_activity_not_found():
    # Arrange
    activity = "Nope"
    email = "someone@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert "activity not found" in response.json()["detail"].lower()
