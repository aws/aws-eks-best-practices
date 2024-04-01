# Amazon VPC CNI

<iframe width="560" height="315" src="https://www.youtube.com/embed/RBE3yk2UlYA" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

Amazon EKS 通过 [Amazon VPC 容器网络接口](https://github.com/aws/amazon-vpc-cni-k8s)[(VPC CNI)](https://github.com/aws/amazon-vpc-cni-k8s) 插件实现集群网络。CNI 插件允许 Kubernetes Pod 在 VPC 网络上拥有相同的 IP 地址。更具体地说，Pod 内的所有容器共享一个网络命名空间，它们可以使用本地端口相互通信。

Amazon VPC CNI 有两个组件：

* CNI 二进制文件，用于设置 Pod 网络以启用 Pod 到 Pod 的通信。CNI 二进制文件运行在节点根文件系统上，并由 kubelet 在节点上添加或删除新 Pod 时调用。
* ipamd,一个长期运行的节点本地 IP 地址管理(IPAM)守护进程，负责：
  * 管理节点上的 ENI，以及
  * 维护可用 IP 地址或前缀的热池

当创建实例时，EC2 会创建并附加与主子网关联的主 ENI。主子网可以是公共的或私有的。在 hostNetwork 模式下运行的 Pod 使用分配给节点主 ENI 的主 IP 地址，并与主机共享相同的网络命名空间。

CNI 插件管理节点上的[弹性网络接口(ENI)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html)。当节点被供应时，CNI 插件会自动从节点的子网中为主 ENI 分配一个插槽池(IP 或前缀)。这个池被称为*热池*,其大小由节点的实例类型决定。根据 CNI 设置，一个插槽可以是 IP 地址或前缀。当 ENI 上的一个插槽被分配后，CNI 可能会将带有热插槽池的其他 ENI 附加到节点上。这些额外的 ENI 被称为辅助 ENI。每个 ENI 只能支持一定数量的插槽，这取决于实例类型。CNI 根据所需的插槽数量(通常对应于 Pod 数量)将更多的 ENI 附加到实例上。这个过程一直持续到节点无法支持额外的 ENI 为止。CNI 还会预先分配"热"ENI 和插槽，以加快 Pod 启动速度。请注意，每种实例类型都有可以附加的最大 ENI 数量。这是 Pod 密度(每个节点的 Pod 数量)的一个约束，除了计算资源之外。

![流程图说明何时需要新的 ENI 委托前缀](./image.png)

可以使用的最大网络接口数和最大插槽数因 EC2 实例类型而异。由于每个 Pod 都会消耗一个插槽上的 IP 地址，因此您可以在特定 EC2 实例上运行的 Pod 数量取决于可以附加到它的 ENI 数量以及每个 ENI 支持的 IP 地址数量。我们建议按照 EKS 用户指南设置每个节点的最大 Pod 数，以避免耗尽实例的 CPU 和内存资源。使用 `hostNetwork` 的 Pod 不包括在此计算中。您可以考虑使用一个名为 [max-pod-calculator.sh](https://github.com/awslabs/amazon-eks-ami/blob/master/files/max-pods-calculator.sh) 的脚本来计算 EKS 为给定实例类型推荐的最大 Pod 数。

## 概述

辅助 IP 模式是 VPC CNI 的默认模式。本指南提供了在启用辅助 IP 模式时 VPC CNI 行为的通用概述。ipamd(IP 地址分配)的功能可能会因 VPC CNI 的配置设置而有所不同，例如 [前缀模式](../prefix-mode/index_linux.md)、[每个 Pod 的安全组](../sgpp/index.md)和[自定义网络](../custom-networking/index.md)。

Amazon VPC CNI 作为名为 aws-node 的 Kubernetes Daemonset 部署在工作节点上。当供应工作节点时，它有一个默认的 ENI 附加到它上面，称为主 ENI。CNI 从附加到节点主 ENI 的子网中分配一个热 ENI 池和辅助 IP 地址。默认情况下，ipamd 会尝试为节点分配一个额外的 ENI。当调度并为主 ENI 分配一个辅助 IP 地址的单个 Pod 时，IPAMD 会分配额外的 ENI。这个"热"ENI 可以实现更快的 Pod 网络。随着辅助 IP 地址池耗尽，CNI 会添加另一个 ENI 以分配更多地址。

ENI 和池中 IP 地址的数量通过名为 [WARM_ENI_TARGET、WARM_IP_TARGET、MINIMUM_IP_TARGET](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/eni-and-ip-target.md) 的环境变量进行配置。`aws-node` Daemonset 会定期检查是否附加了足够数量的 ENI。当满足所有 `WARM_ENI_TARGET` 或 `WARM_IP_TARGET` 和 `MINIMUM_IP_TARGET` 条件时，就表示附加了足够数量的 ENI。如果附加的 ENI 数量不足，CNI 将向 EC2 发出 API 调用以附加更多 ENI，直到达到 `MAX_ENI` 限制为止。

* `WARM_ENI_TARGET` - 整数，值>0表示需求已启用
  * 要维护的热 ENI 数量。当 ENI 作为辅助 ENI 附加到节点但未被任何 Pod 使用时，它就是"热"的。更具体地说，ENI 的 IP 地址都没有与任何 Pod 关联。
  * 示例：考虑一个实例有 2 个 ENI，每个 ENI 支持 5 个 IP 地址。WARM_ENI_TARGET 设置为 1。如果正好有 5 个 IP 地址与实例关联，CNI 会为实例维护 2 个附加的 ENI。第一个 ENI 正在使用中，它的所有 5 个可能的 IP 地址都在使用。第二个 ENI 是"热"的，有 5 个 IP 地址在池中。如果在实例上启动另一个 Pod，就需要第 6 个 IP 地址。CNI 将从第二个 ENI 的池中的 5 个 IP 地址中为这第 6 个 Pod 分配一个 IP 地址。第二个 ENI 现在正在使用中，不再处于"热"状态。CNI 将分配第 3 个 ENI 以维护至少 1 个热 ENI。

!!! 注意
    热 ENI 仍然会从 VPC 的 CIDR 中消耗 IP 地址。IP 地址在与工作负载(如 Pod)关联之前是"未使用"或"热"的。

* `WARM_IP_TARGET`,整数，值>0表示需求已启用
  * 要维护的热 IP 地址数量。热 IP 是在活动附加的 ENI 上可用，但尚未分配给 Pod。换句话说，可用的热 IP 数量就是可以分配给 Pod 而不需要额外 ENI 的 IP 数量。
  * 示例：考虑一个实例有 1 个 ENI，每个 ENI 支持 20 个 IP 地址。WARM_IP_TARGET 设置为 5。WARM_ENI_TARGET 设置为 0。只有在需要第 16 个 IP 地址时，CNI 才会附加第二个 ENI，从子网 CIDR 中消耗 20 个可能的地址。
* `MINIMUM_IP_TARGET`,整数，值>0表示需求已启用
  * 任何时候都要分配的最小 IP 地址数量。这通常用于在实例启动时预先分配多个 ENI。
  * 示例：考虑一个新启动的实例。它有 1 个 ENI，每个 ENI 支持 10 个 IP 地址。MINIMUM_IP_TARGET 设置为 100。ENI 会立即附加 9 个更多的 ENI，总共 100 个地址。这种情况发生时，不考虑任何 WARM_IP_TARGET 或 WARM_ENI_TARGET 值。

本项目包括一个 [子网计算器 Excel 文档](../subnet-calc/subnet-calc.xlsx)。该计算器文档模拟了在不同 ENI 配置选项(如 `WARM_IP_TARGET` 和 `WARM_ENI_TARGET`)下指定工作负载的 IP 地址消耗情况。

![说明分配 IP 地址给 Pod 所涉及的组件的插图](./image-2.png)

当 Kubelet 收到添加 Pod 请求时，CNI 二进制文件会向 ipamd 查询可用的 IP 地址，ipamd 随后会将其提供给 Pod。CNI 二进制文件连接主机和 Pod 网络。

默认情况下，部署在节点上的 Pod 会被分配到与主 ENI 相同的安全组。或者，也可以为 Pod 配置不同的安全组。

![说明分配 IP 地址给 Pod 所涉及的组件的第二个插图](./image-3.png)

随着 IP 地址池的耗尽，插件会自动将另一个弹性网络接口附加到实例上，并为该接口分配另一组辅助 IP 地址。这个过程一直持续到节点无法再支持额外的弹性网络接口为止。

![说明分配 IP 地址给 Pod 所涉及的组件的第三个插图](./image-4.png)

当删除 Pod 时，VPC CNI 会将 Pod 的 IP 地址放入 30 秒的冷却缓存中。冷却缓存中的 IP 不会被分配给新的 Pod。冷却期结束后，VPC CNI 会将 Pod IP 移回热池。冷却期可防止 Pod IP 地址过早被回收，并允许所有集群节点上的 kube-proxy 完成更新 iptables 规则。当 IP 或 ENI 的数量超过热池设置的数量时，ipamd 插件会将 IP 和 ENI 返回给 VPC。

如上所述，在辅助 IP 模式下，每个 Pod 都会从附加到实例的 ENI 之一获得一个辅助私有 IP 地址。由于每个 Pod 都使用一个 IP 地址，因此您可以在特定 EC2 实例上运行的 Pod 数量取决于可以附加到它的 ENI 数量以及它支持的 IP 地址数量。VPC CNI 会检查 [limits](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/pkg/aws/vpc/limits.go) 文件，以找出每种实例类型允许的 ENI 和 IP 地址数量。

您可以使用以下公式来确定可以在节点上部署的最大 Pod 数量。

`(实例类型的网络接口数量 × (每个网络接口的 IP 地址数量 - 1)) + 2`

+2 表示需要主机网络的 Pod，如 kube-proxy 和 VPC CNI。Amazon EKS 要求在每个节点上运行 kube-proxy 和 VPC CNI，并将这些要求计算在最大 Pod 值中。如果您想运行更多使用主机网络的 Pod，请考虑更新最大 Pod 值。

+2 表示使用主机网络的 Kubernetes Pod，如 kube-proxy 和 VPC CNI。Amazon EKS 要求在每个节点上运行 kube-proxy 和 VPC CNI，并将它们计算在最大 Pod 值中。如果您计划运行更多使用主机网络的 Pod，请考虑更新最大 Pod 值。您可以在启动模板的用户数据中指定 `--kubelet-extra-args "—max-pods=110"`。

例如，在一个有 3 个 c5.large 节点(3 个 ENI 和每个 ENI 最多 10 个 IP)的集群中，当集群启动并有 2 个 CoreDNS Pod 时，CNI 将消耗 49 个 IP 地址并将它们保留在热池中。热池可以实现更快的 Pod 启动，当应用程序部署时。

节点 1(带 CoreDNS Pod)：2 个 ENI，分配 20 个 IP

节点 2(带 CoreDNS Pod)：2 个 ENI，分配 20 个 IP

节点 3(无 Pod)：1 个 ENI，分配 10 个 IP

请记住，通常作为 DaemonSet 运行的基础设施 Pod，每个都会占用最大 Pod 数量。这些可能包括：

* CoreDNS
* Amazon 弹性负载均衡器
* 用于指标服务器的操作 Pod

我们建议您通过组合这些 Pod 的容量来规划基础设施。有关每种实例类型支持的最大 Pod 数量的列表，请参阅 GitHub 上的 [eni-max-Pods.txt](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt)。

![多个 ENI 附加到节点的插图](./image-5.png)

## 建议

### 部署 VPC CNI 托管插件

当您供应集群时，Amazon EKS 会自动安装 VPC CNI。不过，Amazon EKS 支持托管插件，使集群能够与底层 AWS 资源(如计算、存储和网络)进行交互。我们强烈建议您使用托管插件(包括 VPC CNI)部署集群。

Amazon EKS 托管插件为 Amazon EKS 集群提供 VPC CNI 安装和管理。Amazon EKS 插件包括最新的安全补丁、错误修复，并经 AWS 验证可与 Amazon EKS 一起使用。VPC CNI 插件使您能够持续确保 Amazon EKS 集群的安全性和稳定性，并减少安装、配置和更新插件所需的工作量。此外，可以通过 Amazon EKS API、AWS 管理控制台、AWS CLI 和 eksctl 添加、更新或删除托管插件。

您可以使用 `kubectl get` 命令的 `--show-managed-fields` 标志查找 VPC CNI 的托管字段。

```
kubectl get daemonset aws-node --show-managed-fields -n kube-system -o yaml
```

托管插件可以防止配置偏移，每 15 分钟自动覆盖一次配置。这意味着在创建插件后通过 Kubernetes API 对托管插件所做的任何更改都将被自动覆盖，并在更新插件时设置为默认值。

由 EKS 管理的字段列在 managedFields 下，manager 为 EKS。由 EKS 管理的字段包括服务账户、镜像、镜像 URL、活跃探针、就绪探针、标签、卷和卷挂载。

!!! 信息
最常用的字段，如 WARM_ENI_TARGET、WARM_IP_TARGET 和 MINIMUM_IP_TARGET 都不受管理，在更新插件时不会被重新协调。对这些字段的更改将在更新插件时得到保留。

我们建议您在生产集群之前，先在非生产集群中测试特定配置的插件行为。此外，请按照 EKS 用户指南中的步骤进行[插件](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html)配置。

#### 迁移到托管插件

您需要自行管理自管理 VPC CNI 的版本兼容性和安全补丁更新。要更新自管理插件，您必须使用 Kubernetes API 和 [EKS 用户指南](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html#updating-vpc-cni-add-on)中概述的说明。我们建议将现有 EKS 集群迁移到托管插件，并强烈建议在迁移之前备份当前的 CNI 设置。您可以使用 Amazon EKS API、AWS 管理控制台或 AWS 命令行界面来配置托管插件。

```
kubectl apply view-last-applied daemonset aws-node -n kube-system > aws-k8s-cni-old.yaml
```

如果某个字段被列为托管字段，Amazon EKS 将用默认设置替换 CNI 配置设置。我们建议不要修改托管字段。插件不会重新协调诸如 *warm* 环境变量和 CNI 模式之类的配置字段。Pod 和应用程序在您迁移到托管 CNI 时将继续运行。

#### 在更新之前备份 CNI 设置

VPC CNI 运行在客户数据平面(节点)上，因此 Amazon EKS 不会在发布新版本或[更新集群](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)到新的 Kubernetes 次要版本后自动更新插件(托管和自管理)。要为现有集群更新插件，您必须通过 update-addon API 或在 EKS 控制台中单击"立即更新"链接来触发更新。如果您部署了自管理插件，请按照[更新自管理 VPC CNI 插件](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html#updating-vpc-cni-add-on)中的步骤操作。

我们强烈建议您一次只更新一个次要版本。例如，如果您当前的次要版本是 `1.9`,而您想要更新到 `1.11`,您应该先更新到 `1.10` 的最新补丁版本，然后再更新到 `1.11` 的最新补丁版本。

在更新 Amazon VPC CNI 之前，请检查 aws-node Daemonset。备份现有设置。如果使用托管插件，请确认您没有更新任何 Amazon EKS 可能会覆盖的设置。我们建议在您的自动化工作流中添加一个更新后的钩子，或者在插件更新后手动应用。

```
kubectl apply view-last-applied daemonset aws-node -n kube-system > aws-k8s-cni-old.yaml
```

对于自管理插件，请将备份与 GitHub 上的 `releases` 进行比较，查看可用版本并熟悉您要更新到的版本中的更改。我们建议使用 Helm 来管理自管理插件，并利用值文件来应用设置。任何涉及 Daemonset 删除的更新操作都会导致应用程序停机，必须避免。

### 了解安全上下文

我们强烈建议您了解为有效管理 VPC CNI 而配置的安全上下文。Amazon VPC CNI 有两个组件：CNI 二进制文件和 ipamd (aws-node) Daemonset。CNI 作为二进制文件运行在节点上，可以访问节点根文件系统，并具有特权访问权限，因为它处理节点级别的 iptables。当 Pod 被添加或删除时，kubelet 会调用 CNI 二进制文件。

aws-node Daemonset 是一个长期运行的进程，负责节点级别的 IP 地址管理。aws-node 在 `hostNetwork` 模式下运行，允许访问回环设备和同一节点上其他 Pod 的网络活动。aws-node init 容器以特权模式运行并挂载 CRI 套接字，允许 Daemonset 监控节点上运行的 Pod 的 IP 使用情况。Amazon EKS 正在努力消除 aws-node init 容器的特权要求。此外，aws-node 需要更新 NAT 条目并加载 iptables 模块，因此以 NET_ADMIN 权限运行。

Amazon EKS 建议部署 aws-node 清单中定义的安全策略，用于 Pod 的 IP 管理和网络设置。请考虑更新到最新版本的 VPC CNI。此外，如果您有特定的安全要求，请考虑在 [GitHub 问题](https://github.com/aws/amazon-vpc-cni-k8s/issues)中提出。

### 为 CNI 使用单独的 IAM 角色

AWS VPC CNI 需要 AWS Identity and Access Management (IAM) 权限。在可以使用 IAM 角色之前，需要设置 CNI 策略。您可以使用 [`AmazonEKS_CNI_Policy`](https://console.aws.amazon.com/iam/home#/policies/arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy%24jsonEditor),这是一个适用于 IPv4 集群的 AWS 托管策略。AmazonEKS CNI 托管策略只有 IPv4 集群的权限。对于 IPv6 集群，您必须创建一个单独的 IAM 策略，其中包含[此处](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-create-ipv6-policy)列出的权限。

默认情况下，VPC CNI 继承 [Amazon EKS 节点 IAM 角色](https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html)(包括托管和自管理节点组)。

**强烈**建议为 Amazon VPC CNI 配置一个单独的 IAM 角色，并附加相关策略。否则，Amazon VPC CNI 的 Pod 将获得分配给节点的实例配置文件的权限。

VPC CNI 插件创建并配置了一个名为 aws-node 的服务账户。默认情况下，该服务账户绑定到附加了 Amazon EKS CNI 策略的 Amazon EKS 节点 IAM 角色。要使用单独的 IAM 角色，我们建议您[创建一个新的服务账户](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-create-role),并附加 Amazon EKS CNI 策略。要使用新的服务账户，您必须[重新部署 CNI Pod](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-redeploy-pods)。在创建新集群时，请考虑为 VPC CNI 托管插件指定 `--service-account-role-arn`。请确保从 Amazon EKS 节点角色中删除 Amazon EKS CNI 策略(包括 IPv4 和 IPv6)。

建议您[阻止访问实例元数据](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#restrict-access-to-the-instance-profile-assigned-to-the-worker-node),以最小化安全漏洞的影响范围。

### 处理活跃/就绪探针故障

我们建议为 EKS 1.20 及更高版本的集群增加活跃和就绪探针超时值(默认 `timeoutSeconds: 10`),以防止探针故障导致您的应用程序的 Pod 陷入 containerCreating 状态。这个问题在数据密集型和批处理集群中已经出现。高 CPU 使用会导致 aws-node 探针健康状况失败，进而导致未满足 Pod CPU 请求。此外，请确保为 aws-node 正确配置了 CPU 资源请求(默认 `CPU: 25m`)。除非您的节点出现问题，否则我们不建议更新这些设置。

我们强烈建议您在节点上运行 `sudo bash /opt/cni/bin/aws-cni-support.sh`,同时与 Amazon EKS 支持部门联系。该脚本将帮助评估 kubelet 日志和节点上的内存利用率。请考虑在 Amazon EKS 工作节点上安装 SSM Agent 以运行该脚本。

### 在非 EKS 优化 AMI 实例上配置 IPTables 转发策略

如果您使用自定义 AMI，请确保在 [kubelet.service](https://github.com/awslabs/amazon-eks-ami/blob/master/files/kubelet.service#L8) 下将 iptables 转发策略设置为 ACCEPT。许多系统将 iptables 转发策略设置为 DROP。您可以使用 [HashiCorp Packer](https://packer.io/intro/why.html) 和来自 [AWS GitHub 上的 Amazon EKS AMI 存储库](https://github.com/awslabs/amazon-eks-ami)的资源和配置脚本的构建规范来构建自定义 AMI。您可以更新 [kubelet.service](https://github.com/awslabs/amazon-eks-ami/blob/master/files/kubelet.service#L8),并按照[此处](https://aws.amazon.com/premiumsupport/knowledge-center/eks-custom-linux-ami/)指定的说明创建自定义 AMI。

### 定期升级 CNI 版本

VPC CNI 向后兼容。最新版本适用于所有 Amazon EKS 支持的 Kubernetes 版本。此外，VPC CNI 作为 EKS 插件提供(参见上面的"部署 VPC CNI 托管插件")。虽然 EKS 插件协调升级插件，但它不会自动升级像 CNI 这样运行在数据平面上的插件。您有责任在托管和自管理工作节点升级后升级 VPC CNI 插件。