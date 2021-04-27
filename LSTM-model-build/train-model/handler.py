import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, LSTM, TimeDistributed, RepeatVector
from keras.layers.normalization import BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
import tensorflow as tf

def handle(req):
    拉modle參數檔, x_train, y_train 下來

    model = modelLoad(modle參數檔)
    model = train(model, x_train, y_train)
    modelSave(model, 訓練完路徑)
    訓練完路徑 = 儲存下來
    return req

def train(model, x_train, y_train):
    callback = EarlyStopping(monitor="loss", patience=10, verbose=1, mode="auto")
    model.fit(x_train, y_train, epochs=3000, batch_size=128, callbacks=[callback])
    return model


def modelSave(model, model_name='訓練完路徑'):
    model.save(model_name)

def modelLoad(model_name='modle參數檔'):
    model = tf.keras.models.load_model(model_name, compile = True)
    model.summary()
    return model
