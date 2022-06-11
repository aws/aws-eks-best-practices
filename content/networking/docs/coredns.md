# CoreDNS

CoreDNS handles name resolution and service discovery in Kubernetes. It is installed by default on EKS clusters. For interoperability, the Kubernetes Service for CoreDNS is still named [kube-dns](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/). CoreDNS Pods run as part of a Deployment in `kube-system` namespace. EKS, by default, runs two replicas of CoreDNS. DNS queries from pods are sent to the `kube-dns` Service that runs in the `kube-system` Namespace. 

## Recommendations

### Monitor CoreDNS Metrics

CoreDNS has built in support for [Prometheus](https://github.com/coredns/coredns/tree/master/plugin/metrics). You should monitor CoreDNS metrics including:

- latency: `coredns_dns_request_duration_seconds_sum`)
- errors: `coredns_dns_response_rcode_count_total`, NXDOMAIN, SERVFAIL, FormErr  
- CoreDNS Pod’s memory consumption. 

For troubleshooting purposes, you can use kubectl to view CoreDNS logs:

```shell
for p in $(kubectl get pods —namespace=kube-system -l k8s-app=kube-dns -o name); do kubectl logs —namespace=kube-system $p; done
```

### Use NodeLocal DNSCache

Improve Cluster DNS performance by running [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/). This feature runs a DNS caching agent on cluster nodes as a DaemonSet. DNS requests from the pods will hit the DNS caching agent on the node first. If no match is found, a request is made to the `kube-dns` Service.

### Configure cluster-proportional-scaler for CoreDNS

Improve Cluster DNS performance by [automatically horizontally scaling the CoreDNS Deployment](https://kubernetes.io/docs/tasks/administer-cluster/dns-horizontal-autoscaling/#enablng-dns-horizontal-autoscaling) based on the number of nodes and CPU cores in the cluster. [Horizontal cluster-proportional-autoscaler](https://github.com/kubernetes-sigs/cluster-proportional-autoscaler/blob/master/README.md) is a container that resizes the number of replicas of a Deployment based on the size of the schedulable data-plane (e.g., number of cores, nodes). 

Nodes and the aggregate of CPU cores in the nodes are the two metrics with which you can scale CoreDNS. You can use both metrics simultaneously. If you use larger nodes, CoreDNS scaling is based on the number of CPU cores. Whereas, if you use smaller nodes, the number of CoreDNS replicas depends on the  CPU cores in your data-plane. 

Sample proportional autoscaler configuration:

```console
linear: '{"coresPerReplica":256,"min":1,"nodesPerReplica":16}'
```
