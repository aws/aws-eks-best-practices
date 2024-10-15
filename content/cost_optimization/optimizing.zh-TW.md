# 隨時間優化 (Right Sizing)

根據 AWS Well-Architected Framework，Right Sizing 是「...使用最低成本的資源來滿足特定工作負載的技術規格」。

當您為 Pod 中的容器指定資源 `requests` 時，調度程序會使用此資訊來決定將 Pod 放置在哪個節點上。當您為容器指定資源 `limits` 時，kubelet 會強制執行這些限制，因此正在運行的容器不被允許使用超過您設置的該資源的限制。Kubernetes 如何管理容器資源的詳細資訊在 [文件](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) 中有說明。

在 Kubernetes 中，這意味著設置正確的計算資源 ([CPU 和記憶體統稱為計算資源](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)) - 設置與實際使用量盡可能接近的資源 `requests`。獲取 Pod 的實際資源使用情況的工具在下面的建議部分中給出。

**Amazon EKS on AWS Fargate**：當 Pod 在 Fargate 上調度時，Pod 規格中的 vCPU 和記憶體預留將決定為 Pod 配置多少 CPU 和記憶體。如果您未指定 vCPU 和記憶體組合，則將使用最小可用組合 (0.25 vCPU 和 0.5 GB 記憶體)。在 Fargate 上運行的 Pod 可用的 vCPU 和記憶體組合列表在 [Amazon EKS 使用者指南](https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html) 中列出。

**Amazon EKS on EC2**：當您創建 Pod 時，可以指定容器需要多少 CPU 和記憶體等資源。我們不應過度配置 (會導致浪費) 或配置不足 (會導致節流) 分配給容器的資源是很重要的。

## 建議
### 使用工具根據觀察到的數據來幫助您分配資源
有像 [kube resource report](https://github.com/hjacobs/kube-resource-report) 這樣的工具可以幫助對部署在 Amazon EKS 上的 EC2 節點的 Pod 進行 Right Sizing。

kube resource report 的部署步驟：
```
$ git clone https://github.com/hjacobs/kube-resource-report
$ cd kube-resource-report
$ helm install kube-resource-report ./unsupported/chart/kube-resource-report
$ helm status kube-resource-report
$ export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=kube-resource-report,app.kubernetes.io/instance=kube-resource-report" -o jsonpath="{.items[0].metadata.name}")
$ echo "Visit http://127.0.0.1:8080 to use your application"
$ kubectl port-forward $POD_NAME 8080:8080
```
來自該工具的示例報告的截圖：

![首頁](../images/kube-resource-report1.png)

![集群級數據](../images/kube-resource-report2.png)

![Pod 級數據](../images/kube-resource-report3.png)

**FairwindsOps Goldilocks**：[FairwindsOps Goldilocks](https://github.com/FairwindsOps/goldilocks) 是一個為命名空間中的每個部署創建垂直 Pod 自動調節器 (VPA) 並查詢它們以獲取資訊的工具。一旦 VPA 就位，我們就會在 Goldilocks 儀表板上看到建議。

按照 [文件](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html) 部署垂直 Pod 自動調節器。

啟用命名空間 - 選擇一個應用程序命名空間並對其進行標記，以便查看一些數據，在以下示例中，我們指定了 default 命名空間：

```
$ kubectl label ns default goldilocks.fairwinds.com/enabled=true
```

查看儀表板 - 默認安裝為儀表板創建了一個 ClusterIP 服務。您可以通過端口轉發訪問：

```
$ kubectl -n goldilocks port-forward svc/goldilocks-dashboard 8080:80
```

然後在瀏覽器中打開 http://localhost:8080

![Goldilocks 建議頁面](../images/Goldilocks.png)

### 使用 CloudWatch Container Insights 和 Prometheus Metrics in Amazon CloudWatch 等應用程序分析工具

使用 [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html) 來查看如何使用原生 CloudWatch 功能來監控您的 EKS 集群性能。您可以使用 CloudWatch Container Insights 來收集、聚合和總結運行在 Amazon Elastic Kubernetes Service 上的容器化應用程序和微服務的指標和日誌。這些指標包括 CPU、記憶體、磁盤和網絡等資源的使用情況 - 這可以幫助對 Pod 進行 Right Sizing 並節省成本。

[Container Insights Prometheus Metrics Monitoring](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights-Prometheus-metrics.html) 目前，對 Prometheus 指標的支持仍處於測試階段。CloudWatch Container Insights 監控自動發現來自容器化系統和工作負載的 Prometheus 指標。Prometheus 是一個開源的系統監控和警報工具包。所有 Prometheus 指標都收集在 ContainerInsights/Prometheus 命名空間中。

cAdvisor 和 kube-state-metrics 提供的指標可用於使用 Prometheus 和 Grafana 監控在 AWS Fargate 上的 Amazon EKS Pod，然後可用於在您的容器中實現 **requests**。更多詳細資訊，請參閱 [此博客](https://aws.amazon.com/blogs/containers/monitoring-amazon-eks-on-aws-fargate-using-prometheus-and-grafana/)。

**Right Size Guide**：[right size guide (rsg)](https://mhausenblas.info/right-size-guide/) 是一個簡單的 CLI 工具，為您的應用程序提供記憶體和 CPU 建議。該工具可跨容器編排器工作，包括 Kubernetes，並且易於部署。

通過使用 CloudWatch Container Insights、Kube Resource Report、Goldilocks 和其他工具，可以對運行在 Kubernetes 集群中的應用程序進行 Right Sizing，從而有可能降低成本。

## 資源
參考以下資源以了解更多有關成本優化的最佳實踐。

### 文件和博客
+ [Amazon EKS Workshop - 設置 EKS CloudWatch Container Insights](https://www.eksworkshop.com/intermediate/250_cloudwatch_container_insights/)
+ [在 Amazon CloudWatch 中使用 Prometheus 指標](https://aws.amazon.com/blogs/containers/using-prometheus-metrics-in-amazon-cloudwatch/)
+ [使用 Prometheus 和 Grafana 監控在 AWS Fargate 上的 Amazon EKS](https://aws.amazon.com/blogs/containers/monitoring-amazon-eks-on-aws-fargate-using-prometheus-and-grafana/)

### 工具
+ [Kube resource report](https://github.com/hjacobs/kube-resource-report)
+ [Right size guide](https://github.com/mhausenblas/right-size-guide)
+ [Fargate count](https://github.com/mreferre/fargatecount)
+ [FairwindsOps Goldilocks](https://github.com/FairwindsOps/goldilocks)
+ [Choose Right Node Size](https://learnk8s.io/research#choosing-node-size)