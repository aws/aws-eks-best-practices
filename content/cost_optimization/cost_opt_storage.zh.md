---
date: 2023-10-31
authors: 
  - Chance Lee
---
# 成本优化 - 存储

## 概述

在某些情况下，您可能需要运行需要保留短期或长期数据的应用程序。对于这种用例，可以定义卷并由 Pod 挂载，以便其容器可以访问不同的存储机制。Kubernetes 支持不同类型的[卷](https://kubernetes.io/docs/concepts/storage/volumes/)用于临时和持久存储。存储的选择在很大程度上取决于应用程序需求。对于每种方法，都有成本影响，下面详细介绍的做法将帮助您在 EKS 环境中为需要某种形式存储的工作负载实现成本效率。

## 临时卷

临时卷适用于需要临时本地卷但不需要在重启后保留数据的应用程序。这包括对临时空间、缓存和只读输入数据(如配置数据和密钥)的需求。您可以在[这里](https://kubernetes.io/docs/concepts/storage/ephemeral-volumes/)找到有关 Kubernetes 临时卷的更多详细信息。大多数临时卷(例如 emptyDir、configMap、downwardAPI、secret、hostpath)都由本地附加的可写设备(通常是根磁盘)或 RAM 支持，因此选择最具成本效率和性能的主机卷很重要。

### 使用 EBS 卷

*我们建议从 [gp3](https://aws.amazon.com/ebs/general-purpose/) 作为主机根卷开始。* 它是亚马逊 EBS 提供的最新一代通用 SSD 卷，与 gp2 卷相比，每 GB 的价格也更低(最高可降低 20%)。

### 使用 Amazon EC2 实例存储

[Amazon EC2 实例存储](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html)为您的 EC2 实例提供临时块级存储。EC2 实例存储提供的存储可通过物理附加到主机的磁盘访问。与 Amazon EBS 不同，您只能在启动实例时附加实例存储卷，并且这些卷只在实例的生命周期内存在。它们无法分离并重新附加到其他实例。您可以在[这里](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html)了解更多关于 Amazon EC2 实例存储的信息。*使用实例存储卷不需要额外费用。* 这使它们(实例存储卷)比具有大型 EBS 卷的通用 EC2 实例*更具成本效率*。

要在 Kubernetes 中使用本地存储卷，您应该[使用 Amazon EC2 用户数据](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-add-user-data.html)分区、配置和格式化磁盘，以便可以将卷作为 [HostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) 在 pod 规范中挂载。或者，您也可以利用 [Local Persistent Volume Static Provisioner](https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner) 来简化本地存储管理。本地持久卷静态供应器允许您通过标准的 Kubernetes PersistentVolumeClaim (PVC) 接口访问本地实例存储卷。此外，它还将提供包含节点亲和性信息的 PersistentVolumes (PVs)，以将 Pod 调度到正确的节点。尽管它使用 Kubernetes PersistentVolumes，但 EC2 实例存储卷本质上是临时的。写入临时磁盘的数据仅在实例的生命周期内可用。实例终止时，数据也会被删除。请参阅这篇[博客](https://aws.amazon.com/blogs/containers/eks-persistent-volumes-for-instance-store/)了解更多详情。

请记住，使用 Amazon EC2 实例存储卷时，总 IOPS 限制与主机共享，并且它将 Pod 绑定到特定主机。在采用 Amazon EC2 实例存储卷之前，您应该彻底审查您的工作负载需求。

## 持久卷

Kubernetes 通常与运行无状态应用程序相关联。但是，在某些情况下，您可能需要运行需要在一个请求到下一个请求之间保留持久数据或信息的微服务。数据库就是这种用例的常见示例。但是，Pod 及其中的容器或进程本质上是临时的。要在 Pod 生命周期之外持久化数据，您可以使用 PV 来定义对独立于 Pod 的特定位置的存储的访问。*与 PV 相关的成本在很大程度上取决于所使用的存储类型以及应用程序如何使用它。*

在 Amazon EKS 上支持 Kubernetes PV 的不同存储选项列在[这里](https://docs.aws.amazon.com/eks/latest/userguide/storage.html)。下面介绍的存储选项包括 Amazon EBS、Amazon EFS、Amazon FSx for Lustre 和 Amazon FSx for NetApp ONTAP。

### Amazon Elastic Block Store (EBS) 卷

Amazon EBS 卷可以作为 Kubernetes PV 使用，以提供块级存储卷。这些非常适合依赖随机读写和吞吐量密集型应用程序的数据库，这些应用程序执行长时间连续的读写操作。[Amazon Elastic Block Store Container Storage Interface (CSI) 驱动程序](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)允许 Amazon EKS 集群管理 Amazon EBS 卷的生命周期，用作持久卷。容器存储接口 (CSI) 启用并促进 Kubernetes 与存储系统之间的交互。当 CSI 驱动程序部署到您的 EKS 集群时，您可以通过本机 Kubernetes 存储资源(如 Persistent Volumes (PVs)、Persistent Volume Claims (PVCs) 和 Storage Classes (SCs))访问其功能。这个[链接](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/tree/master/examples/kubernetes)提供了如何与 Amazon EBS CSI 驱动程序交互使用 Amazon EBS 卷的实际示例。

#### 选择合适的卷

*我们建议使用最新一代块存储 (gp3)，因为它在价格和性能之间提供了合适的平衡*。它还允许您独立于卷大小缩放卷 IOPS 和吞吐量，而无需预置额外的块存储容量。如果您当前正在使用 gp2 卷，我们强烈建议迁移到 gp3 卷。这篇[博客](https://aws.amazon.com/blogs/containers/migrating-amazon-eks-clusters-from-gp2-to-gp3-ebs-volumes/)解释了如何在 Amazon EKS 集群上从 *gp2* 迁移到 *gp3*。

当您有需要更高性能且需要比单个 [gp3 卷](https://aws.amazon.com/ebs/general-purpose/)支持的更大卷的应用程序时，您应该考虑使用 [io2 block express](https://aws.amazon.com/ebs/provisioned-iops/)。这种存储非常适合您最大、I/O 密集型和关键任务部署，如 SAP HANA 或其他具有低延迟要求的大型数据库。请记住，实例的 EBS 性能受实例性能限制的约束，因此并非所有实例都支持 io2 block express 卷。您可以在此[文档](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/provisioned-iops.html)中查看支持的实例类型和其他注意事项。

*单个 gp3 卷最多可支持 16，000 IOPS、1,000 MiB/s 最大吞吐量、最大 16TiB。最新一代 Provisioned IOPS SSD 卷提供高达 256，000 IOPS、4,000 MiB/s 吞吐量和 64TiB。*

在这些选项中，您应该根据应用程序的需求来最佳地调整存储性能和成本。

#### 监控并随时间优化

了解您应用程序的基线性能并监控所选卷以检查其是否满足您的要求/期望或是否过度供应(例如，预置的 IOPS 未被充分利用的情况)很重要。

您可以随着数据的积累逐步增加卷的大小，而不是一开始就分配大卷。您可以使用 Amazon Elastic Block Store CSI 驱动程序 (aws-ebs-csi-driver) 中的[卷调整大小](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/tree/master/examples/kubernetes/resizing)功能动态调整卷大小。*请记住，您只能增加 EBS 卷的大小。*

要识别和删除任何悬空的 EBS 卷，您可以使用 [AWS 可信赖顾问的成本优化类别](https://docs.aws.amazon.com/awssupport/latest/user/cost-optimization-checks.html)。此功能可帮助您识别未附加的卷或在一段时间内写入活动非常低的卷。有一个名为 [Popeye](https://github.com/derailed/popeye) 的云原生开源只读工具，它可以扫描实时 Kubernetes 集群并报告已部署资源和配置中的潜在问题。例如，它可以扫描未使用的 PV 和 PVC，并检查它们是否已绑定或是否存在任何卷挂载错误。

有关监控的深入探讨，请参阅 [EKS 成本优化可观察性指南](https://aws.github.io/aws-eks-best-practices/cost_optimization/cost_opt_observability/)。

您可以考虑的另一个选项是 [AWS Compute Optimizer Amazon EBS 卷建议](https://docs.aws.amazon.com/compute-optimizer/latest/ug/view-ebs-recommendations.html)。该工具可以自动识别所需的最佳卷配置和正确的性能级别。例如，它可用于基于过去 14 天的最大利用率获取 EBS 卷的最佳设置，包括预置 IOPS、卷大小和 EBS 卷类型。它还量化了其建议所带来的潜在每月成本节省。您可以查看这篇[博客](https://aws.amazon.com/blogs/storage/cost-optimizing-amazon-ebs-volumes-using-aws-compute-optimizer/)了解更多详情。

#### 备份保留策略

您可以通过创建时间点快照来备份 Amazon EBS 卷上的数据。Amazon EBS CSI 驱动程序支持卷快照。您可以按照[这里](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/examples/kubernetes/snapshot/README.md)概述的步骤了解如何创建快照和恢复 EBS PV。

后续快照是增量备份，这意味着只保存自上次快照后设备上已更改的块。这最小化了创建快照所需的时间，并通过不复制数据来节省存储成本。但是，在大规模操作时，旧 EBS 快照数量的增长而没有适当的保留策略会导致意外成本。如果您直接通过 AWS API 备份 Amazon EBS 卷，您可以利用 [Amazon Data Lifecycle Manager](https://aws.amazon.com/ebs/data-lifecycle-manager/) (DLM),它为 Amazon Elastic Block Store (EBS) 快照和基于 EBS 的 Amazon Machine Images (AMIs) 提供了自动化、基于策略的生命周期管理解决方案。控制台使自动创建、保留和删除 EBS 快照和 AMI 变得更加容易。

!!! note 
    目前无法通过 Amazon EBS CSI 驱动程序使用 Amazon DLM。

在 Kubernetes 环境中，您可以利用一个名为 [Velero](https://velero.io/) 的开源工具来备份您的 EBS 持久卷。您可以在调度作业时设置 TTL 标志来使备份过期。这是 Velero 提供的一个[指南](https://velero.io/docs/v1.12/how-velero-works/#set-a-backup-to-expire)示例。

### Amazon Elastic File System (EFS)

[Amazon Elastic File System (EFS)](https://aws.amazon.com/efs/) 是一个无服务器、完全弹性的文件系统，允许您使用标准文件系统接口和文件系统语义共享文件数据，适用于广泛的工作负载和应用程序。工作负载和应用程序的示例包括 Wordpress 和 Drupal、开发人员工具(如 JIRA 和 Git)以及共享笔记本系统(如 Jupyter)和主目录。

Amazon EFS 的一个主要优点是它可以由跨多个节点和多个可用区域的多个容器挂载。另一个好处是您只需为使用的存储付费。EFS 文件系统会随着您添加和删除文件而自动增长和缩小，从而消除了容量规划的需要。

要在 Kubernetes 中使用 Amazon EFS，您需要使用 Amazon Elastic File System Container Storage Interface (CSI) 驱动程序 [aws-efs-csi-driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver)。目前，该驱动程序可以动态创建[访问点](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html)。但是，Amazon EFS 文件系统必须先被预置，并作为 Kubernetes 存储类参数的输入提供。

#### 选择合适的 EFS 存储类

Amazon EFS 提供[四种存储类](https://docs.aws.amazon.com/efs/latest/ug/storage-classes.html)。

两种标准存储类：

* Amazon EFS Standard
* [Amazon EFS Standard-Infrequent Access](https://aws.amazon.com/blogs/aws/optimize-storage-cost-with-reduced-pricing-for-amazon-efs-infrequent-access/) (EFS Standard-IA)

两种单区域存储类：

* [Amazon EFS One Zone](https://aws.amazon.com/blogs/aws/new-lower-cost-one-zone-storage-classes-for-amazon-elastic-file-system/)
* Amazon EFS One Zone-Infrequent Access (EFS One Zone-IA)

不经常访问 (IA) 存储类针对不经常访问的文件进行了成本优化。通过 Amazon EFS 生命周期管理，您可以将在生命周期策略持续时间 (7、14、30、60 或 90 天) 内未被访问的文件移动到 IA 存储类，*与 EFS Standard 和 EFS One Zone 存储类相比，可将存储成本降低高达 92%*。

通过 EFS Intelligent-Tiering,生命周期管理可监控您的文件系统的访问模式，并自动将文件移动到最佳存储类。

!!! note 
    aws-efs-csi-driver 目前无法控制更改存储类、生命周期管理或智能分层。这些应该在 AWS 控制台或通过 EFS API 手动设置。

!!! note
    aws-efs-csi-driver 与基于 Window 的容器映像不兼容。

!!! note
    当启用 *vol-metrics-opt-in* (发出卷指标) 时，存在已知的内存问题，这是由于 [DiskUsage](https://github.com/kubernetes/kubernetes/blob/ee265c92fec40cd69d1de010b477717e4c142492/pkg/volume/util/fs/fs.go#L66) 函数消耗的内存量与您的文件系统大小成正比。*目前，我们建议在大型文件系统上禁用 `--vol-metrics-opt-in` 选项，以避免消耗过多内存。这里是一个 github 问题[链接](https://github.com/kubernetes-sigs/aws-efs-csi-driver/issues/1104)了解更多详情。*

### Amazon FSx for Lustre

Lustre 是一种高性能并行文件系统，通常用于需要高达数百 GB/s 的吞吐量和亚毫秒级每操作延迟的工作负载。它用于机器学习训练、金融建模、HPC 和视频处理等场景。[Amazon FSx for Lustre](https://aws.amazon.com/fsx/lustre/) 提供完全托管的共享存储，具有可扩展性和性能，与 Amazon S3 无缝集成。

您可以使用由 FSx for Lustre 支持的 Kubernetes 持久存储卷，无论是在 Amazon EKS 还是您在 AWS 上的自管理 Kubernetes 集群。有关更多详细信息和示例，请参阅 [Amazon EKS 文档](https://docs.aws.amazon.com/eks/latest/userguide/fsx-csi.html)。

#### 链接到 Amazon S3

建议将位于 Amazon S3 上的高持久性长期数据存储库与您的 FSx for Lustre 文件系统链接。一旦链接，大型数据集将根据需要从 Amazon S3 延迟加载到 FSx for Lustre 文件系统。您还可以将分析结果运行回 S3，然后删除您的 [Lustre] 文件系统。

#### 选择合适的部署和存储选项

FSx for Lustre 提供不同的部署选项。第一个选项称为 *scratch*,它不复制数据，而第二个选项称为 *persistent*,顾名思义，它会持久化数据。

第一个选项 (*scratch*) 可用于*减少临时较短期数据处理的成本。* 持久部署选项 _旨在长期存储_，它会自动在 AWS 可用区域内复制数据。它还支持 SSD 和 HDD 存储。

您可以在 FSx for lustre 文件系统的 Kubernetes StorageClass 的参数中配置所需的部署类型。这里是一个[链接](https://github.com/kubernetes-sigs/aws-fsx-csi-driver/tree/master/examples/kubernetes/dynamic_provisioning#edit-storageclass)提供了示例模板。

!!! note
    对于延迟敏感型工作负载或需要最高 IOPS/吞吐量的工作负载，您应该选择 SSD 存储。对于不太关注延迟但需要高吞吐量的工作负载，您应该选择 HDD 存储。

#### 启用数据压缩

您还可以通过将 "Data Compression Type" 指定为 "LZ4" 来为您的文件系统启用数据压缩。一旦启用，所有新写入的文件在写入磁盘之前都将在 FSx for Lustre 上自动压缩，读取时将解压缩。LZ4 数据压缩算法是无损的，因此可以从压缩数据完全重构原始数据。

您可以在 FSx for lustre 文件系统的 Kubernetes StorageClass 的参数中将数据压缩类型配置为 LZ4。当值设置为 NONE (默认值) 时，压缩将被禁用。这个[链接](https://github.com/kubernetes-sigs/aws-fsx-csi-driver/tree/master/examples/kubernetes/dynamic_provisioning#edit-storageclass)提供了示例模板。

!!! note
    Amazon FSx for Lustre 与基于 Window 的容器映像不兼容。

### Amazon FSx for NetApp ONTAP

[Amazon FSx for NetApp ONTAP](https://aws.amazon.com/fsx/netapp-ontap/) 是一个完全托管的共享存储，基于 NetApp 的 ONTAP 文件系统构建。FSx for ONTAP 提供功能丰富、快速且灵活的共享文件存储，可广泛访问运行在 AWS 或本地的 Linux、Windows 和 macOS 计算实例。

Amazon FSx for NetApp ONTAP 支持两层存储： *1/主层* 和 *2/容量池层*。

*主层*是一个预置的高性能 SSD 层，用于活动的延迟敏感数据。完全弹性的*容量池层*针对不经常访问的数据进行了成本优化，随着数据分层到它会自动扩展，并提供了几乎无限的 PB 级容量。您可以在容量池存储上启用数据压缩和重复数据删除，进一步减少数据占用的存储容量。NetApp 的本地基于策略的 FabricPool 功能持续监控数据访问模式，自动在存储层之间双向传输数据，以优化性能和成本。

NetApp 的 Astra Trident 提供了动态存储编排，使用 CSI 驱动程序允许 Amazon EKS 集群管理由 Amazon FSx for NetApp ONTAP 文件系统支持的持久卷 PV 的生命周期。要开始使用，请参阅 Astra Trident 文档中的[将 Astra Trident 与 Amazon FSx for NetApp ONTAP 一起使用](https://docs.netapp.com/us-en/trident/trident-use/trident-fsx.html)。

## 其他注意事项

### 最小化容器镜像大小

一旦容器部署，容器镜像就会作为多个层缓存在主机上。通过减小镜像大小，可以减少主机上所需的存储量。

从一开始就使用精简的基础镜像，如 [scratch](https://hub.docker.com/_/scratch) 镜像或 [distroless](https://github.com/GoogleContainerTools/distroless) 容器镜像(只包含您的应用程序及其运行时依赖项)，*不仅可以降低存储成本，还可以减小攻击面并缩短镜像拉取时间。*

您还应该考虑使用开源工具，如 [Slim.ai](https://www.slim.ai/docs/quickstart),它提供了一种简单、安全的方式来创建最小化镜像。

多层软件包、工具、应用程序依赖项和库很容易使容器镜像大小膨胀。通过使用多阶段构建，您可以选择性地从一个阶段复制工件到另一个阶段，从最终镜像中排除所有不必要的内容。您可以在[这里](https://docs.docker.com/get-started/09_image_best/)查看更多镜像构建最佳实践。

另一个需要考虑的是要持久化缓存镜像的时间长度。当使用了一定量的磁盘空间时，您可能希望从镜像缓存中清理陈旧的镜像。这样做有助于确保主机操作有足够的空间。默认情况下，[kubelet](https://kubernetes.io/docs/reference/generated/kubelet) 每五分钟对未使用的镜像执行垃圾收集，每分钟对未使用的容器执行垃圾收集。

*要配置未使用容器和镜像垃圾收集的选项，请使用[配置文件](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/)调整 kubelet，并使用 [`KubeletConfiguration`](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/) 资源类型更改与垃圾收集相关的参数。*

您可以在 Kubernetes [文档](https://kubernetes.io/docs/concepts/architecture/garbage-collection/#containers-images)中了解更多相关信息。