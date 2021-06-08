import pandas as pd 
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
    
    data = json.loads(req)
    fname = data['fname']
    file_uuid = data['file_uuid']
    last_pipeline_bucket_name = data['bucket_name']
    pipeline = data['pipeline']
    function_name = data['function_name']
    uuid_renamed = function_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]

    # loaddata_renamed_file_path = '/home/app/'+uuid_renamed
    client.fget_object(last_pipeline_bucket_name, fname, '/home/app/test.csv')

    client.fput_object(os.environ['bucket_name'], uuid_renamed, '/home/app/test.csv')
    
    return os.environ['bucket_name']