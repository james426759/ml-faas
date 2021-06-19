#!/usr/bin/env python
import pika

credentials = pika.PlainCredentials('user', 'user')
connection = pika.BlockingConnection(pika.ConnectionParameters('10.20.1.54', 30672, '/', credentials))
channel = connection.channel()

channel.queue_declare(queue='hello')

mess = [True, False, True]
mess1 = ','.join(str(e) for e in mess)
print(mess1)

channel.basic_publish(exchange='',
                      routing_key='hello',
                      body=mess1)

print(" [x] Sent message")
connection.close()