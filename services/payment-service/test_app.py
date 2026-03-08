import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_pay(client):
    response = client.post('/pay', json={'amount': 100})
    assert response.status_code == 200
    assert response.get_json()['status'] == 'paid'