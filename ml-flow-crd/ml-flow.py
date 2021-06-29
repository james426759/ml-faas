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
        try:
          deploy_node = stage['node']
          deploy_datas = f"""constraints:
      -  "node-use={deploy_node}" """
        except:
          deploy_datas = False
          # print("default deploy")

        fun_flow[key] = {'rule': stage['rule'], 'step': []}
        for data in range(len(steps)):
            try:
              limits = steps[data]['limits']
              if 'memory' in limits:
                  limits_memory = f"memory: {limits['memory']}" 
              else:
                  limits_memory = False

              if 'cpu' in limits:
                  limits_cpu = f"cpu: {limits['cpu']}" 
              else:
                  limits_cpu = False

              limits_datas = f"""limits:
    {limits_memory if limits_memory else ""}
    {limits_cpu if limits_cpu else ""} """
            except:
              limits_datas = False
              # print("no limits")

            try:
              requests = steps[data]['requests']
              # requests_status = True
              if 'memory' in requests:
                  requests_memory = f"memory: {requests['memory']}" 
              else:
                  requests_memory = False

              if 'cpu' in requests:
                  requests_cpu = f"cpu: {requests['cpu']}" 
              else:
                  requests_cpu = False

              requests_datas = f"""requests:
    {requests_memory if requests_memory else ""}
    {requests_cpu if requests_cpu else ""} """
            except:
              requests_datas = False
              # print("no requests")
            
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
  {deploy_datas if deploy_datas else ""}
  {limits_datas if limits_datas else ""}
  {requests_datas if requests_datas else ""}
"""
            fun_name = f"""{name}-{steps[data]['name']}"""
            fun_flow[key]['step'].append(fun_name)
            os.system(f"cat <<EOF | kubectl apply -f - \n{ml_Fun}\n")
            if 'scale-fun' in steps[data]:
              scale_datas = f"kubectl autoscale deployment -n openfaas-fn {name}-{steps[data]['name']} --cpu-percent={steps[data]['scale-fun']['cpu-percent']} --max={steps[data]['scale-fun']['scale-fun-max']}"
              os.system(scale_datas)
    return {'api_list': fun_flow}


@kopf.on.delete('mlflows')
def delete_fn(name, meta, spec, status, **_):
    ml_pipelines = spec['pipeline']
    for key, stage in ml_pipelines.items():
        steps = stage['step']
        for data in range(len(steps)):
            os.system(f"kubectl delete function {name}-{steps[data]['name']} -n openfaas-fn")
            if 'scale-fun' in steps[data]:
              os.system(f"kubectl delete hpa {name}-{steps[data]['name']} -n openfaas-fn")
    return 'delete success'