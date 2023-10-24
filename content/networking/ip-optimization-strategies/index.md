# IP Consumption Optimization

Containerized environments are growing in scale at a rapid pace, thanks to application modernization. This means that more and more worker nodes and pods are being deployed.

The [Amazon VPC CNI](https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/) plugin assigns each pod an IP address from the VPC CIDR(s), which can consume a lot of IP addresses from your VPCs.

Therefore, when designing your AWS networking architecture, it is important to optimize EKS IP consumption at the VPC and node level. This will help you avoid IP exhaustion and increase the pod density per node.

In this section, we will discuss techniques that can help you achieve these goals.

## Avoid IP exhaustion

### Use IPv6 (recommended)

!!! SECTIONS_USED_OR_MOVED
    - IPv6 first (why etc etc): https://aws.github.io/aws-eks-best-practices/networking/ipv6/ /link/

Adopting IPv6 is the easiest way to work around RFC1918 limitations, for this reason we strongly recommend to consider adopting IPv6 as your first option when discussing IP exhaustion architectures. 

Amazon EKS clusters support both IPv4 and IPv6. By default, EKS clusters use IPv4 IP. Specifying IPv6 at cluster creation time will enable the use IPv6 clusters. In an IPv6 EKS cluster, pods and services will receive IPv6 addresses while **maintaining the ability for legacy IPv4 endpoints** to connect to services running on IPv6 clusters, as well as pods connecting to legacy IPv4 endpoints outside the cluster. All the pod-to-pod communication within a cluster is always IPV6. Within a VPC (/56), the IPv6 CIDR block size for IPv6 subnets is fixed at /64. This provides 2^64 (approximately 18 quintillion) IPv6 addresses allowing to scale your deployments on EKS. Please, check in the EKS Best Practices [section dedicated to IPv6](https://aws.github.io/aws-eks-best-practices/networking/ipv6/) for more details.

### How to optimize IP consupmtion IPv4 clusters

**REWRITE**
This section is dedicated to organizations that have the requirement to stay on IPv4, for example moving to IPv6 means for you a major reingeneering or refactor of your applications. While we encourage all organizations to migrate to IPv6 as soon as possible, we recognize that some may still need to look into alternative approaches to scale their container workloads with IPv4. For that purpose, we will also walk you through the architectural patterns to optimize IPv4 (RFC1918) address space consumption with Amazon EKS clusters.

#### Plan for Growth

!!! SECTIONS_USED_OR_MOVED
    - [Plan for Growth](https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#plan-for-growth) /moved/
    - [Check available IPs](https://aws.github.io/aws-eks-best-practices/networking/subnets/#check-available-ips) /moved/

As first line in defense against IP exhaustion, we strongly recommend to size your IPv4 VPC and subnets for growth to prevent your clusters to consume all the available IP addresses. You will not be able to create new Pods or nodes if the subnets don’t have enough available IP addresses. 

Before building VPC and subnets, it is advised to work backwards from the required workload scale. When clusters are built using “ekstcl”, /19 subnets are created by default. A netmask of /19 is suitable for the majority of workload types.

When you size your VPCs and subnets there are a number of elements other than number of pods and nodes that consume IPs (e.g.Load Balancers, X-ENIs). X-ENI interfaces can be up to 4 elastic network interfaces created by Amazon EKS in the cluster subnets. When you upgrade the cluster, Amazon EKS creates new X-ENIs and deletes the old ones when the upgrade is successful. For this reason we recommend a netmask of /28 (16 IP addresses) for cluster subnets to accommodate upgrades of the cluster.

Use the [sample EKS Subnet Calculator](../subnet-calc/subnet-calc.xlsx) spreadsheet to plan your network. The spreadsheet calculates IP usage based on workloads and VPC ENI configuration. The IP usage is compared to an IPv4 subnet to determine if the configuration and subnet size is sufficient for your workload. Keep in mind that, if subnets in your VPC run out of available IP addresses, we suggest [creating a new subnet](https://docs.aws.amazon.com/vpc/latest/userguide/working-with-subnets.html#create-subnets) using the VPC’s original CIDR blocks.

#### Configure warm pool CNI environment variables

!!! SECTIONS_USED_OR_MOVED
    - CNI Parameters explained: https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#overview /link/
    - https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#configure-ip-and-eni-target-values-in-address-constrained-environments /moved/

/**REVIEW THIS WORDING. WHY A SECONDARY SOLUTION TO SECONDARY CIDRS??? I UNDERSTAND IPV6, BUT IN MANY CASES THIS SUFFICES AND SECONDARY CIDRS IS A CONFIGURATIONS THAT IS NOT STILL THAT AUTOMATIZED TO BE ADOPTED RAPIDLY BY CUSTOMERS**/

!!! warning
    Improving your VPC design is the recommended response to IP address exhaustion. Consider solutions like IPv6 and Secondary CIDRs. Adjusting these values to minimize the number of Warm IPs should be a temporary solution after other options are excluded. Misconfiguring these values may interfere with cluster operation.

In the default configuration, VPC CNI keeps an entire ENI (and associated IPs) in the warm pool. This may consume a large number of IPs, especially on larger instance types.

If your cluster subnet has a limited number of free IP addresses, scrutinize these VPC CNI configuration environment variables:

* `WARM_IP_TARGET`
* `MINIMUM_IP_TARGET`
* `WARM_ENI_TARGET`

Configure the value of `MINIMUM_IP_TARGET` to closely match the number of Pods you expect to run on your nodes. Doing so will ensure that as Pods get created, and the CNI can assign IP addresses from the warm pool without calling the EC2 API.

Avoid setting the value of `WARM_IP_TARGET` too low as it will cause additional calls to the EC2 API, and that might cause throttling of the requests. For large clusters use along with `MINIMUM_IP_TARGET` to avoid throttling of the requests.

To configure these options, download `aws-k8s-cni.yaml` and set the environment variables. At the time of writing, the latest release is located [here](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/master/aws-k8s-cni.yaml). Check the version of the configuration value matches the installed VPC CNI version.

!!! Warning
    The warm settings will be reset to defaults when you update the CNI. Please take a backup of the CNI, before you update the CNI. Review the configuration settings to determine if you need to reapply them after update is successful.

You can adjust the CNI parameters on the fly without downtime for your applications, but you should choose values that will support your scalability needs. For example, we recommend updating the default `WARM_ENI_TARGET` to match the Pod scale needs for batch workloads. Setting `WARM_ENI_TARGET` to a high value always maintains the warm IP pool required to run large batch workloads and hence avoid data processing delays. 

Before making any changes to a production system, be sure to review the considerations on [this page](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/eni-and-ip-target.md). 




#### Custom networking 

!!! SECTIONS_USED_OR_MOVED
    - https://aws.github.io/aws-eks-best-practices/networking/custom-networking/ /link/

This pattern allows you to conserve routable IPs by scheduling Pods inside dedicated additional subnets. 
While custom networking will accept valid VPC range for secondary CIDR range, we recommend that you use CIDRs (/16) from the CG-NAT space, i.e. `100.64.0.0/10` or `198.19.0.0/16` as those are less likely to be used in a corporate setting than RFC1918 ranges. For more information see [this section](https://aws.github.io/aws-eks-best-practices/networking/custom-networking/) of the EKS best practices.

#### Monitor IP Address Inventory

!!! SECTIONS_USED_OR_MOVED
    - [Monitor IP Address Inventory](https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#monitor-ip-address-inventory /moved/)

In addition to the solutions described above, it is also important to have visibility over IP utilization. You can monitor the IP addresses inventory of subnets using [CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html).

* maximum number of ENIs the cluster can support
* number of ENIs already allocated
* number of IP addresses currently assigned to Pods
* total and maximum number of IP address available

You can also set [CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) to get notified if a subnet is running out of IP addresses. Please visit EKS user guide for install instructions of [CNI metrics helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html). Make sure DISABLE_METRICS variable for VPC CNI is set to false.

#### Other things that help with IP exhastion relying on AWS networking (NAT GW,VPC Sharing, privatelink VPC Lattice) 

!!! SECTIONS_USED_OR_MOVED
    - [guidance-on-designing-hyperscale-vpcs](https://aws.github.io/aws-eks-best-practices/networking/subnets/#guidance-on-designing-hyperscale-vpcs) /moved/
    - NAT GW, privatelink: [Communication Across VPCs](https://aws.github.io/aws-eks-best-practices/networking/subnets/#communication-across-vpcs) /link/ !!! ADD VPC LATTICE TO THIS SECTION!!!!
    - VPC Sharing: [Sharing VPC across multiple accounts](https://aws.github.io/aws-eks-best-practices/networking/subnets/#sharing-vpc-across-multiple-accounts) /link/

An environment can be considered “Hyperscale” once it supports thousands of application endpoints and tens or hundreds of gigabits of traffic per second. 

When operating at Hyperscale, additional planning is required for network connectivity, security, private IPv4 address scarcity and overlap. Hyperscale network design involves leveraging cell-based infrastructure units, and understanding the benefits and limitations of each of the various AWS networking services.

Learn more about [Designing Hyperscale Amazon VPC networks](https://aws.amazon.com/blogs/networking-and-content-delivery/designing-hyperscale-amazon-vpc-networks/) on the AWS Networking & Content Delivery Blog. 


/**BLURB ABOUT NAT GW, PRIVATELINK**/ Check this section of the EKS Best Practices for more information:[Communication Across VPCs](https://aws.github.io/aws-eks-best-practices/networking/subnets/#communication-across-vpcs) /link/ /**ADD VPC LATTICE TO THIS SECTION!**/

/**BLURB ABOUT NAT GW, PRIVATELINK**/ Check this section of the EKS Best Practices for more information: [Sharing VPC across multiple accounts](https://aws.github.io/aws-eks-best-practices/networking/subnets/#sharing-vpc-across-multiple-accounts) /link/



## Optimize node-level IP consumption

!!! SECTIONS_USED_OR_MOVED
    - https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/index_linux/ /link/
    - https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/index_windows/ /link/

Prefix delegation is a feature of Amazon Virtual Private Cloud (Amazon VPC) that allows you to assign IPv4 or IPv6 prefixes to your Amazon Elastic Compute Cloud (Amazon EC2) instances. This can improve your efficiency, reduce your costs, and give you more flexibility. Prefix delegation can improve your efficiency in a number of ways. For example, it can help you to better utilize your instances. When you use prefix delegation, you can assign each instance a larger IP address range. This means that you can fit more pods on each instance, which can improve your pod density and IP utilization. Prefix delegation is flexible and can be used with both IPv6 and custom networking. 

- Check this section of the EKS Best Practices for more information on how to [implement Prefix Delegation with Linux nodes](https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/index_linux/). 

- Check this section of the EKS Best Practices for more information on how to [implement Prefix Delegation with Windows nodes](https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/index_windows/). 

#### Use Secondary IP Mode when

!!! SECTIONS_USED_OR_MOVED
    - https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#use-secondary-ip-mode-when /moved/

Secondary IP mode is an ideal configuration option for ephemeral EKS clusters. Greenfield customers who are either new to EKS or in the process of migrating can take advantage of VPC CNI in secondary mode.

#### Avoid Secondary IP Mode when

!!! SECTIONS_USED_OR_MOVED
    - https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#avoid-secondary-ip-mode-when /moved/

If you are experiencing Pod density issues, we suggest enabling prefix mode. If you are facing IPv4 depletion issues, we advise migrating to IPv6 clusters. If IPv6 is not on the horizon, you may choose to use custom networking.

__________





