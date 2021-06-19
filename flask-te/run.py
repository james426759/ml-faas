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
import pika
import time


app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'user-uploaded-file'
DEV_UPLOAD_FOLDER = 'dev-upload-file'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEV_UPLOAD_FOLDER'] = DEV_UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])

# User upload, get complete data download url, output:{"status_code": int, "url": str}
@app.route('/user/upload/<string:pipeline>/<string:model_bucket>/<string:model_name>', methods=['POST'], strict_slashes=False)
def api_upload(pipeline,model_bucket,model_name=''):

    file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure=False
    )

    kubernetes.config.load_kube_config()
    api_instance = kubernetes.client.CustomObjectsApi()
    api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name=pipeline, namespace='ml-faas')

    f = request.files['file']
    if f:
        fname = f.filename
        f.save(os.path.join(file_dir, fname))

        found = client.bucket_exists(UPLOAD_FOLDER)
        if not found:
            client.make_bucket(UPLOAD_FOLDER)

        try:
            client.fput_object(UPLOAD_FOLDER, fname,
                               os.path.join(file_dir, fname))
        except S3Error as err:
            print(err)

        USER_PIPELINE_LIST = []
        function_bucket = {}
        stage_list = api_response['status']['create_fn']['api_list']
        for i in stage_list:
            if 'user' in stage_list[i]['rule']:
                for j in stage_list[i]['step']:
                    USER_PIPELINE_LIST.append(j)
                    function_bucket.update({j:j})
        function_bucket.update({model_bucket:model_bucket})
        file_uuid = str(uuid.uuid4())
        bucket_name = UPLOAD_FOLDER

        for i in USER_PIPELINE_LIST:
            data = {'fname':fname, 'file_uuid':file_uuid, 'pipeline':pipeline, 'model':model_name, 'function_name':i, 'function_bucket':function_bucket, 'user':'user'}
            print(data)
            r = requests.post(f"""http://10.20.1.54:31112/function/{i}""", json=data)
            if r.status_code == 200:
                res = requests.post(f"""http://admin:admin@10.20.1.54:31112/system/scale-function/{i}""", json={"replicas": 0})
                continue
            else:
                return jsonify({'Function':i, 'status_code':r.status_code, 'text':r.text})
        
        if r.status_code == 200:
            uuid_renamed = i + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
            url = client.presigned_get_object('lstm-pipeline-model-serving-fun', uuid_renamed)
            
            return jsonify({'url':url})
        else:
            return 'no url'

# Dev upload, get complete data download url, output:{"status_code": int, "url": str}
@app.route("/dev/upload/<string:pipeline>", methods=['POST'], strict_slashes=False)
def dev_upload_file(pipeline):

    file_dir = os.path.join(basedir, app.config['DEV_UPLOAD_FOLDER'])
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure=False
    )

    kubernetes.config.load_kube_config()
    api_instance = kubernetes.client.CustomObjectsApi()
    api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name=pipeline, namespace='ml-faas')

    f = request.files['file']
    if f:
        fname = f.filename
        f.save(os.path.join(file_dir, fname))

        found = client.bucket_exists(DEV_UPLOAD_FOLDER)
        if not found:
            client.make_bucket(DEV_UPLOAD_FOLDER)

        try:
            client.fput_object(DEV_UPLOAD_FOLDER, fname,
                               os.path.join(file_dir, fname))
        except S3Error as err:
            print(err)

        DEV_PIPELINE_LIST = []
        function_bucket = {}
        stage_list = api_response['status']['create_fn']['api_list']
        for i in stage_list:
            if 'dev' in stage_list[i]['rule']:
                for j in stage_list[i]['step']:
                    DEV_PIPELINE_LIST.append(j)
                    function_bucket.update({j:j})

        file_uuid = str(uuid.uuid4())
        bucket_name = DEV_UPLOAD_FOLDER

        credentials = pika.PlainCredentials('user', 'user')
        connection = pika.BlockingConnection(pika.ConnectionParameters('10.20.1.54', '30672', '/', credentials))
        channel = connection.channel()
        
        for i in DEV_PIPELINE_LIST:
            data = {'fname':fname, 'file_uuid':file_uuid, 'pipeline':pipeline, 'function_name':i, 'function_bucket':function_bucket, 'user':'dev'}
            channel.queue_declare(queue=f"""{i} is being used""")
            channel.basic_publish(exchange='', routing_key=f"""{i} is being used""", body='start')
            r = requests.post(f"""http://10.20.1.54:31112/function/{i}""", json=data)

            if r.status_code == 200:
                channel.queue_declare(queue=f"""{i} is finsihed""")
                channel.basic_publish(exchange='', routing_key=f"""{i} is finsihed""", body='finished')
                using_list = []
                finish_list = []
                while True:
                    method_frame_used, header_frame_used, body_used = channel.basic_get(f"""{i} is being used""")
                    method_frame_fin, header_frame_fin, body_fin = channel.basic_get(f"""{i} is finsihed""")
                    if method_frame_used and method_frame_fin:
                        using_list.append(body_used.decode("utf-8"))
                        finish_list.append(body_fin.decode("utf-8"))
                    else:
                        break

                time.sleep(1)

                if len(using_list) == len(finish_list):
                    print('=====================================================================')
                    res = requests.post(f"""http://admin:admin@10.20.1.54:31112/system/scale-function/{i}""", json={"replicas": 0})
                    channel.queue_delete(queue=f"""{i} is being used""")
                    channel.queue_delete(queue=f"""{i} is finsihed""")
                    print({'Function':i, 'status_code':r.status_code, 'text':r.text})
                    continue
                else:
                    print({'Function':i, 'status_code':r.status_code, 'text':r.text})
                    continue
            else:
                print({'Function':i, 'status_code':r.status_code, 'text':r.text})
                return jsonify({'Function':i, 'status_code':r.status_code, 'text':r.text})

        if r.status_code == 200:
            uuid_renamed = i + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
            url = client.presigned_get_object(DEV_PIPELINE_LIST[-1], uuid_renamed)
            
            return jsonify({'url':url})
        else:
            return 'no url'
        

# Get pipeline list, output:{"mlpipline_list":[]}
@app.route("/api/list_ml_pipeline", strict_slashes=False)
def list_mlpipline():

    kubernetes.config.load_kube_config()
    api_instance = kubernetes.client.CustomObjectsApi()

    api_response = api_instance.list_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', namespace='ml-faas')

    mlpipline_list = []
    for i in api_response['items']:
        mlpipline_list.append(i['metadata']['name'])
    
    return jsonify({"mlpipline_list": mlpipline_list})

# Get model list, output:{'model_list':[]}
@app.route("/api/list_ml_pipeline_models/<string:pipeline>", strict_slashes=False)
def list_ml_pipeline_models(pipeline):

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure=False
    )
    
    kubernetes.config.load_kube_config()
    api_instance = kubernetes.client.CustomObjectsApi()
    api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name=pipeline, namespace='ml-faas')

    model_bucket = api_response['status']['create_fn']['api_list']['stage2']['step'][2]
    
    object_list = client.list_objects(model_bucket,recursive=True)

    model_list = []
    for i in object_list:
        model_list.append(i.object_name)

    return jsonify({'model_list':model_list})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30089, debug=True)
