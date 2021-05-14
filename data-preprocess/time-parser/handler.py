import pandas as pd 
from minio import Minio
import json
from datetime import datetime, timedelta
from minio.error import S3Error
def handle(req):

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure = False
    )

    try:
        client.fget_object('test01', 'test.csv', '/home/app/test.csv')
    except ResponseError as err:
        print(err)

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

    found = client.bucket_exists("time-parser")
    if not found:
        client.make_bucket("time-parse")
    else:
        print("Bucket 'time-parse' already exists")

    try:
        client.fput_object('time-parse', 'time-parse.csv', '/home/app/parser-test.csv')
    except S3Error as exc:
        print("error occurred.", exc)

    return 1
