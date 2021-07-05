import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
from tqdm import tqdm
from sklearn.ensemble import RandomForestRegressor
import joblib

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
                #     x = x.reshape(x.shape[0], 1)
                    self.x_train.append(x)
                    self.y_train.append(self.data.iloc[i-futureDay:i][self.target_field].tolist())
        else:
            for i in range((past_day+futureDay)*288, self.data.shape[0]):
                # print(self.data.iloc[i-futureDay:i][self.target_field])
                if np.isnan(np.array(self.data[self.target_field].iloc[i-(past_day*288)-(futureDay*288):i-(futureDay*288):288])).sum() > 0:
                    pass
                elif np.isnan(self.data[i-futureDay:i][self.target_field].iloc[0]):
                    pass
                else:
                    x = np.array(self.data[self.target_field].iloc[i-(past_day*288)-(futureDay*288):i-(futureDay*288):288])
                #     x = x.reshape(x.shape[0], 1)
                    self.x_train.append(x)
                    self.y_train.append(self.data.iloc[i-futureDay:i][self.target_field].tolist())
        self.x_train = np.array(self.x_train)
        self.y_train = np.array(self.y_train)
        self.y_train = self.y_train.flatten()
        
    def shuffle(self, seed=10):
        np.random.seed(seed)
        randomList = np.arange(self.x_train.shape[0])
        np.random.shuffle(randomList)
        self.x_train = self.x_train[randomList]
        self.y_train = self.y_train[randomList]

    def buildModel(self, tree_num):
        self.model = RandomForestRegressor(tree_num)
        self.model.fit(self.x_train, self.y_train)

    def modelSave(self, model_name='./models/forest_model.joblib'):
	    joblib.dump(self.model, model_name)

    def modelLoad(self, model_name='./models/forest_model.joblib'):
        self.model = joblib.load(model_name)

    def correction(self, past_day = 24, correction_day = 12):
        if self.direction:
            mask = list(np.isnan(self.data[self.target_field]))
            for i in tqdm(range(past_day+1, len(mask))):
                if mask[i]:
                    if self.condition[i - past_day:i].count(True) < correction_day:
                        if mask[i-past_day:i].count(True) == 0:
                            self.test = []
                            x = np.array(self.data[self.target_field].iloc[i-past_day:i])
                            # x = x.reshape(x.shape[0], 1)
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
                            # x = x.reshape(x.shape[0], 1)
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
    f = ["test.csv"]
    for i in f:
       
        try:
            print(i)
            print("load data start")
            data = NewChebyLSTM("/" + i)
            print("load data done")
            print("time parser start")
            data.timeParser()
            print("time parser done")
            print("anomaly detection start")
            data.normalization()
            data.anomalyDetection()
            print("anomaly detection done")
            data.outputToCsv("/root/" + i)
            
            data.buildTrain(past_day=24)
            data.shuffle()
            data.buildModel(100)
            data.modelSave(model_name="/root/"+i+".joblib")
            data.set_condition()
            data.modelLoad("/root/"+i+".joblib")
            data.newField()
            try:
                print(data.target_field+" vertical correction start")
                data.correction(past_day = 24)
                print(data.target_field+" vertical correction done")
            except Exception as e:
                print(e)

            data.normalization()
            data.outputToCsv("/root/new"+i+".csv")
            print("output done")
 
        
        except Exception as e:
            print(e)