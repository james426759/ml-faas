import pandas as pd 
from minio import Minio
import json
from datetime import datetime, timedelta
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
    x_train, y_train = buildTrain(data=data)

    # 要儲存x_train, y_train
    x_train, y_train = shuffle(x_train=x_train, y_train=y_train)

    return 1

def buildTrain(past_day=24, futureDay=1, data):
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

def shuffle(seed=10, x_train, y_train):
    np.random.seed(seed)
    randomList = np.arange(x_train.shape[0])
    np.random.shuffle(randomList)
    x_train = x_train[randomList]
    y_train = y_train[randomList]
    return x_train, y_train
