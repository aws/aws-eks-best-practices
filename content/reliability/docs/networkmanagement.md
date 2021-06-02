# Networking in EKS

EKS uses Amazon VPC to provide networking capabilities to worker nodes and Kubernetes Pods. An EKS cluster consists of two VPCs: an AWS-managed VPC that hosts the Kubernetes control plane and a second customer-managed VPC that hosts the Kubernetes worker nodes where containers run, as well as other AWS infrastructure (like load balancers) used by the cluster. All worker nodes need the ability to connect to the managed API server endpoint. This connection allows the worker node to register itself with the Kubernetes control plane and to receive requests to run application pods.

Worker nodes connect to the EKS control plane through the EKS public endpoint or EKS-managed elastic network interfaces (ENIs). The subnets that you pass when you create the cluster influence where EKS places these ENIs. You need to provide a minimum of two subnets in at least two Availability Zones. The route that worker nodes take to connect is determined by whether you have enabled or disabled the private endpoint for your cluster. EKS uses the EKS-managed ENI to communicate with worker nodes.

> Insert a diagram about how control plane and worker nodes communicate.

Refer to [Cluster VPC considerations](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html) when architecting a VPC to be used with EKS.

If you deploy worker nodes in private subnets then these subnets should have a default route to a [NAT Gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html). 

## Recommendations

### Deploy NAT Gateways in each Availability Zone
If you deploy worker nodes in private subnets, consider creating a NAT Gateway in each Availability Zone to ensure zone-independent architecture. Each NAT gateway in an AZ is implemented with redundancy.


## Amazon VPC CNI
Amazon EKS supports native VPC networking via the [Amazon VPC Container Network Interface (CNI)](https://github.com/aws/amazon-vpc-cni-k8s) plugin for Kubernetes. The CNI plugin allows Kubernetes Pods to have the same IP address inside the Pod as they do on the VPC network. The CNI plugin uses [Elastic Network Interface (ENI)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html) for Pod networking. The CNI allocates ENIs to each worker node and uses the secondary IP range from each ENI for pods. The CNI pre-allocates ENIs and IP addresses for faster pod startup.

The [maximum number of network interfaces, and the maximum number of private IPv4 addresses](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI) that you can use varies by the type of EC2 Instance. Since each Pod uses an IP address, the number of Pods you can run on a particular EC2 Instance depends on how many ENIs can be attached to it and how many IP addresses it supports.

This [file](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt) contains the maximum number of pods you can run on an EC2 Instance. The limits in the file are invalid if you use CNI custom networking. 

The CNI plugin has two components:

* [CNI plugin](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/#cni), which will wire up host’s and pod’s network stack when called.
* `L-IPAMD` (aws-node DaemonSet) runs on every node is a long-running node-Local IP Address Management (IPAM) daemon and is responsible for:
    * maintaining a warm-pool of available IP addresses, and
    * assigning an IP address to a Pod.
    
You can find more details in [Proposal: CNI plugin for Kubernetes networking over AWS VPC](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/cni-proposal.md).

## Recommendations 

### Plan for growth

Size the subnets you will use for Pod networking for growth. If you have insufficient IP addresses available in the subnet that the CNI uses, your pods will not get an IP address. And the pods will remain pending until an IP address becomes available. This may impact application autoscaling and compromise its availability. 

### Monitor IP address inventory

You can monitor the IP addresses inventory of subnets using [CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html). You can also set [CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) to get notified if a subnet is running out of IP addresses.  

### Using public subnets for worker nodes
If you use public subnets, then they must have the automatic public IP address assignment setting enabled; otherwise, worker nodes will not be able to communicate with the cluster. 

### Run worker nodes and pods in different subnets
Consider creating [separate subnets for Pod networking](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html) (also called **CNI custom networking**) to avoid IP address allocation conflicts between Pods and other resources in the VPC. 

### SNAT
If your Pods with private IP address need to communicate with other private IP address spaces (for example, Direct Connect, VPC Peering or Transit VPC), then you need to [enable external SNAT](https://docs.aws.amazon.com/eks/latest/userguide/external-snat.html) in the CNI:

```bash
kubectl set env daemonset -n kube-system aws-node AWS_VPC_K8S_CNI_EXTERNALSNAT=true
```

### Size your subnets for growth

The CNI pre-allocates and caches a certain number of IP addresses so that Kubernetes scheduler can schedule pods on these worker nodes. The IP addresses are available on the worker nodes, whether you launch pods or not. 

When you provision a worker node, the CNI allocates a pool of secondary IP addresses (called *warm pool*) from the node’s primary ENI. As the pool gets depleted, the CNI attaches another ENI to assign more IP addresses. This process continues until no more ENIs can be attached to the node. 

Sizing your subnets for growth will prevent your subnets from running out of IP addresses as your Pods and nodes scale. You will not be able to create new Pods or nodes if the subnets don’t have available IP addresses. 

If you need to constrain the IP addresses the CNI caches then you can use these CNI environment variables:

- `WARM_IP_TARGET` -- Number of free IP addresses the CNI should keep available. Use this if your subnet is small and you want to reduce IP address usage. 
- `MINIMUM_IP_TARGET` -- Number of minimum IP addresses the CNI should allocate at node startup. 

To configure these options, you can download aws-k8s-cni.yaml compatible with your cluster and set environment variables. At the time of writing, the latest release is located [here](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/v1.6/aws-k8s-cni.yaml).

!!! info Configure the value of `MINIMUM_IP_TARGET` to closely match the number of Pods you expect to run on your nodes. Doing so will ensure that as Pods get created, the CNI can assign IP addresses from the warm pool without calling the EC2 API. 

!!! warning Avoid setting the value of `WARM_IP_TARGET` too low as it will cause additional calls to the EC2 API, and that might cause throttling of the requests.

## CNI custom networking

By default, the CNI assigns Pod’s IP address from the worker node's primary elastic network interface's (ENI) security groups and subnet. If you don’t have enough IP addresses in the worker node subnet or prefer that the worker nodes and Pods reside in separate subnets, you can use [CNI custom networking](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html).  

Enabling a custom network removes an available elastic network interface (and all of its available IP addresses for pods) from each worker node that uses it. The worker node's primary network interface is not used for pod placement when a custom network is enabled.

If you want the CNI to assign IP addresses for Pods from a different subnet, you can set `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG` environment variable to `true`.

```bash
kubectl set env daemonset aws-node -n kube-system AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true
```

> 📝 EKS managed node groups currently don’t support custom networking option. 

When `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true`, the CNI will assign Pod IP address from a subnet defined in `ENIConfig`. The `ENIConfig` custom resource is used to define the subnet in which Pods will be scheduled. 

```yaml
apiVersion: crd.k8s.amazonaws.com/v1alpha1
kind: ENIConfig
metadata: 
  name: us-west-2a
spec: 
  securityGroups: 
    - sg-0dff111a1d11c1c11
  subnet: subnet-011b111c1f11fdf11
```

You will need to create an `ENIconfig` custom resource for each subnet you want to use for Pod networking. 
- The `securityGroups` field should have the ID of the security group attached to the worker nodes. 
- The `name` field should be the name of the Availability Zone in your VPC. If you name your ENIConfig custom resources after each Availability Zone in your VPC, you can enable Kubernetes to automatically apply the corresponding ENIConfig for the worker node Availability Zone with the following command.

```shell
kubectl set env daemonset aws-node \
-n kube-system ENI_CONFIG_LABEL_DEF=failure-domain.beta.kubernetes.io/zone
```

Upon creating the `ENIconfig` custom resources, you will need to create new worker nodes. The existing worker nodes and Pods will remain unaffected. 

You will also need to calculate the maximum number of Pods that can be scheduled on each worker node and pass it in worker nodes’ user-data script.

To determine the number of Pods for each worker node, you will need to know [the number of network interfaces and the IPv4 addresses per network interface the worker node supports](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI). The formula for calculating the maximum number of pods for an EC2 instance is:

```
maxPods = (number of interfaces - 1) * (max IPv4 addresses per interface - 1) + 2
```

For a `c3.large` EC2 instance, the calculation will be:

```
Maximum Pods = ((number of interfaces = 3) - 1) * ((max IPv4 addresses = 10) - 1) +2 
=> Maximum Pods = (3 - 1) * (10 - 1) + 2
=> Maximum Pods = 2 * 9 + 2 = 20
```

You can then pass the `max-pods` value in the worker nodes’ user-data script:

```
--use-max-pods false --kubelet-extra-args '--max-pods=20'
```

Since the node’s primary ENI is no longer used to assign Pod IP addresses, there is a decline in the number of Pods you can run on a given EC2 instance type. 
 
## Using alternate CNI plugins 

AWS VPC CNI plugin is the only officially supported [network plugin](https://kubernetes.io/docs/concepts/cluster-administration/networking/) on EKS. However, since EKS runs upstream Kubernetes and is certified Kubernetes conformant, you can use alternate [CNI plugins](https://github.com/containernetworking/cni).

A compelling reason to opt for an alternate CNI plugin is to run Pods without using a VPC IP address per Pod. Although, using an alternate CNI plugin can come at the expense of network performance. 

Refer to EKS documentation for the list [alternate compatible CNI plugins](https://docs.aws.amazon.com/eks/latest/userguide/alternate-cni-plugins.html). Consider obtaining the CNI vendor’s commercial support if you plan on using an alternate CNI in production. 

## CoreDNS

CoreDNS fulfills name resolution and service discovery functions in Kubernetes. It is installed by default on EKS clusters. For interoperability, the Kubernetes Service for CoreDNS is still named [kube-dns](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/). CoreDNS Pods run as part of a Deployment in `kube-system` namespace, and in EKS, by default, it runs two replicas with declared requests and limits. DNS queries are sent to the `kube-dns` Service that runs in the `kube-system` Namespace. 

## Recommendations
### Monitor CoreDNS metrics
CoreDNS has built in support for [Prometheus](https://github.com/coredns/coredns/tree/master/plugin/metrics). You should especially consider monitoring CoreDNS latency (`coredns_dns_request_duration_seconds_sum`), errors (`coredns_dns_response_rcode_count_total`, NXDOMAIN, SERVFAIL, FormErr) and CoreDNS Pod’s memory consumption. 

For troubleshooting purposes, you can use kubectl to view CoreDNS logs:

`for p in $(kubectl get pods —namespace=kube-system -l k8s-app=kube-dns -o name); do kubectl logs —namespace=kube-system $p; done`

### Use NodeLocal DNSCache
You can improve the Cluster DNS performance by running [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/). This feature runs a DNS caching agent on cluster nodes as a DaemonSet. All the pods use the DNS caching agent running on the node for name resolution instead of using `kube-dns` Service. 

### Configure cluster-proportional-scaler for CoreDNS

Another method of improving Cluster DNS performance is by [automatically horizontally scaling the CoreDNS Deployment](https://kubernetes.io/docs/tasks/administer-cluster/dns-horizontal-autoscaling/#enablng-dns-horizontal-autoscaling) based on the number of nodes and CPU cores in the cluster. [Horizontal cluster-proportional-autoscaler](https://github.com/kubernetes-sigs/cluster-proportional-autoscaler/blob/master/README.md) is a container that resizes the number of replicas of a Deployment based on the size of the schedulable data-plane. 

Nodes and the aggregate of CPU cores in the nodes are the two metrics with which you can scale CoreDNS. You can use both metrics simultaneously. If you use larger nodes, CoreDNS scaling is based on the number of CPU cores. Whereas, if you use smaller nodes, the number of CoreDNS replicas depends on the  CPU cores in your data-plane. Proportional autoscaler configuration looks like this:

```
linear: '{"coresPerReplica":256,"min":1,"nodesPerReplica":16}'
```
