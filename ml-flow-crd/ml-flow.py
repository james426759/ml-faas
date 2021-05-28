import os
import kopf
import kubernetes
import yaml
@kopf.on.create('mlflows')
def create_fn(spec, name, namespace, logger, **kwargs):
    fun_flow = []
    ml_pipelines = spec['pipeline']

    for stage in ml_pipelines:
        steps = ml_pipelines[stage]['step']
        for step in steps:
            data = f"""apiVersion: openfaas.com/v1
kind: Function
metadata:
  name: {step['name']}
  namespace: openfaas-fn
spec:
  name: {step['name']}
  image: {step['mlfun']}
  labels:
    com.openfaas.scale.min: "0"
  environment:
    read_timeout: "21600s"
    write_timeout: "21600s"
    exec_timeout: "21600s"
"""
            fun_flow.append(step['name'])
            os.system(f"cat <<EOF | kubectl apply -f - \n{data}\n")
    return {'api_list': fun_flow}


# @kopf.on.delete('kopfexamples')
# def my_handler(spec, **_):
#     pass
