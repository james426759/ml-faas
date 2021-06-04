from minio import Minio
from minio.error import S3Error
import kubernetes
from pprint import pprint


kubernetes.config.load_kube_config()
api_instance = kubernetes.client.CustomObjectsApi()

api_response = api_instance.list_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', namespace='ml-faas')
a = []
# pprint(api_response['items'][0]['metadata']['name'])
for i in api_response['items']:
    a.append(i['metadata']['name'])
    # print(type(i['metadata']['name']))
print(a)