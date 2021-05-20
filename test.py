import json
import numpy as np

x = [[[23.1], [23.2] ,[23.3] ,[23.4] ,[23.5]], [[24.2], [24.3] ,[24.4] ,[24.5] ,[24.6]] ,[[30.5], [30.6] ,[30.7] ,[30.8] ,[30.9]]]
y = [[23.6] ,[24.7] ,[31.0]]

xa = np.array(x)
ya = np.array(y)

print(xa)
print(ya)

xd = dict()
yd = dict()
for i in range(len(xa)):
    xd[str(i)] = dict()
    for j in range(len(xa[i])):
        xd[str(i)][str(j)] = xa[i][j][0]

for i in range(len(ya)):
    yd[str(i)] = ya[i][0]

print(xd)
print(yd)

# with open('xt.json', 'w', encoding='utf-8') as f:
#     json.dump(xd, f)

# with open('yt.json', 'w', encoding='utf-8') as f:
#     json.dump(yd, f)