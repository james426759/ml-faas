import os
import kopf
import kubernetes
import yaml
@kopf.on.create('mlflows')
def create_fn(spec, name, namespace, logger, **kwargs):
    fun_flow = {}
    ml_pipelines = spec['pipeline']
    for key, stage in ml_pipelines.items():
        steps = stage['step']
        fun_flow[key] = {'rule': stage['rule'], 'step': []}
        for data in range(len(steps)):
            ml_Fun = f"""apiVersion: openfaas.com/v1
kind: Function
metadata:
  name: {name}-{steps[data]['name']}
  namespace: openfaas-fn
spec:
  name: {name}-{steps[data]['name']}
  image: {steps[data]['mlfun']}
  labels:
    com.openfaas.scale.min: "0"
  environment:
    read_timeout: "21600s"
    write_timeout: "21600s"
    exec_timeout: "21600s"
    bucket_name: {name}-{steps[data]['name']}
"""
            fun_name = f"""{name}-{steps[data]['name']}"""
            fun_flow[key]['step'].append(fun_name)
            os.system(f"cat <<EOF | kubectl apply -f - \n{ml_Fun}\n")
    return {'api_list': fun_flow}


@kopf.on.delete('mlflows')
def delete_fn(name, meta, spec, status, **_):
    ml_pipelines = spec['pipeline']
    for key, stage in ml_pipelines.items():
        steps = stage['step']
        for data in range(len(steps)):
            ml_Fun = f"""apiVersion: openfaas.com/v1
kind: Function
metadata:
  name: {name}-{steps[data]['name']}
  namespace: openfaas-fn
spec:
  name: {name}-{steps[data]['name']}
  image: {steps[data]['mlfun']}
  labels:
    com.openfaas.scale.min: "0"
  environment:
    read_timeout: "21600s"
    write_timeout: "21600s"
    exec_timeout: "21600s"
    bucket_name: {name}-{steps[data]['name']}
"""
            os.system(f"cat <<EOF | kubectl delete -f - \n{ml_Fun}\n")
    return 'delete success'