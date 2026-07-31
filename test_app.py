import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_weather_endpoint_structure(client):
    response = client.get('/')
    assert response.status_code == 200
    assert len(response.data) > 0