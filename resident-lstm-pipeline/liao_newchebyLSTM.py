import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, LSTM, TimeDistributed, RepeatVector
from keras.layers.normalization import BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
import tensorflow as tf
# from tensorflow import keras
from datetime import datetime, timedelta
import os
from tqdm import tqdm
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import mean_squared_error
pd.set_option('mode.chained_assignment', None)

class NewChebyLSTM:
    target_field = 'Temp'
    direction = True
    def __init__(self, filename):
        df = pd.read_csv(filename, low_memory=False)
        # df = pd.read_csv(filename, low_memory=False)[:100000]
        self.data = df.copy()       

    def normalization(self):
        self.data = self.data.round(2)
    
    def timeParser(self, time_format="dd/mm/YY HH:MM:SS"):
        if time_format == "dd/mm/YY HH:MM:SS":
            data = self.data['LocalTime'].copy()
            time = []           
            for i in range(data.shape[0]):
                time_split = data.iloc[i].split(' ')
                date_split = time_split[0].split('/')
                year = '20'+date_split[2]
                month = date_split[0]
                day = date_split[1]
                today = year+'-'+month+'-'+day+' '+time_split[1]
                time.append(datetime.strptime(today, '%Y-%m-%d %H:%M:%S'))
            self.data['LocalTime'] = pd.Series(time)
            self.data = self.data.set_index('LocalTime') 
        elif time_format == "YYYY/mm/dd HH:MM":
            data = self.data["LocalTime"].copy()
            time = []  
            for i in range(self.data.shape[0]):
                time.append(datetime.strptime(self.data["LocalTime"][i].replace("/", "-")+":00", '%Y-%m-%d %H:%M:%S'))
            self.data['LocalTime'] = pd.Series(time)
            self.data = self.data.set_index('LocalTime') 
        elif time_format=="YYYY-mm-dd HH:MM:SS":
            data = self.data["LocalTime"].copy()
            time = []  
            for i in range(self.data.shape[0]):
                time.append(datetime.strptime(self.data["LocalTime"][i], '%Y-%m-%d %H:%M:%S'))
            self.data['LocalTime'] = pd.Series(time)
            self.data = self.data.set_index('LocalTime') 

    def newField(self):
        self.data[self.target_field + '_m'] = [np.nan] * self.data.shape[0]
        return self.target_field + '_m'

    def outputToCsv(self, filename, index = True):
        self.data.to_csv(filename, index = index)

    def anomalyDetection(self, method = 'chebyshev', value_maximun = 40, value_minimun = 0):

        def timeParser(date, time, day = 0):
            _date = (date + timedelta(days = day)).strftime('%Y-%m-%d')
            return datetime.strptime(_date + ' ' + time, '%Y-%m-%d %H:%M:%S')

        self.data[self.target_field][self.data[self.target_field] > value_maximun] = np.nan
        self.data[self.target_field][self.data[self.target_field] < value_minimun] = np.nan
        if method == 'chebyshev':
            start_day = self.data.index[0]
            end_day = self.data.index[-1]
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
                avg = self.data.loc[start_time:end_time][self.target_field].mean()
                std = self.data.loc[start_time:end_time][self.target_field].std()
                std *= 2
                self.data.loc[start_time:end_time][self.target_field][self.data[self.target_field] > (avg + std)] = np.nan
                self.data.loc[start_time:end_time][self.target_field][self.data[self.target_field] < (avg - std)] = np.nan
                std = self.data.loc[start_time:end_time][self.target_field].std()
                std *= 4
                self.data.loc[start_time:end_time][self.target_field][self.data[self.target_field] > (avg + std)] = np.nan
                self.data.loc[start_time:end_time][self.target_field][self.data[self.target_field] < (avg - std)] = np.nan
                days += 1
        # self.scaler = MinMaxScaler(feature_range=(0, 1))
        # self.data = self.scaler.fit_transform(self.data)

    def set_condition(self):
        self.condition = np.isnan(self.data[self.target_field])
        self.condition = list(self.condition)

    def buildTrain(self, past_day=24, futureDay=1):
        self.x_train = []
        self.y_train = []
        if self.direction:
            for i in range(past_day+futureDay, self.data.shape[0]):
                if self.data[self.target_field][i-past_day-futureDay:i].count() < past_day+futureDay:
                    pass
                else:
                    x = np.array(self.data[self.target_field].iloc[i-past_day-futureDay:i-futureDay])
                    x = x.reshape(x.shape[0], 1)
                    self.x_train.append(x)
                    self.y_train.append(np.array(self.data.iloc[i-futureDay:i][self.target_field]))
        else:
            for i in range((past_day+futureDay)*288, self.data.shape[0]):
                # print(self.data.iloc[i-futureDay:i][self.target_field])
                if np.isnan(np.array(self.data[self.target_field].iloc[i-(past_day*288)-(futureDay*288):i-(futureDay*288):288])).sum() > 0:
                    pass
                elif np.isnan(self.data[i-futureDay:i][self.target_field].iloc[0]):
                    pass
                else:
                    x = np.array(self.data[self.target_field].iloc[i-(past_day*288)-(futureDay*288):i-(futureDay*288):288])
                    x = x.reshape(x.shape[0], 1)
                    self.x_train.append(x)
                    self.y_train.append(np.array(self.data.iloc[i-futureDay:i][self.target_field]))
        self.x_train = np.array(self.x_train)
        self.y_train = np.array(self.y_train)
        
    def shuffle(self, seed=10):
        np.random.seed(seed)
        randomList = np.arange(self.x_train.shape[0])
        np.random.shuffle(randomList)
        self.x_train = self.x_train[randomList]
        self.y_train = self.y_train[randomList]

    def buildModel(self):
        self.model = Sequential()
        # print(np.unique(np.isnan(self.y_train), return_counts=True))
        # print(np.unique(np.isnan(self.x_train), return_counts=True))
        self.model.add(LSTM(10, input_length=self.x_train.shape[1], input_dim=1))
        # self.model.add(LSTM(16, return_sequences = True, input_length=self.x_train.shape[1], input_dim=1))
        # self.model.add(Dropout(0.2))
        # self.model.add(LSTM(32, return_sequences = True))
        # self.model.add(Dropout(0.2))
        # self.model.add(LSTM(50, return_sequences = True))
        # self.model.add(Dropout(0.2))
        # self.model.add(LSTM(16))
        self.model.add(Dense(1))
        opt = tf.keras.optimizers.Adam(learning_rate=0.001)
        self.model.compile(loss="mse", optimizer=opt)
        self.model.summary()
        callback = EarlyStopping(monitor="loss", patience=10, verbose=1, mode="auto")
        self.x_train = self.x_train.astype(np.float32)
        self.y_train = self.y_train.astype(np.float32)
        self.model.fit(self.x_train, self.y_train, epochs=100, batch_size=128, callbacks=[callback])

    def modelSave(self, model_name='./models/lstm_model.h5'):
        self.model.save(model_name)

    def modelLoad(self, model_name='./models/lstm_model.h5'):
        self.model = tf.keras.models.load_model(model_name, compile = False)
        self.model.summary()

    def correction(self, past_day = 24, correction_day = 12):
        if self.direction:
            mask = list(np.isnan(self.data[self.target_field]))
            for i in tqdm(range(past_day+1, len(mask))):
                if mask[i]:
                    if self.condition[i - past_day:i].count(True) < correction_day:
                        if mask[i-past_day:i].count(True) == 0:
                            self.test = []
                            x = np.array(self.data[self.target_field].iloc[i-past_day:i])
                            x = x.reshape(x.shape[0], 1)
                            self.test.append(x)
                            self.test = np.array(self.test)
                            y_hat = self.model.predict(self.test)
                            self.data[self.target_field][self.data.index[i]] = y_hat[0]
                            mask[i] = False
                            self.data[self.target_field + '_m'][self.data.index[i]] = 'V'
        else:
            mask = list(np.isnan(self.data[self.target_field]))
            for i in tqdm(range((past_day+1)*288, self.data.shape[0])):
                if mask[i]:
                    if self.condition[i - past_day*288:i:288].count(True) < correction_day:
                        if mask[i-past_day*288:i:288].count(True) == 0:
                            self.test = []
                            x = np.array(self.data[self.target_field].iloc[i-past_day*288:i:288])
                            x = x.reshape(x.shape[0], 1)
                            self.test.append(x)
                            self.test = np.array(self.test)
                            y_hat = self.model.predict(self.test)
                            self.data[self.target_field][self.data.index[i]] = y_hat[0]
                            mask[i] = False
                            self.data[self.target_field + '_m'][self.data.index[i]] = 'H'
     
    def reverse(self):
        self.data = self.data.reset_index()
        data_dict = self.data.to_dict(orient ='list')
        data_dict_keys = list(data_dict.keys())
        data_dict_keys.pop(0)
        for i in data_dict_keys:
            data_dict[i].reverse()
        self.condition.reverse()
        self.data = pd.DataFrame(data_dict)
        self.data = self.data.set_index('LocalTime')
   
    def smooth(self, gap = 0.3, fix = 36):
        a_array = self.data[self.target_field].copy().tolist()
        b_array = a_array.copy()
        b_array.pop()
        b_array.insert(0, 0)
        diff_value = np.array(a_array) - np.array(b_array)
        diff_array = pd.Series((diff_value).tolist())
        positive_mask = diff_array >= gap
        negative_mask = diff_array <= -gap
        for i in tqdm(range(1, diff_array.shape[0])):
            if positive_mask[i] or negative_mask[i]:
                if diff_value[i] > 0:
                    x = diff_value[i] / fix
                    for j in range(fix):
                        k = fix - j
                        try:
                            if not np.isnan(self.data.iloc[i+j][self.target_field]) and self.data[self.target_field+"_m"][self.data.index[i + j]] == "H":
                                self.data[self.target_field][self.data.index[i + j]] -= x*k
                        except Exception as e:
                            pass
                        try:
                            if not np.isnan(self.data.iloc[i-j-1][self.target_field]) and self.data[self.target_field+"_m"][self.data.index[i-j-1]] == "H":
                                self.data[self.target_field][self.data.index[i-j-1]] += x*k
                        except Exception as e:
                            pass                                 
                elif diff_value[i] < 0:
                    x = -diff_value[i] / fix
                    for j in range(fix):
                        k = fix - j
                        try:
                            if not np.isnan(self.data.iloc[i+j][self.target_field]) and self.data[self.target_field+"_m"][self.data.index[i + j]] == "H":
                                self.data[self.target_field][self.data.index[i + j]] += x*k
                        except Exception as e:
                            pass
                        try:
                            if not np.isnan(self.data.iloc[i-j-1][self.target_field]) and self.data[self.target_field+"_m"][self.data.index[i-j-1]] == "H":
                                self.data[self.target_field][self.data.index[i-j-1]] -= x*k
                        except Exception as e:
                            pass

if __name__ == "__main__":
    #files = os.listdir("../enddata/")
    # f = [files[:2], files[2:4], files[4:6], files[6:8], files[8:10], files[10:12], files[12:14], files[14:16], files[16:18], files[18:]]
    #files = os.listdir("../new10dataNOna/")
    #f =[files[:2], files[2:4], files[4:6], files[6:8], files[8:10], files[10:12]]
    #key = 5
    # f[key] = ["01_原臺南州廳綜合氣象站.csv"]

    # files = os.listdir("../LSTM/")
    # f = files[:3], files[3:6], files[6:9], files[9:12], files[12:15], files[15:18], files[18:21], files[21:24], files[24:27], files[27:30], files[30:]]
    # key = 0
    f = ["test.csv"]
    for i in f:
       
        try:
            print(i)
            print("load data start")
            # data = NewChebyLSTM("../enddata/" + i)
            data = NewChebyLSTM("/" + i)
            print("load data done")
            print("time parser start")
            data.timeParser()
            #data.timeParser(time_format="YYYY/mm/dd HH:MM")
            print("time parser done")
            print("anomaly detection start")
            data.normalization()
            data.anomalyDetection()
            #data.target_field = 'Hum'
            #data.anomalyDetection(value_maximun = 100, value_minimun = 30)
            #data.target_field = 'Temp'
            print("anomaly detection done")
            data.outputToCsv("/root/" + i)
            # data.outputToCsv("../clean_data/"+str(i))
            # print("clean_data_done")
            data.buildTrain(past_day=24)
            data.shuffle()
            data.buildModel()
            data.modelSave(model_name="/root/"+i+".h5")
            # data.target_field = 'Hum'
            # data.buildTrain(past_day=24)
            # data.shuffle()
            # data.buildModel()
            # data.modelSave(model_name="../model/Hum_V_"+i+".h5")
            # data.direction = False
            # data.target_field = 'Temp'
            # data.buildTrain(past_day=28)
            # data.shuffle()
            # data.buildModel()
            # data.modelSave(model_name="../model/Temp_H_"+i+".h5")
            # data.target_field = 'Hum'
            # data.buildTrain(past_day=28)
            # data.shuffle()
            # data.buildModel()
            # data.modelSave(model_name="../model/Hum_H_"+i+".h5")

            #data.direction = True
            #data.target_field = 'Temp'
            data.set_condition()
            # data.modelLoad("../model/1000Temp_V_"+"01_原臺南州廳綜合氣象站.csv"+".h5")
            data.modelLoad("/root/"+i+".h5")
            data.newField()
            try:
                print(data.target_field+" vertical correction start")
                data.correction(past_day = 24)
                #data.reverse()
                #print("reverse")
                #data.correction(past_day = 24)
                print(data.target_field+" vertical correction done")
            except Exception as e:
                print(e)
            #data.reverse()

            #data.direction = False
            # data.modelLoad("../model/1000Temp_H_"+"01_原臺南州廳綜合氣象站.csv"+".h5")
            #data.modelLoad("../model/Temp_H_"+"01_原臺南州廳綜合氣象站.csv"+".h5")
            #try:
            #    print(data.target_field+" horizontal correction start")
            #    data.correction(past_day = 28, correction_day=14)
            #    data.reverse()
            #    print("reverse")
            #    data.correction(past_day = 28, correction_day=14)
            #    print(data.target_field+" horizontal correction done")
            #except Exception as e:
            #    print(e)
            #data.reverse()

            #data.direction = True
            #data.target_field = 'Hum'
            #data.set_condition()
            # data.modelLoad("../model/1000Hum_V_"+"01_原臺南州廳綜合氣象站.csv"+".h5")
            #data.modelLoad("../model/Hum_V_"+"01_原臺南州廳綜合氣象站.csv"+".h5")
            #data.newField()
            #try:
            #    print(data.target_field+" vertical correction start")
            #    data.correction(past_day = 24)
            #    data.reverse()
            #    print("reverse")
            #    data.correction(past_day = 24)
            #    print(data.target_field+" vertical correction done")
            #except Exception as e:
            #    print(e)
            #data.reverse()
            
            #data.direction = False
            # data.modelLoad("../model/1000Hum_H_"+"01_原臺南州廳綜合氣象站.csv"+".h5")
            #data.modelLoad("../model/Hum_H_"+"01_原臺南州廳綜合氣象站.csv"+".h5")
            #try:
            #    print(data.target_field+" horizontal correction start")
            #    data.correction(past_day = 28, correction_day=14)
            #    data.reverse()
            #    print("reverse")
            #    data.correction(past_day = 28, correction_day=14)
            #    print(data.target_field+" horizontal correction done")
            #except Exception as e:
            #    print(e)
            #data.reverse()

            data.normalization()
            # data.outputToCsv("../LSTM/1000LSTM_"+str(i))
            data.outputToCsv("/root/new"+i+".csv")
            print("output done")
            
            # data = NewChebyLSTM("../LSTM/" + i)
            # data.timeParser(time_format="YYYY-mm-dd HH:MM:SS")
            #data.target_field = 'Temp'
            #data.smooth()
            #data.target_field = "Hum"
            #data.smooth(gap = 3)
            #data.outputToCsv("../LSTM/sm_LSTM_"+str(i))
        
        except Exception as e:
            print(e)

        
