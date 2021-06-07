# datas = {'stage1': {'name': 'data-preprocess', 'step': [{'mlfun': 'james759426/time-parser:0.0.1', 'name': 'time-parser'}, {'mlfun': 'james759426/data-clean:0.0.1', 'name': 'data-clean'}]}, 'stage2': {'name': 'LSTM-model-build', 'step': [{'mlfun': 'james759426/train-data-build:0.0.1', 'name': 'train-data-build'}, {'mlfun': 'james759426/train-model-build:0.0.1', 'name': 'train-model-build'}, {'mlfun': 'james759426/train-model:0.0.1', 'name': 'train-model'}]}, 'stage3': {'name': 'model-serving', 'step': [{'mlfun': 'james759426/model-serving-fun:0.0.1', 'name': 'model-serving-fun'}]}}
# fuck = {}
# for key1, data1 in datas.items():
#     bbb = data1['step']
#     fuck[key1] = []
#     for key2, data2 in enumerate(bbb):
#         fuck[key1].append(data2['name'])
# print(fuck)

datas = {'stage1': {'name': 'data-preprocess', 'step': [{'mlfun': 'james759426/time-parser:0.0.1', 'name': 'time-parser'}, {'mlfun': 'james759426/data-clean:0.0.1', 'name': 'data-clean'}]}, 'stage2': {'name': 'LSTM-model-build', 'step': [{'mlfun': 'james759426/train-data-build:0.0.1', 'name': 'train-data-build'}, {'mlfun': 'james759426/train-model-build:0.0.1', 'name': 'train-model-build'}, {'mlfun': 'james759426/train-model:0.0.1', 'name': 'train-model'}]}, 'stage3': {'name': 'model-serving', 'step': [{'mlfun': 'james759426/model-serving-fun:0.0.1', 'name': 'model-serving-fun'}]}}
api_list = {}
for key1, data1 in datas.items():
    steps = data1['step']
    api_list[key1] = []
    for data2 in range(len(steps)):
        api_list[key1].append(steps[data2]['name'])
print(api_list)