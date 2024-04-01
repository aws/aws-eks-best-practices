# 已知限制和服务配额
Amazon EKS 可用于各种工作负载，并且可以与广泛的 AWS 服务进行交互，我们已经看到客户的工作负载遇到了类似范围的 AWS 服务配额和其他阻碍可扩展性的问题。

您的 AWS 账户有默认配额(您的团队可以请求的每种 AWS 资源的上限数量)。每个 AWS 服务都定义了自己的配额，并且配额通常是特定于区域的。您可以请求增加某些配额(软限制)，而其他配额则无法增加(硬限制)。在设计您的应用程序时，您应该考虑这些值。考虑定期审查这些服务限制，并在应用程序设计中加以考虑。

您可以在 [AWS 服务配额控制台](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html#request-increase)中查看您账户的使用情况并打开配额增加请求，或使用 [AWS CLI](https://repost.aws/knowledge-center/request-service-quota-increase-cli)。有关服务配额的更多详细信息以及任何进一步的限制或增加通知，请参阅各个 AWS 服务的 AWS 文档。

!!! note
    [Amazon EKS 服务配额](https://docs.aws.amazon.com/eks/latest/userguide/service-quotas.html)列出了服务配额，并提供了可用于请求增加配额的链接。

## 其他 AWS 服务配额
我们已经看到 EKS 客户受到了下列其他 AWS 服务的配额影响。其中一些可能仅适用于特定的用例或配置，但是您可能需要考虑您的解决方案在扩展时是否会遇到这些配额。配额按服务组织，每个配额都有一个格式为 L-XXXXXXXX 的 ID，您可以在 [AWS 服务配额控制台](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html#request-increase)中查找。

| 服务           | 配额 (L-xxxxx)                                                                            | **影响**                                                                                                           | **ID (L-xxxxx)** | 默认值  |
| -------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ---------------- | ------- |
| IAM            | 每个账户的角色数                                                                          | 可能会限制账户中的集群或 IRSA 角色数量。                                                                          | L-FE177D64       | 1,000   |
| IAM            | 每个账户的 OpenId Connect 提供程序数                                                       | 可能会限制每个账户的集群数量，IRSA 使用了 OpenID Connect。                                                        | L-858F3967       | 100     |
| IAM            | 角色信任策略长度                                                                           | 可能会限制一个 IAM 角色与 IRSA 关联的集群数量。                                                                   | L-C07B4B0D       | 2,048   |
| VPC            | 每个网络接口的安全组数                                                                    | 可能会限制集群网络的控制或连接。                                                                                 | L-2AFB9258       | 5       |
| VPC            | 每个 VPC 的 IPv4 CIDR 块数                                                                 | 可能会限制 EKS Worker 节点的数量。                                                                                | L-83CA0A9D       | 5       |
| VPC            | 每个路由表的路由数                                                                        | 可能会限制集群网络的控制或连接。                                                                                 | L-93826ACB       | 50      |
| VPC            | 每个 VPC 的活动 VPC 对等连接数                                                             | 可能会限制集群网络的控制或连接。                                                                                 | L-7E9ECCDB       | 50      |
| VPC            | 每个安全组的入站或出站规则数。                                                             | 可能会限制集群网络的控制或连接，EKS 中的一些控制器会创建新规则。                                                  | L-0EA8095F       | 50      |
| VPC            | 每个区域的 VPC 数                                                                          | 可能会限制每个账户的集群数量或集群网络的控制或连接。                                                             | L-F678F1CE       | 5       |
| VPC            | 每个区域的互联网网关数                                                                    | 可能会限制每个账户的集群数量或集群网络的控制或连接。                                                             | L-A4707A72       | 5       |
| VPC            | 每个区域的网络接口数                                                                       | 可能会限制 EKS Worker 节点的数量，或影响 EKS 控制平面的扩展/更新活动。                                            | L-DF5E4CA3       | 5,000   |
| VPC            | 网络地址使用情况                                                                          | 可能会限制每个账户的集群数量或集群网络的控制或连接。                                                             | L-BB24F6E5       | 64,000  |
| VPC            | 对等网络地址使用情况                                                                      | 可能会限制每个账户的集群数量或集群网络的控制或连接。                                                             | L-CD17FD4B       | 128,000 |
| ELB            | 每个网络负载均衡器的监听器数                                                              | 可能会限制集群入口流量的控制。                                                                                   | L-57A373D6       | 50      |
| ELB            | 每个区域的目标组数                                                                        | 可能会限制集群入口流量的控制。                                                                                   | L-B22855CB       | 3,000   |
| ELB            | 每个应用程序负载均衡器的目标数                                                            | 可能会限制集群入口流量的控制。                                                                                   | L-7E6692B2       | 1,000   |
| ELB            | 每个网络负载均衡器的目标数                                                                | 可能会限制集群入口流量的控制。                                                                                   | L-EEF1AD04       | 3,000   |
| ELB            | 每个可用区域每个网络负载均衡器的目标数                                                    | 可能会限制集群入口流量的控制。                                                                                   | L-B211E961       | 500     |
| ELB            | 每个区域每个目标组的目标数                                                                | 可能会限制集群入口流量的控制。                                                                                   | L-A0D0B863       | 1,000   |
| ELB            | 每个区域的应用程序负载均衡器数                                                            | 可能会限制集群入口流量的控制。                                                                                   | L-53DA6B97       | 50      |
| ELB            | 每个区域的经典负载均衡器数                                                                | 可能会限制集群入口流量的控制。                                                                                   | L-E9E9831D       | 20      |
| ELB            | 每个区域的网络负载均衡器数                                                                | 可能会限制集群入口流量的控制。                                                                                   | L-69A177A2       | 50      |
| EC2            | 正在运行的按需标准 (A、C、D、H、I、M、R、T、Z) 实例 (以最大 vCPU 计数)                    | 可能会限制 EKS Worker 节点的数量。                                                                               | L-1216C47A       | 5       |
| EC2            | 所有标准 (A、C、D、H、I、M、R、T、Z) Spot 实例请求 (以最大 vCPU 计数)                      | 可能会限制 EKS Worker 节点的数量。                                                                               | L-34B43A08       | 5       |
| EC2            | EC2-VPC 弹性 IP                                                                           | 可能会限制 NAT 网关的数量(从而限制 VPC 的数量)，这可能会限制一个区域中的集群数量。                                | L-0263D0A3       | 5       |
| EBS            | 每个区域的快照数                                                                          | 可能会限制有状态工作负载的备份策略。                                                                             | L-309BACF6       | 100,000 |
| EBS            | 通用 SSD (gp3) 卷的存储量，以 TiB 为单位                                                    | 可能会限制 EKS Worker 节点的数量或 PersistentVolume 存储。                                                       | L-7A658B76       | 50      |
| EBS            | 通用 SSD (gp2) 卷的存储量，以 TiB 为单位                                                    | 可能会限制 EKS Worker 节点的数量或 PersistentVolume 存储。                                                       | L-D18FCD1D       | 50      |
| ECR            | 已注册的存储库数                                                                          | 可能会限制集群中的工作负载数量。                                                                                 | L-CFEB8E8D       | 10,000  |
| ECR            | 每个存储库的镜像数                                                                        | 可能会限制集群中的工作负载数量。                                                                                 | L-03A36CE1       | 10,000  |
| SecretsManager | 每个区域的密钥数                                                                          | 可能会限制集群中的工作负载数量。                                                                                 | L-2F66C23C       | 500,000 |

## AWS 请求节流

AWS 服务还实现了请求节流，以确保它们对所有客户保持高性能和可用性。与服务配额类似，每个 AWS 服务都维护自己的请求节流阈值。如果您的工作负载需要快速发出大量 API 调用或者您的应用程序出现请求节流错误，请考虑查看相应的 AWS 服务文档。

在大型集群中或集群大幅扩展时，围绕配置 EC2 网络接口或 IP 地址的 EC2 API 请求可能会遇到请求节流。下表显示了我们看到客户遇到请求节流的一些 API 操作。
您可以在 [EC2 文档关于速率限制](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/throttling.html)中查看 EC2 速率限制默认值和请求增加速率限制的步骤。

| 可变操作                       | 只读操作                       |
| ------------------------------- | ------------------------------- |
| AssignPrivateIpAddresses        | DescribeDhcpOptions             |
| AttachNetworkInterface          | DescribeInstances               |
| CreateNetworkInterface          | DescribeNetworkInterfaces       |
| DeleteNetworkInterface          | DescribeSecurityGroups          |
| DeleteTags                      | DescribeTags                    |
| DetachNetworkInterface          | DescribeVpcs                    |
| ModifyNetworkInterfaceAttribute | DescribeVolumes                 |
| UnassignPrivateIpAddresses      |                     |

## 其他已知限制

* Route 53 DNS 解析器限制为 [每秒 1024 个数据包](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html#vpc-dns-limits)。当来自大型集群的 DNS 流量通过少量 CoreDNS Pod 副本时，可能会遇到此限制。[扩展 CoreDNS 和优化 DNS 行为](../cluster-services/#scale-coredns)可以避免 DNS 查找超时。
    * [Route 53 对 Route 53 API 的速率限制也相当低，为每秒 5 个请求](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html#limits-api-requests)。如果您有大量域需要使用 External DNS 等项目进行更新，您可能会看到速率限制和延迟更新域。

* 一些 [Nitro 实例类型的卷附加限制为 28](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html#instance-type-volume-limits),这个限制在 Amazon EBS 卷、网络接口和 NVMe 实例存储卷之间共享。如果您的工作负载挂载了大量 EBS 卷，您可能会遇到这些实例类型的 Pod 密度限制。

* 每个 Ec2 实例可以跟踪的连接数有最大值。[如果您的工作负载处理大量连接，您可能会看到通信失败或错误，因为已达到此最大值。](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-connection-tracking.html#connection-tracking-throttling)您可以使用 `conntrack_allowance_available` 和 `conntrack_allowance_exceeded` [网络性能指标来监控 EKS worker 节点上的跟踪连接数](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-network-performance-ena.html)。

* 在 EKS 环境中，etcd 存储限制为 **8 GiB**,这符合 [上游指导](https://etcd.io/docs/v3.5/dev-guide/limit/#storage-size-limit)。请监控指标 `etcd_db_total_size_in_bytes` 以跟踪 etcd 数据库大小。您可以参考 [警报规则](https://github.com/etcd-io/etcd/blob/main/contrib/mixin/mixin.libsonnet#L213-L240) `etcdBackend QuotaLowSpace` 和 `etcdExcessiveDatabaseGrowth` 来设置此监控。