import kubernetes
import yaml
from pprint import pprint
import requests
def main():
    kubernetes.config.load_kube_config()
    api_instance = kubernetes.client.CustomObjectsApi()
    api_response = api_instance.get_namespaced_custom_object(group='kopf.dev', version='v1', plural='mlflows', name='lstm-pipeline', namespace='default')
    pprint(api_response)
    data = api_response['status']['create_fn']['api_list']
    for i in data:
        r = requests.get(f"""http://10.20.1.54:31112/function/{i}""")
        if r.status_code == 200:
            continue
        else:
            break

if __name__ == "__main__":
    main()