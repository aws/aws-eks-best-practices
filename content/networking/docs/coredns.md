# CoreDNS

CoreDNS fulfills name resolution and service discovery functions in Kubernetes. It is installed by default on EKS clusters. For interoperability, the Kubernetes Service for CoreDNS is still named [kube-dns](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/). CoreDNS Pods run as part of a Deployment in `kube-system` namespace, and in EKS, by default, it runs two replicas with declared requests and limits. DNS queries are sent to the `kube-dns` Service that runs in the `kube-system` Namespace.

## Recommendations

### Monitor CoreDNS metrics

CoreDNS has built in support for [Prometheus](https://github.com/coredns/coredns/tree/master/plugin/metrics). You should especially consider monitoring CoreDNS latency (`coredns_dns_request_duration_seconds_sum`), errors (`coredns_dns_response_rcode_count_total`, NXDOMAIN, SERVFAIL, FormErr) and CoreDNS Pod’s memory consumption. 

For troubleshooting purposes, you can use kubectl to view CoreDNS logs:

```shell
for p in $(kubectl get pods —namespace=kube-system -l k8s-app=kube-dns -o name); do kubectl logs —namespace=kube-system $p; done
```

### Use NodeLocal DNSCache

You can improve the Cluster DNS performance by running [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/). This feature runs a DNS caching agent on cluster nodes as a DaemonSet. All the pods use the DNS caching agent running on the node for name resolution instead of using `kube-dns` Service. 

### Configure cluster-proportional-scaler for CoreDNS

Another method of improving Cluster DNS performance is by [automatically horizontally scaling the CoreDNS Deployment](https://kubernetes.io/docs/tasks/administer-cluster/dns-horizontal-autoscaling/#enablng-dns-horizontal-autoscaling) based on the number of nodes and CPU cores in the cluster. [Horizontal cluster-proportional-autoscaler](https://github.com/kubernetes-sigs/cluster-proportional-autoscaler/blob/master/README.md) is a container that resizes the number of replicas of a Deployment based on the size of the schedulable data-plane. 

Nodes and the aggregate of CPU cores in the nodes are the two metrics with which you can scale CoreDNS. You can use both metrics simultaneously. If you use larger nodes, CoreDNS scaling is based on the number of CPU cores. Whereas, if you use smaller nodes, the number of CoreDNS replicas depends on the  CPU cores in your data-plane. Proportional autoscaler configuration looks like this:

```console
linear: '{"coresPerReplica":256,"min":1,"nodesPerReplica":16}'
```
