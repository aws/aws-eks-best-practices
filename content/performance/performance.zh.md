# 性能效率支柱

性能效率支柱关注于高效利用计算资源以满足需求，以及如何在需求变化和技术发展的情况下保持效率。本节提供了在AWS上构建高性能效率架构的深入最佳实践指导。

## 定义

为确保高效利用EKS容器服务，您应该收集有关架构各个方面的数据，从高级设计到EKS资源类型的选择。通过定期审查您的选择，您可以确保利用不断发展的Amazon EKS和容器服务。监控将确保您了解任何偏离预期性能的情况，以便您可以采取行动。

EKS容器的性能效率由三个领域组成：

- 优化您的容器

- 资源管理

- 可扩展性管理

## 最佳实践

### 优化您的容器

您可以在Docker容器中运行大多数应用程序而不会遇到太多麻烦。但是，为了确保它在生产环境中有效运行，包括简化构建过程，您需要做一些事情。以下最佳实践将帮助您实现这一目标。

#### 建议

- **使您的容器镜像无状态：** 使用Docker镜像创建的容器应该是临时的和不可变的。换句话说，容器应该是可处理的和独立的，即可以构建和放置一个新的容器而无需进行任何配置更改。设计无状态容器。如果您想使用持久数据，请使用[卷](https://docs.docker.com/engine/admin/volumes/volumes/)。如果您想存储机密或服务使用的敏感应用程序数据，您可以使用诸如AWS [Systems Manager](https://aws.amazon.com/systems-manager/)[Parameter Store](https://aws.amazon.com/ec2/systems-manager/parameter-store/)或第三方产品或开源解决方案(如[HashiCorp Valut](https://www.vaultproject.io/)和[Consul](https://www.consul.io/))之类的解决方案进行运行时配置。
- [**最小基础镜像**](https://docs.docker.com/develop/develop-images/baseimages/)**:** 从一个小的基础镜像开始。Dockerfile中的每个其他指令都是在此镜像之上构建的。基础镜像越小，生成的镜像就越小，下载速度就越快。例如，[alpine:3.7](https://hub.docker.com/r/library/alpine/tags/)镜像比[centos:7](https://hub.docker.com/r/library/centos/tags/)镜像小71 MB。您甚至可以使用[scratch](https://hub.docker.com/r/library/scratch/)基础镜像，这是一个空镜像，您可以在其上构建自己的运行时环境。
- **避免不必要的包：** 在构建容器镜像时，只包含您的应用程序所需的依赖项，避免安装不必要的包。例如，如果您的应用程序不需要SSH服务器，请不要包含它。这将减少复杂性、依赖项、文件大小和构建时间。要排除与构建无关的文件，请使用.dockerignore文件。
- [**使用多阶段构建**](https://docs.docker.com/v17.09/engine/userguide/eng-image/multistage-build/#use-multi-stage-builds):多阶段构建允许您在第一个"构建"容器中构建应用程序，并在另一个容器中使用结果，同时使用相同的Dockerfile。稍微详细说明一下，在多阶段构建中，您在Dockerfile中使用多个FROM语句。每个FROM指令可以使用不同的基础，每个指令都开始构建的新阶段。您可以选择性地从一个阶段复制工件到另一个阶段，而将您不想在最终镜像中的所有内容都留在后面。这种方法极大地减小了最终镜像的大小，而无需努力减少中间层和文件的数量。
- **最小化层数：** Dockerfile中的每个指令都会为Docker镜像添加一个额外的层。指令和层的数量应保持在最小，因为这会影响构建性能和时间。例如，第一条指令将创建多个层，而第二条指令通过使用&&(链接)我们减少了层的数量，这将有助于提供更好的性能。这是减少Dockerfile中将创建的层数的最佳方式。
- 
    ```
            RUN apt-get -y update
            RUN apt-get install -y python
            RUN apt-get -y update && apt-get install -y python
    ```
            
- **正确标记您的镜像：** 构建镜像时，始终使用有用和有意义的标签对它们进行标记。这是一种组织和记录描述镜像的元数据的好方法，例如，包括来自CI服务器(如CodeBuild或Jenkins)的唯一计数器(如构建ID)，以帮助识别正确的镜像。如果您在Docker命令中没有提供标签，则默认使用latest标签。我们建议不要使用自动创建的latest标签，因为使用此标签，您将自动运行未来的主要版本，其中可能包含应用程序的重大更改。最佳实践是避免使用latest标签，而是使用由CI服务器创建的唯一摘要。
- **使用** [**构建缓存**](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/) **提高构建速度** : 缓存允许您利用现有的缓存镜像，而不是从头开始构建每个镜像。例如，您应该尽可能晚地将应用程序的源代码添加到Dockerfile中，这样基础镜像和应用程序的依赖项就会被缓存，并且不会在每次构建时都重新构建。要重用已缓存的镜像，默认情况下，在Amazon EKS中，kubelet将尝试从指定的注册表中拉取每个镜像。但是，如果容器的imagePullPolicy属性设置为IfNotPresent或Never，则将使用本地镜像(优先或专用)。
- **镜像安全：** 使用公共镜像可能是开始使用容器和将其部署到Kubernetes的一个很好的方式。但是，在生产中使用它们可能会带来一系列挑战。特别是在安全方面。确保遵循打包和分发容器/应用程序的最佳实践。例如，不要在容器中构建密码，您可能还需要控制它们的内容。建议使用私有存储库，如[Amazon ECR](https://aws.amazon.com/ecr/),并利用内置的[镜像扫描](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)功能来识别容器镜像中的软件漏洞。

- **正确调整容器大小：** 在开发和运行容器应用程序时，有一些关键领域需要考虑。您调整容器大小和管理应用程序部署的方式可能会对您提供的服务的最终用户体验产生负面影响。为了帮助您取得成功，以下最佳实践将帮助您正确调整容器大小。在确定应用程序所需的资源数量后，您应该在Kubernetes中设置请求和限制，以确保您的应用程序正常运行。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*(a) 对应用程序进行测试*: 收集关键统计数据和其他性能数据。根据这些数据，您可以确定容器的最佳配置，即内存和CPU。关键统计数据包括： __*CPU、延迟、I/O、内存使用量、网络*__ 。通过单独进行负载测试(如有必要)，确定预期、平均和峰值容器内存和CPU使用量。还要考虑可能并行运行在容器中的所有进程。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;建议使用[CloudWatch Container insights](https://aws.amazon.com/blogs/mt/introducing-container-insights-for-amazon-ecs/)或合作伙伴产品，它将为您提供正确的信息来调整容器和Worker节点的大小。


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*(b)独立测试服务：* 由于许多应用程序在真正的微服务架构中相互依赖，您需要以高度独立的方式对它们进行测试，这意味着服务能够正确独立运行，也能作为一个协调的系统运行。

### 资源管理

在采用Kubernetes时，最常见的问题之一是"*我应该在一个Pod中放什么？*"。例如，一个三层LAMP应用程序容器。我们应该将此应用程序保留在同一个pod中吗？这确实有效地作为一个单一的pod工作，但这是一个Pod创建的反模式示例。有两个原因

***(a)*** 如果您在同一个Pod中有两个容器，您将被迫使用相同的扩展策略，这对于生产环境来说是不理想的，您也无法根据使用情况有效地管理或约束资源。*例如：* 您可能只需要扩展前端，而不是将前端和后端(MySQL)作为一个单元进行扩展，如果您想仅增加专用于后端的资源，您也无法这样做。

***(b)*** 如果您有两个单独的Pod，一个用于前端，另一个用于后端。扩展将非常容易，并且您将获得更好的可靠性。

上述情况可能并不适用于所有用例。在上面的示例中，前端和后端可能会落在不同的机器上，它们将通过网络相互通信，因此您需要问这个问题："***如果它们被放置并在不同的机器上运行，我的应用程序是否会正常工作？***"如果答案是"***否***",可能是因为应用程序设计或其他一些技术原因，那么在单个pod中对容器进行分组是有意义的。如果答案是"***是***",那么多个Pod就是正确的方法。

#### 建议

+ **每个容器打包一个应用程序：**
容器在其中运行单个应用程序时效果最佳。该应用程序应该有一个单一的父进程。例如，不要在同一个容器中运行PHP和MySQL：这样更难调试，而且您无法单独水平扩展PHP容器。这种分离允许您更好地将应用程序的生命周期与容器的生命周期相关联。您的容器应该是无状态和不可变的。无状态意味着任何状态(任何类型的持久数据)都存储在容器之外，例如，如果需要，您可以使用不同类型的外部存储，如持久磁盘、Amazon EBS和Amazon EFS，或托管数据库，如Amazon RDS。不可变意味着容器在其生命周期内不会被修改：没有更新、补丁或配置更改。要更新应用程序代码或应用补丁，您需要构建一个新镜像并部署它。

+ **为Kubernetes对象使用标签：**
[标签](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/#labels)允许批量查询和操作Kubernetes对象。它们还可用于识别和组织Kubernetes对象到组中。因此，定义标签应该是任何Kubernetes最佳实践列表的首要任务。

+ **设置资源请求限制：**
设置请求限制是控制容器可以消耗的系统资源(如CPU和内存)数量的机制。这些设置是容器启动时保证获得的资源。如果容器请求资源，容器编排器(如Kubernetes)将只在可以提供该资源的节点上调度它。另一方面，限制确保容器永远不会超过某个值。容器只允许达到限制，然后就会受到限制。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 在下面的Pod清单示例中，我们添加了1.0 CPU和256 MB内存的限制

```
        apiVersion: v1
        kind: Pod
        metadata:
          name: nginx-pod-webserver
          labels:
            name: nginx-pod
        spec:
          containers:
          - name: nginx
            image: nginx:latest
            resources:
              limits:
                memory: "256Mi"
                cpu: "1000m"
              requests:
                memory: "128Mi"
                cpu: "500m"
            ports:
            - containerPort: 80

         
```


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;在pod定义中定义这些请求和限制是最佳实践。如果您不包含这些值，调度程序就无法了解所需的资源。如果没有这些信息，调度程序可能会将pod调度到没有足够资源提供可接受应用程序性能的节点上。

+ **限制并发中断的数量：**
使用_PodDisruptionBudget_，此设置允许您在自愿驱逐事件期间设置可用和不可用pod的最小和最大策略。驱逐的一个示例是在对节点进行维护或排空节点时。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; _示例：_ 一个Web前端可能希望在任何给定时间都有8个Pod可用。在这种情况下，驱逐可以驱逐任意多的pod，只要有八个可用即可。
```
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: frontend-demo
spec:
  minAvailable: 8
  selector:
    matchLabels:
      app: frontend
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**注意：** 您也可以通过使用maxAvailable或maxUnavailable参数以百分比的形式指定pod中断预算。

+ **使用命名空间：**
命名空间允许多个团队共享一个物理集群。命名空间允许将创建的资源划分到一个逻辑命名组中。这允许您每个命名空间设置资源配额、每个命名空间的基于角色的访问控制(RBAC)以及每个命名空间的网络策略。它为您提供了软多租户功能。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;例如，如果您在单个Amazon EKS集群上运行三个应用程序，由三个不同的团队访问，每个团队都需要多个资源约束和不同级别的QoS，您可以为每个团队创建一个命名空间，并为每个团队提供可以使用的资源(如CPU和内存)的配额。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您还可以通过启用[LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/)准入控制器在Kubernetes命名空间级别指定默认限制。这些默认限制将约束给定Pod可以使用的CPU或内存量，除非Pod的配置显式覆盖了这些默认值。

+ **管理资源配额：** 
每个命名空间都可以分配资源配额。指定配额允许限制在命名空间中所有资源可以消耗的集群资源量。资源配额可以由[ResourceQuota](https://kubernetes.io/docs/concepts/policy/resource-quotas/)对象定义。命名空间中ResourceQuota对象的存在确保了资源配额的实施。

+ **为Pod配置健康检查：**
健康检查是让系统知道应用程序实例是否正常工作的一种简单方式。如果应用程序实例不工作，其他服务就不应该访问它或向它发送请求。相反，应该将请求发送到正在工作的另一个应用程序实例。系统还应该将您的应用程序恢复到健康状态。默认情况下，所有正在运行的pod都将重启策略设置为always，这意味着节点上运行的kubelet将在容器遇到错误时自动重启pod。健康检查通过[容器探针](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)的概念扩展了kubelet的这一功能。

  Kubernetes提供两种[健康检查](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/):就绪和存活探针。例如，考虑一下，如果您的应用程序通常会长时间运行，但转换到非运行状态，并且只能通过重新启动来恢复。您可以使用存活探针来检测和补救此类情况。使用健康检查可以为您的应用程序提供更好的可靠性和更高的正常运行时间。


+ **高级调度技术：**
通常，调度程序确保只将pod放置在有足够可用资源的节点上，并且在节点之间，它们会尝试平衡资源利用率，例如节点、部署、副本等。但有时您希望控制如何调度pod。例如，也许您希望确保某些pod只在具有专用硬件(如GPU机器)的节点上调度，以用于ML工作负载。或者您希望将频繁通信的服务放在一起。

  Kubernetes提供了许多[高级调度功能](https://kubernetes.io/blog/2017/03/advanced-scheduling-in-kubernetes/)和多个过滤器/约束，以便在正确的节点上调度pod。例如，在使用Amazon EKS时，您可以使用[污点和容忍度](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#taints-and-toleations-beta-feature)来限制哪些工作负载可以在特定节点上运行。您还可以使用[节点选择器](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#nodeselector)和[亲和性和反亲和性](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity)构造来控制pod调度，甚至可以为此目的构建自己的自定义调度程序。

#### 可扩展性管理
  容器是无状态的。它们出生时，当它们死亡时，它们不会复活。您可以在Amazon EKS上利用许多技术，不仅可以扩展容器化应用程序，还可以扩展Kubernetes工作节点。
  
#### 建议

  + 在Amazon EKS上，您可以配置[Horizontal pod autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/),它根据观察到的CPU利用率(或使用[自定义指标](https://git.k8s.io/community/contributors/design-proposals/instrumentation/custom-metrics-api.md)基于应用程序提供的指标)自动扩展复制控制器、部署或副本集中的pod数量。

  + 您可以使用[Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler),它会自动调整pod的CPU和内存预留，以帮助"正确调整"应用程序的大小。这种调整可以提高集群资源利用率，并为其他pod释放CPU和内存。这在诸如您的生产数据库"MongoDB"与无状态应用程序前端不同方式扩展的情况下很有用。在这种情况下，您可以使用VPA来扩展MongoDB Pod。

  + 要启用VPA，您需要使用Kubernetes指标服务器，它是集群中资源使用数据的聚合器。它没有默认部署在Amazon EKS集群中。在[配置VPA](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html)之前，您需要配置它，或者您也可以使用Prometheus为Vertical Pod Autoscaler提供指标。

  + 虽然HPA和VPA可以扩展部署和pod，但[Cluster Autoscaler](https://github.com/kubernetes/autoscaler)将扩展和缩减工作节点池的大小。它根据当前利用率调整Kubernetes集群的大小。当有pod由于资源不足而无法在任何当前节点上调度，或者添加新节点会增加集群资源的整体可用性时，Cluster Autoscaler会增加集群的大小。请按照此[分步指南](https://eksworkshop.com/scaling/deploy_ca/)设置Cluster Autoscaler。如果您在AWS Fargate上使用Amazon EKS，AWS将为您管理控制平面。

     有关详细信息，请查看可靠性支柱。
     
#### 监控
#### 部署最佳实践
#### 权衡