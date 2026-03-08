import pytest
from flask import Flask

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True

    @app.route('/orders', methods=['POST'])
    def create_order():
        return {'message': 'Order created'}, 201

    yield app.test_client()

def test_create_order(client):
    response = client.post('/orders', json={'product_id': 1, 'quantity': 2})
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Order created'