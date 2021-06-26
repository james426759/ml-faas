from minio import Minio
from minio.error import S3Error
import kubernetes
from pprint import pprint
import requests
import json
import warnings
import os
import json

client = Minio(
    "10.20.1.54:30020",
    access_key="admin",
    secret_key="secretsecret",
    secure = False
    )

# kubernetes.config.load_kube_config()
# api_instance = kubernetes.client.CustomObjectsApi()
# api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name='random-forest-pipeline', namespace='ml-faas')

# result = client.stat_object("lstm-pipeline-model-serving-fun", "lstm-pipeline-model-serving-fun-test-cc104c5b-90c5-426f-90c9-0dabc5fabbe6.csv")
# print(result.last_modified)
# a = os.popen("mc --json ls ml-faas-storage/lstm-pipeline-model-serving-fun ").read()
# # b = json.loads(a)
# b = a.split('\n')
# print(b[1])
# object_list = client.list_objects('lstm-pipeline-model-serving-fun',recursive=True)
# a = []
# # # print(object_list)
# for i in object_list:
#     result = client.stat_object("lstm-pipeline-model-serving-fun", i.object_name)
#     a.append(result.last_modified)
#     if max(a) == result.last_modified:
#         b = i.object_name
#     else:
#         continue
#     # print(type(result.last_modified))
# print(b)
# print(a)
# print(a)
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

# client.fget_object("random-forest-condition", 'random-forest-condition-a05160ef-dc21-4d01-b5a9-68739ba8ede2.json', '/home/ubuntu/ml-faas-k/flask-te/user-uploaded-file/random-forest-condition-a05160ef-dc21-4d01-b5a9-68739ba8ede2.json')

# with open('/home/ubuntu/ml-faas-k/flask-te/user-uploaded-file/random-forest-condition-a05160ef-dc21-4d01-b5a9-68739ba8ede2.json', 'r') as obj:
#     x_dict = json.load(obj)

# print(type(x_dict["condition"]))