from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_cors import CORS
from minio import Minio
from minio.error import S3Error
import os
import requests
import kubernetes
import yaml
from pprint import pprint

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'user-uploaded-file'
DEV_UPLOAD_FOLDER = 'dev-upload-file'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEV_UPLOAD_FOLDER'] = DEV_UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])

# User上傳資料
@app.route('/user/upload', methods=['POST'], strict_slashes=False)
def api_upload():

    file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure=False
    )

    f = request.files['file']
    if f:
        fname = f.filename
        f.save(os.path.join(file_dir, fname))

        try:
            client.fput_object('user-upload-file', fname,
                               os.path.join(file_dir, fname))
        except S3Error as err:
            print(err)

        r = requests.post(
            'http://10.20.1.54:31112/function/model-serving', data=fname)

        if r == 200:
            url = client.presigned_get_object("complete-data", "complete-data.csv")
        else:
            return jsonify({"errno": r, "errmsg": "產生下載url失敗!"})

        return jsonify({"errno": 0, "errmsg": "上傳成功"})
    else:
        return jsonify({"errno": 1001, "errmsg": "上傳失败"})

# Dev上傳資料
@app.route("/dev/upload", methods=['POST'], strict_slashes=False)
def dev_upload_file():

    # file_dir = os.path.join(basedir, app.config['DEV_UPLOAD_FOLDER'])
    file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure=False
    )

    f = request.files['file']

    if f:
        fname = f.filename
        f.save(os.path.join(file_dir, fname))

        try:
            client.fput_object('user-upload-file', fname,
                               os.path.join(file_dir, fname))
        except S3Error as err:
            print(err)

    # if f:
    #     fname = f.filename
    #     f.save(os.path.join(file_dir, fname))

    #     try:
    #         client.fput_object('dev-upload-file', fname,
    #                            os.path.join(file_dir, fname))
    #     except S3Error as err:
    #         print(err)

        kubernetes.config.load_kube_config()
        api_instance = kubernetes.client.CustomObjectsApi()
        api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name='lstm-pipeline', namespace='ml-faas')

        data = api_response['status']['create_fn']['api_list']
        for i in data:

            if i == 'lstm-pipeline-model-serving-fun':
                r = requests.post(f"""http://10.20.1.54:31112/function/{i}""", data=fname)
            else:
                r = requests.get(f"""http://10.20.1.54:31112/function/{i}""")
            if r.status_code == 200:
                continue
            else:
                return (f"""Function {i} status code: {r.status_code}""")
                
    url = client.presigned_get_object("complete-data", "complete-data.csv")
    
    return jsonify({"status_code": r.status_code, "url": url})

@app.route("/api/list_ml_pipeline", strict_slashes=False)
def list_mlpipline():

    kubernetes.config.load_kube_config()
    api_instance = kubernetes.client.CustomObjectsApi()

    api_response = api_instance.list_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', namespace='ml-faas')

    mlpipline_list = []
    for i in api_response['items']:
        mlpipline_list.append(i['metadata']['name'])
    
    return jsonify({"mlpipline_list": mlpipline_list})
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30089, debug=True)
