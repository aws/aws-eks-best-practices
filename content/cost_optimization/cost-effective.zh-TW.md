# 具有成本效益的資源
具有成本效益的資源意味著使用適當的服務、資源和配置來運行在 Kubernetes 集群上的工作負載,這將導致成本節省。

## 建議
### 確保用於部署容器化服務的基礎設施與應用程序配置文件和擴展需求相匹配

Amazon EKS 支援幾種類型的 Kubernetes 自動擴展 - [Cluster Autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html)、[Horizontal Pod Autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html) 和 [Vertical Pod Autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html)。本節涵蓋其中兩個,Cluster Auto Scaler 和 Horizontal Pod Autoscaler。

### 使用 Cluster Autoscaler 調整 Kubernetes 集群的大小以滿足當前需求

[Kubernetes Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) 在由於缺乏資源而無法啟動 pod 或集群中的節點未充分利用且其 pod 可以重新調度到集群中的其他節點時,自動調整 EKS 集群中的節點數量。Cluster Autoscaler 在任何指定的 Auto Scaling 組中擴展工作節點,並作為部署在您的 EKS 集群中運行。

Amazon EKS 與 EC2 受管節點組自動化為 Amazon EKS Kubernetes 集群配置和管理節點(Amazon EC2 實例)的生命週期。所有受管節點都被配置為 Amazon EC2 Auto Scaling 組的一部分,由 Amazon EKS 為您管理,所有資源包括 Amazon EC2 實例和 Auto Scaling 組都在您的 AWS 帳戶中運行。Amazon EKS 標記受管節點組資源,以便 Kubernetes Cluster Autoscaler 可以發現它們。

https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html 的文檔提供了設置受管節點組並部署 Kubernetes Cluster Auto Scaler 的詳細指南。如果您正在跨多個可用區運行使用 Amazon EBS 卷作為支持的有狀態應用程序,並使用 Kubernetes Cluster Autoscaler,您應該配置多個節點組,每個節點組範圍限定在單個可用區。

*EC2 基礎工作節點的 Cluster Autoscaler 日誌 -*
![Kubernetes Cluster Auto Scaler 日誌](../images/cluster-auto-scaler.png)

當由於缺乏可用資源而無法調度 pod 時,Cluster Autoscaler 確定集群必須擴展,並增加節點組的大小。當使用多個節點組時,Cluster Autoscaler 根據 Expander 配置選擇一個。目前,EKS 支持以下策略:
+ **random** - 默認 expander,隨機選擇實例組
+ **most-pods** - 選擇可以調度最多 pod 的實例組。
+ **least-waste** - 選擇在擴展後將有最少空閒 CPU(如果並列,則為未使用的內存)的節點組。當您有不同類別的節點時,例如高 CPU 或高內存節點,並且只想在有需要大量這些資源的待處理 pod 時才擴展它們,這很有用。
+ **priority** - 選擇用戶分配的最高優先級的節點組

如果作為工作節點使用 EC2 Spot 實例,您可以使用 Cluster Autoscaler 中的 **random** 放置策略作為 Expander。這是默認的 expander,在集群必須擴展時任意選擇一個節點組。隨機 expander 最大限度地利用了多個 Spot 容量池。

[**Priority**](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/expander/priority/readme.md) 基於 expander 根據用戶為擴展組分配的優先級選擇擴展選項。示例優先級可以是讓 Autoscaler 首先嘗試擴展 Spot 實例節點組,如果無法擴展,則退而求其次擴展按需節點組。

當您使用 nodeSelector 確保某些 pod 落在特定節點上時,**most-pods** 基於 expander 很有用。

根據[文檔](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html),為 Cluster Autoscaling 配置指定 **least-waste** 作為 expander 類型:

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

### 部署 Horizontal Pod Autoscaling 以根據資源利用率或其他應用程序相關指標自動擴展部署、複製控制器或複製集中的 pod 數量

[Kubernetes Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) 根據資源指標(如 CPU 利用率)或具有自定義指標支持的其他應用程序提供的指標,自動擴展部署、複製控制器或複製集中的 pod 數量。這可以幫助您的應用程序擴展以滿足增加的需求,或在不需要資源時縮減,從而為其他應用程序釋放工作節點。當您設置目標指標利用率百分比時,Horizontal Pod Autoscaler 會擴展或縮減您的應用程序以嘗試滿足該目標。

[k8s-cloudwatch-adapter](https://github.com/awslabs/k8s-cloudwatch-adapter) 是 Kubernetes Custom Metrics API 和 External Metrics API 的實現,集成了 CloudWatch 指標。它允許您使用 Horizontal Pod Autoscaler (HPA) 根據 CloudWatch 指標擴展 Kubernetes 部署。

有關使用資源指標(如 CPU)進行擴展的示例,請按照 https://eksworkshop.com/beginner/080_scaling/test_hpa/ 部署示例應用程序、執行簡單的負載測試以測試 pod 自動擴展,並模擬 pod 自動擴展。

參考此[博客](https://aws.amazon.com/blogs/compute/scaling-kubernetes-deployments-with-amazon-cloudwatch-metrics/)中的示例,應用程序根據 Amazon SQS (Simple Queue Service) 隊列中的消息數量進行擴展的自定義指標。

來自博客的 Amazon SQS 外部指標示例:

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

利用此外部指標的 HPA 示例:

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

Kubernetes 工作節點的 Cluster Auto Scaler 和 pod 的 Horizontal Pod Autoscaler 的組合將確保配置的資源與實際利用率盡可能接近。

![Kubernetes Cluster AutoScaler 和 HPA](../images/ClusterAS-HPA.png)
***(圖像來源: https://aws.amazon.com/blogs/containers/cost-optimization-for-kubernetes-on-aws/)***

***Amazon EKS 與 Fargate***

****Horizontal Pod Autoscaling of Pods****

可以通過以下機制自動擴展 EKS on Fargate:

1. 使用 Kubernetes 指標服務器並根據 CPU 和/或內存使用情況配置自動擴展。
2. 根據 HTTP 流量等自定義指標使用 Prometheus 和 Prometheus 指標適配器配置自動擴展
3. 根據 App Mesh 流量配置自動擴展

上述情況在一篇關於["使用自定義指標自動擴展 EKS on Fargate"](https://aws.amazon.com/blogs/containers/autoscaling-eks-on-fargate-with-custom-metrics/)的實踐博客中有所解釋。

****Vertical Pod Autoscaling****

對於在 Fargate 上運行的 pod,使用 [Vertical Pod Autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html) 來優化應用程序使用的 CPU 和內存。但是,由於更改 pod 的資源分配需要重新啟動 pod,因此必須將 pod 更新策略設置為 Auto 或 Recreate 以確保正確功能。

## 建議

### 使用 Down Scaling 在非工作時間縮減 Kubernetes Deployments、StatefulSets 和/或 HorizontalPodAutoscalers。

作為控制成本的一部分,縮減未使用的資源也可以對總體成本產生巨大影響。有像 [kube-downscaler](https://github.com/hjacobs/kube-downscaler) 和 [Descheduler for Kubernetes](https://github.com/kubernetes-sigs/descheduler) 這樣的工具。

**Kube-descaler** 可用於在工作時間之後或在設定的時間段內縮減 Kubernetes 部署。

**Descheduler for Kubernetes** 根據其策略,可以找到可以移動的 pod 並將其驅逐。在目前的實現中,kubernetes descheduler 不會重新調度被驅逐的 pod,而是依賴默認的調度程序。

**Kube-descaler**

*安裝 kube-downscaler*:
```
git clone https://github.com/hjacobs/kube-downscaler
cd kube-downscaler
kubectl apply -k deploy/
```

示例配置使用 --dry-run 作為安全標誌以防止縮減 --- 通過編輯部署來刪除它以啟用縮減器,例如:
```
$ kubectl edit deploy kube-downscaler
```

部署一個 nginx pod 並安排它在時區 - 星期一至星期五 09:00-17:00 Asia/Kolkata 運行:
```
$ kubectl run nginx1 --image=nginx
$ kubectl annotate deploy nginx1 'downscaler/uptime=Mon-Fri 09:00-17:00 Asia/Kolkata'
```
!!! 注意
    新的 nginx 部署的默認寬限期為 15 分鐘,即如果當前時間不在星期一至星期五 9-17 (Asia/Kolkata 時區),它將不會立即縮減,而是在 15 分鐘後縮減。

![Kube-down-scaler for nginx](../images/kube-down-scaler.png)

更高級的縮減部署場景可在 [kube-down-scaler github 項目](https://github.com/hjacobs/kube-downscaler)中找到。

**Kubernetes descheduler**

Descheduler 可以作為作業或 CronJob 在 k8s 集群內運行。Descheduler 的策略是可配置的,並包括可以啟用或禁用的策略。目前已實現了七種策略 *RemoveDuplicates*、*LowNodeUtilization*、*RemovePodsViolatingInterPodAntiAffinity*、*RemovePodsViolatingNodeAffinity*、*RemovePodsViolatingNodeTaints*、*RemovePodsHavingTooManyRestarts* 和 *PodLifeTime*。更多詳細信息可以在他們的[文檔](https://github.com/kubernetes-sigs/descheduler)中找到。

一個示例策略,其中 descheduler 針對節點的低 CPU 利用率(涵蓋了利用率過低和過高的情況)、刪除太多重啟的 pod 和其他情況啟用:

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

**Cluster Turndown**

[Cluster Turndown](https://github.com/kubecost/cluster-turndown) 是根據自定義計劃和關閉條件自動縮減和擴展 Kubernetes 集群的後端節點。此功能可用於在閒置時間減少支出和/或減少安全風險面。最常見的用例是在非工作時間將非生產環境(例如開發集群)縮減為零。Cluster Turndown 目前處於 ALPHA 發行版。

Cluster Turndown 使用 Kubernetes 自定義資源定義來創建計劃。以下計劃將創建一個在指定的開始日期時間開始關閉,在指定的結束日期時間重新開啟的計劃(時間應為 RFC3339 格式,即基於與 UTC 的偏移的時間)。

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

### 使用 LimitRanges 和 Resource Quotas 通過限制在命名空間級別分配的資源量來幫助管理成本

默認情況下,容器在 Kubernetes 集群上運行時具有無限制的計算資源。使用資源配額,集群管理員可以限制基於命名空間的資源消耗和創建。在一個命名空間中,Pod 或容器可以消耗由該命名空間的資源配額定義的 CPU 和內存。存在一個 Pod 或容器可能會壟斷所有可用資源的問題。

Kubernetes 使用 Resource Quotas 和 Limit Ranges 控制對資源(如 CPU、內存、PersistentVolumeClaims 等)的分配。ResourceQuota 在命名空間級別,而 LimitRange 在容器級別應用。

***Limit Ranges***

LimitRange 是一種限制命名空間中資源分配(給 Pod 或容器)的策略。

以下是使用 Limit Range 設置默認內存請求和默認內存限制的示例。

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

更多示例可在 [Kubernetes 文檔](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/)中找到。

***Resource Quotas***

當多個用戶或團隊在具有固定節點數的集群上共享時,存在一個團隊可能使用超過其公平份額資源的問題。資源配額是管理員解決此問題的工具。

以下是如何在 ResourceQuota 對象中指定配額來設置所有在命名空間中運行的容器可以使用的總內存和 CPU 量的示例。這指定容器必須有內存請求、內存限制、CPU 請求和 CPU 限制,並且不應超過在 ResourceQuota 中設置的閾值。

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

更多示例可在 [Kubernetes 文檔](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/quota-memory-cpu-namespace/)中找到。

### 使用定價模型實現有效利用

Amazon EKS 的定價詳情在[定價頁面](https://aws.amazon.com/eks/pricing/)中給出。Amazon EKS on Fargate 和 EC2 有一個共同的控制平面成本。

如果您使用 AWS Fargate,定價是根據從開始下載容器映像到 Amazon EKS pod 終止時使用的 vCPU 和內存資源計算的,並向上捨入到最接近的秒。最低收費為 1 分鐘。請參閱 [AWS Fargate 定價頁面](https://aws.amazon.com/fargate/pricing/)上的詳細定價信息。

***Amazon EKS on EC2:***

Amazon EC2 提供了各種[實例類型](https://aws.amazon.com/ec2/instance-types/)來適應不同的用例。實例類型包括不同組合的 CPU、內存、存儲和網絡容量,並使您能夠靈活選擇適合目標工作負載的適當資源組合。每種實例類型包括一個或多個實例大小,允許您將資源擴展到目標工作負載的要求。

除了 CPU 數量、內存、處理器系列類型之外,與實例類型相關的一個關鍵決策參數是[Elastic 網絡接口(ENI)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html)的數量,這反過來又影響了您可以在該 EC2 實例上運行的最大 pod 數量。[每個 EC2 實例類型的最大 pod 數](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt)列表在 github 中維護。

****按需 EC2 實例:****

使用[按需實例](https://aws.amazon.com/ec2/pricing/),您可以按小時或秒為您運行的實例付費。不需要長期承諾或預付款。

Amazon EC2 A1 實例提供了顯著的成本節省,非常適合支持廣泛 Arm 生態系統的擴展和基於 ARM 的工作負載。您現在可以使用 Amazon Elastic Container Service for Kubernetes (EKS) 作為[公開開發者預覽](https://github.com/aws/containers-roadmap/tree/master/preview-programs/eks-arm-preview)的一部分在 Amazon EC2 A1 實例上運行容器。Amazon ECR 現在支持[多架構容器映像](https://aws.amazon.com/blogs/containers/introducing-multi-architecture-container-images-for-amazon-ecr/),這簡化了從同一映像庫部署不同架構和操作系統的容器映像。

您可以使用 [AWS Simple Monthly Calculator](https://calculator.s3.amazonaws.com/index.html) 或新的[定價計算器](https://calculator.aws/)來獲取 EKS 工作節點的按需 EC2 實例的定價。

### 使用 Spot EC2 實例:

Amazon [EC2 Spot 實例](https://aws.amazon.com/ec2/pricing/)允許您以高達按需價格的 90% 的折扣請求閒置的 Amazon EC2 計算容量。

Spot 實例通常非常適合無狀態的容器化工作負載,因為容器和 Spot 實例的方法類似;它們都是短暫的和自動擴展的容量。這意味著它們都可以被添加和刪除,同時遵守 SLA 並且不會影響應用程序的性能或可用性。

您可以創建多個節點組,其中包含按需實例類型和 EC2 Spot 實例的組合,以利用這兩種實例類型之間的定價優勢。

![按需和 Spot 節點組](../images/spot_diagram.png)
***(圖像來源: https://ec2spotworkshops.com/using_ec2_spot_instances_with_eks/spotworkers/workers_eksctl.html)***

下面是使用 eksctl 創建 EC2 Spot 實例節點組的示例 yaml 文件。在創建節點組期間,我們配置了一個節點標籤,以便 kubernetes 知道我們配置了什麼類型的節點。我們將節點的生命週期設置為 Ec2Spot。我們還使用 PreferNoSchedule 來污染,以便優先不將 pod 調度到 Spot 實例上。這是 NoSchedule 的"首選"或"軟"版本,即系統將嘗試避免將不容忍污點的 pod 放置在節點上,但這不是必需的。我們使用這種技術來確保只有正確類型的工作負載被調度到 Spot 實例上。

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
    instancesDistribution: # 應至少指定兩種實例類型
      instanceTypes:
        - m4.large
        - c4.large
        - c5.large
      onDemandBaseCapacity: 0
      onDemandPercentageAboveBaseCapacity: 0 # 所有實例都將是 Spot 實例
      spotInstancePools: 2
```
使用節點標籤來識別節點的生命週期。
```
$ kubectl get nodes --label-columns=lifecycle --selector=lifecycle=Ec2Spot
```

我們還應該在每個 Spot 實例上部署 [AWS Node Termination Handler](https://github.com/aws/aws-node-termination-handler)。它將監視實例上的 EC2 元數據服務以獲取中斷通知。終止處理程序由 ServiceAccount、ClusterRole、ClusterRoleBinding 和 DaemonSet 組成。AWS Node Termination Handler 不僅適用於 Spot 實例,它還可以捕獲一般 EC2 維護事件,因此可以在集群的所有工作節點上使用。

如果客戶使用容量優化分配策略並進行了良好的分散,Spot 實例將可用。您可以在清單文件中使用 Node Affinity 進行配置,以首選 Spot 實例,但不要求使用它們。這將允許在沒有可用或正確標記的 Spot 實例時,將 pod 調度到按需節點。

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

您可以在[在線 EC2 Spot 研討會](https://ec2spotworkshops.com/using_ec2_spot_instances_with_eks.html)中完成有關 EC2 Spot 實例的完整研討會。

### 使用計算節省計劃

計算節省計劃是一種靈活的折扣模式,它以承諾在一年或三年內使用特定金額(以美元/小時計)的計算能力為代價,為您提供與預留實例相同的折扣。詳細信息在[節省計劃發布常見問題解答](https://aws.amazon.com/savingsplans/faq/)中有所介紹。該計劃自動應用於任何 EC2 工作節點,無論地區、實例系列、操作系統或租賃,包括作為 EKS 集群一部分的節點。例如,您可以從 C4 轉移到 C5 實例,將工作負載從都柏林移至倫敦,並在此過程中受益於節省計劃價格,而無需做任何操作。

AWS Cost Explorer 將幫助您選擇節省計劃,並指導您完成購買過程。
![計算節省計劃](../images/Compute-savings-plan.png)

注意 - 計算節省計劃現在也適用於 [AWS Fargate for AWS Elastic Kubernetes Service (EKS)](https://aws.amazon.com/about-aws/whats-new/2020/08/amazon-fargate-aws-eks-included-compute-savings-plan/)。

注意 - 上述定價不包括 Kubernetes 應用程序可能使用的其他 AWS 服務,如數據傳輸費用、CloudWatch、Elastic Load Balancer 和其他 AWS 服務。

## 資源
參考以下資源以了解有關成本優化最佳實踐的更多信息。

### 視頻
+	[AWS re:Invent 2019: 以高達 90% 的折扣在 Spot 實例上運行生產工作負載 (CMP331-R1)](https://www.youtube.com/watch?v=7q5AeoKsGJw)

### 文檔和博客
+	[AWS 上 Kubernetes 的成本優化](https://aws.amazon.com/blogs/containers/cost-optimization-for-kubernetes-on-aws/)
+	[使用 Spot 實例為 EKS 構建成本優化和彈性](https://aws.amazon.com/blogs/compute/cost-optimization-and-resilience-eks-with-spot-instances/)
+ [使用自定義指標自動擴展 EKS on Fargate](https://aws.amazon.com/blogs/containers/autoscaling-eks-on-fargate-with-custom-metrics/)
+ [AWS Fargate 注意事項](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)
+	[在 EKS 中使用 Spot 實例](https://ec2spotworkshops.com/using_ec2_spot_instances_with_eks.html)
+   [擴展 EKS API: 受管節點組](https://aws.amazon.com/blogs/containers/eks-managed-node-groups/)
+	[Amazon EKS 自動擴展](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html) 
+	[Amazon EKS 定價](https://aws.amazon.com/eks/pricing/)
+	[AWS Fargate 定價](https://aws.amazon.com/fargate/pricing/)
+   [節省計劃](https://docs.aws.amazon.com/savingsplans/latest/userguide/what-is-savings-plans.html)
+   [在 AWS 上使用 Kubernetes 節省雲端成本](https://srcco.de/posts/saving-cloud-costs-kubernetes-aws.html) 

### 工具
+  [Kube downscaler](https://github.com/hjacobs/kube-downscaler)
+  [Kubernetes Descheduler](https://github.com/kubernetes-sigs/descheduler)
+  [Cluster TurnDown](https://github.com/kubecost/cluster-turndown)