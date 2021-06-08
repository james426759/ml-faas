import pandas as pd 
from minio import Minio
import json
from datetime import datetime, timedelta
from minio.error import S3Error
import os
import json

def handle(req):

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure = False
    )

    data = json.loads(req)
    fname = data['fname']
    file_uuid = data['file_uuid']
    last_pipeline_bucket_name = data['bucket_name']
    pipeline = data['pipeline']
    function_name = data['function_name']
    last_pipeline_file_name = data['bucket_name'] + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
    uuid_renamed = function_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
    # loaddata_renamed_file_path = '/home/app/'+uuid_renamed


    # try:
    client.fget_object(last_pipeline_bucket_name, last_pipeline_file_name, '/home/app/test.csv')
    # except S3Error as err:
    #     print(err)

    data = pd.read_csv("/home/app/test.csv").copy()
    
    local_time = data['LocalTime'].copy()
    time = []           
    for i in range(local_time.shape[0]):
        time_split = local_time.iloc[i].split(' ')
        date_split = time_split[0].split('/')
        year = '20'+date_split[2]
        month = date_split[0]
        day = date_split[1]
        today = year+'-'+month+'-'+day+' '+time_split[1]
        time.append(datetime.strptime(today, '%Y-%m-%d %H:%M:%S'))
    data['LocalTime'] = pd.Series(time)
    data = data.set_index('LocalTime')
    data.to_csv("/home/app/parser-test.csv")

    found = client.bucket_exists(os.environ['bucket_name'])
    if not found:
        client.make_bucket(os.environ['bucket_name'])
    # else:
    #     print(f"""Bucket {os.environ['bucket_name']} already exists""")

    # try:
    client.fput_object(os.environ['bucket_name'], uuid_renamed, '/home/app/parser-test.csv')
    # except S3Error as exc:
    #     print("error occurred.", exc)

    return os.environ['bucket_name']
