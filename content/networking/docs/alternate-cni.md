# Using Aletrenate CNI Plugins

AWS VPC CNI plugin is the only officially supported [network plugin](https://kubernetes.io/docs/concepts/cluster-administration/networking/) on EKS. However, since EKS runs upstream Kubernetes and is certified Kubernetes conformant, you can use alternate [CNI plugins](https://github.com/containernetworking/cni).

A compelling reason to opt for an alternate CNI plugin is to run Pods without using a VPC IP address per Pod. Although, using an alternate CNI plugin can come at the expense of network performance. 

Refer to EKS documentation for the list [alternate compatible CNI plugins](https://docs.aws.amazon.com/eks/latest/userguide/alternate-cni-plugins.html). Consider obtaining the CNI vendor’s commercial support if you plan on using an alternate CNI in production.
