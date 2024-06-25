# Kubernetes 集群自动扩缩器

<iframe width="560" height="315" src="https://www.youtube.com/embed/FIBc8GkjFU0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## 概述

[Kubernetes 集群自动扩缩器](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)是由 [SIG Autoscaling](https://github.com/kubernetes/community/tree/master/sig-autoscaling) 维护的一种流行的集群自动扩缩解决方案。它负责确保您的集群有足够的节点来调度您的 Pod，而不会浪费资源。它会监视无法调度的 Pod 和利用率较低的节点。然后，它会模拟添加或删除节点，然后再将更改应用到您的集群。集群自动扩缩器中的 AWS 云驱动程序实现控制您的 EC2 Auto Scaling 组的 `.DesiredReplicas` 字段。

![](./architecture.png)

本指南将为配置集群自动扩缩器和选择最佳的权衡集来满足您组织的需求提供一个思维模型。虽然没有一种最佳配置，但有一组配置选项可以让您在性能、可扩展性、成本和可用性之间进行权衡。此外，本指南还将提供在 AWS 上优化配置的技巧和最佳实践。

### 术语表

以下术语将在本文档中频繁使用。这些术语可能有广泛的含义，但在本文档中仅限于以下定义。

**可扩展性**是指集群自动扩缩器在 Pod 和节点数量增加时的性能表现。当达到可扩展性限制时，集群自动扩缩器的性能和功能将会降低。当集群自动扩缩器超出其可扩展性限制时，它可能无法在您的集群中添加或删除节点。

**性能**是指集群自动扩缩器能够做出和执行扩缩决策的速度。一个完美的性能集群自动扩缩器将立即做出决策并触发扩缩操作以响应刺激，例如一个 Pod 无法调度。

**可用性**意味着 Pod 可以快速调度且不会中断。这包括新创建的 Pod 需要被调度以及缩减节点终止其上任何剩余调度的 Pod 的情况。

**成本**由扩缩事件背后的决策决定。如果现有节点利用率较低或添加的新节点对于即将到来的 Pod 来说太大，资源就会被浪费。根据使用情况，由于过于积极的缩减决策而过早终止 Pod 可能会产生相关成本。

**节点组**是集群中节点组的一个抽象 Kubernetes 概念。它不是一个真正的 Kubernetes 资源，而是存在于集群自动扩缩器、集群 API 和其他组件中的一个抽象概念。同一节点组中的节点共享属性，如标签和污点，但可能包含多个可用区或实例类型。

**EC2 Auto Scaling 组**可用作 EC2 上节点组的一种实现。EC2 Auto Scaling 组被配置为启动实例，这些实例会自动加入其 Kubernetes 集群并将标签和污点应用到相应的 Kubernetes API 中的节点资源。

**EC2 托管节点组**是 EC2 上节点组的另一种实现。它抽象了手动配置 EC2 Auto Scaling 组的复杂性，并提供了其他管理功能，如节点版本升级和优雅节点终止。

### 操作集群自动扩缩器

集群自动扩缩器通常作为[Deployment](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws/examples)安装在您的集群中。它使用[领导者选举](https://en.wikipedia.org/wiki/Leader_election)来确保高可用性，但工作由单个副本一次完成。它不是水平可扩展的。对于基本设置，使用提供的[安装说明](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html),默认情况下应该可以正常工作，但有一些需要注意的地方。

确保：

* 集群自动扩缩器的版本与集群的版本匹配。不支持跨版本兼容性[不经测试或支持](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/README.md#releases)。
* 启用了[自动发现](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws#auto-discovery-setup),除非您有特定的高级用例阻止使用此模式。

### 为 IAM 角色采用最小权限访问

当使用[自动发现](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md#Auto-discovery-setup)时，我们强烈建议您采用最小权限访问，将 `autoscaling:SetDesiredCapacity` 和 `autoscaling:TerminateInstanceInAutoScalingGroup` 操作限制在与当前集群相关的 Auto Scaling 组上。

这将防止在一个集群中运行的集群自动扩缩器修改另一个集群中的节点组，即使 `--node-group-auto-discovery` 参数没有使用标签 (例如 `k8s.io/cluster-autoscaler/<cluster-name>`) 将其范围缩小到集群的节点组。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:ResourceTag/k8s.io/cluster-autoscaler/enabled": "true",
                    "aws:ResourceTag/k8s.io/cluster-autoscaler/<my-cluster>": "owned"
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeScalingActivities",
                "autoscaling:DescribeTags",
                "ec2:DescribeImages",
                "ec2:DescribeInstanceTypes",
                "ec2:DescribeLaunchTemplateVersions",
                "ec2:GetInstanceTypesFromInstanceRequirements",
                "eks:DescribeNodegroup"
            ],
            "Resource": "*"
        }
    ]
}
```

### 配置您的节点组

有效的自动扩缩从正确配置一组节点组开始。选择正确的节点组集对于最大化您的工作负载的可用性和降低成本至关重要。AWS 使用 EC2 Auto Scaling 组实现节点组，这些组对于大量用例来说非常灵活。但是，集群自动扩缩器对您的节点组做出了一些假设。保持您的 EC2 Auto Scaling 组配置与这些假设一致将最小化意外行为。

确保：

* 每个节点组中的每个节点都具有相同的调度属性，如标签、污点和资源。
  * 对于 MixedInstancePolicies，实例类型必须具有相同的 CPU、内存和 GPU 形状
  * 将使用策略中指定的第一个实例类型来模拟调度。
  * 如果您的策略包含更多资源的其他实例类型，在扩缩后资源可能会被浪费。
  * 如果您的策略包含较少资源的其他实例类型，由于容量不足，您的 Pod 可能无法在新实例上调度。
* 相比于许多节点较少的节点组，更倾向于使用节点较多的节点组。这将对可扩展性产生最大影响。
* 在两个系统都提供支持的情况下，尽可能优先选择 EC2 功能 (例如区域、MixedInstancePolicy)

*注意：我们建议使用 [EKS 托管节点组](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)。托管节点组带有强大的管理功能，包括集群自动扩缩器的功能，如自动 EC2 Auto Scaling 组发现和优雅节点终止。*

## 优化性能和可扩展性

了解自动扩缩算法的运行时复杂度将有助于您调整集群自动扩缩器，以便在大于 [1,000 个节点](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/proposals/scalability_tests.md)的大型集群中继续顺利运行。

调整集群自动扩缩器可扩展性的主要旋钮是提供给进程的资源、算法的扫描间隔以及集群中的节点组数量。还有其他因素涉及到这个算法的真正运行时复杂度，例如调度插件的复杂性和 Pod 的数量。这些被认为是不可配置的参数，因为它们是集群工作负载的自然属性，无法轻易调整。

集群自动扩缩器将整个集群的状态加载到内存中，包括 Pod、节点和节点组。在每个扫描间隔，算法识别无法调度的 Pod 并为每个节点组模拟调度。调整这些因素会带来不同的权衡，应该根据您的用例仔细考虑。

### 垂直自动扩缩集群自动扩缩器

扩大集群自动扩缩器以支持更大的集群的最简单方法是增加其部署的资源请求。对于大型集群，内存和 CPU 都应该增加，尽管这因集群大小而有很大差异。通常需要手动增加资源。如果您发现不断调整资源会带来运营负担，可以考虑使用 [Addon Resizer](https://github.com/kubernetes/autoscaler/tree/master/addon-resizer) 或 [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)。

### 减少节点组的数量

最小化节点组的数量是确保集群自动扩缩器在大型集群上继续良好运行的一种方式。对于一些组织来说，这可能是一个挑战，因为他们按团队或应用程序来构造节点组。虽然 Kubernetes API 完全支持这种做法，但这被视为集群自动扩缩器的反模式，会对可扩展性产生影响。有许多使用多个节点组的原因 (例如 Spot 或 GPU)，但在许多情况下，有替代设计可以实现相同的效果，同时使用较少的组。

确保：

* 使用命名空间而不是节点组来实现 Pod 隔离。
  * 在低信任多租户集群中可能无法做到这一点。
  * 正确设置 Pod ResourceRequests 和 ResourceLimits 以避免资源争用。
  * 更大的实例类型将导致更优的装箱和减少系统 Pod 开销。
* 使用 NodeTaints 或 NodeSelectors 来调度 Pod 作为例外情况，而不是常规情况。
* 将区域资源定义为具有多个可用区的单个 EC2 Auto Scaling 组。

### 减少扫描间隔

较低的扫描间隔 (例如 10 秒) 将确保集群自动扩缩器在 Pod 无法调度时尽快做出响应。但是，每次扫描都会导致对 Kubernetes API 和 EC2 Auto Scaling 组或 EKS 托管节点组 API 的多次 API 调用。这些 API 调用可能会导致速率限制，甚至导致您的 Kubernetes 控制平面服务不可用。

默认扫描间隔为 10 秒，但在 AWS 上，启动新节点需要更长的时间来启动新实例。这意味着可以增加间隔而不会显著增加整体扩缩时间。例如，如果启动一个节点需要 2 分钟，将间隔更改为 1 分钟将导致 API 调用减少 6 倍，而扩缩速度仅慢 38%。

### 跨节点组分片

集群自动扩缩器可以配置为仅在特定的节点组集上运行。使用此功能，您可以部署多个集群自动扩缩器实例，每个实例配置为在不同的节点组集上运行。这种策略使您能够使用任意大量的节点组，以可扩展性为代价。我们只建议在最后一次尝试提高性能时使用此配置。

集群自动扩缩器最初并非为此配置而设计，因此会产生一些副作用。由于分片不会相互通信，因此有可能多个自动扩缩器会尝试调度无法调度的 Pod。这可能会导致多个节点组不必要地扩缩。这些额外的节点将在 `scale-down-delay` 后缩减。

```
metadata:
  name: cluster-autoscaler
  namespace: cluster-autoscaler-1

...

--nodes=1:10:k8s-worker-asg-1
--nodes=1:10:k8s-worker-asg-2

---

metadata:
  name: cluster-autoscaler
  namespace: cluster-autoscaler-2

...

--nodes=1:10:k8s-worker-asg-3
--nodes=1:10:k8s-worker-asg-4
```

确保：

* 每个分片都配置为指向一组唯一的 EC2 Auto Scaling 组
* 每个分片都部署在单独的命名空间中，以避免领导者选举冲突

## 优化成本和可用性

### Spot 实例

您可以在节点组中使用 Spot 实例，节省高达 90% 的按需价格，但权衡是 Spot 实例可能会在 EC2 需要回收容量时随时中断。当您的 EC2 Auto Scaling 组由于缺乏可用容量而无法扩缩时，将发生容量不足错误。通过选择多个实例系列来最大化多样性，可以增加您实现所需扩缩的机会，并减少 Spot 实例中断对集群可用性的影响，同时利用多个 Spot 容量池。使用 Spot 实例的 Mixed Instance Policies 是增加多样性而不增加节点组数量的好方法。请记住，如果您需要保证资源，请使用按需实例而不是 Spot 实例。

在配置 Mixed Instance Policies 时，确保所有实例类型都具有相似的资源容量至关重要。自动扩缩器的调度模拟器使用 MixedInstancePolicy 中的第一个实例类型。如果后续实例类型更大，在扩缩后资源可能会被浪费。如果更小，由于容量不足，您的 Pod 可能无法在新实例上调度。例如，M4、M5、M5a 和 M5n 实例都具有相似的 CPU 和内存量，是 MixedInstancePolicy 的绝佳候选。[EC2 实例选择器](https://github.com/aws/amazon-ec2-instance-selector)工具可以帮助您识别相似的实例类型。

![](./spot_mix_instance_policy.jpg)

建议将按需和 Spot 容量隔离到单独的 EC2 Auto Scaling 组中。这比使用[基本容量策略](https://docs.aws.amazon.com/autoscaling/ec2/userguide/asg-purchase-options.html#asg-instances-distribution)更可取，因为调度属性根本不同。由于 Spot 实例可能会在任何时候中断 (当 EC2 需要回收容量时)，用户通常会为其可抢占节点添加污点，需要显式的 Pod 容忍该抢占行为。这些污点导致节点的调度属性不同，因此应将它们分离到多个 EC2 Auto Scaling 组中。

集群自动扩缩器有一个[扩展器](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#what-are-expanders)的概念，它提供了不同的策略来选择要扩缩的节点组。`--expander=least-waste` 策略是一个不错的通用默认值，如果您要为 Spot 实例多样性使用多个节点组 (如上图所示)，它可以进一步优化节点组的成本，通过扩缩在扩缩活动后利用率最高的组。

### 优先扩缩节点组/ASG

您还可以使用 Priority 扩展器配置基于优先级的自动扩缩。`--expander=priority` 使您的集群能够优先扩缩一个节点组/ASG,如果由于任何原因无法扩缩，它将选择优先级列表中的下一个节点组。在某些情况下，这很有用，例如，您希望使用 P3 实例类型，因为它们的 GPU 为您的工作负载提供了最佳性能，但作为第二选择，您也可以使用 P2 实例类型。

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    10:
      - .*p2-node-group.*
    50:
      - .*p3-node-group.*
```

集群自动扩缩器将尝试扩缩与名称 *p3-node-group* 匹配的 EC2 Auto Scaling 组。如果在 `--max-node-provision-time` 内此操作不成功，它将尝试扩缩与名称 *p2-node-group* 匹配的 EC2 Auto Scaling 组。
此值默认为 15 分钟，可以缩短以获得更响应的节点组选择，但如果值太低，可能会导致不必要的扩缩。

### 过度配置

集群自动扩缩器通过确保只在需要时才向集群添加节点，并在未使用时将其删除，从而最小化成本。这严重影响了部署延迟，因为许多 Pod 将被迫等待节点扩缩才能被调度。节点可能需要几分钟才能可用，这可能会将 Pod 调度延迟增加一个数量级。

这可以通过使用[过度配置](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-can-i-configure-overprovisioning-with-cluster-autoscaler)来缓解，以成本换取调度延迟。过度配置是使用具有负优先级的临时 Pod 实现的，这些 Pod 占用集群中的空间。当新创建的 Pod 无法调度且具有更高优先级时，临时 Pod 将被抢占以腾出空间。然后，这些临时 Pod 将变为无法调度，从而触发集群自动扩缩器扩缩新的过度配置节点。

过度配置还有其他不太明显的好处。如果没有过度配置，高度利用的集群的一个副作用是 Pod 将根据 Pod 或节点亲和性的 `preferredDuringSchedulingIgnoredDuringExecution` 规则做出不太理想的调度决策。一个常见的用例是使用反亲和性将高可用应用程序的 Pod 分离到不同的可用区。过度配置可以显著增加正确区域的节点可用的机会。

您组织的过度配置容量量是一个谨慎的业务决策。从本质上讲，这是性能和成本之间的权衡。做出这个决定的一种方式是确定您的平均扩缩频率，然后除以扩缩新节点所需的时间。例如，如果平均每 30 秒需要一个新节点，而 EC2 需要 30 秒来配置一个新节点，则单个节点的过度配置将确保总有一个额外的节点可用，从而将调度延迟减少 30 秒，代价是一个额外的 EC2 实例。为了改善区域调度决策，请过度配置与 EC2 Auto Scaling 组中可用区数量相等的节点数，以确保调度程序可以为传入的 Pod 选择最佳区域。

### 防止缩减驱逐

某些工作负载驱逐成本很高。大数据分析、机器学习任务和测试运行器最终会完成，但如果中断，必须重新启动。集群自动扩缩器将尝试缩减利用率低于 `scale-down-utilization-threshold` 的任何节点，这将中断该节点上的任何剩余 Pod。这可以通过确保昂贵的无法驱逐的 Pod 由集群自动扩缩器识别的标签保护来防止。

确保：

* 昂贵的无法驱逐的 Pod 具有注解 `cluster-autoscaler.kubernetes.io/safe-to-evict=false`

## 高级用例

### EBS 卷

持久存储对于构建有状态应用程序 (如数据库或分布式缓存) 至关重要。[EBS 卷](https://aws.amazon.com/premiumsupport/knowledge-center/eks-persistent-storage/)支持在 Kubernetes 上实现此用例，但受限于特定区域。如果使用单独的 EBS 卷跨多个可用区分片这些应用程序，则可以实现高可用性。然后，集群自动扩缩器可以平衡 EC2 Auto Scaling 组的扩缩。

确保：

* 通过设置 `balance-similar-node-groups=true` 启用节点组平衡。
* 除了不同的可用区和 EBS 卷外，节点组配置相同。

### 协同调度

机器学习分布式训练作业可以从同区域节点配置的最小化延迟中获得显著好处。这些工作负载将多个 Pod 部署到特定区域。这可以通过为所有协同调度的 Pod 设置 Pod 亲和性或使用 `topologyKey: failure-domain.beta.kubernetes.io/zone` 的节点亲和性来实现。然后，集群自动扩缩器将扩缩特定区域以满足需求。您可能希望为每个可用区分配多个 EC2 Auto Scaling 组，以实现整个协同调度工作负载的故障转移。

确保：

* 通过设置 `balance-similar-node-groups=false` 禁用节点组平衡
* 当集群包含区域和区域节点组时，使用[节点亲和性](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)和/或[Pod抢占](https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/)。
  * 使用[节点亲和性](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)强制或鼓励区域 Pod 避开区域节点组，反之亦然。
  * 如果区域 Pod 调度到区域节点组，这将导致您的区域 Pod 容量不平衡。
  * 如果您的区域工作负载可以容忍中断和重新调度，请配置[Pod抢占](https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/),以使区域扩缩的 Pod 能够强制抢占和重新调度到竞争较少的区域。

### 加速器

某些集群利用了诸如 GPU 之类的专用硬件加速器。在扩缩时，加速器设备插件可能需要几分钟才能向集群公布资源。集群自动扩缩器已模拟该节点将具有加速器，但在加速器准备就绪并更新节点的可用资源之前，待处理的 Pod 无法在该节点上调度。这可能会导致[重复不必要的扩缩](https://github.com/kubernetes/kubernetes/issues/54959)。

此外，即使加速器未被使用，具有加速器和高 CPU 或内存利用率的节点也不会被视为缩减对象。由于加速器的相对成本，这种行为可能会很昂贵。相反，集群自动扩缩器可以应用特殊规则，如果加速器未被占用，则将节点视为缩减对象。

为确保这些情况的正确行为，您可以配置加速器节点上的 kubelet 在加入集群之前标记节点。集群自动扩缩器将使用此标签选择器触发加速器优化行为。

确保：

* 配置 GPU 节点的 Kubelet 使用 `--node-labels k8s.amazonaws.com/accelerator=$ACCELERATOR_TYPE`
* 具有加速器的节点遵守上述相同的调度属性规则。

### 从 0 扩缩

集群自动扩缩器能够将节点组扩缩到 0，从而可以节省大量成本。它通过检查 Auto Scaling 组的 LaunchConfiguration 或 LaunchTemplate 中指定的实例类型来检测 CPU、内存和 GPU 资源。某些 Pod 需要其他资源，如 `WindowsENI` 或 `PrivateIPv4Address`,或特定的 NodeSelectors 或 Taints，这些资源无法从 LaunchConfiguration 中发现。集群自动扩缩器可以通过从 EC2 Auto Scaling 组上的标签发现这些因素来考虑这些因素。例如：

```
Key: k8s.io/cluster-autoscaler/node-template/resources/$RESOURCE_NAME
Value: 5
Key: k8s.io/cluster-autoscaler/node-template/label/$LABEL_KEY
Value: $LABEL_VALUE
Key: k8s.io/cluster-autoscaler/node-template/taint/$TAINT_KEY
Value: NoSchedule
```

*注意：请记住，当扩缩到零时，您的容量将返回给 EC2，将来可能无法使用。*

## 其他参数

有许多配置选项可用于调整集群自动扩缩器的行为和性能。
完整的参数列表可在 [GitHub](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#what-are-the-parameters-to-ca) 上找到。

|  |  |  |
|-|-|-|
| 参数 | 描述 | 默认值 |
| scan-interval | 集群重新评估扩缩的频率 | 10 秒 |
| max-empty-bulk-delete | 同时可删除的最大空节点数 | 10 |
| scale-down-delay-after-add | 扩缩后恢复缩减评估的时间 | 10 分钟 |
| scale-down-delay-after-delete | 节点删除后恢复缩减评估的时间，默认为扫描间隔 | 扫描间隔 |
| scale-down-delay-after-failure | 缩减失败后恢复缩减评估的时间 | 3 分钟 |
| scale-down-unneeded-time | 节点被视为不需要之前的时间，才有资格缩减 | 10 分钟 |
| scale-down-unready-time | 未就绪节点被视为不需要之前的时间，才有资格缩减 | 20 分钟 |
| scale-down-utilization-threshold | 节点利用率级别，定义为请求资源之和除以容量，低于此值的节点可被视为缩减对象 | 0.5 |
| scale-down-non-empty-candidates-count | 在一次迭代中作为缩减候选对象的非空节点的最大数量。较低的值意味着更好的 CA 响应能力，但可能会导致较慢的缩减延迟。对于大型集群 (数百个节点)，较高的值可能会影响 CA 性能。将其设置为非正值以关闭此启发式算法 - CA 将不会限制它考虑的节点数量。" | 30 |
| scale-down-candidates-pool-ratio | 当前迭代中某些候选对象不再有效时，作为额外非空缩减候选对象考虑的节点比率。较低的值意味着更好的 CA 响应能力，但可能会导致较慢的缩减延迟。对于大型集群 (数百个节点)，较高的值可能会影响 CA 性能。将其设置为 1.0 以关闭此启发式算法 - CA 将把所有节点视为额外候选对象。 | 0.1 |
| scale-down-candidates-pool-min-count | 当前迭代中某些候选对象不再有效时，作为额外非空缩减候选对象考虑的最小节点数。在计算额外候选对象的池大小时，我们取 `max(#nodes * scale-down-candidates-pool-ratio, scale-down-candidates-pool-min-count)` | 50 |

## 其他资源

本页面包含了一系列集群自动扩缩器演示文稿和演示。如果您想在此处添加演示文稿或演示，请发送拉取请求。

| 演示文稿/演示 | 演讲者 |
| ------------ | ------- |
| [Autoscaling and Cost Optimization on Kubernetes: From 0 to 100](https://sched.co/Zemi) | Guy Templeton, Skyscanner & Jiaxin Shan, Amazon |
| [SIG-Autoscaling Deep Dive](https://youtu.be/odxPyW_rZNQ) | Maciek Pytel & Marcin Wielgus |

## 参考

* [https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md)
* [https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md)
* [https://github.com/aws/amazon-ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector)
* [https://github.com/aws/aws-node-termination-handler](https://github.com/aws/aws-node-termination-handler)