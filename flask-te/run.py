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
import datetime


app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'user-uploaded-file'
DEV_UPLOAD_FOLDER = 'dev-upload-file'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEV_UPLOAD_FOLDER'] = DEV_UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])

@app.route('/user/upload/<string:pipeline>/<string:model_bucket>', methods=['POST'], strict_slashes=False)
def api_upload2(pipeline,model_bucket,model_name=''):
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
    file_uuid = str(uuid.uuid4())

    f = request.files['file']
    if f:
        fname = f"""{file_uuid}-{f.filename}"""
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
        bucket_name = UPLOAD_FOLDER
        if model_name == '':
            object_list = client.list_objects(f"""{pipeline}-train-model""",recursive=True)
            time_list = []
            for i in object_list:
                result = client.stat_object(f"""{pipeline}-train-model""", i.object_name)
                time_list.append(result.last_modified)
                if max(time_list) == result.last_modified:
                    model_name = i.object_name
                else:
                    continue

        credentials = pika.PlainCredentials('user', 'user')
        connection = pika.BlockingConnection(pika.ConnectionParameters('10.20.1.54', '30672', '/', credentials, heartbeat=0))
        channel = connection.channel()

        for i in USER_PIPELINE_LIST:
            data = {'fname':fname, 'file_uuid':file_uuid, 'pipeline':pipeline, 'model':model_name, 'function_name':i, 'function_bucket':function_bucket, 'user':'user'}
            channel.queue_declare(queue=i)
            channel.basic_publish(exchange='', routing_key=i, body='1')
            print(datetime.datetime.now())
            r = requests.post(f"""http://10.20.1.54:31112/function/{i}""", json=data)

            if r.status_code == 200:
                print(datetime.datetime.now())
                method_frame, header_frame, body = channel.basic_get(queue=i, auto_ack=True)
                if method_frame.message_count == 0:
                    print('=====================================================================')
                    res = requests.post(f"""http://admin:admin@10.20.1.54:31112/system/scale-function/{i}""", json={"replicas": 0})
                    print({'Function':i, 'status_code':r.status_code, 'text':r.text})
            else:
                return jsonify({'Function':i, 'status_code':r.status_code, 'text':r.text, 'fail':'fail'})
        
        if r.status_code == 200:
            # uuid_renamed = i + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
            # url = client.presigned_get_object(f"""{pipeline}-model-serving-fun""", uuid_renamed)
            # return jsonify({'url':url})
            return 'success'
        else:
            return 'no url'

# User upload, get complete data download url, output:{"status_code": int, "url": str}
@app.route('/user/upload/<string:pipeline>/<string:model_bucket>/<string:model_name>', methods=['POST'], strict_slashes=False)
def api_upload(pipeline,model_bucket,model_name):
    return api_upload2(pipeline,model_bucket,model_name)

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
    file_uuid = str(uuid.uuid4())
    if f:
        fname = f"""{file_uuid}-{f.filename}"""
        # fname = f.filename
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

        # file_uuid = str(uuid.uuid4())
        bucket_name = DEV_UPLOAD_FOLDER

        credentials = pika.PlainCredentials('user', 'user')
        connection = pika.BlockingConnection(pika.ConnectionParameters('10.20.1.54', '30672', '/', credentials, heartbeat=0))
        channel = connection.channel()
        
        for i in DEV_PIPELINE_LIST[0:6]:
            data = {'fname':fname, 'file_uuid':file_uuid, 'pipeline':pipeline, 'function_name':i, 'function_bucket':function_bucket, 'user':'dev'}
            channel.queue_declare(queue=i)
            channel.basic_publish(exchange='', routing_key=i, body='1')
            print(datetime.datetime.now())
            while True:
                r = requests.post(f"""http://10.20.1.54:31112/function/{i}""", json=data)

                if r.status_code == 200:
                    print(datetime.datetime.now())
                    method_frame, header_frame, body = channel.basic_get(queue=i, auto_ack=True)
                    if method_frame.message_count == 0:
                        print('=====================================================================')
                        res = requests.post(f"""http://admin:admin@10.20.1.54:31112/system/scale-function/{i}""", json={"replicas": 0})
                        print({'Function':i, 'status_code':r.status_code, 'text':r.text})
                        break
                # else:
                #     return jsonify({'Function':i, 'status_code':r.status_code, 'text':r.text, 'fail':'fail'})
                elif r.status_code == 503:
                    # return jsonify({'Function':i, 'status_code':r.status_code, 'text':r.text, 'fail':'fail'})
                    print(f"""fuck-pending-{i}-{datetime.datetime.now()}""")
                    continue

        if r.status_code == 200:
            # uuid_renamed = i + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
            # url = client.presigned_get_object(DEV_PIPELINE_LIST[-1], uuid_renamed)
            # return jsonify({'url':url})
            return 'success'
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

# # Dev upload, get complete data download url, output:{"status_code": int, "url": str}
# @app.route("/dev/upload/<string:pipeline>", methods=['POST'], strict_slashes=False)
# def dev_upload_file(pipeline):

#     file_dir = os.path.join(basedir, app.config['DEV_UPLOAD_FOLDER'])
#     if not os.path.exists(file_dir):
#         os.makedirs(file_dir)

#     client = Minio(
#         "10.20.1.54:30020",
#         access_key="admin",
#         secret_key="secretsecret",
#         secure=False
#     )

#     kubernetes.config.load_kube_config()
#     api_instance = kubernetes.client.CustomObjectsApi()
#     api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name=pipeline, namespace='ml-faas')

#     f = request.files['file']
#     if f:
#         fname = f.filename
#         f.save(os.path.join(file_dir, fname))

#         found = client.bucket_exists(DEV_UPLOAD_FOLDER)
#         if not found:
#             client.make_bucket(DEV_UPLOAD_FOLDER)

#         try:
#             client.fput_object(DEV_UPLOAD_FOLDER, fname,
#                                os.path.join(file_dir, fname))
#         except S3Error as err:
#             print(err)

#         DEV_PIPELINE_LIST = []
#         function_bucket = {}
#         stage_list = api_response['status']['create_fn']['api_list']
#         for i in stage_list:
#             if 'dev' in stage_list[i]['rule']:
#                 for j in stage_list[i]['step']:
#                     DEV_PIPELINE_LIST.append(j)
#                     function_bucket.update({j:j})

#         file_uuid = str(uuid.uuid4())
#         bucket_name = DEV_UPLOAD_FOLDER

#         credentials = pika.PlainCredentials('user', 'user')
#         connection = pika.BlockingConnection(pika.ConnectionParameters('10.20.1.54', '30672', '/', credentials))
#         channel = connection.channel()
        
#         for i in DEV_PIPELINE_LIST:
#             data = {'fname':fname, 'file_uuid':file_uuid, 'pipeline':pipeline, 'function_name':i, 'function_bucket':function_bucket, 'user':'dev'}
#             channel.queue_declare(queue=f"""{i} is being used""")
#             channel.basic_publish(exchange='', routing_key=f"""{i} is being used""", body='start')
#             r = requests.post(f"""http://10.20.1.54:31112/function/{i}""", json=data)

#             if r.status_code == 200:
#                 channel.queue_declare(queue=f"""{i} is finsihed""")
#                 channel.basic_publish(exchange='', routing_key=f"""{i} is finsihed""", body='finished')
#                 using_list = []
#                 finish_list = []
#                 while True:
#                     method_frame_used, header_frame_used, body_used = channel.basic_get(f"""{i} is being used""")
#                     method_frame_fin, header_frame_fin, body_fin = channel.basic_get(f"""{i} is finsihed""")
#                     if method_frame_used and method_frame_fin:
#                         using_list.append(body_used.decode("utf-8"))
#                         finish_list.append(body_fin.decode("utf-8"))
#                     else:
#                         break

#                 time.sleep(1)

#                 if len(using_list) == len(finish_list):
#                     print('=====================================================================')
#                     res = requests.post(f"""http://admin:admin@10.20.1.54:31112/system/scale-function/{i}""", json={"replicas": 0})
#                     channel.queue_delete(queue=f"""{i} is being used""")
#                     channel.queue_delete(queue=f"""{i} is finsihed""")
#                     print({'Function':i, 'status_code':r.status_code, 'text':r.text})
#                     continue
#                 else:
#                     print({'Function':i, 'status_code':r.status_code, 'text':r.text})
#                     continue
#             else:
#                 print({'Function':i, 'status_code':r.status_code, 'text':r.text})
#                 return jsonify({'Function':i, 'status_code':r.status_code, 'text':r.text})

#         if r.status_code == 200:
#             uuid_renamed = i + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
#             url = client.presigned_get_object(DEV_PIPELINE_LIST[-1], uuid_renamed)
            
#             return jsonify({'url':url})
#         else:
#             return 'no url'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30089, debug=True)
