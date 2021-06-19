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

kubernetes.config.load_kube_config()
api_instance = kubernetes.client.CustomObjectsApi()
api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name='random-forest-pipeline', namespace='ml-faas')

DEV_PIPELINE_LIST = []
function_bucket = {}
stage_list = api_response['status']['create_fn']['api_list']
for i in stage_list:
    if 'dev' in stage_list[i]['rule']:
        for j in stage_list[i]['step']:
            DEV_PIPELINE_LIST.append(j)
            function_bucket.update({j:j})
a = function_bucket['random-forest-pipeline-train-model']
print(a)

# client.fget_object('lstm-pipeline-train-data-build', 'xt-'+'lstm-pipeline-train-data-build'+'-test'+'-ca7ba161-5f60-4502-998a-05b343827773.json', '/home/app/xt.json')

# DEV_PIPELINE_LIST = []

# dev_b_list = {}
# stage_list = api_response['status']['create_fn']['api_list']
# for i in stage_list:
#     if 'dev' in stage_list[i]['rule']:
#         for j in stage_list[i]['step']:
#             dev_b_list.update({j:j})
# data = {'fname':'fname', 'file_uuid':'file_uuid', 'pipeline':'pipeline', 'function_name':i, 'dev_b_list':dev_b_list}
# print(data)
# kubernetes.config.load_kube_config()
# api_instance = kubernetes.client.CustomObjectsApi()
# api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name='lstm-pipeline', namespace='ml-faas')

# print(api_response['status']['create_fn']['api_list']['stage2']['step'][2])