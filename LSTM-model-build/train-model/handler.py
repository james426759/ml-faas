import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, LSTM, TimeDistributed, RepeatVector
from keras.layers.normalization import BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
import tensorflow as tf
from minio import Minio
from minio.error import S3Error
import json
import os

def handle(req):

    client = Minio(
        "10.20.1.54:30020",
        access_key="admin",
        secret_key="secretsecret",
        secure = False
    )

    try:
        client.fget_object('train-model-setup', 'model_setup.h5', '/home/app/model_setup.h5')
        client.fget_object('train-dataset', 'xt.json', '/home/app/xt.json')
        client.fget_object('train-dataset', 'yt.json', '/home/app/yt.json')
    except ResponseError as err:
        print(err)

    x_dict = ""
    with open('/home/app/xt.json', 'r') as obj:
        x_dict = json.load(obj)

    y_dict = ""
    with open('/home/app/yt.json', 'r') as obj:
        y_dict = json.load(obj)

    # print(x_dict)
    # print(y_dict)

    x_train = []
    y_train = []

    for i in x_dict:
        x_train.append([])
        for j in x_dict[i]:
            x_train[int(i)].append([x_dict[i][j]])

    for i in y_dict:
        y_train.append([y_dict[i]])

    x_train = np.array(x_train)
    y_train = np.array(y_train)
    x_train = x_train.astype(np.float32)
    y_train = y_train.astype(np.float32)

    # 拉modle參數檔, x_train, y_train 下來
    model = modelLoad(model_name='/home/app/model_setup.h5')
    model = train(model, x_train, y_train)
    modelSave(model, model_name='/home/app/model_LSTM.h5')
    
    found = client.bucket_exists(os.environ['bucket_name'])
    if not found:
        client.make_bucket(os.environ['bucket_name'])
    else:
        print(f"""Bucket {os.environ['bucket_name']} already exists""")

    try:
        client.fput_object(os.environ['bucket_name'], 'model-lstm.h5', '/home/app/model_LSTM.h5')
    except S3Error as exc:
        print("error occurred.", exc)

    return 1

def train(model, x_train, y_train):
    callback = EarlyStopping(monitor="loss", patience=10, verbose=1, mode="auto")
    model.fit(x_train, y_train, epochs=3, batch_size=128, callbacks=[callback])
    return model


def modelSave(model, model_name):
    model.save(model_name)

def modelLoad(model_name='/home/app/model_setup.h5'):
    model = tf.keras.models.load_model(model_name, compile = True)
    model.summary()
    return model
