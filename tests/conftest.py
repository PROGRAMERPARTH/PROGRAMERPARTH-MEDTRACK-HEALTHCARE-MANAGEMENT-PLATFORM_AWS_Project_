"""Test fixtures and client setup."""
import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-key"})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login_as(client, email, password):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)
