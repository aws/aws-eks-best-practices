# Networking in EKS

Kubernetes was designed to run distributed applications on a cluster of connected machines. Networking plays an integral part in orchestrating and running distributed applications in any Kubernetes environment. It is critical to understand the Kubernetes networking paradigm in order to build, run, and operate your applications efficiently. This section of the best practices advises on different cluster networking modes possible with EKS.

## How to use this guide?

This guide is meant for EKS cluster administrators, operators, and developers. Although the main aim of the guide is to provide guidance and recommendations about cluster networking operations supported by EKS. However, we have also tried to cover the [basic networking concepts](./networking.md) in the context of Kubernetes and [Kubernetes networking model](./k8s-networking.md). The guide covers EKS relevant [AWS Networking concepts] (./aws-networking.md). Through the [Amazon VPC Container Network Interface (CNI)](https://github.com/aws/amazon-vpc-cni-k8s) plugin, Amazon EKS handles cluster networking. Amazon EKS supports native VPC networking via the VPC CNI plugin for Kubernetes. 

Amazon VPC CNI supports different networking modes. You can use this guide to learn about different networking modes supported by EKS so you can choose the best option for your needs. We strongly recommend you learn about proposal and design of [Amazon VPC CNI](./vpc-cni.md) before considering the EKS cluster networking modes.

The guide is organized into different networking modes for easier consumption. Each topic begins with a brief overview, followed by use cases supported by each of the available modes, and a list of recommendations and best practices for ensuring the stability of your EKS clusters.

## Amazon VPC CNI and Configuration Modes

The [Amazon VPC CNI plugin] (./vpc-cni.md) offers networking for pods and enables Kubernetes Pods to have the same IP address on the VPC network and inside the pod. You may leverage Amazon VPC CNI's diverse modes and plugin configurations to address a variety of use cases, including:

* extending AWS native security group features to Pods
* increasing the number of IPs available to Pods
* enhancing Pod security by running Pods and nodes in different subnets
* allowing network seggregation via multi-homed pods
* scaling beyond IPv4 limits
* extending AWS native security group features to Pods
* supporting different Amazon EKS node and operating system types
* accelerating Pod launch times
* establishing tenant isolation and network segmentation

Teh networking modes supported by Amazon VPC CNI can be boradly classified as:

* Secondary IP Mode
* Prefix Delegation Mode
* Security Groups Per Pod
* Custom Networking
  
Amazon VPC CNI exposes different setting under each of the modes to accelerate Pod luanch times, and to support Pod churn rates. We will cover these setting under each of the modes and also recommended values for each of the settings.

By default, VPC CNI supports IPv4 cluster networking. However, if you are primarily concerned with resolving the IPv4 exhaustion issue, you can provision cluster in IPv6 mode. Please refer to the following section to understand the distinction between IPv6 support and upstream dual-stack. This tutorial intends to address both IPv6 migration recommended practices and IPv6 mechanics.

## Understanding IPv6 and Kubernetes Dual-Stack

Kubernetes IPv4/IPv6 dual-stack networking enables the allocation of both IPv4 and IPv6 addresses to Pods and Services. Wherein, EKS’s support for IPv6 is focused on resolving the IP exhaustion problem, which is constrained by the limited size of the IPv4 address space, a significant concern raised by a number of our customers and is distinct from Kubernetes’ “IPv4/IPv6 dual-stack” feature. Amazon EKS doesn't support dual-stacked pods or services. As a result, you can't assign both IPv4 and IPv6 addresses to your pods and services.

By default, EKS assigns IPv4 addresses to your Pods and Services. In an IPv6 EKS cluster, pods and services will receive IPv6 addresses. Amazon VPC CNI supports IPv6 in prefix assignment mode and assigns IPv6 address to Pods, while maintaining the ability for legacy IPv4 endpoints to connect to services running on IPv6 clusters, as well as pods connecting to legacy IPv4 endpoints outside the cluster.

This guide aims to cover the implementation details for IPv6 along with best practices for running and migrating to IPv6 cluster.

## Using Alternate CNI Plugins

AWS VPC CNI plugin is the only officially supported [network plugin](https://kubernetes.io/docs/concepts/cluster-administration/networking/) on EKS. VPC CNI provides native integration with AWS VPC and works in Undrelay mode. In Underlay mode, containers and hosts are located at the same network layer and share the same position. Network interconnection between containers depends on the underlying network. Using this plugin allows Kubernetes pods to have the same IP address inside the pod as they do on the VPC network.

However, since EKS runs upstream Kubernetes and is certified Kubernetes conformant, you can use alternate [CNI plugins](https://github.com/containernetworking/cni).Alternate CNIs works in overlay network mode over Amazon VPC.

An overlay network allows network devices to communicate across an underlying network (referred to as the underlay) without the underlay network having any knowledge of the devices connected to the overlay network. From the point of view of the devices connected to the overlay network, it looks just like a normal network. The overlay network takes a network packet, referred to as the inner packet, and encapsulating it inside an outer network packet. In this way the underlay sees the outer packets without needing to understand how to handle the inner packets. In Overlay mode, a container is independent of the host's IP address range. During cross-host communication, tunnels are established between hosts and all packets in the container CIDR block are encapsulated as packets exchanged between hosts in the underlying physical network. This mode removes the dependency on the underlying network.

How the overlay knows where to send packets varies by overlay type and the protocols they use. For example Weavenet and Flannel provides Layer2 and multicast support vs. Calico which uses BGP to program route tables and avoids packet encapsulation. A compelling reason to opt for an alternate CNI plugin is to run Pods without using a VPC IP address per Pod. Although, using an alternate CNI plugin can come at the expense of network performance which you might want to avoid if running network internsive workloads.

## Support for Multi-Homed Pods

Typically, in Kubernetes each pod only has one network interface (apart from a loopback). In certain situations, such as the telecommunications industry, Pods require multiple network interfaces to isolate signaling, media, and management networks. Multus CNI is a container network interface plugin for Kubernetes that enables attaching multiple network interfaces to Pods. With Multus, you can create multi-homed pods that have multiple interfaces. Multus acts as ‘meta’ plugin that can call other CNI plugins to configure additional interfaces.

Multiple network interfaces for pods are useful in various use cases; examples include:

* Traffic splitting: Running network functions (NF) that require separation of control/management, and data/user plane network traffic to meet low latency Quality of Service (QoS) requirements.
* Performance: Additional interfaces often leverage specialized hardware specifications such as Single Root I/O Virtualization (SR-IOV) and Data Plane Development Kit (DPDK), which bypass the operating system kernel for increased bandwidth and network performance.
* Security: Supporting multi-tenant networks with strict traffic isolation requirements. Connecting multiple subnets to pods to meet compliance requirements.

Multus section of this guide covers in detail on how to setup multi-homed Pods and best practices to run them at scale.