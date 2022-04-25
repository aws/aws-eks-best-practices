# Kubernetes Networking

Networking is a crucial component in Kubernetes. Pod-to-Pod networking also known as cluster networking is central part of Kubernetes and is focus of this guide. Kubernetes makes opinionated choices about how Pods are networked. In particular, Kubernetes dictates the following requirements on cluster networking.

* Pods scheduled on the same node must be able to communicate with other Pods without using NAT (Network Address Translation).
* All system daemons (background processes, for example, [kubelet](https://kubernetes.io/docs/concepts/overview/components/) running on a particular node can communicate with the Pods running on the same node.
* Pods that use the [host network](https://docs.docker.com/network/host/) must be able to contact all other Pods on all other nodes without using NAT.

The Kubernetes network model defines a “flat” network and uses an IP per Pod model to meet the above requirements. Every Pod gets its own IP address and communicates with other Pods using IP addresses, reducing the complexity of mapping container ports to host ports. A Pod is modeled as a group of containers that share a network namespace, including their IP address and MAC address. Containers within a Pod all have the same IP address and port space assigned through the network namespace assigned to the Pod, and can find each other via localhost since they reside in the same namespace.

This creates a clean, backwards-compatible model where pods can be treated much like VMs or physical hosts from the perspectives of port allocation, naming, service discovery, load balancing, application configuration, and migration. Network segmentation can be defined using network policies to restrict traffic within these base networking capabilities.

## Kubernetes Network Model

There are many different ways to implement the Kubernetes networking model. One of the most common ways to implement the Kubernetes networking model is by using the CNI (Container Networking Interface) API. CNI (Container Network Interface) is a standard API which allows different network implementations to plug into Kubernetes. CNI consists of a CNI specification, a set of references, and sample plugins. There are many different kinds of CNI plugins, but the two main ones are:

* Network plugins: responsible for adding or deleting pods to/from the Kubernetes pod network. This includes creating/deleting each pod’s network interface and connecting/disconnecting it to the rest of the network implementation.
* IPAM (IP Address Management) plugins: which are responsible for allocating and releasing IP addresses for pods as they are created and deleted. Depending on the plugin, this may include one or more interfaces and ranges of IP addresses (CIDRs) to each node, allocate to pods.

The CNI plugin is selected by Kubelet when --network-plugin command-line option is set as CNI. Kubelet reads a file from --cni-conf-dir (default /etc/cni/net.d) and uses the CNI configuration from that file to set up each Pod's network. The CNI configuration file must match the CNI specification (v0.4.0) and any required CNI plugins referenced by the configuration must be present in --cni-bin-dir (default /opt/cni/bin). If there are multiple CNI configuration files in the directory, the kubelet uses the configuration file that comes first by name in lexicographic order.

## Kubernetes Services

### kube-proxy

## Kubernetes & DNS
