while :
do
    kubectl get pods -n openfaas-fn >> watch-data.txt
    sleep 1
done