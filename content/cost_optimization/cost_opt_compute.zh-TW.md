---
日期: 2023-09-29
作者:
  - Justin Garrison
  - Rajdeep Saha
---
# 成本優化 - 計算和自動擴展

作為開發人員，您將對應用程式的資源需求做出估計，例如 CPU 和記憶體，但如果您不持續調整它們，它們可能會過時，從而增加成本並降低性能和可靠性。持續調整應用程式的資源需求比一開始就設置正確更為重要。

下面提到的最佳實踐將幫助您構建和運行具有成本意識的工作負載，實現業務目標並最小化成本，讓您的組織能夠最大化投資回報。優化集群計算成本的高級重要性順序如下:

1. 正確調整工作負載大小
2. 減少未使用的容量
3. 優化計算容量類型 (例如 Spot) 和加速器 (例如 GPU)

## 正確調整工作負載大小

在大多數 EKS 集群中，大部分成本來自用於運行容器化工作負載的 EC2 實例。如果不了解工作負載的需求，您將無法正確調整計算資源大小。這就是為什麼設置適當的請求和限制並根據需要對這些設置進行調整非常重要。此外,依賴項(如實例大小和存儲選擇)可能會影響工作負載性能,從而對成本和可靠性產生各種意外影響。

*請求* 應與實際利用率相匹配。如果容器的請求過高,將會產生未使用的容量,這是總集群成本的一個主要因素。Pod 中的每個容器(例如應用程式和 sidecar)都應該有自己的請求和限制設置,以確保 Pod 的總限制盡可能準確。

利用 [Goldilocks](https://www.youtube.com/watch?v=DfmQWYiwFDk)、[KRR](https://www.youtube.com/watch?v=uITOzpf82RY) 和 [Kubecost](https://aws.amazon.com/blogs/containers/aws-and-kubecost-collaborate-to-deliver-cost-monitoring-for-eks-customers/) 等工具為您的容器估算資源請求和限制。根據應用程式的性質、性能/成本要求和複雜性,您需要評估最佳擴展指標、應用程式性能降級的臨界點(飽和點),以及如何相應調整請求和限制。有關此主題的進一步指導,請參閱 [應用程式正確調整大小](https://aws.github.io/aws-eks-best-practices/scalability/docs/node_efficiency/#application-right-sizing)。

我們建議使用 Horizontal Pod Autoscaler (HPA) 來控制應運行多少個應用程式副本,使用 Vertical Pod Autoscaler (VPA) 來調整每個副本所需的請求和限制,以及使用 [Karpenter](http://karpenter.sh/) 或 [Cluster Autoscaler](https://github.com/kubernetes/autoscaler) 等節點自動擴展器來持續調整集群中的總節點數量。本文件後面的一節記錄了使用 Karpenter 和 Cluster Autoscaler 進行成本優化的技術。

Vertical Pod Autoscaler 可以調整分配給容器的請求和限制,以使工作負載以最佳方式運行。您應該在審核模式下運行 VPA,這樣它就不會自動進行更改和重新啟動您的 Pod。它將根據觀察到的指標建議進行更改。對於影響生產工作負載的任何更改,您應該首先在非生產環境中審查和測試這些更改,因為它們可能會影響您應用程式的可靠性和性能。

## 減少消耗

節省資金的最佳方式是配置更少的資源。一種方法是根據當前需求調整工作負載。您應該從確保工作負載定義其需求並動態擴展開始任何成本優化工作。這將需要從您的應用程式獲取指標,並設置配置,如 [`PodDisruptionBudgets`](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) 和 [Pod 就緒性檢查](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.5/deploy/pod_readiness_gate/),以確保您的應用程式可以安全地動態擴展。請注意,過於嚴格的 PodDisruptionBudgets 可能會阻止 Cluster Autoscaler 和 Karpenter 縮減節點,因為 Cluster Autoscaler 和 Karpenter 都會遵守 PodDisruptionBudgets。PodDisruptionBudget 中的 'minAvailable' 值應始終低於部署中的 Pod 數量,並且您應該在兩者之間保留一個良好的緩衝區,例如在有 6 個 Pod 的部署中,您希望始終至少有 4 個 Pod 運行,請將 PodDisruptionBidget 中的 'minAvailable' 設置為 4。這將允許 Cluster Autoscaler 和 Karpenter 在節點縮減事件期間安全地從利用率低的節點中排空和逐出 Pod。請參閱 [Cluster Autoscaler FAQ](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#what-types-of-pods-can-prevent-ca-from-removing-a-node) 文檔。

Horizontal Pod Autoscaler 是一個靈活的工作負載自動擴展器,可以根據各種指標(如 CPU、內存或自定義指標,例如隊列深度、與 Pod 的連接數等)調整所需的副本數量,以滿足應用程式的性能和可靠性需求。它有一個靈活的模型來定義何時根據各種指標進行擴展。

Kubernetes Metrics Server 支持根據內置指標(如 CPU 和內存使用情況)進行擴展,但如果您希望根據其他指標(如 Amazon CloudWatch 或 SQS 隊列深度)進行擴展,您應該考慮使用事件驅動的自動擴展項目,如 [KEDA](https://keda.sh/)。請參閱 [這篇博客文章](https://aws.amazon.com/blogs/mt/proactive-autoscaling-of-kubernetes-workloads-with-keda-using-metrics-ingested-into-amazon-cloudwatch/) 了解如何將 KEDA 與 CloudWatch 指標一起使用。如果您不確定要監控和擴展哪些指標,請查看 [監控重要指標的最佳實踐](https://aws-observability.github.io/observability-best-practices/guides/#monitor-what-matters)。

減少工作負載消耗會在集群中產生多餘的容量,並且通過適當的自動擴展配置,可以自動縮減節點並減少總支出。我們建議您不要嘗試手動優化計算容量。Kubernetes 調度器和節點自動擴展器旨在為您處理此過程。

## 減少未使用的容量

在確定了應用程式的正確大小並減少了多餘的請求之後,您可以開始減少配置的計算容量。如果您已經花時間正確調整工作負載大小,您應該能夠動態完成此操作。有兩個主要的節點自動擴展器可與 AWS 中的 Kubernetes 一起使用。

### Karpenter 和 Cluster Autoscaler

Karpenter 和 Kubernetes Cluster Autoscaler 都會隨著 Pod 的創建或刪除以及計算需求的變化而擴展集群中的節點數量。兩者的主要目標是相同的,但 Karpenter 採用了不同的節點管理配置和取消配置方法,可以幫助降低成本並優化整個集群的使用情況。

隨著集群規模的增長和工作負載種類的增加,預先配置節點組和實例變得越來越困難。就像工作負載請求一樣,設置一個初始基線並根據需要不斷調整非常重要。

如果您使用 Cluster Autoscaler,它將遵守每個自動擴展組 (ASG) 的"最小"和"最大"值,並且只調整"期望"值。在設置這些 ASG 的基礎值時要格外小心,因為 Cluster Autoscaler 將無法將 ASG 縮減到"最小"計數以下。將"期望"計數設置為您在正常營業時間需要的節點數量,將"最小"設置為您在非營業時間需要的節點數量。請參閱 [Cluster Autoscaler FAQ](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md#auto-discovery-setup) 文檔。

### Cluster Autoscaler 優先級擴展器

Kubernetes Cluster Autoscaler 通過根據應用程式的擴展和縮減來擴展和縮減節點組(稱為節點組)的規模來工作。如果您沒有動態擴展工作負載,那麼 Cluster Autoscaler 將無法幫助您節省資金。Cluster Autoscaler 需要集群管理員提前為工作負載創建節點組。節點組需要配置為使用具有相同"配置文件"的實例,即大致相同的 CPU 和內存。

您可以有多個節點組,並且可以配置 Cluster Autoscaler 設置優先級擴展級別,每個節點組可以包含不同大小的節點。節點組可以包含不同的容量類型,並且可以使用優先級擴展器首先擴展較便宜的組。

以下是一個使用 `ConfigMap` 優先擴展保留容量而不是按需實例的集群配置片段示例。您可以使用相同的技術來優先擴展 Graviton 或 Spot 實例而不是其他類型。

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: my-cluster
managedNodeGroups:
  - name: managed-ondemand
    minSize: 1
    maxSize: 7
    instanceType: m5.xlarge
  - name: managed-reserved
    minSize: 2
    maxSize: 10
    instanceType: c5.2xlarge
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    10:
      - .*ondemand.*
    50:
      - .*reserved.*
```

使用節點組可以幫助底層計算資源按預期執行,例如跨多個可用區域分佈節點,但並非所有工作負載都具有相同的需求或期望,最好讓應用程式明確聲明其需求。有關 Cluster Autoscaler 的更多信息,請參閱 [最佳實踐部分](https://aws.github.io/aws-eks-best-practices/cluster-autoscaling/)。

### Descheduler

Cluster Autoscaler 可以根據需要調度新的 Pod 或節點利用率不足來從集群中添加和刪除節點容量。但它無法全面查看 Pod 在調度到節點後的放置情況。如果您使用 Cluster Autoscaler,您還應該查看 [Kubernetes descheduler](https://github.com/kubernetes-sigs/descheduler),以避免浪費集群中的容量。

如果您的集群中有 10 個節點,每個節點的利用率為 60%,那麼您就浪費了集群中 40% 的配置容量。使用 Cluster Autoscaler,您可以為每個節點設置 60% 的利用率閾值,但只有在利用率低於 60% 時才會嘗試縮減單個節點。

使用 descheduler,它可以在 Pod 被調度或節點被添加到集群後查看集群容量和利用率。它會嘗試將集群的總容量保持在指定的閾值以上。它還可以根據節點污點或加入集群的新節點來刪除 Pod,以確保 Pod 在最佳計算環境中運行。請注意,descheduler 不會調度被逐出的 Pod 的替換,而是依賴默認調度器進行此操作。

### Karpenter 整合

Karpenter 採用了一種"無組"的節點管理方法。與其預先定義組並隨著工作負載需求擴展每個組,不如使用 provisioner 和節點模板來廣泛定義可以創建哪種類型的 EC2 實例以及實例創建時的設置。

Bin packing 是利用更多實例資源的做法,將更多工作負載打包到較少的、大小最佳的實例上。雖然這有助於減少計算成本,因為您只配置了工作負載使用的資源,但它也存在權衡。啟動新工作負載可能需要更長時間,因為需要向集群添加容量,尤其是在大規模擴展事件期間。在設置 bin packing 時,請考慮成本優化、性能和可用性之間的平衡。

Karpenter 可以持續監控和整合以提高實例資源利用率並降低計算成本。Karpenter 還可以為您的工作負載選擇更具成本效益的工作節點。這可以通過將 provisioner 中的"consolidation"標誌設置為 true 來實現(示例代碼片段如下)。下面的示例顯示了一個啟用整合的 provisioner。在撰寫本指南時,Karpenter 不會用更便宜的 Spot 實例替換正在運行的 Spot 實例。有關 Karpenter 整合的更多詳細信息,請參閱 [這篇博客文章](https://aws.amazon.com/blogs/containers/optimizing-your-kubernetes-compute-costs-with-karpenter-consolidation/)。

```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: enable-binpacking
spec:
  consolidation:
    enabled: true
```

對於可能無法中斷的工作負載(例如沒有檢查點的長期運行批處理作業),請考慮使用 `do-not-evict` 註釋來註釋 Pod。通過選擇不逐出 Pod,您是在告訴 Karpenter 它不應該自願刪除包含此 Pod 的節點。但是,如果在節點正在排空時添加了 `do-not-evict` Pod,其餘 Pod 仍將被逐出,但該 Pod 將阻止終止,直到被刪除為止。在任何一種情況下,該節點都將被封鎖,以防止在該節點上調度其他工作。以下是設置註釋的示例:

```yaml hl_lines="8"
apiVersion: v1
kind: Pod
metadata:
  name: label-demo
  labels:
    environment: production
  annotations:  
    "karpenter.sh/do-not-evict": "true"
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```

### 通過調整 Cluster Autoscaler 參數刪除利用率低的節點

節點利用率定義為請求的資源總和除以容量。默認情況下,`scale-down-utilization-threshold` 設置為 50%。此參數可以與 `scale-down-unneeded-time` 一起使用,後者確定節點在有資格縮減之前應該保持未使用狀態的時間 - 默認為 10 分鐘。仍在節點上運行的 Pod 將由 kube-scheduler 調度到其他節點。調整這些設置可以幫助刪除利用率低的節點,但重要的是您要先測試這些值,以免集群過早縮減。

您可以通過確保昂貴的 Pod 無法被逐出來防止縮減發生,Cluster Autoscaler 可以識別這些 Pod 的標籤。為此,請確保昂貴的 Pod 具有 `cluster-autoscaler.kubernetes.io/safe-to-evict=false` 註釋。下面是設置註釋的示例 yaml:

```yaml hl_lines="8"
apiVersion: v1
kind: Pod
metadata:
  name: label-demo
  labels:
    environment: production
  annotations:  
    "cluster-autoscaler.kubernetes.io/safe-to-evict": "false"
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```

### 為 Cluster Autoscaler 和 Karpenter 標記節點

AWS 資源 [標籤](https://docs.aws.amazon.com/tag-editor/latest/userguide/tagging.html) 用於組織您的資源,並詳細跟踪您的 AWS 成本。它們與 Kubernetes 標籤沒有直接關係,無法用於成本跟踪。建議從 Kubernetes 資源標籤開始,並利用 [Kubecost](https://aws.amazon.com/blogs/containers/aws-and-kubecost-collaborate-to-deliver-cost-monitoring-for-eks-customers/) 等工具獲取基於 Pod、命名空間等 Kubernetes 標籤的基礎設施成本報告。

工作節點需要有標籤才能在 AWS Cost Explorer 中顯示計費信息。對於 Cluster Autoscaler,請使用 [啟動模板](https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html) 標記托管節點組中的工作節點。對於自管理節點組,請使用 [EC2 自動擴展組](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-tagging.html) 標記您的實例。對於由 Karpenter 配置的實例,請使用 [spec.tags in the node template](https://karpenter.sh/docs/concepts/nodeclasses/#spectags) 進行標記。

### 多租戶集群

在處理由不同團隊共享的集群時,您可能無法查看在同一節點上運行的其他工作負載。雖然資源請求可以隔離某些"嘈雜鄰居"問題(如 CPU 共享),但它們可能無法隔離所有資源界限,如磁盤 I/O 耗盡。並非工作負載消耗的每種資源都可以被隔離或限制。消耗共享資源比率高於其他工作負載的工作負載應通過節點 [污點和容忍度](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) 進行隔離。對於此類工作負載的另一種高級技術是 [CPU 釘綁](https://kubernetes.io/docs/tasks/administer-cluster/cpu-management-policies/#static-policy),它可確保容器獲得獨占 CPU 而不是共享 CPU。

在節點級別隔離工作負載可能會更昂貴,但您可能可以調度 [BestEffort](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/#besteffort) 作業或利用使用 [保留實例](https://aws.amazon.com/ec2/pricing/reserved-instances/)、[Graviton 處理器](https://aws.amazon.com/ec2/graviton/) 或 [Spot](https://aws.amazon.com/ec2/spot/) 的額外節省。

共享集群還可能存在集群級資源限制,如 IP 耗盡、Kubernetes 服務限制或 API 擴展請求。您應該查看 [可擴展性最佳實踐指南](https://aws.github.io/aws-eks-best-practices/scalability/docs/control-plane/) 以確保您的集群避免這些限制。

您可以在命名空間或 Karpenter provisioner 級別隔離資源。[資源配額](https://kubernetes.io/docs/concepts/policy/resource-quotas/) 提供了一種限制命名空間中的工作負載可以消耗多少資源的方式。這可以作為一個很好的初始防護欄,但應該持續評估以確保它不會人為地限制工作負載的擴展。

Karpenter provisioner 可以 [設置集群中某些可消耗資源的限制](https://karpenter.sh/docs/concepts/nodepools/#speclimitsresources)(例如 CPU、GPU),但您需要配置租戶應用程式使用適當的 provisioner。這可以防止單個 provisioner 在集群中創建太多節點,但您應該持續評估以確保限制沒有設置過低而阻止工作負載擴展。

### 計劃自動擴展

您可能需要在週末和非工作時間縮減集群。這對於測試和非生產集群尤其重要,因為您希望在不使用時將其縮減為零。[cluster-turndown](https://github.com/kubecost/cluster-turndown) 和 [kube-downscaler](https://codeberg.org/hjacobs/kube-downscaler) 等解決方案可以根據 cron 計劃將副本縮減為零。

## 優化計算容量類型

在優化集群中的總計算容量並利用 bin packing 之後,您應該查看配置在集群中的計算類型以及您為這些資源支付的費用。AWS 有 [計算儲蓄計劃](https://aws.amazon.com/savingsplans/compute-pricing/),可以減少您的計算支出,我們將其分為以下容量類型:

* Spot
* 儲蓄計劃
* 按需
* Fargate

每種容量類型都有不同的管理開銷、可用性和長期承諾權衡,您需要決定哪種適合您的環境。任何環境都不應僅依賴單一容量類型,您可以在單個集群中混合使用多種運行類型,以優化特定工作負載的需求和成本。

### Spot

[Spot](https://aws.amazon.com/ec2/spot/) 容量類型從可用區域中的閒置容量配置 EC2 實例。Spot 提供高達 90% 的折扣,但這些實例可能會在需要時被中斷。此外,可能並非總是有容量來配置新的 Spot 實例,現有的 Spot 實例也可能會在 [2 分鐘中斷通知](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html) 後被回收。如果您的應用程式有較長的啟動或關閉過程,Spot 實例可能不是最佳選擇。

Spot 計算應使用各種實例類型,以減少沒有 Spot 容量可用的可能性。需要處理實例中斷以安全關閉節點。由 Karpenter 或作為托管節點組的一部分配置的節點自動支持 [實例中斷通知](https://aws.github.io/aws-eks-best-practices/karpenter/#enable-interruption-handling-when-using-spot)。如果您使用自管理節點,您將需要單獨運行 [節點終止處理程序](https://github.com/aws/aws-node-termination-handler) 以正常關閉 Spot 實例。

在單個集群中平衡 Spot 和按需實例是可能的。使用 Karpenter,您可以創建 [加權 provisioner](https://karpenter.sh/docs/concepts/scheduling/#on-demandspot-ratio-split) 來實現不同容量類型的平衡。使用 Cluster Autoscaler,您可以創建 [包含 Spot 和按需或保留實例的混合節點組](https://aws.amazon.com/blogs/containers/amazon-eks-now-supports-provisioning-and-managing-ec2-spot-instances-in-managed-node-groups/)。

以下是一個示例,展示如何使用 Karpenter 優先配置 Spot 實例而不是按需實例。在創建 provisioner 時,您可以指定 Spot、按需或兩者(如下所示)。當您同時指定兩者時,如果 Pod 沒有明確指定需要使用 Spot 還是按需,則 Karpenter 在配置節點時會優先使用 Spot,並採用 [價格-容量優化分配策略](https://aws.amazon.com/blogs/compute/introducing-price-capacity-optimized-allocation-strategy-for-ec2-spot-instances/)。

```yaml hl_lines="9"
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: spot-prioritized
spec:
  requirements:
    - key: "karpenter.sh/capacity-type" 
      operator: In
        values: ["spot", "on-demand"]
```

### 儲蓄計劃、保留實例和 AWS EDP

您可以通過使用 [計算儲蓄計劃](https://aws.amazon.com/savingsplans/compute-pricing/) 來減少計算支出。儲蓄計劃為 1 年或 3 年的計算使用承諾提供了降低價格。使用情況可以應用於 EKS 集群中的 EC2 實例,但也適用於 Lambda 和 Fargate 等任何計算使用。使用儲蓄計劃,您可以在承諾期內減少成本,同時仍可選擇任何 EC2 實例類型。

計算儲蓄計劃可以將您的 EC2 成本降低高達 66%,而無需承諾使用哪些實例類型、系列或區域。當您使用實例時,儲蓄將自動應用。

EC2 實例儲蓄計劃提供高達 72% 的計算節省,但需要在特定區域和 EC2 系列(例如 C 系列)中承諾使用。您可以在該區域內的任何可用區域使用該系列的任何代、任何大小的實例。折扣將自動應用於您帳戶中符合儲蓄計劃條件的任何實例。

[保留實例](https://aws.amazon.com/ec2/pricing/reserved-instances/) 類似於 EC2 實例儲蓄計劃,但它們還可以在可用區域或區域內保證容量,並比按需實例節省高達 72% 的成本。一旦您計算出需要多少保留容量,您就可以選擇保留的時間長度(1 年或 3 年)。折扣將自動應用於您帳戶中運行的那些 EC2 實例。

客戶還可以選擇與 AWS 簽訂企業協議。企業協議使客戶能夠量身定制最適合其需求的協議。客戶可以享受基於 AWS EDP (企業折扣計劃) 的定價折扣。有關企業協議的更多信息,請聯繫您的 AWS 銷售代表。

### 按需

與 Spot 相比,按需 EC2 實例具有不中斷的可用性優勢;與儲蓄計劃相比,沒有長期承諾。如果您希望在集群中降低成本,您應該減少對按需 EC2 實例的使用。

在優化工作負載需求後,您應該能夠為集群計算最小和最大容量。這個數字可能會隨時間變化,但很少會降低。考慮為低於最小值的所有內容使用儲蓄計劃,為不會影響應用程式可用性的容量使用 Spot。任何其他可能不會持續使用或需要可用性的內容都可以使用按需。

如本節所述,減少使用量的最佳方式是消耗更少的資源,並盡可能充分利用您配置的資源。使用 Cluster Autoscaler,您可以通過 `scale-down-utilization-threshold` 設置刪除利用率低的節點。對於 Karpenter,建議啟用整合。

要手動識別可用於您的工作負載的 EC2 實例類型,您應該使用 [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector),它可以顯示每個區域中可用的實例以及與 EKS 兼容的實例。以下是在 us-east-1 區域中具有 x86 處理器架構、4 Gb 內存、2 個 vCPU 並可用於 EKS 的實例的使用示例。

```bash
ec2-instance-selector --memory 4 --vcpus 2 --cpu-architecture x86_64 \
  -r us-east-1 --service eks
c5.large
c5a.large
c5ad.large
c5d.large
c6a.large
c6i.large
t2.medium
t3.medium
t3a.medium
```

對於非生產環境,您可以在夜間和週末等未使用時段自動縮減集群。kubecost 項目 [cluster-turndown](https://github.com/kubecost/cluster-turndown) 就是一個可以根據設置的時間表自動縮減集群的控制器示例。

### Fargate 計算

Fargate 計算是 EKS 集群的完全托管計算選項。它通過在 Kubernetes 集群中為每個 Pod 調度一個節點來提供 Pod 隔離。它允許您根據工作負載的 CPU 和 RAM 需求來調整計算節點的大小,從而精確控制集群中的工作負載使用情況。

Fargate 可以將工作負載縮小到 0.25 vCPU 和 0.5 GB 內存,最大可達 16 vCPU 和 120 GB 內存。可用的 [Pod 大小變體](https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html) 有限制,您需要了解您的工作負載最適合哪種 Fargate 配置。例如,如果您的工作負載需要 1 vCPU 和 0.5 GB 內存,最小的 Fargate Pod 將是 1 vCPU 和 2 GB 內存。

雖然 Fargate 有許多好處,如無需管理 EC2 實例或操作系統,但由於每個部署的 Pod 都在集群中作為單獨的節點進行隔離,因此它可能需要比傳統 EC2 實例更多的計算容量。這需要為 Kubelet、日誌代理和您通常會部署到節點的任何 DaemonSet 進行更多重複。Fargate 不支持 DaemonSet,它們需要轉換為與應用程式一起運行的 Pod "sidecar"。

Fargate 無法從 bin packing 或 CPU 過度配置中獲益,因為工作負載的邊界是一個節點,該節點不可突發或在工作負載之間共享。Fargate 將為您節省 EC2 實例管理時間(本身也是一種成本),但 CPU 和內存成本可能會比其他 EC2 容量類型更高。Fargate Pod 可以利用計算儲蓄計劃來降低按需成本。

## 優化計算使用

節省計算基礎設施費用的另一種方式是為工作負載使用更高效的計算。這可以來自更高性能的通用計算,如 [Graviton 處理器](https://aws.amazon.com/ec2/graviton/),比 x86 便宜 20% 且能源效率高 60% - 或特定於工作負載的加速器,如 GPU 和 [FPGA](https://aws.amazon.com/ec2/instance-types/f1/)。您需要構建可以 [在 arm 架構上運行](https://aws.amazon.com/blogs/containers/how-to-build-your-containers-for-arm-and-save-with-graviton-and-spot-instances-on-amazon-ecs/) 的容器,並 [設置具有正確加速器](https://aws.amazon.com/blogs/compute/running-gpu-accelerated-kubernetes-workloads-on-p3-and-p2-ec2-instances-with-amazon-eks/) 的節點供您的工作負載使用。

EKS 能夠運行具有混合架構(例如 amd64 和 arm64)的集群,如果您的容器為多個架構編譯,您可以通過在 provisioner 中允許兩種架構來利用 Karpenter 上的 Graviton 處理器。但是,為了保持一致的性能,建議您將每個工作負載保持在單一計算架構上,只有在沒有其他可用容量時才使用不同的架構。

Provisioner 可以配置為使用多個架構,工作負載也可以在其工作負載規範中請求特定架構。

```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: default
spec:
  requirements:
  - key: "kubernetes.io/arch"
    operator: In
    values: ["arm64", "amd64"]
```

使用 Cluster Autoscaler,您將需要為 Graviton 實例創建一個節點組,並在您的工作負載上設置 [節點容忍度](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) 以利用新的容量。

GPU 和 FPGA 可以大大提高工作負載的性能,但工作負載需要優化以使用加速器。許多用於機器學習和人工智能的工作負載類型都可以使用 GPU 進行計算,實例可以添加到集群中並通過資源請求掛載到工作負載中。

```yaml
spec:
  template:
    spec:
    - containers:
      ...
      resources:
          limits:
            nvidia.com/gpu: "1"
```

某些 GPU 硬件可以跨多個工作負載共享,因此單個 GPU 可以被配置和使用。要查看如何配置工作負載 GPU 共享,請參閱 [虛擬 GPU 設備插件](https://aws.amazon.com/blogs/opensource/virtual-gpu-device-plugin-for-inference-workload-in-kubernetes/) 以了解更多信息。您還可以參考以下博客:

* [在 Amazon EKS 上使用 NVIDIA 時間分片和加速型 EC2 實例實現 GPU 共享](https://aws.amazon.com/blogs/containers/gpu-sharing-on-amazon-eks-with-nvidia-time-slicing-and-accelerated-ec2-instances/)
* [在 Amazon EKS 上使用 NVIDIA 的 Multi-Instance GPU (MIG) 最大化 GPU 利用率: 每個 GPU 運行更多 Pod 以提高性能](https://aws.amazon.com/blogs/containers/maximizing-gpu-utilization-with-nvidias-multi-instance-gpu-mig-on-amazon-eks-running-more-pods-per-gpu-for-enhanced-performance/)
