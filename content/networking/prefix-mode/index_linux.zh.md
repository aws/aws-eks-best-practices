# 用于 Linux 的前缀模式

Amazon VPC CNI 会为 [Amazon EC2 网络接口](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-prefix-eni.html)分配网络前缀，以增加可分配给节点的 IP 地址数量，并提高每个节点的 Pod 密度。您可以配置 Amazon VPC CNI 插件的 1.9.0 或更高版本，以分配 IPv4 和 IPv6 CIDR 而不是为网络接口分配单个辅助 IP 地址。

前缀模式在 IPv6 集群上默认启用，并且是唯一支持的选项。VPC CNI 会为 ENI 上的一个插槽分配一个 /80 IPv6 前缀。有关更多信息，请参阅本指南的 [IPv6 部分](../ipv6/index.md)。

使用前缀分配模式时，每种实例类型的最大弹性网络接口数量保持不变，但您现在可以配置 Amazon VPC CNI 以分配 /28 (16 个 IP 地址) IPv4 地址前缀，而不是为网络接口上的插槽分配单个 IPv4 地址。当 `ENABLE_PREFIX_DELEGATION` 设置为 true 时，VPC CNI 会从分配给 ENI 的前缀中为 Pod 分配一个 IP 地址。请按照 [EKS 用户指南](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html)中的说明启用前缀 IP 模式。

![illustration of two worker subnets, comparing ENI secondary IPvs to ENIs with delegated prefixes](./image.png)

可以分配给网络接口的最大 IP 地址数量取决于实例类型。分配给网络接口的每个前缀都算作一个 IP 地址。例如，`c5.large` 实例每个网络接口的 IPv4 地址限制为 `10` 个。此实例的每个网络接口都有一个主 IPv4 地址。如果网络接口没有辅助 IPv4 地址，您最多可以为该网络接口分配 9 个前缀。对于您为网络接口分配的每个额外 IPv4 地址，您可以为该网络接口分配一个较少的前缀。请查看 AWS EC2 文档中关于 [每种实例类型每个网络接口的 IP 地址数量](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI)和[为网络接口分配前缀](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-prefix-eni.html)的内容。

在工作节点初始化期间，VPC CNI 会为主 ENI 分配一个或多个前缀。CNI 通过维护一个热池来预分配一个前缀，以加快 Pod 启动速度。可以通过设置环境变量来控制要在热池中保留的前缀数量。

* `WARM_PREFIX_TARGET`,超出当前需求而分配的前缀数量。
* `WARM_IP_TARGET`,超出当前需求而分配的 IP 地址数量。
* `MINIMUM_IP_TARGET`,任何时候都必须可用的最小 IP 地址数量。
* 如果设置了 `WARM_IP_TARGET` 和 `MINIMUM_IP_TARGET`,它们将覆盖 `WARM_PREFIX_TARGET`。

随着更多 Pod 被调度，将为现有 ENI 请求额外的前缀。首先，VPC CNI 尝试为现有 ENI 分配一个新前缀。如果 ENI 已达到容量上限，VPC CNI 将尝试为节点分配一个新的 ENI。将继续附加新的 ENI，直到达到最大 ENI 限制(由实例类型定义)。当附加新的 ENI 时，ipamd 将分配一个或多个前缀，以维持 `WARM_PREFIX_TARGET`、`WARM_IP_TARGET` 和 `MINIMUM_IP_TARGET` 设置。

![flow chart of procedure for assigning IP to pod](./image-2.jpeg)

## 建议

### 何时使用前缀模式

如果您在工作节点上遇到 Pod 密度问题，请使用前缀模式。为避免 VPC CNI 错误，我们建议在迁移到前缀模式之前检查子网是否有连续的 /28 前缀地址块。有关子网保留的详细信息，请参阅"[使用子网保留避免子网碎片化(IPv4)](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html)"部分。

为了向后兼容，已将 [max-pods](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt) 限制设置为支持辅助 IP 模式。要增加 Pod 密度，请为 Kubelet 指定 `max-pods` 值，并将 `--use-max-pods=false` 作为节点的用户数据。您可以考虑使用 [max-pod-calculator.sh](https://github.com/awslabs/amazon-eks-ami/blob/master/files/max-pods-calculator.sh) 脚本来计算 EKS 为给定实例类型推荐的最大 Pod 数量。有关示例用户数据，请参阅 EKS [用户指南](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html)。

```
./max-pods-calculator.sh --instance-type m5.large --cni-version ``1.9``.0 --cni-prefix-delegation-enabled
```

对于使用 [CNI 自定义网络](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html)的用户而言，前缀分配模式尤其相关，在这种情况下，主 ENI 不用于 Pod。使用前缀分配，即使主 ENI 未用于 Pod，您仍然可以在几乎所有 Nitro 实例类型上附加更多 IP。

### 何时避免使用前缀模式

如果您的子网非常分散，没有足够的可用 IP 地址来创建 /28 前缀，请避免使用前缀模式。如果生成前缀的子网存在碎片(一个使用率很高且分散了辅助 IP 地址的子网)，前缀附加可能会失败。您可以通过创建一个新的子网并为其保留前缀来避免此问题。

在前缀模式下，分配给工作节点的安全组也会被 Pod 共享。如果您有安全要求需要在共享计算资源上运行具有不同网络安全要求的应用程序以实现合规性，请考虑使用 [Pod 的安全组](../sgpp/index.md)。

### 在同一节点组中使用相似的实例类型

您的节点组可能包含多种类型的实例。如果某个实例的最大 Pod 数较低，则该值将应用于节点组中的所有节点。考虑在一个节点组中使用相似的实例类型，以最大化节点利用率。如果您使用 Karpenter 进行自动节点扩缩，我们建议在 Provisioner API 的 requirements 部分配置 [node.kubernetes.io/instance-type](https://karpenter.sh/docs/concepts/nodepools/)。

!!! warning
    特定节点组中所有节点的最大 Pod 数由该节点组中任何单个实例类型的*最低*最大 Pod 数定义。

### 配置 `WARM_PREFIX_TARGET` 以节省 IPv4 地址

[安装清单](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/v1.9/aws-k8s-cni.yaml#L158)中 `WARM_PREFIX_TARGET` 的默认值为 1。在大多数情况下，`WARM_PREFIX_TARGET` 的推荐值 1 将提供快速的 Pod 启动时间和最小未使用的分配给实例的 IP 地址之间的良好平衡。

如果您需要进一步节省每个节点的 IPv4 地址，请使用 `WARM_IP_TARGET` 和 `MINIMUM_IP_TARGET` 设置，它们在配置时将覆盖 `WARM_PREFIX_TARGET`。通过将 `WARM_IP_TARGET` 设置为小于 16 的值，您可以防止 CNI 保留一个整个多余的前缀。

### 优先分配新前缀而不是附加新的 ENI

为现有 ENI 分配额外前缀是一个比为实例创建和附加新 ENI 更快的 EC2 API 操作。使用前缀可提高性能，同时节省 IPv4 地址分配。附加前缀通常在一秒钟内完成，而附加新的 ENI 可能需要长达 10 秒。对于大多数用例，在前缀模式下运行时，CNI 每个工作节点只需一个 ENI。如果您可以承受(在最坏情况下)每个节点最多 15 个未使用的 IP，我们强烈建议使用较新的前缀分配网络模式，并实现随之而来的性能和效率提升。

### 使用子网保留避免子网碎片化(IPv4)

当 EC2 为 ENI 分配一个 /28 IPv4 前缀时，它必须是来自您子网的一个连续 IP 地址块。如果生成前缀的子网存在碎片(一个使用率很高且分散了辅助 IP 地址的子网)，前缀附加可能会失败，您将在 VPC CNI 日志中看到以下错误消息：

```
failed to allocate a private IP/Prefix address: InsufficientCidrBlocks: There are not enough free cidr blocks in the specified subnet to satisfy the request.
```

为了避免碎片化并有足够的连续空间来创建前缀，您可以使用 [VPC 子网 CIDR 保留](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html#work-with-subnet-cidr-reservations)在子网内保留 IP 空间，专门用于前缀。创建保留后，VPC CNI 插件将调用 EC2 API 来从保留的空间自动分配前缀。

建议创建一个新的子网，为前缀保留空间，并为在该子网中运行的工作节点启用前缀分配和 VPC CNI。如果新子网仅专用于在您的 EKS 集群中运行的 Pod，并且已为其启用了 VPC CNI 前缀分配，那么您可以跳过前缀保留步骤。

### 避免降级 VPC CNI

前缀模式适用于 VPC CNI 1.9.0 及更高版本。一旦启用了前缀模式并为 ENI 分配了前缀，就必须避免将 Amazon VPC CNI 插件降级到低于 1.9.0 的版本。如果您决定降级 VPC CNI，必须删除并重新创建节点。

### 在过渡到前缀委派期间替换所有节点

强烈建议您创建新的节点组来增加可用 IP 地址的数量，而不是滚动替换现有工作节点。腾空并排空所有现有节点，以安全地逐出所有现有 Pod。为防止服务中断，我们建议在生产集群上为关键工作负载实施 [Pod 中断预算](https://kubernetes.io/docs/tasks/run-application/configure-pdb)。在新节点上，Pod 将从分配给 ENI 的前缀中获得一个 IP。确认 Pod 正在运行后，您可以删除旧节点和节点组。如果您使用托管节点组，请按照此处所述步骤安全 [删除节点组](https://docs.aws.amazon.com/eks/latest/userguide/delete-managed-node-group.html)。