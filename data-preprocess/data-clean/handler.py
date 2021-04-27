from minio import Minio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
def handle(req):

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure = False
    )

    try:
        client.fget_object('time-parse', 'time-parse.csv', '/home/app/time-parse.csv')
    except ResponseError as err:
        print(err)

    data = pd.read_csv("/home/app/time-parse.csv").copy()

    # normalization
    data = data.round(2)

    # condition list 存下來
    data, condition = anomalyDetection(data=data)

    data.to_csv("/home/app/data-clean.csv")

    if not found:
        client.make_bucket("data-clean")
    else:
        print("Bucket 'data-clean' already exists")

    try:
        client.fput_object('data-clean', 'data-clean.csv', '/home/app/data-clean.csv')
    except ResponseError as err:
        print(err)

    return 1


def anomalyDetection(method = 'chebyshev', value_maximun = 40, value_minimun = 0, data):

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
                