from minio import Minio
from minio.error import S3Error
import kubernetes
from pprint import pprint
import requests
import json


client = Minio(
    "10.20.1.54:30020",
    access_key="admin",
    secret_key="secretsecret",
    secure = False
    )


# minio_object_list = client.list_objects('lstm-pipeline-load-data',recursive=True)
# object_list=[]
# for i in minio_object_list:
#     # object_list.append(i.object_name)
#     client.remove_object('lstm-pipeline-load-data',i.object_name)

# "serviceName":"lstm-pipeline-load-data",
# client.remove_objects('lstm-pipeline-load-data',object_list)
# data = {"replicas": 0}
# r = requests.post('http://admin:admin@10.20.1.54:31112/system/scale-function/lstm-pipeline-data-clean', json=data)
# print(r)
# kubernetes.config.load_kube_config()
# api_instance = kubernetes.client.CustomObjectsApi()
# api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name='lstm-pipeline', namespace='ml-faas')

# USER_PIPELINE_LIST = []
# a = api_response['status']['create_fn']['api_list']
# for i in a:
#     if 'user' in a[i]['rule']:
#         for j in a[i]['step']:
#             USER_PIPELINE_LIST.append(j)
# for i in USER_PIPELINE_LIST[0:3]:

#     print(i)
# rule = api_response['status']['create_fn']['api_list']['stage1']['rule']
# if 'user' in rule:
#     print('111111')
# print(rule)


for i in range(5):
    print(i)
print(i)