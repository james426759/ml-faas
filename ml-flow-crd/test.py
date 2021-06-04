datas = {'stage1': {'name': 'data-preprocess', 'step': [{'mlfun': 'james759426/time-parser:0.0.1', 'name': 'time-parser'}, {'mlfun': 'james759426/data-clean:0.0.1', 'name': 'data-clean'}]}, 'stage2': {'name': 'LSTM-model-build', 'step': [{'mlfun': 'james759426/train-data-build:0.0.1', 'name': 'train-data-build'}, {'mlfun': 'james759426/train-model-build:0.0.1', 'name': 'train-model-build'}]}}
for data in datas:
    # print(datas[data]['step'])
    steps = datas[data]['step']
    for step in steps:
        # print(step['mlfun'])