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

def test_reserve_inventory(client):
    # Assuming a reserve endpoint
    response = client.post('/reserve', json={'product_id': 1, 'quantity': 1})
    assert response.status_code == 200