from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL',
                              'http://localhost:5001')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL',
                                'http://localhost:5002')
INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL',
                                  'http://localhost:5003')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "API Gateway is healthy"})


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    # Primeiro, verificar estoque
    inventory_response = requests.post(
        f"{INVENTORY_SERVICE_URL}/reserve", json=data)
    if inventory_response.status_code != 200:
        return jsonify({"error": "Inventory reservation failed"}), 400

    # Criar pedido
    order_response = requests.post(
        f"{ORDER_SERVICE_URL}/orders", json=data)
    if order_response.status_code != 201:
        # Rollback inventory
        requests.post(f"{INVENTORY_SERVICE_URL}/release", json=data)
        return jsonify({"error": "Order creation failed"}), 400

    # Processar pagamento
    payment_response = requests.post(
        f"{PAYMENT_SERVICE_URL}/pay", json=data)
    if payment_response.status_code != 200:
        # Rollback
        requests.delete(
            f"{ORDER_SERVICE_URL}/orders/{order_response.json()['id']}")
        requests.post(f"{INVENTORY_SERVICE_URL}/release", json=data)
        return jsonify({"error": "Payment failed"}), 400

    return jsonify({"message": "Order created successfully",
                    "order": order_response.json()}), 201


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    response = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
    return response.json(), response.status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
