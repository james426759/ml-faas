import requests

r = requests.get('http://10.20.1.54:31112/function/data-clean')

print(r.status_code)
