import pytest
from flask import Flask

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True

    @app.route('/pay', methods=['POST'])
    def pay():
        return {'status': 'paid'}, 200

    yield app.test_client()

def test_pay(client):
    response = client.post('/pay', json={'amount': 100})
    assert response.status_code == 200
    assert response.get_json()['status'] == 'paid'