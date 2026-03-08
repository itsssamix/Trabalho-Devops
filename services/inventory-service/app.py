from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pika
import json
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/pedidos')
db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=100)


def publish_event(event_type, data):
    connection = pika.BlockingConnection(
        pika.URLParameters(
            os.getenv('RABBITMQ_URL',
                      'amqp://guest:guest@localhost:5672/')))
    channel = connection.channel()
    channel.queue_declare(queue='events')
    channel.basic_publish(exchange='',
                          routing_key='events',
                          body=json.dumps({'type': event_type,
                                           'data': data}))
    connection.close()


@app.route('/reserve', methods=['POST'])
def reserve():
    data = request.json
    product = Product.query.get_or_404(data['product_id'])
    if product.quantity >= data['quantity']:
        product.quantity -= data['quantity']
        db.session.commit()
        publish_event('InventoryReserved',
                      {'product_id': product.id,
                       'quantity': data['quantity']})
        return jsonify({'status': 'reserved'}), 200
    return jsonify({'error': 'Insufficient stock'}), 400


@app.route('/release', methods=['POST'])
def release():
    data = request.json
    product = Product.query.get_or_404(data['product_id'])
    product.quantity += data['quantity']
    db.session.commit()
    publish_event('InventoryReleased',
                  {'product_id': product.id,
                   'quantity': data['quantity']})
    return jsonify({'status': 'released'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5003)
