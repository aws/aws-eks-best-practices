# Networking in EKS

EKS uses Amazon VPC to provide networking capabilities to worker nodes and Kubernetes Pods. An EKS cluster consists of two VPCs: one VPC managed by AWS that hosts the Kubernetes control plane and a second VPC managed by customers that hosts the Kubernetes worker nodes where containers run, as well as other AWS infrastructure (like load balancers) used by the cluster. All worker nodes need the ability to connect to the managed API server endpoint. This connection allows the worker node to register itself with the Kubernetes control plane and to receive requests to run application pods.

Worker nodes connect to the EKS control plane through the EKS public endpoint or EKS-managed elastic network interfaces (ENIs). The subnets that you pass when you create the cluster influence where places these ENIs. You need to provide a minimum of two subnets in at least two Availability Zones. The route that worker nodes take to connect is determined by whether you have enabled or disabled the private endpoint for your cluster. EKS-managed ENI are used for all control plane to worker node communication

> Insert a diagram about how control plane and worker nodes communicate.

Refer to [Cluster VPC considerations](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html) when architecting a VPC to be used with EKS.

If you deploy worker nodes in private subnets then these subnets should have a default route to a [NAT Gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html). 

## Recommendations
- A VPC with public and private subnets is recommended so that Kubernetes can create load balancers in public subnets and the worker nodes can run in private subnets.
- If you deploy worker nodes in private subnets then consider creating a NAT Gateway in each Availability Zone to ensure zone-independent architecture. Each NAT gateway is created in a specific Availability Zone and implemented with redundancy in that zone.


## Amazon VPC CNI
Amazon EKS supports native VPC networking via the [Amazon VPC Container Network Interface (CNI)](https://github.com/aws/amazon-vpc-cni-k8s) plugin for Kubernetes. The CNI plugin allows Kubernetes Pods to have the same IP address inside the Pod as they do on the VPC network.The CNI plugin uses [Elastic Network Interface (ENI)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html) for Pod networking. The CNI allocates ENIs to each Kubernetes node and using the secondary IP range from each ENI for pods on the node. The CNI includes controls for pre-allocation of ENIs and IP addresses for fast pod startup time.

The [maximum number of network interfaces, and the maximum number of private IPv4 addresses](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI) that you can use varies by the type of EC2 Instance. Since each Pod uses an IP address, the number of Pods you can run on a particular EC2 Instance depends on how many ENIs can be attached to it and how many IP addresses it supports.

The CNI plugin has two componenets:

* [CNI plugin](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/#cni), which will wire up host’s and pod’s network stack when called.
* `L-IPAMD` (aws-node DaemonSet) runs on every node is a long running node-Local IP Address Management (IPAM) daemon and is responsible for:
    * maintaining a warm-pool of available IP addresses, and
    * assigning an IP address to a Pod.
    
The details can be found in [Proposal: CNI plugin for Kubernetes networking over AWS VPC](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/cni-proposal.md).

By default, the CNI assigns Pod’s IP address from the worker node's primary elastic network interface's (ENI) security groups and subnet. If you don’t have enough IP addresses in the worker node subnet or if you worker nodes and Pods in different subnets then you can use [CNI custom networking](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html).

## CNI custom networking

Creating a separate subnet for Pods can prevent any IP address conflicts with other resources in your VPC. 

> You can customize AWS VPC CNI behavior through [CNI configuration variables](https://docs.aws.amazon.com/eks/latest/userguide/cni-env-vars.html). 
 
If you want the CNI to assign IP addresses for Pods from a different subnet CIDR you can set `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG` environment variable to `true`.

```bash
kubectl set env daemonset aws-node -n kube-system AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true
```

> EKS managed node groups currently don’t support custom networking option. 


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

You will need to create an `ENIconfig` custom resource for each subnet you want to use for Pod networking. The `securityGroups` field should have the ID of the security group that is attached to the worker nodes. The `name` field should be the name of the Availability Zone in your VPC. If you name your ENIConfig custom resources after each Availability Zone in your VPC then you can enable Kubernetes to automatically apply the corresponding ENIConfig for the worker node's Availability Zone with the following command.

```shell
kubectl set env daemonset aws-node \
-n kube-system ENI_CONFIG_LABEL_DEF=failure-domain.beta.kubernetes.io/zone
```

Upon creating the `ENIconfig` custom resources you will need to create new worker nodes. The existing worker nodes and Pods will remain unaffected. 

You will also need to calculate the maximum number of Pods that can be scheduled on each worker node and pass it in worker nodes’ user-data script.

To determine the number of Pods for each worker node you will need to know [the number of network interfaces and the IPv4 addresses per network interface the worker node supports](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI). The formula for calculating maximum number of pods for an EC2 instance is:
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


### Limit IP address and ENI allocation (WIP)

> https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html

The CNI caches a certain number of IP addresses so that Kubernetes scheduler can schedule pods on these worker nodes. The IP addresses are available on the worker nodes whether you launch pods or not. 

If you need to constrain these IP addresses, you can customize them at the worker node level. The CNI supports customization of a number of configurations options, these options are set through environment variables. To configure these options, you can download aws-k8s-cni.yaml compatible with your cluster and set environment variables. At the time of writing, the latest release is located [here](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/v1.6/aws-k8s-cni.yaml).

## Recommendations
- Size the subnets you will use for Pod networking for growth. If you have insufficient IP addresses available in the subnet that the CNI uses, your pods will not get an IP address. And the pods will remain in pending state until an IP address is available.
- Consider using [CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html) to monitor the number of IP addresses. 
- If your cluster has high pod churn rate, then consider creating [separate subnets for Pod networking](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html) in each Availability Zone. Doing so will prevent IP address allocation conflicts with other resources in the VPC. 
- If you need to constrain IPs then use `blah` variable. 

## External SNAT (WIP)

## Alternate CNI plugins


---

Things to add:
* you need two subnets to for eks owned eni
* Amazon EKS does not automatically upgrade the CNI plugin on your cluster when new versions are released. To get a newer version of the CNI plugin on existing clusters, you must manually upgrade the plugin.
* https://docs.aws.amazon.com/eks/latest/userguide/alternate-cni-plugins.html