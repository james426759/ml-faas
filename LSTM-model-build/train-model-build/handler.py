import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, LSTM, TimeDistributed, RepeatVector
from keras.layers.normalization import BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
import tensorflow as tf

def handle(req):

    buildModel()
    
    return req

def buildModel(self):
    model = Sequential()
    print(x_train.shape)
    model.add(LSTM(10, input_length=x_train.shape[1], input_dim=1))
    model.add(Dense(1))
    model.compile(loss="mse", optimizer="adam")
    model.summary()
    # callback = EarlyStopping(monitor="loss", patience=10, verbose=1, mode="auto")
    x_train = x_train.astype(np.float32)
    y_train = y_train.astype(np.float32)

    model.save(路徑)
    # self.model.fit(self.x_train, self.y_train, epochs=3000, batch_size=128, callbacks=[callback])