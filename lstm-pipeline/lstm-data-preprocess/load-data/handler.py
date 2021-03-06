import json
from minio import Minio
import os

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure = False
    )

    found = client.bucket_exists(os.environ['bucket_name'])
    if not found:
        client.make_bucket(os.environ['bucket_name'])
    
    # 讀取所需資料req {'fname':[], 'file_uuid':[], 'pipeline':[], 'model':[](only for user upload), 'function_name':[], 'function_bucket':[], 'user':[]}
    data = json.loads(req)
    fname = data['fname']
    file_uuid = data['file_uuid']
    pipeline = data['pipeline']
    function_name = data['function_name']

    # 使用uuid更改檔案名
    uuid_renamed_file_csv = function_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]

    if data['user'] == 'dev':
        user_upload_file_bucket = 'dev-upload-file'
    elif data['user'] == 'user':
        user_upload_file_bucket = 'user-uploaded-file'
        
    client.fget_object(user_upload_file_bucket, fname, f"""/home/app/{fname}""")
    client.fput_object(os.environ['bucket_name'], uuid_renamed_file_csv, f"""/home/app/{fname}""")
    
    return os.environ['bucket_name']