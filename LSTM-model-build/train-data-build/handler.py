import pandas as pd
import numpy as np
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
        client.fget_object('data-clean', 'data-clean.csv', '/home/app/data-clean.csv')
    except ResponseError as err:
        print(err)

    data = pd.read_csv("/home/app/data-clean.csv").copy()

    # 每個都要加
    for i in range(data.shape[0]):
        data["LocalTime"][i] = datetime.strptime(data["LocalTime"][i], '%Y-%m-%d %H:%M:%S')
    data = data.set_index('LocalTime') 
    # 

    x_train, y_train = buildTrain(data=data)

    x_train, y_train = shuffle(x_train=x_train, y_train=y_train)

    x_dict = dict()
    y_dict = dict()
    for i in range(len(x_train)):
        x_dict[str(i)] = dict()
        for j in range(len(x_train[i])):
            x_dict[str(i)][str(j)] = x_train[i][j][0]

    for i in range(len(y_train)):
        y_dict[str(i)] = y_train[i][0]

    with open('/home/app/xt.json', 'w', encoding='utf-8') as f:
        json.dump(x_dict, f)

    with open('/home/app/yt.json', 'w', encoding='utf-8') as f:
        json.dump(y_dict, f)

    found = client.bucket_exists("train-dataset")
    if not found:
        client.make_bucket("train-dataset")
    else:
        print("Bucket 'train-dataset' already exists")

    try:
        client.fput_object('train-dataset', 'xt.json', '/home/app/xt.json')
        client.fput_object('train-dataset', 'yt.json', '/home/app/yt.json')
    except S3Error as exc:
        print("error occurred.", exc)

    return 1

def buildTrain(data, past_day=24, futureDay=1):
        #全域變數   
        target_field = 'Temp'
        direction = True

        x_train = []
        y_train = []
        if direction:
            for i in range(past_day+futureDay, data.shape[0]):
                if data[target_field][i-past_day-futureDay:i].count() < past_day+futureDay:
                    pass
                else:
                    x = np.array(data[target_field].iloc[i-past_day-futureDay:i-futureDay])
                    x = x.reshape(x.shape[0], 1)
                    x_train.append(x)
                    y_train.append(np.array(data.iloc[i-futureDay:i][target_field]))
        else:
            for i in range((past_day+futureDay)*288, data.shape[0]):
                if data[target_field][i-(past_day*288)-(futureDay*288):i:288].count() < past_day+futureDay:
                    pass
                else:
                    x = np.array(data[target_field].iloc[i-(past_day*288)-(futureDay*288):i-(futureDay*288):288])
                    x = x.reshape(x.shape[0], 1)
                    x_train.append(x)
                    y_train.append(np.array(data.iloc[i-(futureDay*288):i][target_field]))
        x_train = np.array(x_train)
        y_train = np.array(y_train)
        return x_train, y_train

def shuffle(x_train, y_train, seed=10):
    np.random.seed(seed)
    randomList = np.arange(x_train.shape[0])
    np.random.shuffle(randomList)
    x_train = x_train[randomList]
    y_train = y_train[randomList]
    return x_train, y_train
