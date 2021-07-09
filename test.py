# import json
# import numpy as np

# x = [[[23.1], [23.2] ,[23.3] ,[23.4] ,[23.5]], [[24.2], [24.3] ,[24.4] ,[24.5] ,[24.6]] ,[[30.5], [30.6] ,[30.7] ,[30.8] ,[30.9]]]
# y = [[23.6] ,[24.7] ,[31.0]]

# xa = np.array(x)
# ya = np.array(y)

# print(xa)
# print(ya)

# xd = dict()
# yd = dict()
# for i in range(len(xa)):
#     xd[str(i)] = dict()
#     for j in range(len(xa[i])):
#         xd[str(i)][str(j)] = xa[i][j][0]

# for i in range(len(ya)):
#     yd[str(i)] = ya[i][0]

# print(xd)
# print(yd)

# # with open('xt.json', 'w', encoding='utf-8') as f:
# #     json.dump(xd, f)

# # with open('yt.json', 'w', encoding='utf-8') as f:
# #     json.dump(yd, f)

# b = True
# d = 123
# limits = {'memory': 123, 'cpu': 456}
# c = f"""limits:
#   {f"memory: limits['memory']" if b else ""}
# """
# cpu: {limits['cpu']}

# a = f"""apiVersion: openfaas.com/v1
# kind: Function
# metadata:
#   name: lstm-pipeline-model-serving-fun
#   namespace: openfaas-fn
# spec:
#   name: lstm-pipeline-model-serving-fun
#   image: james759426/lstm-model-serving-fun:0.0.1
#   labels:
#     com.openfaas.scale.min: "0"
#   environment:
#     read_timeout: "21600s"
#     write_timeout: "21600s"
#     exec_timeout: "21600s"
#     bucket_name: lstm-pipeline-model-serving-fun
#     {c if b else ""}
# """

# print(c)
import requests

res = requests.post(f"""http://admin:admin@10.20.1.54:31112/system/scale-function/nodeinfo-1""", json={"replicas": 1})
print(res)