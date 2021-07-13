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
    pipeline = data['pipeline']
    function_name = data['function_name']

    function_bucket_list = data['function_bucket']
    load_data_func_bucket_name = function_bucket_list[f'''{data['pipeline']}-load-data''']

    load_data_func_file_name = load_data_func_bucket_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
    uuid_renamed_file_csv = function_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]

    client.fget_object(load_data_func_bucket_name, load_data_func_file_name, f"""/home/app/{load_data_func_file_name}""")

    data = pd.read_csv(f"""/home/app/{load_data_func_file_name}""").copy()
    
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
    data.to_csv(f"""/home/app/{uuid_renamed_file_csv}""")

    found = client.bucket_exists(os.environ['bucket_name'])
    if not found:
        client.make_bucket(os.environ['bucket_name'])

    client.fput_object(os.environ['bucket_name'], uuid_renamed_file_csv, f"""/home/app/{uuid_renamed_file_csv}""")

    return os.environ['bucket_name']
