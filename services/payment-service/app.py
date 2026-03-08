from flask import Flask, request, jsonify
import pika
import json
import os
import time

app = Flask(__name__)

def publish_event(event_type, data):
    connection = pika.BlockingConnection(pika.URLParameters(os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')))
    channel = connection.channel()
    channel.queue_declare(queue='events')
    channel.basic_publish(exchange='', routing_key='events', body=json.dumps({'type': event_type, 'data': data}))
    connection.close()

@app.route('/pay', methods=['POST'])
def pay():
    data = request.json
    # Simular processamento de pagamento
    time.sleep(1)  # Simular delay
    # Assumir sucesso
    publish_event('PaymentProcessed', {'order_id': data.get('order_id'), 'amount': data.get('amount', 100)})
    return jsonify({'status': 'paid'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)