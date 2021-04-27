import pandas as pd 
import json
def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    json_req = json.loads(req)
    file_path = requests.get(json_req["path"])
    data = pd.read_csv(file_path).copy()
    return 