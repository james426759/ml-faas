from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_cors import CORS
from minio import Minio
from minio.error import S3Error
import os
import requests
import kubernetes
import yaml
from pprint import pprint
import json
import uuid


DEV_UPLOAD_FOLDER = 'dev-upload-file'

def dev_upload_file():

    

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure=False
    )

    kubernetes.config.load_kube_config()
    api_instance = kubernetes.client.CustomObjectsApi()
    api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name='lstm-pipeline', namespace='ml-faas')


    DEV_PIPELINE_LIST = []
    stage_list = api_response['status']['create_fn']['api_list']
    for i in stage_list:
        if 'dev' in stage_list[i]['rule']:
            for j in stage_list[i]['step']:
                DEV_PIPELINE_LIST.append(j)

    file_uuid = str(uuid.uuid4())
    bucket_name = DEV_UPLOAD_FOLDER
    fname = 'test.csv'

    # DEV_PIPELINE_LIST = ['lstm-pipeline-load-data', 'lstm-pipeline-time-parser', 'lstm-pipeline-data-clean']
    for i in DEV_PIPELINE_LIST:
        data = {'fname':fname, 'file_uuid':file_uuid, 'bucket_name':bucket_name, 'pipeline':'lstm-pipeline', 'function_name':i}
        print(data)
        r = requests.post(f"""http://10.20.1.54:31112/function/{i}""", json=data)
        bucket_name = r.text
        bucket_name = bucket_name.replace('\n', '').replace('\r', '')
        # # print(r.json())
        if r.status_code == 200:
            res = requests.post(f"""http://admin:admin@10.20.1.54:31112/system/scale-function/{i}""", json={"replicas": 0})
            continue
        else:
            print({'Function':i,'status_code':r.status_code})
            return 'r.status_code'
    # return "q123"
    if r.status_code == 200:
        uuid_renamed = i + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
        url = client.presigned_get_object('lstm-pipeline-model-serving-fun', uuid_renamed)
        return url
    else:
        return 'no url'

    # return jsonify({'status_code':r.status_code, 'text':r.text})
a = dev_upload_file()
print(a)