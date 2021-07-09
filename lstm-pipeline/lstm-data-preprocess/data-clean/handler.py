from minio import Minio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from minio.error import S3Error
import os
import json
import warnings
from pandas.core.common import SettingWithCopyWarning

def handle(req):

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure = False
    )
    warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

    data = json.loads(req)
    fname = data['fname']
    file_uuid = data['file_uuid']
    pipeline = data['pipeline']
    function_name = data['function_name']

    function_bucket_list = data['function_bucket']
    time_parser_func_bucket_name = function_bucket_list[f'''{data['pipeline']}-time-parser''']

    time_parser_func_file_name = time_parser_func_bucket_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
    uuid_renamed_file_csv = function_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]

    # try:
    client.fget_object(time_parser_func_bucket_name, time_parser_func_file_name, f"""/home/app/{time_parser_func_file_name}""")
    # except S3Error as err:
    #     print(err)

    data = pd.read_csv(f"""/home/app/{time_parser_func_file_name}""").copy()

    data = data.round(2)

    # 每個都要加
    for i in range(data.shape[0]):
        data["LocalTime"][i] = datetime.strptime(data["LocalTime"][i], '%Y-%m-%d %H:%M:%S')
    data = data.set_index('LocalTime') 
    # 

    data, condition = anomalyDetection(data)

    data.to_csv(f"""/home/app/{uuid_renamed_file_csv}""")

    found = client.bucket_exists(os.environ['bucket_name'])
    if not found:
        client.make_bucket(os.environ['bucket_name'])

    client.fput_object(os.environ['bucket_name'], uuid_renamed_file_csv, f"""/home/app/{uuid_renamed_file_csv}""")

    return os.environ['bucket_name']


def anomalyDetection(data, method = 'chebyshev', value_maximun = 40, value_minimun = 0):
    # 全域變數
    target_field = 'Temp'
    
    def timeParser(date, time, day = 0):
        _date = (date + timedelta(days = day)).strftime('%Y-%m-%d')
        return datetime.strptime(_date + ' ' + time, '%Y-%m-%d %H:%M:%S')

    data[target_field][data[target_field] > value_maximun] = np.nan
    data[target_field][data[target_field] < value_minimun] = np.nan
    if method == 'chebyshev':
        start_day = data.index[0]
        end_day = data.index[-1]
        days = 0
        run = True
        while run:
            if days == 0:
                start_time = start_day
                end_time = timeParser(start_time.date(), '23:55:00')
            elif timeParser(start_day.date(), '00:00:00', day = days).date() == end_day.date():
                start_time = timeParser(start_day.date(), '00:00:00', day = days)
                end_time = end_day    
                run = False
            else:
                start_time = timeParser(start_day.date(), '00:00:00', day = days)
                end_time = timeParser(start_day.date(), '23:55:00', day = days)                
            avg = data.loc[start_time:end_time][target_field].mean()
            std = data.loc[start_time:end_time][target_field].std()
            std *= 2
            data.loc[start_time:end_time][target_field][data[target_field] > (avg + std)] = np.nan
            data.loc[start_time:end_time][target_field][data[target_field] < (avg - std)] = np.nan
            std = data.loc[start_time:end_time][target_field].std()
            std *= 4
            data.loc[start_time:end_time][target_field][data[target_field] > (avg + std)] = np.nan
            data.loc[start_time:end_time][target_field][data[target_field] < (avg - std)] = np.nan
            condition = np.isnan(data[target_field])
            condition = list(condition)
            days += 1
    return data, condition
                