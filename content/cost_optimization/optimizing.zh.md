# 随时间优化 (合理调整规模)

根据 AWS 架构优化白皮书，合理调整规模是"...使用满足特定工作负载技术规范的最低成本资源"。

当您为 Pod 中的容器指定资源 `requests` 时，调度程序会使用此信息来决定将 Pod 放置在哪个节点上。当您为容器指定资源 `limits` 时，kubelet 会强制执行这些限制，以便运行中的容器不被允许使用超过您设置的该资源的限制。Kubernetes 如何管理容器资源的详细信息在 [文档](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) 中给出。

在 Kubernetes 中，这意味着设置正确的计算资源 ([CPU 和内存统称为计算资源](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)) - 设置与实际利用率尽可能接近的资源 `requests`。获取 Pod 实际资源使用情况的工具在下面的建议部分给出。

**AWS Fargate 上的 Amazon EKS**:当 Pod 在 Fargate 上调度时，Pod 规范中的 vCPU 和内存预留决定为 Pod 预留多少 CPU 和内存。如果您不指定 vCPU 和内存组合，则使用最小可用组合 (0.25 vCPU 和 0.5 GB 内存)。在 Fargate 上运行的 Pod 可用的 vCPU 和内存组合列表在 [Amazon EKS 用户指南](https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html) 中列出。

**EC2 上的 Amazon EKS**:当您创建 Pod 时，可以指定容器需要多少 CPU 和内存等资源。我们不能过度配置 (会导致浪费) 或者欠配置 (会导致节流) 分配给容器的资源是很重要的。

## 建议
### 使用工具帮助您根据观察到的数据分配资源
有一些工具，如 [kube resource report](https://github.com/hjacobs/kube-resource-report)，可以帮助合理调整部署在 Amazon EKS EC2 节点上的 Pod 的规模。

kube resource report 的部署步骤：
```
$ git clone https://github.com/hjacobs/kube-resource-report
$ cd kube-resource-report
$ helm install kube-resource-report ./unsupported/chart/kube-resource-report
$ helm status kube-resource-report
$ export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=kube-resource-report,app.kubernetes.io/instance=kube-resource-report" -o jsonpath="{.items[0].metadata.name}")
$ echo "访问 http://127.0.0.1:8080 以使用您的应用程序"
$ kubectl port-forward $POD_NAME 8080:8080
```
来自该工具的示例报告的屏幕截图：

![主页](../images/kube-resource-report1.png)

![集群级数据](../images/kube-resource-report2.png)

![Pod 级数据](../images/kube-resource-report3.png)

**FairwindsOps Goldilocks**: [FairwindsOps Goldilocks](https://github.com/FairwindsOps/goldilocks) 是一个为命名空间中的每个部署创建垂直 Pod 自动缩放器 (VPA) 并查询它们以获取信息的工具。一旦 VPA 就绪，我们就会在 Goldilocks 仪表板上看到建议。

根据 [文档](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html) 部署垂直 Pod 自动缩放器。

启用命名空间 - 选择一个应用程序命名空间并对其进行标记，以便查看一些数据，在以下示例中，我们指定了默认命名空间：

```
$ kubectl label ns default goldilocks.fairwinds.com/enabled=true
```

查看仪表板 - 默认安装为仪表板创建了一个 ClusterIP 服务。您可以通过端口转发访问：

```
$ kubectl -n goldilocks port-forward svc/goldilocks-dashboard 8080:80
```

然后在浏览器中打开 http://localhost:8080

![Goldilocks 建议页面](../images/Goldilocks.png)

### 使用 Amazon CloudWatch 中的 CloudWatch Container Insights 和 Prometheus 指标等应用程序分析工具

使用 [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html) 来查看如何使用原生 CloudWatch 功能来监控您的 EKS 集群性能。您可以使用 CloudWatch Container Insights 来收集、聚合和汇总运行在 Amazon Elastic Kubernetes Service 上的容器化应用程序和微服务的指标和日志。这些指标包括 CPU、内存、磁盘和网络等资源的利用率，这可以帮助合理调整 Pod 的规模并节省成本。

[Container Insights Prometheus 指标监控](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights-Prometheus-metrics.html) 目前，对 Prometheus 指标的支持仍处于测试阶段。CloudWatch Container Insights 监控自动发现来自容器化系统和工作负载的 Prometheus 指标。Prometheus 是一个开源的系统监控和警报工具包。所有 Prometheus 指标都收集在 ContainerInsights/Prometheus 命名空间中。

cAdvisor 和 kube-state-metrics 提供的指标可用于使用 Prometheus 和 Grafana 监控在 AWS Fargate 上的 Amazon EKS Pod，然后可用于在您的容器中实现 **requests**。更多详细信息请参阅 [此博客](https://aws.amazon.com/blogs/containers/monitoring-amazon-eks-on-aws-fargate-using-prometheus-and-grafana/)。

**Right Size Guide**: [right size guide (rsg)](https://mhausenblas.info/right-size-guide/) 是一个简单的 CLI 工具，为您的应用程序提供内存和 CPU 建议。该工具可跨容器编排器工作，包括 Kubernetes，并且易于部署。

通过使用 CloudWatch Container Insights、Kube Resource Report、Goldilocks 和其他工具，可以合理调整运行在 Kubernetes 集群中的应用程序的规模，从而可能降低成本。

## 资源
参考以下资源，了解有关成本优化最佳实践的更多信息。

### 文档和博客
+ [Amazon EKS 研讨会 - 设置 EKS CloudWatch Container Insights](https://www.eksworkshop.com/intermediate/250_cloudwatch_container_insights/)
+ [在 Amazon CloudWatch 中使用 Prometheus 指标](https://aws.amazon.com/blogs/containers/using-prometheus-metrics-in-amazon-cloudwatch/)
+ [使用 Prometheus 和 Grafana 监控在 AWS Fargate 上的 Amazon EKS](https://aws.amazon.com/blogs/containers/monitoring-amazon-eks-on-aws-fargate-using-prometheus-and-grafana/)

### 工具
+ [Kube resource report](https://github.com/hjacobs/kube-resource-report)
+ [Right size guide](https://github.com/mhausenblas/right-size-guide)
+ [Fargate count](https://github.com/mreferre/fargatecount)
+ [FairwindsOps Goldilocks](https://github.com/FairwindsOps/goldilocks)
+ [Choose Right Node Size](https://learnk8s.io/research#choosing-node-size)