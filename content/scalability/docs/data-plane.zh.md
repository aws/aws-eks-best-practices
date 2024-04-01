# Kubernetes 数据平面

Kubernetes 数据平面包括 EC2 实例、负载均衡器、存储和其他由 Kubernetes 控制平面使用的 API。为了组织目的，我们将[集群服务](./cluster-services.md)分组在一个单独的页面中，而负载均衡器扩缩可以在[工作负载部分](./workloads.md)中找到。本节将重点介绍计算资源的扩缩。

选择 EC2 实例类型可能是客户面临的最困难的决策之一，因为在具有多个工作负载的集群中没有一刀切的解决方案。以下是一些提示，可帮助您避免在扩缩计算时遇到常见的陷阱。

## 自动节点自动扩缩

我们建议您使用节点自动扩缩功能，以减少工作量并深度集成到 Kubernetes 中。[托管节点组](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)和 [Karpenter](https://karpenter.sh/) 是大规模集群的推荐选择。

托管节点组将为您提供 Amazon EC2 Auto Scaling 组的灵活性，同时还具有托管升级和配置的额外优势。它可以与 [Kubernetes 集群自动扩缩器](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)一起扩缩，并且是具有各种计算需求的集群的常见选择。

Karpenter 是由 AWS 创建的开源、面向工作负载的节点自动扩缩器。它根据工作负载对资源（如 GPU）和污点和容忍度（如区域分布）的要求来扩缩集群中的节点，而无需管理节点组。节点是直接从 EC2 创建的，这避免了默认节点组配额（每组 450 个节点）的限制，并提供了更大的实例选择灵活性和更少的操作开销。我们建议客户尽可能使用 Karpenter。

## 使用多种不同的 EC2 实例类型

每个 AWS 区域对每种实例类型的可用实例数量都有限制。如果您创建了一个仅使用一种实例类型的集群，并将节点数量扩缩超出该区域的容量，您将收到一个错误，指出没有可用的实例。为了避免这种情况，您不应该任意限制集群中可以使用的实例类型。

Karpenter 默认情况下会使用广泛的兼容实例类型，并将根据待处理工作负载的要求、可用性和成本在供应时选择实例。您可以通过 [NodePools](https://karpenter.sh/docs/concepts/nodepools/#instance-types) 中的 `karpenter.k8s.aws/instance-category` 键来扩大所使用的实例类型列表。

Kubernetes 集群自动扩缩器要求节点组的大小相似，以便可以一致地扩缩它们。您应该根据 CPU 和内存大小创建多个组，并独立扩缩它们。使用 [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector) 来识别与您的节点组大小相似的实例。

```
ec2-instance-selector --service eks --vcpus-min 8 --memory-min 16
a1.2xlarge
a1.4xlarge
a1.metal
c4.4xlarge
c4.8xlarge
c5.12xlarge
c5.18xlarge
c5.24xlarge
c5.2xlarge
c5.4xlarge
c5.9xlarge
c5.metal
```

## 更偏向于使用较大的节点以减少 API 服务器负载

在决定使用哪些实例类型时，较少的大型节点会给 Kubernetes 控制平面带来较小的负载，因为运行的 kubelet 和 DaemonSet 会更少。但是，大型节点可能无法像较小的节点那样得到充分利用。节点大小应根据您的工作负载可用性和扩缩要求进行评估。

一个由三个 u-24tb1.metal 实例（24 TB 内存和 448 个内核）组成的集群有 3 个 kubelet，并且默认情况下每个节点的 Pod 数量将被限制为 110 个。如果您的 Pod 每个使用 4 个内核，那么这可能是预期的结果（4 个内核 x 110 = 每个节点 440 个内核）。对于一个 3 节点集群，如果发生实例故障，您处理该故障的能力会很低，因为 1 个实例故障可能会影响到整个集群的 1/3。您应该在工作负载中指定节点要求和 Pod 分布，以便 Kubernetes 调度器可以正确地放置工作负载。

工作负载应该定义它们所需的资源以及通过污点、容忍度和 [PodTopologySpread](https://kubernetes.io/blog/2020/05/introducing-podtopologyspread/) 所需的可用性。它们应该更偏向于使用可以充分利用并满足可用性目标的最大节点，以减少控制平面负载、降低操作开销并降低成本。

如果有可用资源，Kubernetes 调度器将自动尝试跨可用区域和主机分布工作负载。如果没有可用容量，Kubernetes 集群自动扩缩器将尝试在每个可用区域均匀地添加节点。Karpenter 将尽可能快速和经济地添加节点，除非工作负载指定了其他要求。

要强制工作负载使用调度器分布并在可用区域中创建新节点，您应该使用 topologySpreadConstraints：

```
spec:
  topologySpreadConstraints:
    - maxSkew: 3
      topologyKey: "topology.kubernetes.io/zone"
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          dev: my-deployment
    - maxSkew: 2
      topologyKey: "kubernetes.io/hostname"
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          dev: my-deployment
```

## 使用相似大小的节点以获得一致的工作负载性能

工作负载应该定义它们需要在哪种大小的节点上运行，以允许一致的性能和可预测的扩缩。请求 500m CPU 的工作负载在具有 4 个内核的实例上与在具有 16 个内核的实例上的表现会有所不同。避免使用 T 系列等使用可突发 CPU 的实例类型。

为了确保您的工作负载获得一致的性能，工作负载可以使用 [Karpenter 支持的标签](https://karpenter.sh/docs/concepts/scheduling/#labels)来定位特定的实例大小。

```
kind: deployment
...
spec:
  template:
    spec:
    containers:
    nodeSelector:
      karpenter.k8s.aws/instance-size: 8xlarge
```

在使用 Kubernetes 集群自动扩缩器的集群中调度工作负载时，应该将节点选择器与基于标签匹配的节点组相匹配。

```
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: eks.amazonaws.com/nodegroup
            operator: In
            values:
            - 8-core-node-group    # 匹配您的节点组名称
```

## 高效利用计算资源

计算资源包括 EC2 实例和可用区域。有效利用计算资源将提高您的可扩展性、可用性、性能，并降低总体成本。在具有多个应用程序的自动扩缩环境中，很难预测有效利用资源。[Karpenter](https://karpenter.sh/) 就是为了根据工作负载需求按需供应实例，以最大限度地提高利用率和灵活性而创建的。

Karpenter 允许工作负载声明它需要哪种类型的计算资源，而无需先创建节点组或为特定节点配置标签污点。有关更多信息，请参阅 [Karpenter 最佳实践](https://aws.github.io/aws-eks-best-practices/karpenter/)。考虑在您的 Karpenter 供应器中启用[合并](https://aws.github.io/aws-eks-best-practices/karpenter/#configure-requestslimits-for-all-non-cpu-resources-when-using-consolidation)，以替换利用率较低的节点。

## 自动更新 Amazon Machine Image (AMI)

保持工作节点组件的最新状态可确保您拥有最新的安全补丁和与 Kubernetes API 兼容的功能。更新 kubelet 是 Kubernetes 功能最重要的组件，但自动化操作系统、内核和本地安装的应用程序补丁也将减少您在扩缩时的维护工作。

建议您使用最新的 [Amazon EKS 优化的 Amazon Linux 2](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) 或 [Amazon EKS 优化的 Bottlerocket AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami-bottlerocket.html) 作为您的节点映像。Karpenter 将自动使用[最新可用的 AMI](https://karpenter.sh/docs/concepts/nodepools/#instance-types) 在集群中供应新节点。托管节点组将在[节点组更新](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html)期间更新 AMI，但不会在节点供应时更新 AMI ID。

对于托管节点组，您需要在有新的 AMI ID 可用时，使用新的 AMI ID 更新 Auto Scaling 组 (ASG) 启动模板。EKS 控制台和 API 中将提供 AMI 次要版本（例如从 1.23.5 到 1.24.3）作为[节点组的升级](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html)。补丁版本（例如从 1.23.5 到 1.23.6）将不会作为节点组的升级提供。如果您希望保持节点组与 AMI 补丁版本同步，您需要创建新的启动模板版本，并让节点组使用新的 AMI 版本替换实例。

您可以从[此页面](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html)或使用 AWS CLI 找到最新可用的 AMI。

```
aws ssm get-parameter \
  --name /aws/service/eks/optimized-ami/1.24/amazon-linux-2/recommended/image_id \
  --query "Parameter.Value" \
  --output text
```

## 为容器使用多个 EBS 卷

EBS 卷的输入/输出 (I/O) 配额取决于卷的类型（如 gp3）和磁盘大小。如果您的应用程序与主机共享单个 EBS 根卷，这可能会耗尽整个主机的磁盘配额，从而导致其他应用程序等待可用容量。如果应用程序将文件写入其覆盖分区、从主机挂载本地卷以及在将日志写入标准输出 (STDOUT) 时（具体取决于所使用的日志代理），它们就会写入磁盘。

为了避免磁盘 I/O 耗尽，您应该为容器状态文件夹（如 /run/containerd）挂载第二个卷、为工作负载存储使用单独的 EBS 卷，并禁用不必要的本地日志记录。

要使用 [eksctl](https://eksctl.io/) 为您的 EC2 实例挂载第二个卷，您可以使用具有以下配置的节点组：

```
managedNodeGroups:
  - name: al2-workers
    amiFamily: AmazonLinux2
    desiredCapacity: 2
    volumeSize: 80
    additionalVolumes:
      - volumeName: '/dev/sdz'
        volumeSize: 100
    preBootstrapCommands:
    - |
      "systemctl stop containerd"
      "mkfs -t ext4 /dev/nvme1n1"
      "rm -rf /var/lib/containerd/*"
      "mount /dev/nvme1n1 /var/lib/containerd/"
      "systemctl start containerd"
```

如果您使用 Terraform 来供应节点组，请参阅 [EKS Blueprints for Terraform](https://aws-ia.github.io/terraform-aws-eks-blueprints/patterns/stateful/#eks-managed-nodegroup-w-multiple-volumes) 中的示例。如果您使用 Karpenter 来供应节点，您可以使用 [`blockDeviceMappings`](https://karpenter.sh/docs/concepts/nodeclasses/#specblockdevicemappings) 和节点用户数据来添加额外的卷。

要直接将 EBS 卷挂载到您的 Pod，您应该使用 [AWS EBS CSI 驱动程序](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)并使用存储类消费一个卷。

```
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 4Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: public.ecr.aws/docker/library/nginx
    volumeMounts:
    - name: persistent-storage
      mountPath: /data
  volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: ebs-claim
```

## 避免使用 EBS 附加限制较低的实例（如果工作负载使用 EBS 卷）

EBS 是为工作负载提供持久存储的最简单方式之一，但它也有可扩展性限制。每种实例类型都有可以附加的 [EBS 卷的最大数量](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html)。工作负载需要声明它们应该在哪些实例类型上运行，并使用 Kubernetes 污点限制在单个实例上的副本数量。

## 禁用不必要的磁盘日志记录

避免不必要的本地日志记录，不要在生产环境中以调试日志运行您的应用程序，并禁用频繁读写磁盘的日志记录。Journald 是本地日志记录服务，它在内存中保留日志缓冲区并定期刷新到磁盘。Journald 优于 syslog，后者会立即将每一行日志写入磁盘。禁用 syslog 还可降低您需要的总存储量，并避免需要复杂的日志轮转规则。要禁用 syslog，您可以将以下代码段添加到您的 cloud-init 配置中：

```
runcmd:
  - [ systemctl, disable, --now, syslog.service ]
```

## 在操作系统更新速度是必需时就地修补实例

!!! 注意
    只有在必要时才应该就地修补实例。Amazon 建议将基础设施视为不可变的，并像应用程序一样彻底测试升级到较低环境中的更新。本节适用于无法执行此操作的情况。

在现有 Linux 主机上安装软件包只需几秒钟，而不会中断容器化工作负载。可以安装并验证软件包，而无需隔离、排空或替换实例。

要替换实例，您首先需要创建、验证和分发新的 AMI。需要为实例创建替换实例，并隔离和排空旧实例。然后需要在新实例上创建工作负载、进行验证，并对需要修补的所有实例重复此过程。在不中断工作负载的情况下安全地替换实例需要数小时、数天或数周的时间。

Amazon 建议使用可以从自动化、声明式系统构建、测试和升级的不可变基础设施，但如果您需要快速修补系统，则需要就地修补系统并在新的 AMI 可用时替换它们。由于修补系统和替换系统之间存在巨大的时间差异，我们建议在需要时使用 [AWS Systems Manager Patch Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-patch.html) 来自动修补节点。

修补节点将允许您快速推出安全更新，并在您的 AMI 更新后定期替换实例。如果您使用的是具有只读根文件系统的操作系统，如 [Flatcar Container Linux](https://flatcar-linux.org/) 或 [Bottlerocket OS](https://github.com/bottlerocket-os/bottlerocket)，我们建议使用与这些操作系统配合使用的更新操作符。[Flatcar Linux 更新操作符](https://github.com/flatcar/flatcar-linux-update-operator)和 [Bottlerocket 更新操作符](https://github.com/bottlerocket-os/bottlerocket-update-operator)将自动重启实例以保持节点的最新状态。