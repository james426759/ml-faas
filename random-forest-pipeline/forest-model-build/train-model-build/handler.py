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
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import joblib

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
    train_data_build_func_bucket_name = function_bucket_list['random-forest-pipeline-train-data-build']

    train_data_build_file_name = train_data_build_func_bucket_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + fname.split('.')[1]
    uuid_renamed_json = train_data_build_func_bucket_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + 'json'
    uuid_renamed_h5 = function_name + '-' + fname.split('.')[0] + '-' + file_uuid + '.' + 'joblib'

    
    client.fget_object(train_data_build_func_bucket_name, 'xt-'+uuid_renamed_json, '/home/app/xt.json')
    client.fget_object(train_data_build_func_bucket_name, 'yt-'+uuid_renamed_json, '/home/app/yt.json')


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
            x_train[int(i)].append(x_dict[i][j])

    for i in y_dict:
        y_train.append(y_dict[i])

    x_train = np.array(x_train)
    y_train = np.array(y_train)

    # print(x_train)
    # print(y_train)

    buildModel(x_train, y_train)
    
    # x_dict = dict()
    # y_dict = dict()
    # for i in range(len(x_train)):
    #     x_dict[str(i)] = dict()
    #     for j in range(len(x_train[i])):
    #         x_dict[str(i)][str(j)] = x_train[i][j][0]

    # for i in range(len(y_train)):
    #     y_dict[str(i)] = y_train[i][0]

    # with open('/home/app/x_train_data.json', 'w', encoding='utf-8') as f:
    #     json.dump(x_dict, f)

    # with open('/home/app/y_train_data.json', 'w', encoding='utf-8') as f:
    #     json.dump(y_dict, f)

    found = client.bucket_exists(os.environ['bucket_name'])
    if not found:
        client.make_bucket(os.environ['bucket_name'])


        # client.fput_object('train-model-setup', 'x_train_data.json', '/home/app/x_train_data.json')
        # client.fput_object('train-model-setup', 'y_train_data.json', '/home/app/y_train_data.json')
    client.fput_object(os.environ['bucket_name'], uuid_renamed_h5, '/home/app/forest_model.joblib')

    return os.environ['bucket_name']

def buildModel(x_train, y_train):
    forest = RandomForestRegressor()
    joblib.dump(forest, "/home/app/forest_model.joblib")

    # model = Sequential()
    # print(x_train.shape)
    # model.add(LSTM(10, input_length=x_train.shape[1], input_dim=1))
    # model.add(Dense(1))
    # model.compile(loss="mse", optimizer="adam")
    # model.summary()
    # # callback = EarlyStopping(monitor="loss", patience=10, verbose=1, mode="auto")
    # # x_train = x_train.astype(np.float32)
    # # y_train = y_train.astype(np.float32)

    # model.save("/home/app/model_setup.h5")
    # # self.model.fit(self.x_train, self.y_train, epochs=3000, batch_size=128, callbacks=[callback])