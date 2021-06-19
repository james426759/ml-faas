import pika
import pandas as pd

credentials = pika.PlainCredentials('user', 'user')
connection = pika.BlockingConnection(pika.ConnectionParameters('10.20.1.54', 30672, '/', credentials))

channel = connection.channel()

channel.queue_declare(queue='hello')

method_frame, header_frame, body = channel.basic_get(queue = 'hello', auto_ack=True)

if method_frame:
    a = body.decode("utf-8").split(",")
    a = pd.Series(a).astype("bool").tolist()
    print(a)
    print(type(a))
else:
    print('No message returned')