# Karpenter 最佳实践

## Karpenter

Karpenter 是一种开源集群自动扩缩器，可自动为无法调度的 Pod 预配新节点。Karpenter 会评估待处理 Pod 的总体资源需求，并选择最佳实例类型来运行它们。它还会自动缩减或终止没有任何非 daemonset Pod 的实例以减少浪费。它还支持一个整合功能，可主动移动 Pod，并删除或替换为更便宜的版本以降低集群成本。

**使用 Karpenter 的原因**

在 Karpenter 推出之前，Kubernetes 用户主要依赖于 [Amazon EC2 Auto Scaling 组](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) 和 [Kubernetes 集群自动扩缩器](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) (CAS) 来动态调整集群的计算能力。使用 Karpenter，您不需要创建数十个节点组就可以获得与 Karpenter 一样的灵活性和多样性。此外，Karpenter 与 Kubernetes 版本的耦合性不像 CAS 那样紧密，也不需要您在 AWS 和 Kubernetes API 之间来回切换。

Karpenter 将实例编排职责合并到一个系统中，这更简单、更稳定且对集群有意识。Karpenter 旨在通过提供简化的方式来克服集群自动扩缩器带来的一些挑战：

* 根据工作负载需求预配节点。
* 使用灵活的 NodePool 选项通过实例类型创建不同的节点配置。与管理许多特定的自定义节点组不同，Karpenter 可让您使用单个灵活的 NodePool 管理不同工作负载的容量。
* 通过快速启动节点和调度 Pod 来实现大规模 Pod 调度的改进。

有关使用 Karpenter 的信息和文档，请访问 [karpenter.sh](https://karpenter.sh/) 网站。

## 建议

最佳实践分为关于 Karpenter 本身、NodePool 和 Pod 调度的几个部分。

## Karpenter 最佳实践

以下最佳实践涵盖了与 Karpenter 本身相关的主题。

### 对于容量需求不断变化的工作负载使用 Karpenter

与 [Auto Scaling 组](https://aws.amazon.com/blogs/containers/amazon-eks-cluster-multi-zone-auto-scaling-groups/) (ASG) 和 [Managed Node 组](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) (MNG) 相比，Karpenter 将扩缩管理更接近 Kubernetes 原生 API。ASG 和 MNG 是 AWS 原生抽象，其中扩缩是基于 AWS 级别的指标(如 EC2 CPU 负载)触发的。[集群自动扩缩器](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html#cluster-autoscaler) 将 Kubernetes 抽象桥接到 AWS 抽象，但由于这种方式失去了一些灵活性，例如为特定可用区域调度。

Karpenter 消除了一层 AWS 抽象，将一些灵活性直接引入 Kubernetes。Karpenter 最适合用于遇到高峰期或具有不同计算需求的工作负载的集群。MNG 和 ASG 更适合运行工作负载相对静态和一致的集群。根据您的需求，您可以混合使用动态和静态管理的节点。

### 在以下情况下考虑其他自动扩缩项目...

如果您需要 Karpenter 仍在开发的功能。由于 Karpenter 是一个相对较新的项目，如果您暂时需要 Karpenter 尚未包含的功能，请考虑使用其他自动扩缩项目。

### 在 EKS Fargate 上或属于节点组的工作节点上运行 Karpenter 控制器

Karpenter 使用 [Helm 图表](https://karpenter.sh/docs/getting-started/) 进行安装。Helm 图表会安装 Karpenter 控制器和一个 Webhook Pod 作为 Deployment，在使用 Karpenter 进行集群扩缩之前，这些 Pod 需要运行。我们建议至少有一个小型节点组，其中至少有一个工作节点。或者，您可以通过为 `karpenter` 命名空间创建 Fargate 配置文件，在 EKS Fargate 上运行这些 Pod。这样做会导致部署到此命名空间的所有 Pod 都在 EKS Fargate 上运行。不要在 Karpenter 管理的节点上运行 Karpenter。

### 避免使用自定义启动模板与 Karpenter

Karpenter 强烈建议不要使用自定义启动模板。使用自定义启动模板会阻止多架构支持、自动升级节点的能力以及 securityGroup 发现。使用启动模板也可能导致混淆，因为某些字段在 Karpenter 的 NodePool 中是重复的，而其他字段(如子网和实例类型)则被 Karpenter 忽略。

您通常可以通过使用自定义用户数据和/或直接在 AWS 节点模板中指定自定义 AMI 来避免使用启动模板。有关如何执行此操作的更多信息，请参阅 [NodeClasses](https://karpenter.sh/docs/concepts/nodeclasses/)。

### 排除不适合您工作负载的实例类型

如果您的集群中运行的工作负载不需要某些实例类型，请考虑使用 [node.kubernetes.io/instance-type](http://node.kubernetes.io/instance-type) 键排除这些特定实例类型。

以下示例显示了如何避免预配大型 Graviton 实例。

```yaml
- key: node.kubernetes.io/instance-type
  operator: NotIn
  values:
  - m6g.16xlarge
  - m6gd.16xlarge
  - r6g.16xlarge
  - r6gd.16xlarge
  - c6g.16xlarge
```

### 启用中断处理时使用 Spot

Karpenter 支持通过 `--interruption-queue-name` CLI 参数和 SQS 队列名称启用[原生中断处理](https://karpenter.sh/docs/concepts/disruption/#interruption)。中断处理会监视即将发生的可能导致工作负载中断的非自愿中断事件，例如：

* Spot 中断警告
* 计划更改运行状况事件(维护事件)
* 实例终止事件
* 实例停止事件

当 Karpenter 检测到这些事件将发生在您的节点上时，它会自动封锁、排空和终止节点，以在中断事件发生前提供最大的时间进行工作负载清理。不建议与 Karpenter 一起使用 AWS Node Termination Handler，原因如[此处](https://karpenter.sh/docs/faq/#interruption-handling)所述。

需要检查点或其他形式的正常排空的 Pod，在关闭前需要 2 分钟，应在其集群中启用 Karpenter 中断处理。

### **没有出站互联网访问的 Amazon EKS 私有集群**

当在没有路由到互联网的 VPC 中预配 EKS 集群时，您必须确保已根据 EKS 文档中出现的私有集群[要求](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html#private-cluster-requirements)配置了环境。此外，您需要确保已在 VPC 中创建了 STS VPC 区域端点。否则，您将看到类似于下面显示的错误。

```console
{"level":"FATAL","time":"2024-02-29T14:28:34.392Z","logger":"controller","message":"Checking EC2 API connectivity, WebIdentityErr: failed to retrieve credentials\ncaused by: RequestError: send request failed\ncaused by: Post \"https://sts.<region>.amazonaws.com/\": dial tcp 54.239.32.126:443: i/o timeout","commit":"596ea97"}
```

在私有集群中需要进行这些更改，因为 Karpenter 控制器使用服务账户的 IAM 角色 (IRSA)。配置了 IRSA 的 Pod 通过调用 AWS 安全令牌服务 (AWS STS) API 来获取凭证。如果没有出站互联网访问，您必须在 VPC 中创建和使用 ***AWS STS VPC 端点***。

私有集群还要求您为 SSM 创建 ***VPC 端点***。当 Karpenter 尝试预配新节点时，它会查询启动模板配置和 SSM 参数。如果您的 VPC 中没有 SSM VPC 端点，它将导致以下错误：

```console
{"level":"ERROR","time":"2024-02-29T14:28:12.889Z","logger":"controller","message":"Unable to hydrate the AWS launch template cache, RequestCanceled: request context canceled\ncaused by: context canceled","commit":"596ea97","tag-key":"karpenter.k8s.aws/cluster","tag-value":"eks-workshop"}
...
{"level":"ERROR","time":"2024-02-29T15:08:58.869Z","logger":"controller.nodeclass","message":"discovering amis from ssm, getting ssm parameter \"/aws/service/eks/optimized-ami/1.27/amazon-linux-2/recommended/image_id\", RequestError: send request failed\ncaused by: Post \"https://ssm.<region>.amazonaws.com/\": dial tcp 67.220.228.252:443: i/o timeout","commit":"596ea97","ec2nodeclass":"default","query":"/aws/service/eks/optimized-ami/1.27/amazon-linux-2/recommended/image_id"}
```

没有 ***[价格列表查询 API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-pelong.html) 的 VPC 端点***。
因此，定价数据将随着时间的推移而过时。
Karpenter 通过在其二进制文件中包含按需定价数据来解决这个问题，但只有在升级 Karpenter 时才会更新该数据。
获取定价数据的失败请求将导致以下错误消息：

```console
{"level":"ERROR","time":"2024-02-29T15:08:58.522Z","logger":"controller.pricing","message":"retreiving on-demand pricing data, RequestError: send request failed\ncaused by: Post \"https://api.pricing.<region>.amazonaws.com/\": dial tcp 18.196.224.8:443: i/o timeout; RequestError: send request failed\ncaused by: Post \"https://api.pricing.<region>.amazonaws.com/\": dial tcp 18.185.143.117:443: i/o timeout","commit":"596ea97"}
```

总之，要在完全私有的 EKS 集群中使用 Karpenter，您需要创建以下 VPC 端点：

```console
com.amazonaws.<region>.ec2
com.amazonaws.<region>.ecr.api
com.amazonaws.<region>.ecr.dkr
com.amazonaws.<region>.s3 – 用于拉取容器镜像
com.amazonaws.<region>.sts – 用于服务账户的 IAM 角色
com.amazonaws.<region>.ssm - 用于解析默认 AMI
com.amazonaws.<region>.sqs - 用于访问 SQS(如果使用中断处理)
```

!!! 注意
    Karpenter (控制器和 Webhook 部署)容器镜像必须在 Amazon ECR 私有中或复制到其他可从 VPC 内部访问的私有注册表中。原因是 Karpenter 控制器和 Webhook Pod 当前使用公共 ECR 镜像。如果这些镜像在 VPC 内部或与 VPC 对等的网络中不可用，您将在 Kubernetes 尝试从 ECR 公共拉取这些镜像时获得镜像拉取错误。

有关更多信息，请参阅 [Issue 988](https://github.com/aws/karpenter/issues/988) 和 [Issue 1157](https://github.com/aws/karpenter/issues/1157)。

## 创建 NodePool

以下最佳实践涵盖了与创建 NodePool 相关的主题。

### 在以下情况下创建多个 NodePool...

当不同团队共享集群并需要在不同的工作节点上运行他们的工作负载，或者有不同的操作系统或实例类型要求时，请创建多个 NodePool。例如，一个团队可能希望使用 Bottlerocket，而另一个团队可能希望使用 Amazon Linux。同样，一个团队可能可以访问昂贵的 GPU 硬件，而另一个团队则不需要。使用多个 NodePool 可确保每个团队都可获得最合适的资源。

### 创建相互排斥或加权的 NodePool

建议创建相互排斥或加权的 NodePool，以提供一致的调度行为。如果它们不是，并且多个 NodePool 匹配，Karpenter 将随机选择使用哪一个，从而导致意外结果。创建多个 NodePool 的有用示例包括以下内容：

创建一个带有 GPU 的 NodePool，并且只允许特殊工作负载在这些(昂贵的)节点上运行：

```yaml
# NodePool for GPU Instances with Taints
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: gpu
spec:
  disruption: 
    consolidateAfter: 1m0s
    consolidationPolicy: WhenEmpty
    expireAfter: Never
  template:
    metadata: {}
    spec:
      nodeClassRef:
        name: default
      requirements:
      - key: node.kubernetes.io/instance-type
        operator: In
        values:
        - p3.8xlarge
        - p3.16xlarge
      - key: kubernetes.io/os
        operator: In
        values:
        - linux
      - key: kubernetes.io/arch
        operator: In
        values:
        - amd64
      - key: karpenter.sh/capacity-type
        operator: In
        values:
        - on-demand
      taints:
      - effect: NoSchedule
        key: nvidia.com/gpu
        value: "true"
```

带有容忍污点的部署：

```yaml
# Deployment of GPU Workload will have tolerations defined
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inflate-gpu
spec:
  ...
    spec:
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
```

对于另一个团队的一般部署，NodePool 规范可以包括 nodeAffinify。然后，Deployment 可以使用 nodeSelectorTerms 匹配 `billing-team`。

```yaml
# NodePool for regular EC2 instances
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: generalcompute
spec:
  disruption:
    expireAfter: Never
  template:
    metadata:
      labels:
        billing-team: my-team
    spec:
      nodeClassRef:
        name: default
      requirements:
      - key: node.kubernetes.io/instance-type
        operator: In
        values:
        - m5.large
        - m5.xlarge
        - m5.2xlarge
        - c5.large
        - c5.xlarge
        - c5a.large
        - c5a.xlarge
        - r5.large
        - r5.xlarge
      - key: kubernetes.io/os
        operator: In
        values:
        - linux
      - key: kubernetes.io/arch
        operator: In
        values:
        - amd64
      - key: karpenter.sh/capacity-type
        operator: In
        values:
        - on-demand
```

使用 nodeAffinity 的部署：

```yaml
# Deployment will have spec.affinity.nodeAffinity defined
kind: Deployment
metadata:
  name: workload-my-team
spec:
  replicas: 200
  ...
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                - key: "billing-team"
                  operator: "In"
                  values: ["my-team"]
```

### 使用计时器 (TTL) 自动从集群中删除节点

您可以在预配的节点上使用计时器来设置何时删除没有工作负载 Pod 或已达到过期时间的节点。节点过期可用作升级的一种方式，以便淘汰旧节点并用更新版本替换。有关使用 `spec.disruption.expireAfter` 配置节点过期的信息，请参阅 Karpenter 文档中的 [过期](https://karpenter.sh/docs/concepts/disruption/)。

### 避免过度限制 Karpenter 可以预配的实例类型，尤其是在使用 Spot 时

使用 Spot 时，Karpenter 使用 [价格容量优化](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-fleet-allocation-strategy.html) 分配策略来预配 EC2 实例。该策略指示 EC2 从您要启动的实例数量中最深的池中预配实例，并且中断风险最低。然后，EC2 Fleet 会从这些池中价格最低的池中请求 Spot 实例。您允许 Karpenter 使用的实例类型越多，EC2 就越能优化您的 Spot 实例的运行时间。默认情况下，Karpenter 将使用 EC2 在您的集群所在的区域和可用区域中提供的所有实例类型。Karpenter 根据待处理的 Pod 智能地从所有实例类型集合中进行选择，以确保您的 Pod 被调度到合适大小和配置的实例上。例如，如果您的 Pod 不需要 GPU，Karpenter 就不会将您的 Pod 调度到支持 GPU 的 EC2 实例类型。当您不确定要使用哪些实例类型时，可以运行 Amazon [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector) 来生成与您的计算要求匹配的实例类型列表。例如，CLI 将内存、vCPU、架构和区域作为输入参数，并为您提供满足这些约束的 EC2 实例列表。

```console
$ ec2-instance-selector --memory 4 --vcpus 2 --cpu-architecture x86_64 -r ap-southeast-1
c5.large
c5a.large
c5ad.large
c5d.large
c6i.large
t2.medium
t3.medium
t3a.medium
```

在使用 Spot 实例时，您不应对 Karpenter 施加太多约束，因为这可能会影响您的应用程序的可用性。例如，如果某种特定类型的所有实例都被回收，而没有合适的替代实例可用于替换，您的 Pod 将保持待处理状态，直到为配置的实例类型重新补充 Spot 容量。您可以通过跨不同可用区域分布实例来降低容量不足错误的风险，因为不同可用区域的 Spot 池是不同的。不过，一般最佳实践是在使用 Spot 时允许 Karpenter 使用多种实例类型。

## 调度 Pod

以下最佳实践与在使用 Karpenter 进行节点预配的集群中部署 Pod 有关。

### 遵循 EKS 高可用性最佳实践

如果您需要运行高度可用的应用程序，请遵循一般 EKS 最佳实践[建议](https://aws.github.io/aws-eks-best-practices/reliability/docs/application/#recommendations)。有关如何跨节点和区域分布 Pod 的详细信息，请参阅 Karpenter 文档中的 [拓扑分布](https://karpenter.sh/docs/concepts/scheduling/#topology-spread)。使用 [中断预算](https://karpenter.sh/docs/troubleshooting/#disruption-budgets) 设置在尝试驱逐或删除 Pod 时需要维护的最小可用 Pod 数量。

### 使用分层约束来约束来自您的云提供商的计算功能

Karpenter 的分层约束模型允许您创建一组复杂的 NodePool 和 Pod 部署约束，以获得 Pod 调度的最佳匹配。Pod 规范可以请求的约束示例包括以下内容：

* 需要在特定应用程序可用的可用区域中运行。例如，假设您有一个 Pod 需要与在特定可用区域中的 EC2 实例上运行的另一个应用程序通信。如果您的目标是减少 VPC 中的跨可用区域流量，您可能希望将 Pod 与 EC2 实例位于同一可用区域。这种定位通常是使用节点选择器来实现的。有关 [节点选择器](https://karpenter.sh/docs/concepts/scheduling/#selecting-nodes)的更多信息，请参阅 Kubernetes 文档。
* 需要特定类型的处理器或其他硬件。请参阅 Karpenter 文档中的 [加速器](https://karpenter.sh/docs/concepts/scheduling/#acceleratorsgpu-resources) 部分，了解需要在 GPU 上运行的 Pod 规范示例。

### 创建计费警报以监控您的计算支出

当您配置集群自动扩缩时，您应创建计费警报，以在您的支出超过阈值时发出警告，并在 Karpenter 配置中添加资源限制。使用 Karpenter 设置资源限制类似于设置 AWS 自动扩缩组的最大容量，它表示 Karpenter NodePool 可以预配的最大计算资源量。

!!! 注意
    无法为整个集群设置全局限制。限制适用于特定的 NodePool。

下面的代码片段告诉 Karpenter 最多只预配 1000 个 CPU 内核和 1000Gi 内存。只有在达到或超过限制时，Karpenter 才会停止添加容量。当超过限制时，Karpenter 控制器将在控制器的日志中写入 `memory resource usage of 1001 exceeds limit of 1000` 或类似的消息。如果您将容器日志路由到 CloudWatch 日志，您可以创建一个 [指标过滤器](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html) 来查找日志中的特定模式或术语，然后创建一个 [CloudWatch 警报](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) 以在您配置的指标阈值被触发时发出警报。

有关在 Karpenter 中使用限制的更多信息，请参阅 Karpenter 文档中的 [设置资源限制](https://karpenter.sh/docs/concepts/nodepools/#speclimits)。

```yaml
spec:
  limits:
    cpu: 1000
    memory: 1000Gi
```

如果您不使用限制或限制 Karpenter 可以预配的实例类型，Karpenter 将继续根据需要向集群添加计算容量。虽然以这种方式配置 Karpenter 允许您的集群自由扩缩，但也可能会产生重大的成本影响。这就是我们建议配置计费警报的原因。计费警报允许您在您的账户中的估计费用超过定义的阈值时得到主动通知。有关更多信息，请参阅 [设置 Amazon CloudWatch 计费警报以主动监控估计费用](https://aws.amazon.com/blogs/mt/setting-up-an-amazon-cloudwatch-billing-alarm-to-proactively-monitor-estimated-charges/)。

您还可能希望启用成本异常检测，这是一项 AWS 成本管理功能，使用机器学习持续监控您的成本和使用情况，以检测异常支出。更多信息可以在 [AWS 成本异常检测入门](https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html) 指南中找到。如果您已经在 AWS Budgets 中创建了预算，您还可以配置一个操作，在特定阈值被触发时通知您。使用预算操作，您可以发送电子邮件、发布消息到 SNS 主题或向 Slack 等聊天机器人发送消息。有关更多信息，请参阅 [配置 AWS Budgets 操作](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)。

### 使用 karpenter.sh/do-not-disrupt 注解以防止 Karpenter 取消预配节点

如果您在 Karpenter 预配的节点上运行关键应用程序(如*长期运行*的批处理作业或有状态应用程序)，*并且*节点的 TTL 已过期，则当实例终止时，应用程序将被中断。通过向 Pod 添加 `karpenter.sh/karpenter.sh/do-not-disrupt` 注解，您正在指示 Karpenter 保留该节点，直到 Pod 终止或删除 `karpenter.sh/do-not-disrupt` 注解。有关更多信息，请参阅 [中断](https://karpenter.sh/docs/concepts/disruption/#node-level-controls) 文档。

如果节点上剩下的唯一非 daemonset Pod 与作业相关联，只要作业状态为 succeed 或 failed，Karpenter 就能够定位和终止这些节点。

### 在使用整合时为所有非 CPU 资源配置 requests=limits

整合和调度通常通过比较 Pod 的资源请求与节点上的可分配资源量来工作。不考虑资源限制。例如，内存限制大于内存请求的 Pod 可以超过请求值。如果同一节点上的多个 Pod 同时突增，这可能会导致某些 Pod 由于内存不足 (OOM) 而被终止。整合可能会增加这种情况发生的可能性，因为它只考虑 Pod 的请求来将 Pod 打包到节点上。

### 使用 LimitRange 为资源请求和限制配置默认值

由于 Kubernetes 不设置默认请求或限制，容器从底层主机消耗的资源(CPU 和内存)是无限制的。Kubernetes 调度程序查看 Pod 的总请求(来自 Pod 容器或 Pod 的 Init 容器的总请求中的较高值)来确定将 Pod 调度到哪个工作节点。同样，Karpenter 也考虑 Pod 的请求来确定预配哪种类型的实例。您可以使用限制范围为命名空间应用合理的默认值，以防某些 Pod 未指定资源请求。

请参阅 [为命名空间配置默认内存请求和限制](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/)

### 为所有工作负载应用准确的资源请求

当 Karpenter 对您的工作负载要求的信息准确时，它就能够启动最适合您的工作负载的节点。如果使用 Karpenter 的整合功能，这一点尤其重要。

请参阅 [为所有工作负载配置和调整资源请求/限制](https://aws.github.io/aws-eks-best-practices/reliability/docs/dataplane/#configure-and-size-resource-requestslimits-for-all-workloads)

## CoreDNS 建议

### 更新 CoreDNS 配置以保持可靠性
在将 CoreDNS Pod 部署到由 Karpenter 管理的节点上时，鉴于 Karpenter 动态地快速终止/创建新节点以满足需求，建议遵循以下最佳实践：

[CoreDNS lameduck 持续时间](https://aws.github.io/aws-eks-best-practices/scalability/docs/cluster-services/#coredns-lameduck-duration)

[CoreDNS 就绪探针](https://aws.github.io/aws-eks-best-practices/scalability/docs/cluster-services/#coredns-readiness-probe)

这将确保不会将 DNS 查询定向到尚未就绪或已终止的 CoreDNS Pod。

## Karpenter 蓝图
由于 Karpenter 采用面向应用程序的方法来为 Kubernetes 数据平面预配计算容量，您可能想知道如何正确配置一些常见的工作负载场景。[Karpenter 蓝图](https://github.com/aws-samples/karpenter-blueprints)是一个存储库，其中包含了遵循此处描述的最佳实践的常见工作负载场景列表。您将拥有所需的所有资源，甚至可以创建一个配置了 Karpenter 的 EKS 集群，并测试存储库中包含的每个蓝图。您可以组合不同的蓝图来最终创建您的工作负载所需的蓝图。

## 其他资源
* [Karpenter/Spot 研讨会](https://ec2spotworkshops.com/karpenter.html)
* [Karpenter 节点预配程序](https://youtu.be/_FXRIKWJWUk)
* [TGIK Karpenter](https://youtu.be/zXqrNJaTCrU)
* [Karpenter 与集群自动扩缩器](https://youtu.be/3QsVRHVdOnM)
* [Karpenter 无组自动扩缩](https://www.youtube.com/watch?v=43g8uPohTgc)
* [教程：使用 Amazon EC2 Spot 和 Karpenter 以更低成本运行 Kubernetes 集群](https://community.aws/tutorials/run-kubernetes-clusters-for-less-with-amazon-ec2-spot-and-karpenter#step-6-optional-simulate-spot-interruption)