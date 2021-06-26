import pika
# import pandas as pd

credentials = pika.PlainCredentials('user', 'user')
connection = pika.BlockingConnection(pika.ConnectionParameters('10.20.1.54', 30672, '/', credentials))

channel = connection.channel()

# a = channel.queue_declare(queue='lstm-pipeline-data-clean is being used')
# b = a.method.message_count
# print(type(b))

method_frame, header_frame, body = channel.basic_get(queue = 'lstm-pipeline-model-serving-fun', auto_ack=True)
print(method_frame)
channel.basic_ack(delivery_tag = method_frame.delivery_tag)


# if method_frame:
#     a = body.decode("utf-8").split(",")
#     a = pd.Series(a).astype("bool").tolist()
#     print(a)
#     print(type(a))
# else:
#     print('No message returned')