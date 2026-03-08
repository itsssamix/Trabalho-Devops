import pytest
from flask import Flask

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True

    @app.route('/reserve', methods=['POST'])
    def reserve():
        return {'status': 'reserved'}, 200

    yield app.test_client()

def test_reserve_inventory(client):
    response = client.post('/reserve', json={'product_id': 1, 'quantity': 1})
    assert response.status_code == 200