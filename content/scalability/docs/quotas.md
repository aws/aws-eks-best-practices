---
redirect: https://docs.aws.amazon.com/eks/latest/best-practices/known_limits_and_service_quotas.html
---


!!! info "We've Moved to the AWS Docs! 🚀"
    This content has been updated and relocated to improve your experience. 
    Please visit our new site for the latest version:
    [AWS EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/known_limits_and_service_quotas.html) on the AWS Docs

    Bookmarks and links will continue to work, but we recommend updating them for faster access in the future.

---

# Known Limits and Service Quotas
Amazon EKS can be used for a variety of workloads and can interact with a wide range of AWS services, and we have seen customer workloads encounter a similar range of AWS service quotas and other issues that hamper scalability. 

Your AWS account has default quotas (an upper limit on the number of each AWS resource your team can request). Each AWS service defines their own quota, and quotas are generally region-specific. You can request increases for some quotas (soft limits), and other quotas cannot be increased (hard limits). You should consider these values when architecting your applications. Consider reviewing these service limits periodically and incorporate them during in your application design.

You can review the usage in your account and open a quota increase request at the [AWS Service Quotas console](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html#request-increase), or using [the AWS CLI](https://repost.aws/knowledge-center/request-service-quota-increase-cli). Refer to the AWS documentation from the respective AWS Service for more details on the Service Quotas and any further restrictions or notices on their increase.


!!! note
    [Amazon EKS Service Quotas](https://docs.aws.amazon.com/eks/latest/userguide/service-quotas.html) lists the service quotas and has links to request increases where available.


## Other AWS Service Quotas 
We have seen EKS customers impacted by the quotas listed below for other AWS services. Some of these may only apply to specific use cases or configurations, however you may consider if your solution will encounter any of these as it scales. The Quotas are organized by Service and each Quota has an ID in the format of L-XXXXXXXX you can use to look it up in the [AWS Service Quotas console](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html#request-increase)


| Service        | Quota (L-xxxxx)                                                                            | **Impact**                                                                                                         | **ID (L-xxxxx)** | default |
| -------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ---------------- | ------- |
| IAM            | Roles per account                                                                          | Can limit the number of clusters or IRSA roles in an account.                                                      | L-FE177D64       | 1,000   |
| IAM            | OpenId connect providers per account                                                       | Can limit the number of Clusters per account, OpenID Connect is used by IRSA                                       | L-858F3967       | 100     |
| IAM            | Role trust policy length                                                                   | Can limit the number of of clusters an IAM role is associated with for IRSA                                        | L-C07B4B0D       | 2,048   |
| VPC            | Security groups per network interface                                                      | Can limit the control or connectivity of the networking for your cluster                                           | L-2AFB9258       | 5       |
| VPC            | IPv4 CIDR blocks per VPC                                                                   | Can limit the number of EKS Worker Nodes                                                                           | L-83CA0A9D       | 5       |
| VPC            | Routes per route table                                                                     | Can limit the control or connectivity of the networking for your cluster                                           | L-93826ACB       | 50      |
| VPC            | Active VPC peering connections per VPC                                                     | Can limit the control or connectivity of the networking for your cluster                                           | L-7E9ECCDB       | 50      |
| VPC            | Inbound or outbound rules per security group.                                              | Can limit the control or connectivity of the networking for your cluster, some controllers in EKS create new rules | L-0EA8095F       | 50      |
| VPC            | VPCs per Region                                                                            | Can limit the number of Clusters per account or the control or connectivity of the networking for your cluster     | L-F678F1CE       | 5       |
| VPC            | Internet gateways per Region                                                               | Can limit the number of Clusters per account or the control or connectivity of the networking for your cluster     | L-A4707A72       | 5       |
| VPC            | Network interfaces per Region                                                              | Can limit the number of EKS Worker nodes, or Impact EKS control plane scaling/update activities.                   | L-DF5E4CA3       | 5,000   |
| VPC            | Network Address Usage                                                                      | Can limit the number of Clusters per account or the control or connectivity of the networking for your cluster     | L-BB24F6E5       | 64,000  |
| VPC            | Peered Network Address Usage                                                               | Can limit the number of Clusters per account or the control or connectivity of the networking for your cluster     | L-CD17FD4B       | 128,000 |
| ELB            | Listeners per Network Load Balancer                                                        | Can limit the control of traffic ingress to the cluster.                                                           | L-57A373D6       | 50      |
| ELB            | Target Groups per Region                                                                   | Can limit the control of traffic ingress to the cluster.                                                           | L-B22855CB       | 3,000   |
| ELB            | Targets per Application Load Balancer                                                      | Can limit the control of traffic ingress to the cluster.                                                           | L-7E6692B2       | 1,000   |
| ELB            | Targets per Network Load Balancer                                                          | Can limit the control of traffic ingress to the cluster.                                                           | L-EEF1AD04       | 3,000   |
| ELB            | Targets per Availability Zone per Network Load Balancer                                    | Can limit the control of traffic ingress to the cluster.                                                           | L-B211E961       | 500     |
| ELB            | Targets per Target Group per Region                                                        | Can limit the control of traffic ingress to the cluster.                                                           | L-A0D0B863       | 1,000   |
| ELB            | Application Load Balancers per Region                                                      | Can limit the control of traffic ingress to the cluster.                                                           | L-53DA6B97       | 50      |
| ELB            | Classic Load Balancers per Region                                                          | Can limit the control of traffic ingress to the cluster.                                                           | L-E9E9831D       | 20      |
| ELB            | Network Load Balancers per Region                                                          | Can limit the control of traffic ingress to the cluster.                                                           | L-69A177A2       | 50      |
| EC2            | Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances (as a maximum vCPU count) | Can limit the number of EKS Worker Nodes                                                                           | L-1216C47A       | 5       |
| EC2            | All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests (as a maximum vCPU count)  | Can limit the number of EKS Worker Nodes                                                                           | L-34B43A08       | 5       |
| EC2            | EC2-VPC Elastic IPs                                                                        | Can limit the number of NAT GWs (and thus VPCs), which may limit the number of clusters in a region                | L-0263D0A3       | 5       |
| EBS            | Snapshots per Region                                                                       | Can limit the backup strategy for stateful workloads                                                               | L-309BACF6       | 100,000 |
| EBS            | Storage for General Purpose SSD (gp3) volumes, in TiB                                      | Can limit the number of EKS Worker Nodes, or PersistentVolume storage                                              | L-7A658B76       | 50      |
| EBS            | Storage for General Purpose SSD (gp2) volumes, in TiB                                      | Can limit the number of EKS Worker Nodes,  or PersistentVolume storage                                             | L-D18FCD1D       | 50      |
| ECR            | Registered repositories                                                                    | Can limit the number of workloads in your clusters                                                                 | L-CFEB8E8D       | 10,000  |
| ECR            | Images per repository                                                                      | Can limit the number of workloads in your clusters                                                                 | L-03A36CE1       | 10,000  |
| SecretsManager | Secrets per Region                                                                         | Can limit the number of workloads in your clusters                                                                 | L-2F66C23C       | 500,000 |


## AWS Request Throttling

AWS services also implement request throttling to ensure that they remain performant and available for all customers. Simliar to Service Quotas, each AWS service maintains their own request throttling thresholds. Consider reviewing the respective AWS Service documentation if your workloads will need to quickly issue a large number of API calls or if you notice request throttling errors in your application. 

EC2 API requests around provisioning EC2 network interfaces or IP addresses can encounter request throttling in large clusters or when clusters scale drastically. The table below shows some of the API actions that we have seen customers encounter request throttling from.
You can review the EC2 rate limit defaults and the steps to request a rate limit increase in the [EC2 documentation on Rate Throttling](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/throttling.html).


| Mutating Actions                | Read-only Actions               |
| ------------------------------- | ------------------------------- |
| AssignPrivateIpAddresses        | DescribeDhcpOptions             |
| AttachNetworkInterface          | DescribeInstances               |
| CreateNetworkInterface          | DescribeNetworkInterfaces       |
| DeleteNetworkInterface          | DescribeSecurityGroups          |
| DeleteTags                      | DescribeTags                    |
| DetachNetworkInterface          | DescribeVpcs                    |
| ModifyNetworkInterfaceAttribute | DescribeVolumes                 |
| UnassignPrivateIpAddresses      |                     |





## Other Known Limits

* Route 53 DNS resolvers are limited to [1024 Packets per second](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html#vpc-dns-limits). This limit can be encountered when DNS traffic from a large cluster is funneled through a small number of CoreDNS Pod replicas. [Scaling CoreDNS and optimizing DNS behavior](../cluster-services/#scale-coredns) can avoid timeouts on DNS lookups.
    * [Route 53 also has a fairly low rate limit of 5 requests per second to the Route 53 API](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html#limits-api-requests). If you have a large number of domains to update with a project like External DNS you may see rate throttling and delays in updating domains.

* Some [Nitro instance types have a volume attachment limit of 28](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html#instance-type-volume-limits) that is shared between Amazon EBS volumes, network interfaces, and NVMe instance store volumes. If your workloads are mounting numerous EBS volumes you may encounter limits to the pod density you can achieve with these instance types

* There is a maximum number of connections that can be tracked per Ec2 instance. [If your workloads are handling a large number of connections you may see communication failures or errors because this maximum has been hit.](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-connection-tracking.html#connection-tracking-throttling) You can use the `conntrack_allowance_available` and `conntrack_allowance_exceeded` [network performance metrics to monitor the number of tracked connections on your EKS worker nodes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-network-performance-ena.html).


* In EKS environment, etcd storage limit is **8 GiB** as per [upstream guidance](https://etcd.io/docs/v3.5/dev-guide/limit/#storage-size-limit). Please monitor metric `etcd_db_total_size_in_bytes` to track etcd db size. You can refer to [alert rules](https://github.com/etcd-io/etcd/blob/main/contrib/mixin/mixin.libsonnet#L213-L240) `etcdBackendQuotaLowSpace` and `etcdExcessiveDatabaseGrowth` to setup this monitoring.
