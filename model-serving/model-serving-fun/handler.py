from minio import Minio
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from minio.error import S3Error
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, LSTM, TimeDistributed, RepeatVector
from keras.layers.normalization import BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
import tensorflow as tf

def handle(req):
    target_field = 'Temp'
    direction = True
    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure = False
    )

    basic_basth = '/home/app'
    file_name = req 
    file_path = os.path.join(basic_basth, req)

    try:
        client.fget_object('model-lstm', 'model-lstm.h5', '/home/app/model-lstm.h5')
        client.fget_object('user-upload-file', req, file_path)
    except ResponseError as err:
        print(err)

    data = pd.read_csv(file_path)
    model = modelLoad(model_name='/home/app/model-lstm.h5')
    data = newField(data, target_field=target_field)
    data_ok = correction(data=data, past_day=24, direction=direction, model=model, target_field=target_field)
    data_ok.to_csv('/home/app/complete-data2.csv')
    
    found = client.bucket_exists("complete-data")
    if not found:
        client.make_bucket("complete-data")
    else:
        print("Bucket 'complete-data' already exists")

    try:
        client.fput_object('complete-data', 'complete-data.csv', '/home/app/complete-data2.csv')
    except S3Error as exc:
        print("error occurred.", exc)

    return 1

def modelLoad(model_name):
    model = tf.keras.models.load_model(model_name, compile = False)
    model.summary()
    return model

def correction(data, past_day, direction, model, target_field):
    if direction:
        for times in range(int(past_day/2)):
            mask = list(np.isnan(data[target_field]))
            for i in range(past_day+1, len(mask)):
                if mask[i]:
                    if mask[i-past_day:i].count(True) > 0:
                        pass
                    else:
                        test = []
                        x = np.array(data[target_field].iloc[i-past_day:i])
                        x = x.reshape(x.shape[0], 1)
                        test.append(x)
                        test = np.array(test)
                        y_hat = model.predict(test)
                        data[target_field][data.index[i]] = y_hat[0]
                        data[target_field + '_m'][data.index[i]] = 'V'
    else:
        mask = data[target_field] == True
        for i in range((past_day+1)*288, data.shape[0]):
            if np.isnan(data[target_field][data.index[i]]):
                if data[target_field][i-(past_day*288):i:288].count() < past_day:
                    pass
                elif mask[i-(past_day*288):i:288].count(True) > int(past_day/2):
                    pass
                else:
                    test = []
                    x = np.array(data[target_field].iloc[i-past_day*288:i:288])
                    x = x.reshape(x.shape[0], 1)
                    test.append(x)
                    test = np.array(test)
                    y_hat = model.predict(test)
                    data[target_field][data.index[i]] = y_hat[0]
                    data[target_field + '_m'][data.index[i]] = 'H'
    return data

def newField(data, target_field):
    data[target_field + '_m'] = [np.nan] * data.shape[0]
    return data
