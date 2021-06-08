import requests

fname = {'file_name':'KKKKK', 'BNAME':'BBBBBBBB'}
r = requests.post("http://10.20.1.54:30089/test", json=fname)
print(r.text)