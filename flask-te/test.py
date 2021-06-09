from minio import Minio
from minio.error import S3Error
import kubernetes
from pprint import pprint
import requests
import json
import warnings


client = Minio(
    "10.20.1.54:30020",
    access_key="admin",
    secret_key="secretsecret",
    secure = False
    )

# kubernetes.config.load_kube_config()
# api_instance = kubernetes.client.CustomObjectsApi()
# api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name='lstm-pipeline', namespace='ml-faas')

# DEV_PIPELINE_LIST = []
# stage_list = api_response['status']['create_fn']['api_list']
# for i in stage_list:
#     if 'dev' in stage_list[i]['rule']:
#         for j in stage_list[i]['step']:
#             DEV_PIPELINE_LIST.append(j)
# # print(DEV_PIPELINE_LIST)
# for j in DEV_PIPELINE_LIST[0:6]:
#     print(j)
# client.fget_object('lstm-pipeline-train-data-build', 'xt-'+'lstm-pipeline-train-data-build'+'-test'+'-ca7ba161-5f60-4502-998a-05b343827773.json', '/home/app/xt.json')

print(client.presigned_get_object('lstm-pipeline-model-serving-fun', 'aaa'))