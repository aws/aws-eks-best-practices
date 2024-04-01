# 高性价比资源
高性价比资源意味着为在 Kubernetes 集群上运行的工作负载使用适当的服务、资源和配置，这将带来成本节省。

## 建议
### 确保用于部署容器化服务的基础设施与应用程序配置文件和扩展需求相匹配

Amazon EKS 支持几种类型的 Kubernetes 自动扩缩 - [集群自动扩缩器](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html)、[水平 Pod 自动扩缩器](https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html) 和 [垂直 Pod 自动扩缩器](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html)。本节涵盖其中两个，集群自动扩缩器和水平 Pod 自动扩缩器。

### 使用集群自动扩缩器来调整 Kubernetes 集群的大小以满足当前需求

[Kubernetes 集群自动扩缩器](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)在 Pod 由于资源不足而无法启动或集群中的节点利用率不足且其 Pod 可以重新调度到集群中的其他节点时，会自动调整 EKS 集群中的节点数量。集群自动扩缩器在任何指定的自动扩缩组中扩缩工作节点，并作为部署运行在您的 EKS 集群中。

Amazon EKS 与 EC2 托管节点组自动化为 Amazon EKS Kubernetes 集群配置和管理节点(Amazon EC2 实例)的生命周期。所有托管节点都作为 Amazon EC2 自动扩缩组的一部分进行配置，由 Amazon EKS 为您管理，包括 Amazon EC2 实例和自动扩缩组的所有资源都在您的 AWS 账户中运行。Amazon EKS 为托管节点组资源添加标签，以便 Kubernetes 集群自动扩缩器可以发现它们。

https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html 上的文档提供了设置托管节点组然后部署 Kubernetes 集群自动扩缩器的详细指导。如果您在跨多个可用区域运行有 Amazon EBS 卷支持的有状态应用程序，并使用 Kubernetes 集群自动扩缩器，您应该为每个可用区域配置一个节点组。

*EC2 工作节点的集群自动扩缩器日志 -*
![Kubernetes 集群自动扩缩器日志](../images/cluster-auto-scaler.png)

当由于缺乏可用资源而无法调度 Pod 时，集群自动扩缩器会确定集群必须扩展，并增加节点组的大小。当使用多个节点组时，集群自动扩缩器会根据 Expander 配置选择一个。目前，在 EKS 中支持以下策略：
+ **random** - 默认扩展器，随机选择实例组
+ **most-pods** - 选择可以调度最多 Pod 的实例组。
+ **least-waste** - 选择在扩展后将有最少空闲 CPU(如果相同，则为未使用内存)的节点组。当您有不同类型的节点时，例如高 CPU 或高内存节点，并且只想在有需要大量这些资源的待处理 Pod 时才扩展这些节点时，这很有用。
+ **priority** - 选择用户分配的优先级最高的节点组

如果使用 EC2 Spot 实例作为工作节点，您可以为集群自动扩缩器的 Expander 使用 **random** 放置策略。这是默认的扩展器，在集群必须扩展时任意选择一个节点组。随机扩展器最大限度地利用了多个 Spot 容量池。

[**Priority**](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/expander/priority/readme.md) 基于扩展器根据用户为扩缩组分配的优先级选择扩展选项。示例优先级可以是让自动扩缩器首先尝试扩展 Spot 实例节点组，如果无法扩展，则回退到扩展按需节点组。

**most-pods** 基于扩展器在您使用 nodeSelector 确保某些 Pod 落在特定节点上时很有用。

根据[文档](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html),为集群自动扩缩配置指定 **least-waste** 作为扩展器类型：

```
    spec:
      containers:
      - command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/<YOUR CLUSTER NAME>
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
```

### 部署水平 Pod 自动扩缩器，根据资源的 CPU 利用率或其他应用程序相关指标自动扩缩部署、复制控制器或副本集中的 Pod 数量

[Kubernetes 水平 Pod 自动扩缩器](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)根据 CPU 利用率等资源指标或通过自定义指标支持的其他应用程序提供的指标，自动扩缩部署、复制控制器或副本集中的 Pod 数量。这可以帮助您的应用程序扩展以满足增加的需求，或在不需要资源时缩减，从而为其他应用程序释放工作节点。当您设置目标指标利用率百分比时，水平 Pod 自动扩缩器会扩展或缩减您的应用程序以尝试满足该目标。

[k8s-cloudwatch-adapter](https://github.com/awslabs/k8s-cloudwatch-adapter) 是 Kubernetes 自定义指标 API 和外部指标 API 的实现，与 CloudWatch 指标集成。它允许您使用 CloudWatch 指标通过水平 Pod 自动扩缩器 (HPA) 扩缩您的 Kubernetes 部署。

有关使用 CPU 等资源指标进行扩缩的示例，请按照 https://eksworkshop.com/beginner/080_scaling/test_hpa/ 部署示例应用程序、执行简单的负载测试以测试 Pod 自动扩缩，并模拟 Pod 自动扩缩。

参考此[博客](https://aws.amazon.com/blogs/compute/scaling-kubernetes-deployments-with-amazon-cloudwatch-metrics/)了解应用程序自定义指标的示例，以根据 Amazon SQS (Simple Queue Service) 队列中的消息数量进行扩缩。

来自博客的 Amazon SQS 外部指标示例：

```yaml
apiVersion: metrics.aws/v1alpha1
kind: ExternalMetric:
  metadata:
    name: hello-queue-length
  spec:
    name: hello-queue-length
    resource:
      resource: "deployment"
    queries:
      - id: sqs_helloworld
        metricStat:
          metric:
            namespace: "AWS/SQS"
            metricName: "ApproximateNumberOfMessagesVisible"
            dimensions:
              - name: QueueName
                value: "helloworld"
          period: 300
          stat: Average
          unit: Count
        returnData: true
```

利用此外部指标的 HPA 示例：

``` yaml
kind: HorizontalPodAutoscaler
apiVersion: autoscaling/v2beta1
metadata:
  name: sqs-consumer-scaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1beta1
    kind: Deployment
    name: sqs-consumer
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: External
    external:
      metricName: hello-queue-length
      targetAverageValue: 30
```

集群自动扩缩器用于 Kubernetes 工作节点，水平 Pod 自动扩缩器用于 Pod，将确保配置的资源尽可能接近实际利用率。

![Kubernetes 集群自动扩缩器和 HPA](../images/ClusterAS-HPA.png)
***(图片来源： https://aws.amazon.com/blogs/containers/cost-optimization-for-kubernetes-on-aws/)***

***Amazon EKS with Fargate***

****水平 Pod 自动扩缩****

可以通过以下机制实现 Fargate 上的 EKS 自动扩缩：

1. 使用 Kubernetes 指标服务器并基于 CPU 和/或内存使用情况配置自动扩缩。
2. 基于 HTTP 流量等自定义指标使用 Prometheus 和 Prometheus 指标适配器配置自动扩缩
3. 基于 App Mesh 流量配置自动扩缩

上述场景在一篇关于["使用自定义指标自动扩缩 EKS on Fargate"](https://aws.amazon.com/blogs/containers/autoscaling-eks-on-fargate-with-custom-metrics/)的实践博客中有解释。

****垂直 Pod 自动扩缩****

对于在 Fargate 上运行的 Pod，使用[垂直 Pod 自动扩缩器](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html)来优化应用程序使用的 CPU 和内存。但是，由于更改 Pod 的资源分配需要重新启动 Pod，因此必须将 Pod 更新策略设置为 Auto 或 Recreate 以确保正确功能。

## 建议

### 使用缩减来在非工作时间缩减 Kubernetes 部署、StatefulSet 和/或 HorizontalPodAutoscaler。

作为控制成本的一部分，缩减未使用的资源也可以对总体成本产生巨大影响。有一些工具，如 [kube-downscaler](https://github.com/hjacobs/kube-downscaler) 和 [Descheduler for Kubernetes](https://github.com/kubernetes-sigs/descheduler)。

**Kube-descaler** 可用于在工作时间后或在设定的时间段内缩减 Kubernetes 部署。

**Descheduler for Kubernetes** 根据其策略，可以找到可以移动的 Pod 并将其驱逐。在当前实现中，kubernetes descheduler 不会重新调度被驱逐的 Pod，而是依赖默认调度器。

**Kube-descaler**

*安装 kube-downscaler*:
```
git clone https://github.com/hjacobs/kube-downscaler
cd kube-downscaler
kubectl apply -k deploy/
```

示例配置使用 --dry-run 作为安全标志以防止缩减 --- 通过编辑部署来删除它以启用缩减器：
```
$ kubectl edit deploy kube-downscaler
```

部署一个 nginx pod 并安排它在时区 - 周一至周五 09：00-17:00 Asia/Kolkata 运行：
```
$ kubectl run nginx1 --image=nginx
$ kubectl annotate deploy nginx1 'downscaler/uptime=Mon-Fri 09:00-17:00 Asia/Kolkata'
```
!!! note
    默认 15 分钟的宽限期适用于新的 nginx 部署，即如果当前时间不在周一至周五 9-17 (Asia/Kolkata 时区)，它将不会立即缩减，而是在 15 分钟后缩减。

![Kube-down-scaler for nginx](../images/kube-down-scaler.png)

更高级的缩减部署场景可在 [kube-down-scaler github 项目](https://github.com/hjacobs/kube-downscaler)中找到。

**Kubernetes descheduler**

Descheduler 可以作为作业或 CronJob 在 k8s 集群内运行。Descheduler 的策略是可配置的，并包括可启用或禁用的策略。目前已实现了七种策略 *RemoveDuplicates*、*LowNodeUtilization*、*RemovePodsViolatingInterPodAntiAffinity*、*RemovePodsViolatingNodeAffinity*、*RemovePodsViolatingNodeTaints*、*RemovePodsHavingTooManyRestarts* 和 *PodLifeTime*。更多详细信息可在其[文档](https://github.com/kubernetes-sigs/descheduler)中找到。

一个示例策略，其中 descheduler 针对节点的低 CPU 利用率(涵盖了利用率不足和过高的场景)、删除重启过多的 Pod 等启用：

``` yaml
apiVersion: "descheduler/v1alpha1"
kind: "DeschedulerPolicy"
strategies:
  "RemoveDuplicates":
     enabled: true
  "RemovePodsViolatingInterPodAntiAffinity":
     enabled: true
  "LowNodeUtilization":
     enabled: true
     params:
       nodeResourceUtilizationThresholds:
         thresholds:
           "cpu" : 20
           "memory": 20
           "pods": 20
         targetThresholds:
           "cpu" : 50
           "memory": 50
           "pods": 50
  "RemovePodsHavingTooManyRestarts":
     enabled: true
     params:
       podsHavingTooManyRestarts:
         podRestartThresholds: 100
         includingInitContainers: true
```

**集群关闭**

[集群关闭](https://github.com/kubecost/cluster-turndown)是根据自定义计划和关闭条件自动缩减和扩展 Kubernetes 集群的后端节点。此功能可用于在闲置时间减少支出和/或减少安全风险面。最常见的用例是在非工作时间将非生产环境(例如开发集群)缩减为零。集群关闭目前处于 ALPHA 发布阶段。

集群关闭使用 Kubernetes 自定义资源定义来创建计划。以下计划将在指定的开始日期时间创建一个计划，并在指定的结束日期时间关闭(时间应为 RFC3339 格式，即基于与 UTC 的偏移的时间)。

```yaml
apiVersion: kubecost.k8s.io/v1alpha1
kind: TurndownSchedule
metadata:
  name: example-schedule
  finalizers:
  - "finalizer.kubecost.k8s.io"
spec:
  start: 2020-03-12T00:00:00Z
  end: 2020-03-12T12:00:00Z
  repeat: daily
```

### 使用 LimitRanges 和 ResourceQuotas 来帮助管理成本，限制在命名空间级别分配的资源量

默认情况下，容器在 Kubernetes 集群上运行时具有无限制的计算资源。通过资源配额，集群管理员可以限制基于命名空间的资源消耗和创建。在一个命名空间中，Pod 或容器可以消耗由该命名空间的资源配额定义的 CPU 和内存。存在一个问题，即一个 Pod 或容器可能会垄断所有可用资源。

Kubernetes 使用资源配额和限制范围来控制 CPU、内存、PersistentVolumeClaims 和其他资源的分配。ResourceQuota 在命名空间级别，而 LimitRange 在容器级别应用。

***限制范围***

LimitRange 是一种策略，用于约束命名空间中资源的分配(对 Pod 或容器)。

以下是使用限制范围设置默认内存请求和默认内存限制的示例。

``` yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit-range
spec:
  limits:
  - default:
      memory: 512Mi
    defaultRequest:
      memory: 256Mi
    type: Container
```

更多示例可在 [Kubernetes 文档](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/)中找到。

***资源配额***

当多个用户或团队在具有固定节点数的集群上共享时，存在一个问题，即一个团队可能会使用超出其公平份额的资源。资源配额是管理员解决此问题的一种工具。

以下是如何在 ResourceQuota 对象中指定配额来设置所有在命名空间中运行的容器可以使用的总内存和 CPU 量的示例。这指定容器必须有内存请求、内存限制、CPU 请求和 CPU 限制，并且不应超过在 ResourceQuota 中设置的阈值。

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mem-cpu-demo
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
```

更多示例可在 [Kubernetes 文档](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/quota-memory-cpu-namespace/)中找到。

### 使用定价模型实现有效利用

Amazon EKS 的定价详情在[定价页面](https://aws.amazon.com/eks/pricing/)中给出。无论是 Amazon EKS on Fargate 还是 EC2，控制平面成本都是通用的。

如果您使用 AWS Fargate，定价是根据从开始下载容器映像到 Amazon EKS Pod 终止时使用的 vCPU 和内存资源计算的，精确到最近的秒。最低收费为 1 分钟。请参阅 [AWS Fargate 定价页面](https://aws.amazon.com/fargate/pricing/)上的详细定价信息。

***Amazon EKS on EC2:***

Amazon EC2 提供了各种[实例类型](https://aws.amazon.com/ec2/instance-types/),针对不同用例进行了优化。实例类型包括不同组合的 CPU、内存、存储和网络容量，让您可以灵活选择适合目标工作负载的适当资源组合。每种实例类型包括一个或多个实例大小，允许您将资源扩展到目标工作负载的要求。

除了 CPU 数量、内存、处理器系列类型之外，实例类型的一个关键决策参数是[弹性网络接口(ENI)的数量](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html),这反过来会影响您可以在该 EC2 实例上运行的最大 Pod 数量。[每种 EC2 实例类型的最大 Pod 数量](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt)列表维护在 github 上。

****按需 EC2 实例：****

使用[按需实例](https://aws.amazon.com/ec2/pricing/),您可以按小时或秒付费使用计算容量，具体取决于您运行的实例。不需要长期承诺或预付费用。

Amazon EC2 A1 实例提供了显著的成本节省，非常适合由广泛的 Arm 生态系统支持的扩展和基于 ARM 的工作负载。您现在可以使用 Amazon Elastic Container Service for Kubernetes (EKS) 作为[公开开发者预览版](https://github.com/aws/containers-roadmap/tree/master/preview-programs/eks-arm-preview)的一部分在 Amazon EC2 A1 实例上运行容器。Amazon ECR 现在支持[多架构容器映像](https://aws.amazon.com/blogs/containers/introducing-multi-architecture-container-images-for-amazon-ecr/),这简化了从同一映像存储库部署不同架构和操作系统的容器映像。

您可以使用 [AWS 简单月度计算器](https://calculator.s3.amazonaws.com/index.html)或新的[定价计算器](https://calculator.aws/)获取 EKS 工作节点的按需 EC2 实例定价。

### 使用 Spot EC2 实例：

Amazon [EC2 Spot 实例](https://aws.amazon.com/ec2/pricing/)允许您以高达按需价格的 90% 的折扣请求 Amazon EC2 的备用计算能力。

Spot 实例通常非常适合无状态的容器化工作负载，因为容器和 Spot 实例的方法类似;临时和自动扩缩容量。这意味着它们都可以添加和删除，同时遵守 SLA 并且不会影响应用程序的性能或可用性。

您可以创建多个节点组，其中包含按需实例类型和 EC2 Spot 实例的混合，以利用这两种实例类型之间的定价优势。

![按需和 Spot 节点组](../images/spot_diagram.png)
***(图片来源： https://ec2spotworkshops.com/using_ec2_spot_instances_with_eks/spotworkers/workers_eksctl.html)***

下面是使用 eksctl 创建 EC2 Spot 实例节点组的示例 yaml 文件。在创建节点组期间，我们配置了一个节点标签，以便 kubernetes 知道我们配置了什么类型的节点。我们将节点的生命周期设置为 Ec2Spot。我们还使用 PreferNoSchedule 进行了污点，以优先不将 Pod 调度到 Spot 实例上。这是一种"优先"或"软"版本的 NoSchedule，即系统将尝试避免将不容忍污点的 Pod 放置在节点上，但这不是必需的。我们使用这种技术来确保只有正确类型的工作负载才会调度到 Spot 实例上。

``` yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: my-cluster-testscaling
  region: us-west-2
nodeGroups:
  - name: ng-spot
    labels:
      lifecycle: Ec2Spot
    taints:
      spotInstance: true:PreferNoSchedule
    minSize: 2
    maxSize: 5
    instancesDistribution: # 应至少指定两种实例类型
      instanceTypes:
        - m4.large
        - c4.large
        - c5.large
      onDemandBaseCapacity: 0
      onDemandPercentageAboveBaseCapacity: 0 # 所有实例都将是 Spot 实例
      spotInstancePools: 2
```
使用节点标签来识别节点的生命周期。
```
$ kubectl get nodes --label-columns=lifecycle --selector=lifecycle=Ec2Spot
```

我们还应该在每个 Spot 实例上部署 [AWS 节点终止处理程序](https://github.com/aws/aws-node-termination-handler)。它将监视实例上的 EC2 元数据服务以获取中断通知。终止处理程序由 ServiceAccount、ClusterRole、ClusterRoleBinding 和 DaemonSet 组成。AWS 节点终止处理程序不仅适用于 Spot 实例，还可以捕获一般 EC2 维护事件，因此可以在集群的所有工作节点上使用。

如果客户使用了良好的多样化和容量优化分配策略，Spot 实例将可用。您可以在清单文件中使用节点亲和力来进行配置，以优先使用 Spot 实例，但不是必需的。这将允许在没有可用或正确标记的 Spot 实例时，将 Pod 调度到按需节点上。

``` yaml

affinity:
nodeAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
  - weight: 1
    preference:
      matchExpressions:
      - key: lifecycle
        operator: In
        values:
        - Ec2Spot
tolerations:
- key: "spotInstance"
operator: "Equal"
value: "true"
effect: "PreferNoSchedule"

```

您可以在[在线 EC2 Spot 研讨会](https://ec2spotworkshops.com/using_ec2_spot_instances_with_eks.html)上完成有关 EC2 Spot 实例的完整研讨会。

### 使用计算节省计划

计算节省计划是一种灵活的折扣模式，它提供与预留实例相同的折扣，作为在一年或三年期内使用特定金额(以美元/小时计)计算能力的承诺。详细信息在[节省计划发布常见问题解答](https://aws.amazon.com/savingsplans/faq/)中介绍。这些计划会自动应用于任何 EC2 工作节点，无论区域、实例系列、操作系统或租赁，包括作为 EKS 集群一部分的节点。例如，您可以从 C4 切换到 C5 实例，将工作负载从都柏林移至伦敦，在此过程中仍可享受节省计划价格，而无需做任何操作。

AWS 成本资源管理器将帮助您选择节省计划，并指导您完成购买流程。
![计算节省计划](../images/Compute-savings-plan.png)

注意 - 计算节省计划现在也适用于 [AWS Fargate for AWS Elastic Kubernetes Service (EKS)](https://aws.amazon.com/about-aws/whats-new/2020/08/amazon-fargate-aws-eks-included-compute-savings-plan/)。

注意 - 上述定价不包括 Kubernetes 应用程序可能使用的其他 AWS 服务，如数据传输费用、CloudWatch、Elastic Load Balancer 和其他 AWS 服务。

## 资源
参考以下资源，了解有关成本优化最佳实践的更多信息。

### 视频
+	[AWS re:Invent 2019: 在 Spot 实例上以高达 90% 的折扣运行生产工作负载 (CMP331-R1)](https://www.youtube.com/watch?v=7q5AeoKsGJw)

### 文档和博客
+	[AWS 上 Kubernetes 的成本优化](https://aws.amazon.com/blogs/containers/cost-optimization-for-kubernetes-on-aws/)
+	[使用 Spot 实例为 EKS 构建成本优化和弹性](https://aws.amazon.com/blogs/compute/cost-optimization-and-resilience-eks-with-spot-instances/)
+ [使用自定义指标自动扩缩 EKS on Fargate](https://aws.amazon.com/blogs/containers/autoscaling-eks-on-fargate-with-custom-metrics/)
+ [AWS Fargate 注意事项](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)
+	[在 EKS 中使用 Spot 实例](https://ec2spotworkshops.com/using_ec2_spot_instances_with_eks.html)
+   [扩展 EKS API： 托管节点组](https://aws.amazon.com/blogs/containers/eks-managed-node-groups/)
+	[Amazon EKS 自动扩缩](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html)
+	[Amazon EKS 定价](https://aws.amazon.com/eks/pricing/)
+	[AWS Fargate 定价](https://aws.amazon.com/fargate/pricing/)
+   [节省计划](https://docs.aws.amazon.com/savingsplans/latest/userguide/what-is-savings-plans.html)
+   [在 AWS 上使用 Kubernetes 节省云成本](https://srcco.de/posts/saving-cloud-costs-kubernetes-aws.html)

### 工具
+  [Kube downscaler](https://github.com/hjacobs/kube-downscaler)
+  [Kubernetes Descheduler](https://github.com/kubernetes-sigs/descheduler)
+  [Cluster TurnDown](https://github.com/kubecost/cluster-turndown)