# IP Optimization strategies

Why you need to plan in advance for IP exhaustion and prepare VPCs for scale.


## Avoid IP exhaustion w/ IPv6

- IPv6 first (why etc etc): https://aws.github.io/aws-eks-best-practices/networking/ipv6/ /link/

## Otherwise if IPv4

VPC and Subnet 

- [Plan for Growth](https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#plan-for-growth) /move/
- [guidance-on-designing-hyperscale-vpcs](https://aws.github.io/aws-eks-best-practices/networking/subnets/#guidance-on-designing-hyperscale-vpcs) /move/
- https://aws.github.io/aws-eks-best-practices/networking/subnets/#vpc-configurations /move/
- https://aws.github.io/aws-eks-best-practices/networking/subnets/#check-available-ips /move/
- Monitoring: https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#monitor-ip-address-inventory /move/


Check CNI Parameters 

- CNI Parameters explained: https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#overview /link/
- https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#use-secondary-ip-mode-when /move/
- https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#avoid-secondary-ip-mode-when /move/
- https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#configure-ip-and-eni-target-values-in-address-constrained-environments /move/
- https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/#configure-warm-eni-value-for-batch-workloads /move/



Custom networking 

- https://aws.github.io/aws-eks-best-practices/networking/custom-networking/ /link/


Other things that help with IP exhastion relying on AWS networking (NAT GW,VPC Sharing, privatelink VPC Lattice) 

- NAT GW, privatelink: [Communication Across VPCs](https://aws.github.io/aws-eks-best-practices/networking/subnets/#communication-across-vpcs) /link/ !!! ADD VPC LATTICE TO THIS SECTION!!!!
- VPC Sharing: [Sharing VPC across multiple accounts](https://aws.github.io/aws-eks-best-practices/networking/subnets/#sharing-vpc-across-multiple-accounts) /link/




## Optimize node-level IP consumption

Prefix delegation (link)

- https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/index_linux/ /link/
- https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/index_windows/ /link/
__________






The [Amazon VPC CNI plugin](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/cni-proposal.md#proposal-cni-plugin-for-kubernetes-networking-over-aws-vpc) assigns each pod an IP address from the VPC CIDR(s) which essentially makes the Pod a first-class citizen in the VPC. This approach provides full visibility of the Pod addresses with tools such as [VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html) and other monitoring solutions.

As a result of application modernization containerized environments experience significant growth in scale. This entails the deployment of an ever growing number of worker nodes and pods. Hence when you design your AWS networking architecture you need to consider various aspects such as the subnet size, access type - routable or isolated, where/when/how to use Network Address Translation (NAT) etc. 

In the grand scheme of things, the ever-growing size of Internet-connected devices and mobile applications made the public IPv4 exhaustion more obvious than ever. The limited number of addresses became a blocker to the expansion of the digital world. ([RIPE announcement](https://www.ripe.net/publications/news/about-ripe-ncc-and-ripe/the-ripe-ncc-has-run-out-of-ipv4-addresses), [ARIN announcement](https://www.arin.net/vault/announcements/20150924/)). In parallel we also see that many organizations private IPv4 (RFC1918) space become exhausted and too fragmented within their corporate network structure. 

Considering above, we announced [IPv6 support for EKS](https://aws.amazon.com/blogs/containers/amazon-eks-launches-ipv6-support/) back in January 2022. Our primary recommendation is to utilize IPv6 to address the connectivity requirements within the ever-expanding landscape of application containers. Although IPv6 is a different protocol implementation it can co-exist with IPv4. IPv6 workloads can communicate with legacy IPv4 resources; which we will explain in detail later.

We also acknowledge the fact that not every organization is ready to migrate to IPv6 soon enough and may still need to look into alternative approaches to scale their container workloads with IPv4. For that purpose we will also walk you through those solutions as well.


Recommendations¶
Use Secondary IP Mode when¶
Secondary IP mode is an ideal configuration option for ephemeral EKS clusters. Greenfield customers who are either new to EKS or in the process of migrating can take advantage of VPC CNI in secondary mode.

Avoid Secondary IP Mode when¶
If you are experiencing Pod density issues, we suggest enabling prefix mode. If you are facing IPv4 depletion issues, we advise migrating to IPv6 clusters. If IPv6 is not on the horizon, you may choose to use custom networking.