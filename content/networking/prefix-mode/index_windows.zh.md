# Windows 节点的前缀模式
在 Amazon EKS 中，默认情况下，运行在 Windows 主机上的每个 Pod 都会被 [VPC 资源控制器](https://github.com/aws/amazon-vpc-resource-controller-k8s)分配一个辅助 IP 地址。这个 IP 地址是一个可路由到 VPC 的地址，从主机所在的子网中分配。在 Linux 上，每个附加到实例的 ENI 都有多个插槽可以填充辅助 IP 地址或 /28 CIDR（前缀）。但是，Windows 主机只支持一个 ENI 及其可用插槽。仅使用辅助 IP 地址可能会人为地限制您在 Windows 主机上可以运行的 Pod 数量，即使有大量可分配的 IP 地址。

为了提高 Windows 主机上的 Pod 密度，特别是在使用较小实例类型时，您可以为 Windows 节点启用**前缀委派**。启用前缀委派后，/28 IPv4 前缀将被分配到 ENI 插槽，而不是辅助 IP 地址。可以通过在 `amazon-vpc-cni` 配置映射中添加 `enable-windows-prefix-delegation: "true"` 条目来启用前缀委派。这与您需要设置 `enable-windows-ipam: "true"` 条目以启用 Windows 支持的配置映射是相同的。

请按照 [EKS 用户指南](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html)中提到的说明为 Windows 节点启用前缀委派模式。

![比较两个工作节点子网，ENI 辅助 IP 与 ENI 委派前缀的示意图](./windows-1.jpg)

图：辅助 IP 模式与前缀委派模式的比较

您可以分配给网络接口的最大 IP 地址数量取决于实例类型及其大小。分配给网络接口的每个前缀都会消耗一个可用插槽。例如，`c5.large` 实例每个网络接口的限制为 `10` 个插槽。网络接口上的第一个插槽始终由接口的主 IP 地址占用，因此剩下 9 个插槽可用于前缀和/或辅助 IP 地址。如果这些插槽被分配前缀，则节点可支持 (9 * 16) 144 个 IP 地址，而如果分配辅助 IP 地址，则只能支持 9 个 IP 地址。有关更多信息，请参阅[每种实例类型每个网络接口的 IP 地址数量](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI)和[将前缀分配给网络接口](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-prefix-eni.html)的文档。

在工作节点初始化期间，VPC 资源控制器会通过维护一个预热池来为主 ENI 分配一个或多个前缀，以加快 Pod 启动速度。可以通过在 `amazon-vpc-cni` 配置映射中设置以下配置参数来控制预热池中要保留的前缀数量。

* `warm-prefix-target`，超出当前需求而分配的前缀数量。
* `warm-ip-target`，超出当前需求而分配的 IP 地址数量。
* `minimum-ip-target`，任何时候都必须可用的最小 IP 地址数量。
* 如果设置了 `warm-ip-target` 和/或 `minimum-ip-target`，它们将覆盖 `warm-prefix-target`。

当更多 Pod 被调度到节点上时，将为现有 ENI 请求额外的前缀。当 Pod 被调度到节点上时，VPC 资源控制器首先会尝试从节点上现有的前缀中分配一个 IPv4 地址。如果这不可能，只要子网有所需的容量，就会请求一个新的 IPv4 前缀。

![为 Pod 分配 IP 地址的流程图](./windows-2.jpg)

图：为 Pod 分配 IPv4 地址的工作流程

## 建议
### 何时使用前缀委派
如果您在工作节点上遇到 Pod 密度问题，请使用前缀委派。为避免出错，我们建议在迁移到前缀模式之前检查子网是否有 /28 前缀的连续地址块。有关子网预留的详细信息，请参阅"[使用子网预留避免子网碎片化（IPv4）](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html)"部分。

默认情况下，Windows 节点上的 `max-pods` 设置为 `110`。对于绝大多数实例类型，这应该是足够的。如果您想增加或减少此限制，请在用户数据中的引导命令中添加以下内容：
```
-KubeletExtraArgs '--max-pods=example-value'
```
有关 Windows 节点的引导配置参数的更多详细信息，请访问[此处](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html#bootstrap-script-configuration-parameters)的文档。

### 何时避免使用前缀委派
如果您的子网非常分散且没有足够的可用 IP 地址来创建 /28 前缀，请避免使用前缀模式。如果生成前缀的子网存在碎片化（高度使用且具有分散的辅助 IP 地址的子网），则前缀附加可能会失败。可以通过创建新的子网并预留前缀来避免此问题。

### 配置前缀委派参数以节省 IPv4 地址
`warm-prefix-target`、`warm-ip-target` 和 `minimum-ip-target` 可用于微调使用前缀进行预扩展和动态扩展的行为。默认情况下使用以下值：
```
warm-ip-target: "1"
minimum-ip-target: "3"
```
通过微调这些配置参数，您可以在节省 IP 地址和确保由于 IP 地址分配而降低 Pod 延迟之间达到最佳平衡。有关这些配置参数的更多信息，请访问[此处](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/docs/windows/prefix_delegation_config_options.md)的文档。

### 使用子网预留避免子网碎片化（IPv4）
当 EC2 将 /28 IPv4 前缀分配给 ENI 时，它必须是来自您子网的连续 IP 地址块。如果生成前缀的子网存在碎片化（高度使用且具有分散的辅助 IP 地址的子网），则前缀附加可能会失败，您将看到以下节点事件：
```
InsufficientCidrBlocks: 指定的子网没有足够的可用 CIDR 块来满足请求
```
为了避免碎片化并有足够的连续空间来创建前缀，请使用 [VPC 子网 CIDR 预留](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html#work-with-subnet-cidr-reservations)在子网内预留 IP 空间供前缀专用使用。创建预留后，预留块中的 IP 地址将不会分配给其他资源。这样，VPC 资源控制器就能在向节点 ENI 分配时从可用前缀中获取。

建议创建一个新的子网，为前缀预留空间，并为在该子网中运行的工作节点启用前缀分配。如果新子网仅专用于在您的 EKS 集群中运行启用了前缀委派的 Pod，那么您可以跳过前缀预留步骤。

### 从辅助 IP 模式迁移到前缀委派模式或相反时替换所有节点
强烈建议您创建新的节点组以增加可用 IP 地址的数量，而不是滚动替换现有工作节点。

使用自管理节点组时，过渡步骤如下：

* 增加集群容量，以便新节点能够容纳您的工作负载
* 为 Windows 启用/禁用前缀委派功能
* 封锁并排空所有现有节点以安全地逐出所有现有 Pod。为防止服务中断，我们建议在生产集群上为关键工作负载实施 [Pod 中断预算](https://kubernetes.io/docs/tasks/run-application/configure-pdb)。
* 确认 Pod 在运行后，您可以删除旧节点和节点组。新节点上的 Pod 将从分配给节点 ENI 的前缀中获取 IPv4 地址。

使用托管节点组时，过渡步骤如下：

* 为 Windows 启用/禁用前缀委派功能
* 按照[此处](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html)所述的步骤更新节点组。这执行了类似于上述步骤，但由 EKS 管理。

!!! warning
    在同一模式下运行节点上的所有 Pod

对于 Windows，我们建议您避免同时以辅助 IP 模式和前缀委派模式运行 Pod。当您从辅助 IP 模式迁移到前缀委派模式或相反时，如果有正在运行的 Windows 工作负载，就可能出现这种情况。

虽然这不会影响您正在运行的 Pod，但节点的 IP 地址容量可能会不一致。例如，考虑一个 t3.xlarge 节点，它有 14 个插槽用于辅助 IPv4 地址。如果您正在运行 10 个 Pod，那么 ENI 上的 10 个插槽将被辅助 IP 地址占用。启用前缀委派后，向 kube-api 服务器公布的容量将是 (14 个插槽 * 每个前缀 16 个 IP 地址) 244，但实际容量在那一刻将是 (剩余 4 个插槽 * 每个前缀 16 个地址) 64。公布的容量量与实际容量量（剩余插槽）之间的这种不一致可能会导致问题，如果您运行的 Pod 多于可用于分配的 IP 地址。

也就是说，您可以使用上述迁移策略安全地将您的 Pod 从辅助 IP 地址过渡到从前缀获取的地址。在切换模式时，Pod 将继续正常运行，并且：

* 从辅助 IP 模式切换到前缀委派模式时，分配给正在运行的 Pod 的辅助 IP 地址不会被释放。前缀将被分配到空闲插槽。一旦 Pod 终止，它所使用的辅助 IP 和插槽将被释放。
* 从前缀委派模式切换到辅助 IP 模式时，当其范围内的所有 IP 都不再分配给 Pod 时，前缀将被释放。如果前缀中的任何 IP 被分配给 Pod，则该前缀将被保留，直到 Pod 终止。

### 调试前缀委派问题
您可以使用我们的调试指南[此处](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/docs/troubleshooting.md)深入了解您在 Windows 上使用前缀委派时遇到的问题。