---
redirect: https://docs.aws.amazon.com/eks/latest/best-practices/networking.html
---


!!! info "We've Moved to the AWS Docs! 🚀"
    This content has been updated and relocated to improve your experience. 
    Please visit our new site for the latest version:
    [AWS EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/networking.html) on the AWS Docs

    Bookmarks and links will continue to work, but we recommend updating them for faster access in the future.

---

# Amazon EKS Best Practices Guide for Networking

It is critical to understand Kubernetes networking to operate your cluster and applications efficiently. Pod networking, also called the cluster networking, is the center of Kubernetes networking. Kubernetes supports [Container Network Interface](https://github.com/containernetworking/cni) (CNI) plugins for cluster networking. 

Amazon EKS officially supports [Amazon Virtual Private Cloud (VPC)](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) CNI plugin to implement Kubernetes Pod networking. The VPC CNI provides native integration with AWS VPC and works in underlay mode. In underlay mode, Pods and hosts are located at the same network layer and share the network namespace. The IP address of the Pod is consistent from the cluster and VPC perspective. 

This guide introduces the [Amazon VPC Container Network Interface](https://github.com/aws/amazon-vpc-cni-k8s)[(VPC CNI)](https://github.com/aws/amazon-vpc-cni-k8s) in the context of Kubernetes cluster networking. The VPC CNI is the default networking plugin supported by EKS and hence is the focus of the guide. The VPC CNI is highly configurable to support different use cases. This guide further includes dedicated sections on different VPC CNI use cases, operating modes, sub-components, followed by the recommendations.

Amazon EKS runs upstream Kubernetes and is certified Kubernetes conformant. Although you can use alternate CNI plugins, this guide does not provide recommendations for managing alternate CNIs. Check the [EKS Alternate CNI](https://docs.aws.amazon.com/eks/latest/userguide/alternate-cni-plugins.html) documentation for a list of partners and resources for managing alternate CNIs effectively.

## Kubernetes Networking Model

Kubernetes sets the following requirements on cluster networking:

* Pods scheduled on the same node must be able to communicate with other Pods without using NAT (Network Address Translation).
* All system daemons (background processes, for example, [kubelet](https://kubernetes.io/docs/concepts/overview/components/)) running on a particular node can communicate with the Pods running on the same node.
* Pods that use the [host network](https://docs.docker.com/network/host/) must be able to contact all other Pods on all other nodes without using NAT.

See [the Kubernetes network model](https://kubernetes.io/docs/concepts/services-networking/#the-kubernetes-network-model) for details on what Kubernetes expects from compatible networking implementations. The following figure illustrates the relationship between Pod network namespaces and the host network namespace.


![illustration of host network and 2 pod network namespaces](image.png)
## Container Networking Interface (CNI)

Kubernetes supports CNI specifications and plugins to implement Kubernetes network model. A CNI consists of a [specification](https://github.com/containernetworking/cni/blob/main/SPEC.md) (current version 1.0.0) and libraries for writing plugins to configure network interfaces in containers, along with a number of supported plugins. CNI concerns itself only with network connectivity of containers and removing allocated resources when the container is deleted. 

The CNI plugin is enabled by passing kubelet the `--network-plugin=cni` command-line option. Kubelet reads a file from `--cni-conf-dir` (default /etc/cni/net.d) and uses the CNI configuration from that file to set up each Pod's network. The CNI configuration file must match the CNI specification (minimum v0.4.0) and any required CNI plugins referenced by the configuration must be present in the `--cni-bin-dir` directory (default /opt/cni/bin). If there are multiple CNI configuration files in the directory, *the kubelet uses the configuration file that comes first by name in lexicographic order*.


## Amazon Virtual Private Cloud (VPC) CNI

The AWS-provided VPC CNI is the default networking add-on for EKS clusters. VPC CNI add-on is installed by default when you provision EKS clusters. VPC CNI runs on Kubernetes worker nodes. The VPC CNI add-on consists of the CNI binary and the IP Address Management (ipamd) plugin. The CNI assigns an IP address from the VPC network to a Pod. The ipamd manages AWS Elastic Networking Interfaces (ENIs) to each Kubernetes node and maintains the warm pool of IPs. The VPC CNI provides configuration options for pre-allocation of ENIs and IP addresses for fast Pod startup times. Refer to [Amazon VPC CNI](../vpc-cni/index.md) for recommended plugin management best practices.

Amazon EKS recommends you specify subnets in at least two availability zones when you create a cluster. Amazon VPC CNI allocates IP addresses to Pods from the node subnets. We strongly recommend checking the subnets for available IP addresses. Please consider [VPC and Subnet](../subnets/index.md) recommendations before deploying EKS clusters. 

Amazon VPC CNI allocates a warm pool of ENIs and secondary IP addresses from the subnet attached to the node's primary ENI. This mode of VPC CNI is called the "[secondary IP mode](../vpc-cni/index.md)." The number of IP addresses and hence the number of Pods (Pod density) is defined by the number of ENIs and the IP address per ENI (limits) as defined by the instance type. The secondary mode is the default and works well for small clusters with smaller instance types. Please consider using [prefix mode](../prefix-mode/index_linux.md) if you are experiencing pod density challenges. You can also increase the available IP addresses on node for Pods by assigning prefixes to ENIs.

Amazon VPC CNI natively integrates with AWS VPC and allows users to apply existing AWS VPC networking and security best practices for building Kubernetes clusters. This includes the ability to use VPC flow logs, VPC routing policies, and security groups for network traffic isolation. By default, the Amazon VPC CNI applies security group associated with the primary ENI on the node to the Pods. Consider enabling [security groups for Pods](../sgpp/index.md) when you would like to assign different network rules for a Pod.

By default, VPC CNI assigns IP addresses to Pods from the subnet assigned to the primary ENI of a node. It is common to experience a shortage of IPv4 addresses when running large clusters with thousands of workloads. AWS VPC allows you to extend available IPs by [assigning a secondary CIDRs](https://docs.aws.amazon.com/vpc/latest/userguide/configure-your-vpc.html#add-cidr-block-restrictions) to work around exhaustion of IPv4 CIDR blocks. AWS VPC CNI allows you to use a different subnet CIDR range for Pods. This feature of VPC CNI is called [custom networking](../custom-networking/index.md). You might consider using custom networking to use 100.64.0.0/10 and 198.19.0.0/16 CIDRs (CG-NAT) with EKS. This effectively allows you to create an environment where Pods no longer consume any RFC1918 IP addresses from your VPC.

Custom networking is one option to address the IPv4 address exhaustion problem, but it requires operational overhead. We recommend IPv6 clusters over custom networking to resolve this problem. Specifically, we recommend migrating to [IPv6 clusters](../ipv6/index.md) if you have completely exhausted all available IPv4 address space for your VPC. Evaluate your organization's plans to support IPv6, and consider if investing in IPv6 may have more long-term value. 

EKS's support for IPv6 is focused on solving the IP exhaustion problem caused by a limited IPv4 address space. In response to customer issues with IPv4 exhaustion, EKS has prioritized IPv6-only Pods over dual-stack Pods. That is, Pods may be able to access IPv4 resources, but they are not assigned an IPv4 address from VPC CIDR range. The VPC CNI assigns IPv6 addresses to Pods from the AWS managed VPC IPv6 CIDR block. 

## Subnet Calculator

This project includes a [Subnet Calculator Excel Document](../subnet-calc/subnet-calc.xlsx). This calculator document simulates the IP address consumption of a specified workload under different ENI configuration options, such as `WARM_IP_TARGET` and `WARM_ENI_TARGET`. The document includes two sheets, a first for Warm ENI mode, and a second for Warm IP mode. Review the [VPC CNI guidance](../vpc-cni/index.md) for more information on these modes. 

Inputs:
- Subnet CIDR Size
- Warm ENI Target *or* Warm IP Target
- List of instances
    - type, number, and number of workload pods scheduled per instance

Outputs:
- Total number of pods hosted
- Number of Subnet IPs consumed
- Number of Subnet IPs remaining
- Instance Level Details
    - Number of Warm IPs/ENIs per instance
    - Number of Active IPs/ENIs per instance

