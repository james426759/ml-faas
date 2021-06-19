kubectl delete function lstm-pipeline-data-clean -n openfaas-fn
kubectl delete function lstm-pipeline-load-data -n openfaas-fn
kubectl delete function lstm-pipeline-model-serving-fun -n openfaas-fn
kubectl delete function lstm-pipeline-time-parser -n openfaas-fn
kubectl delete function lstm-pipeline-train-data-build -n openfaas-fn
kubectl delete function lstm-pipeline-train-model -n openfaas-fn
kubectl delete function lstm-pipeline-train-model-build -n openfaas-fn