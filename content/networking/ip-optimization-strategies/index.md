# Optimizing IP Address Utilization 

Containerized environments are growing in scale at a rapid pace, thanks to application modernization. This means that more and more worker nodes and pods are being deployed.

The [Amazon VPC CNI](../vpc-cni/) plugin assigns each pod an IP address from the VPC CIDR(s). This approach provides full visibility of the Pod addresses with tools such as VPC Flow Logs and other monitoring solutions. On the other hand, depending on your workload type this can cause a substantial number of IP addresses to be consumed by the pods.

Therefore, when designing your AWS networking architecture, it is important to optimize Amazon EKS IP consumption at the VPC and at the node level. This will help you mitigate IP exhaustion issues and increase the pod density per node.

In this section, we will discuss techniques that can help you achieve these goals.

## Optimize node-level IP consumption
 
[Prefix delegation](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html) is a feature of Amazon Virtual Private Cloud (Amazon VPC) that allows you to assign IPv4 or IPv6 prefixes to your Amazon Elastic Compute Cloud (Amazon EC2) instances. It enables increased IP addresses on a network interface thus increases pod density per node and improves compute efficiency. Prefix delegation is also supported with Custom Networking. 

For detailed information please see [Prefix Delegation with Linux nodes](../prefix-mode/index_linux/) and [Prefix Delegation with Windows nodes](../prefix-mode/index_windows/) sections.

## Mitigate IP exhaustion

To prevent your clusters from consuming all available IP addresses, we strongly recommend sizing your VPCs and subnets with growth in mind. 

Adopting [IPv6](../ipv6/) is a great way to avoid these problems from the very beginning. However, for organizations whose scalability needs exceed the initial planning and cannot adopt IPv6, improving the VPC design is the recommended response to IP address exhaustion. The most commonly used technique among Amazon EKS customers is adding non-routable Secondary CIDRs to the VPC and configure pods to consume this additional IP space with Amazon EKS. This is referred in our documentation as [Custom Networking](../custom-networking/). 

We will also cover which variables of the Amazon VPC CNI you can use to optimize the warm pool of IPs assigned to your nodes. We will close this section with some other architectural patterns that are not intrinsic to Amazon EKS but can help mitigate IP exhaustion.


### Use IPv6 (recommended)

Adopting IPv6 is the easiest way to work around RFC1918 limitations; we strongly recommend to consider adopting IPv6 as your first option when choosing network architectures. IPv6 provides a significantly larger total IP address space, and Kubernetes cluster administrators can focus on migrating and scaling applications without devoting effort towards working around IPv4 limits.

Amazon EKS clusters support both IPv4 and IPv6. By default, EKS clusters use IPv4 address space. Specifying IPv6 based address space at cluster creation time will enable the use of IPv6 clusters. In an IPv6 EKS cluster, pods and services will receive IPv6 addresses while **maintaining the ability for legacy IPv4 endpoints to connect to services running on IPv6 clusters and viceversa**. All the pod-to-pod communication within a cluster is always IPv6. Within a VPC (/56), the IPv6 CIDR block size for IPv6 subnets is fixed at /64. This provides 2^64 (approximately 18 quintillion) IPv6 addresses allowing to scale your deployments on EKS. P

For detailed information please see the [Running IPv6 EKS Clusters](../ipv6/) section and for hands-on experience please see the [Understanding IPv6 on Amazon EKS](https://catalog.workshops.aws/ipv6-on-aws/en-US/lab-6) section of the [Get hands-on with IPv6 workshop](https://catalog.workshops.aws/ipv6-on-aws/en-US).

![EKS Cluster in IPv6 Mode, traffic flow](./ipv6.gif)


### Optimize IP consumption in IPv4 clusters

This section is dedicated to customers that are running legacy applications, and/or are not ready to migrate to IPv6. While we encourage all organizations to migrate to IPv6 as soon as possible, we recognize that some may still need to look into alternative approaches to scale their container workloads with IPv4. For this reason, we will also walk you through the architectural patterns to optimize IPv4 (RFC1918) address space consumption with Amazon EKS clusters.

#### Plan for Growth

As a first line of defense against IP exhaustion, we strongly recommend to size your IPv4 VPCs and subnets with growth in mind, to prevent your clusters to consume all the available IP addresses. You will not be able to create new Pods or nodes if the subnets don’t have enough available IP addresses. 

Before building VPC and subnets, it is advised to work backwards from the required workload scale. For example, when clusters are built using “eksctl” (a simple CLI tool for creating and managing clusters on EKS) /19 subnets are created by default. A netmask of /19 is suitable for the majority of workload types allowing more than 8000 addresses to be allocated.

It should be noted, that when you size VPCs and subnets, there might be a number of elements (other than pods and nodes) which can consume IP addresses, for example Load Balancers, RDS Databases and other in-vpc services. 
Additionally, Amazon EKS, can create up to 4 elastic network interfaces (X-ENI) that are required to allow communication towards the control plane (more info [here](../subnets/)). During cluster upgrades, Amazon EKS creates new X-ENIs and deletes the old ones when the upgrade is successful. For this reason we recommend a netmask of at least /28 (16 IP addresses) for subnets associated with an EKS cluster.

You can use the [sample EKS Subnet Calculator](../subnet-calc/subnet-calc.xlsx) spreadsheet to plan for your network. The spreadsheet calculates IP usage based on workloads and VPC ENI configuration. The IP usage is compared to an IPv4 subnet to determine if the configuration and subnet size is sufficient for your workload. Keep in mind that, if subnets in your VPC run out of available IP addresses, we suggest [creating a new subnet](https://docs.aws.amazon.com/vpc/latest/userguide/working-with-subnets.html#create-subnets) using the VPC’s original CIDR blocks. Notice that now [Amazon EKS now allows modification of cluster subnets and security groups](https://aws.amazon.com/about-aws/whats-new/2023/10/amazon-eks-modification-cluster-subnets-security/).

#### Custom networking 

This pattern allows you to conserve routable IPs by scheduling Pods inside dedicated additional subnets. 
While custom networking will accept valid VPC range for secondary CIDR range, we recommend that you use CIDRs (/16) from the CG-NAT space, i.e. `100.64.0.0/10` or `198.19.0.0/16` as those are less likely to be used in a corporate setting than RFC1918 ranges. 

For detailed information please see the dedicated section for [Custom Networking](../custom-networking/).

![Custom Networking, traffic flow](./custom-networking.gif)

#### Configure CNI environment variables

With the default configuration, the VPC CNI keeps an entire ENI (and associated IPs) in the warm pool. This may consume a large number of IPs, especially on larger instance types.

If your cluster subnet has a limited number of IP addresses available, scrutinize these VPC CNI configuration environment variables:

* `WARM_IP_TARGET`
* `MINIMUM_IP_TARGET`
* `WARM_ENI_TARGET`

You can configure the value of `MINIMUM_IP_TARGET` to closely match the number of Pods you expect to run on your nodes. Doing so will ensure that as Pods get created, and the CNI can assign IP addresses from the warm pool without calling the EC2 API.

Please be mindful that setting the value of `WARM_IP_TARGET` too low, will cause additional calls to the EC2 API, and that might cause throttling of the requests. For large clusters use along with `MINIMUM_IP_TARGET` to avoid throttling of the requests.

To configure these options, you can download the `aws-k8s-cni.yaml` manifest and set the environment variables. At the time of writing, the latest release is located [here](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/master/aws-k8s-cni.yaml). Check the version of the configuration value matches the installed VPC CNI version.

!!! Warning
    These settings will be reset to defaults when you update the CNI. Please take a backup of the CNI, before you update it. Review the configuration settings to determine if you need to reapply them after update is successful.

You can adjust the CNI parameters on the fly without downtime for your existing applications, but you should choose values that will support your scalability needs. As an example, if you're working with batch workloads, we recommend updating the default `WARM_ENI_TARGET` to match the Pod scale needs. Moreover, setting `WARM_ENI_TARGET` to a high value always maintains the warm IP pool required to run large batch workloads and hence avoid data processing delays. 

!!! warning
    Improving your VPC design is the recommended response to IP address exhaustion. Consider solutions like IPv6 and Secondary CIDRs. Adjusting these values to minimize the number of Warm IPs should be a temporary solution after other options are excluded. Misconfiguring these values may interfere with cluster operation. 

    **Before making any changes to a production system**, be sure to review the considerations on [this page](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/eni-and-ip-target.md).

#### Monitor IP Address Inventory

In addition to the solutions described above, it is also important to have visibility over IP utilization. You can monitor the IP addresses inventory of subnets using [CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html). Some of the metrics available are:

* maximum number of ENIs the cluster can support
* number of ENIs already allocated
* number of IP addresses currently assigned to Pods
* total and maximum number of IP address available

You can also set [CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) to get notified if a subnet is running out of IP addresses. Please visit EKS user guide for install instructions of [CNI metrics helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html) 

!!! warning
    Make sure `DISABLE_METRICS` variable for VPC CNI is set to false.

#### Further considerations

There are other architectural patterns not intrinsic to Amazon EKS that can help with IP exhaustion. For example, you can [optimize communication across VPCs](../subnets/#communication-across-vpcs) or [share a VPC across multiple accounts](../subnets/#sharing-vpc-across-multiple-accounts) to limit the IPv4 address allocation. 

Learn more about these patterns here:

* [Designing hyperscale Amazon VPC networks](https://aws.amazon.com/blogs/networking-and-content-delivery/designing-hyperscale-amazon-vpc-networks/),
* [Build secure multi-account multi-VPC connectivity with Amazon VPC Lattice](https://aws.amazon.com/blogs/networking-and-content-delivery/build-secure-multi-account-multi-vpc-connectivity-for-your-applications-with-amazon-vpc-lattice/).