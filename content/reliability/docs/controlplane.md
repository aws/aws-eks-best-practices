# EKS Control Plane

Amazon Elastic Kubernetes Service (EKS) is a managed Kubernetes service that makes it easy for you to run Kubernetes on AWS without needing to install, operate, and maintain your own Kubernetes control plane. It runs upstream Kubernetes and is certified Kubernetes conformant. This conformance ensures that EKS supports the Kubernetes APIs, just like the open source community version that you can install on EC2 or on-premises. Existing applications running on upstream Kubernetes are compatible with Amazon EKS.

EKS automatically manages the availability and scalability of the Kubernetes control plane nodes and it automatically replaces unhealthy control plane nodes.

## EKS Architecture 

EKS architecture is designed to eliminate any single points of failure which may compromise the availability and durability of the Kubernetes control plane.

> Insert EKS architecture diagram here

EKS control plane runs inside an EKS managed VPC. The EKS control plane comprises the Kubernetes master nodes, etcd cluster. Kubernetes master nodes that run components like the API server, scheduler, and `kube-controller-manager` run in an auto-scaling group. This auto-scaling group is spread across a minimum of three Availability Zones (AZs). Likewise, for durability the etcd server nodes also run in an auto-scaling group that is spread across three AZs. EKS runs a NAT Gateway in each AZ and master nodes and etcd servers run in a private subnet. This ensures that an event in a single AZ doesn’t affect the availability of the etcd cluster.  

When you create a new cluster, Amazon EKS creates a highly-available endpoint for the managed Kubernetes API server that you use to communicate with your cluster (using tools like `kubectl`). The managed endpoint uses NLB to load balance Kubernetes API servers. EKS also provisions two ENIs in different AZs to facilitate communication to your worker nodes.

You can configure whether your Kubernetes cluster’s API server is reachable from the public internet (using the public endpoint) or through your VPC (using the EKS-managed ENIs) or both.  

Whether users and worker nodes connect to the API server using the public endpoint or the EKS-managed ENI, there are redundant paths for connection. 

## Recommendations

## Monitor Control Plane Metrics

Monitoring Kubernetes API response times (latencies) can help you understand how the control plane is performing. Poorly written controllers can overload the API servers and affect cluster performance. 

You can monitor the control plane using metrics exposed by Kubernetes `/metrics` endpoint. 

You can view the metrics exposed using `kubectl`:

```
kubectl get --raw /metrics
```

These metrics are represented in a [Prometheus text format](https://github.com/prometheus/docs/blob/master/content/docs/instrumenting/exposition_formats.md). 

You can use Prometheus to collect and store these metrics. In May 2020, CloudWatch added support for monitoring Prometheus metrics in CloudWatch Container Insights. So you can also use Amazon CloudWatch to monitor the EKS control plane. 

The Kubernetes API server metrics can be found [here](https://github.com/kubernetes/apiserver/blob/master/pkg/endpoints/metrics/metrics.go). For example, `apiserver_request_duration_seconds` can indicate how long API requests are taking to run. 

You can use [Grafana dashboard 12006](https://grafana.com/grafana/dashboards/12006) to visualize and monitor Kubernetes API server requests and latency and etcd latency metrics. 

## Control Plane Scaling

EKS clusters by default are sized to handle up to 200 nodes and 30 pods per node. If your cluster exceeds this size, you can request a scale up through a support ticket. The EKS team is working on automatically scaling the control plane, at which point this will not be required.

## Additional Resources:

[De-mystifying cluster networking for Amazon EKS worker nodes](https://aws.amazon.com/blogs/containers/de-mystifying-cluster-networking-for-amazon-eks-worker-nodes/)

[Amazon EKS cluster endpoint access control](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)

[AWS re:Invent 2019: Amazon EKS under the hood (CON421-R1)](https://www.youtube.com/watch?v=7vxDWDD2YnM)
