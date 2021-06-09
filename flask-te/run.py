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

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'user-uploaded-file'
DEV_UPLOAD_FOLDER = 'dev-upload-file'
DEV_PIPELINE_LIST = ['lstm-pipeline-time-parser', 'lstm-pipeline-data-clean', 'lstm-pipeline-train-data-build', 
    'lstm-pipeline-train-model-build', 'lstm-pipeline-train-model', 'lstm-pipeline-model-serving-fun']
USER_PIPELINE_LIST = ['lstm-pipeline-time-parser', 'lstm-pipeline-data-clean', 'lstm-pipeline-model-serving-fun']

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEV_UPLOAD_FOLDER'] = DEV_UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])

# User upload, get complete data download url, output:{"status_code": int, "url": str}
@app.route('/user/upload/<string:pipeline>/<string:model_name>', methods=['POST'], strict_slashes=False)
def api_upload(pipeline,model_name):

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

    ################################################################################
    # 利用kubernetes api抓取所需之function name (尚未完成)
    # kubernetes.config.load_kube_config()
    # api_instance = kubernetes.client.CustomObjectsApi()
    # api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name=pipeline, namespace='ml-faas')
    ################################################################################

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
            
            ### load-data function (create load-function bucket)
            ###################################################
            # file_uuid = str(uuid.uuid4())

            # uuid_renamed = fname.split('.')[0]+'-'+file_uuid+'.'+fname.split('.')[1]
            # loaddata_renamed_file_path = '/home/app/'+uuid_renamed
            # client.fget_object('user-upload-file', fname, loaddata_renamed_file_path)

            # found = client.bucket_exists('lstm-pipeline-load-data')
            # if not found:
            #     client.make_bucket('lstm-pipeline-load-data')
            # else:
            #     print("Bucket lstm-pipeline-load-data already exists")
            # client.fput_object('lstm-pipeline-load-data', uuid_renamed, loaddata_renamed_file_path)
            ###################################################

        except S3Error as err:
            print(err)

        USER_PIPELINE_LIST = []
        stage_list = api_response['status']['create_fn']['api_list']
        for i in stage_list:
            if 'user' in stage_list[i]['rule']:
                for j in stage_list[i]['step']:
                    USER_PIPELINE_LIST.append(j)

        # for i in api_response['status']['create_fn']['api_list']['stage1']:
        #     USER_PIPELINE_LIST.append(i)
        # model serving 未改
        # for i in api_response['status']['create_fn']['api_list']['stage3']:
        #     USER_PIPELINE_LIST.append(i)

        file_uuid = str(uuid.uuid4())
        bucket_name = UPLOAD_FOLDER

        #### model serving未完成 ####
        for i in USER_PIPELINE_LIST[0:3]:
            data = {'fname':fname, 'file_uuid':file_uuid, 'bucket_name':bucket_name, 'pipeline':pipeline, 'function_name':i}
            print(data)
            r = requests.post(f"""http://10.20.1.54:31112/function/{i}""", json=data)
            bucket_name = r.text
            bucket_name = bucket_name.replace('\n', '').replace('\r', '')
            # print(r.json())
            if r.status_code == 200:
                res = requests.post(f"""http://admin:admin@10.20.1.54:31112/system/scale-function/{i}""", json={"replicas": 0})
                continue
            else:
                return jsonify({'Function':i,'status_code':r.status_code, 'text':r.text})
        
        return jsonify({"status_code": r.status_code})

        #### model serving未完成 ####
        # if r.status_code == 200:
        #     url = client.presigned_get_object("complete-data", "complete-data.csv")
        #     return jsonify({"status_code": r.status_code, "url": url})
        # else:
        #     return jsonify({"status_code": r.status_code, "errmsg": "產生下載url失敗!"})
    else:
        return jsonify({"errno": 111, "errmsg": "上傳"})

# Dev upload, get complete data download url, output:{"status_code": int, "url": str}
@app.route("/dev/upload/<string:pipeline>/<string:model_name>", methods=['POST'], strict_slashes=False)
def dev_upload_file(pipeline, model_name=''):

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
        stage_list = api_response['status']['create_fn']['api_list']
        for i in stage_list:
            if 'dev' in stage_list[i]['rule']:
                for j in stage_list[i]['step']:
                    DEV_PIPELINE_LIST.append(j)

        file_uuid = str(uuid.uuid4())
        bucket_name = DEV_UPLOAD_FOLDER

        # DEV_PIPELINE_LIST = ['lstm-pipeline-load-data', 'lstm-pipeline-time-parser', 'lstm-pipeline-data-clean']
        for i in DEV_PIPELINE_LIST:
            data = {'fname':fname, 'file_uuid':file_uuid, 'bucket_name':bucket_name, 'pipeline':pipeline, 'function_name':i}
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

        if r.status_code == 200:
            uuid_renamed = i + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
            url = client.presigned_get_object('lstm-pipeline-model-serving-fun', uuid_renamed)
            
            return json.dumps({'url':url})
        else:
            return 'no url'
        # if r.status_code == 200:
        #     uuid_renamed = function_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
        #     url = client.presigned_get_object(bucket_name, uuid_renamed)
        #     return jsonify({"status_code": r.status_code, "url": url})
        # else:
        #     return jsonify({"status_code": r.status_code, "errmsg": "產生下載url失敗!"})

        # return jsonify({'status_code':r.status_code, 'text':r.text})
    # return jsonify({'Function':i,'status_code':r.status_code, 'text':r.text})

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

    model_bucket = pipeline + '-' + api_response['status']['create_fn']['api_list']['stage2'][2]
    
    object_list = client.list_objects(model_bucket,recursive=True)

    model_list = []
    for i in object_list:
        model_list.append(i.object_name)

    return jsonify({'model_list':model_list})

@app.route("/test/", methods=['POST'], strict_slashes=False)
def test():

    # client = Minio(
    #     "10.20.1.54:30020",
    #     access_key="admin",
    #     secret_key="secretsecret",
    #     secure=False
    # )
    
    # kubernetes.config.load_kube_config()
    # api_instance = kubernetes.client.CustomObjectsApi()
    # api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name=pipeline, namespace='ml-faas')
    function_name = 'lstm-pipeline-train-model-build'
    data = {'fname': 'test.csv', 'file_uuid': '61acf91a-e5a6-41bd-a2cc-8582dd0cd942', 'bucket_name': 'lstm-pipeline-train-data-build', 'pipeline': 'lstm-pipeline', 'function_name': 'lstm-pipeline-train-model-build'}
    r = requests.post(f"""http://10.20.1.54:31112/function/{function_name}""", json=data)

    return jsonify({'Function':function_name,'status_code':r.status_code, 'text':r.text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30089, debug=True)
