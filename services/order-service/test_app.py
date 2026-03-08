import pytest
from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_create_order(client):
    response = client.post('/orders', json={'product_id': 1, 'quantity': 2})
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data