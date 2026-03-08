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


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='pending')


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


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    order = Order(product_id=data['product_id'],
                  quantity=data['quantity'])
    db.session.add(order)
    db.session.commit()
    publish_event('OrderCreated',
                  {'order_id': order.id,
                   'product_id': order.product_id,
                   'quantity': order.quantity})
    return jsonify({'id': order.id,
                    'product_id': order.product_id,
                    'quantity': order.quantity,
                    'status': order.status}), 201


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({'id': order.id,
                    'product_id': order.product_id,
                    'quantity': order.quantity,
                    'status': order.status})


@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    publish_event('OrderCancelled', {'order_id': order_id})
    return jsonify({'message': 'Order deleted'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001)