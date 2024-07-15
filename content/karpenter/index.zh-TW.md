# Karpenter 最佳實踐

## Karpenter

Karpenter 是一個開源叢集自動擴展器,可自動為無法調度的 Pod 佈建新節點。Karpenter 會評估待處理 Pod 的總體資源需求,並選擇最佳的執行個體類型來執行它們。它將自動縮減或終止沒有任何非 daemonset Pod 的執行個體,以減少浪費。它還支援合併功能,可主動移動 Pod,並刪除或替換為較便宜的版本,以降低叢集成本。

**使用 Karpenter 的原因**

在推出 Karpenter 之前,Kubernetes 使用者主要依賴 [Amazon EC2 Auto Scaling 群組](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) 和 [Kubernetes Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) (CAS) 來動態調整叢集的計算容量。使用 Karpenter,您不需要建立數十個節點群組來達到 Karpenter 所提供的靈活性和多樣性。此外,Karpenter 與 Kubernetes 版本的耦合性不像 CAS 那麼緊密,也不需要您在 AWS 和 Kubernetes API 之間跳轉。

Karpenter 將執行個體編排職責合併到單一系統中,這種方式更簡單、更穩定且具有叢集感知能力。Karpenter 的設計旨在克服 Cluster Autoscaler 所面臨的一些挑戰,提供簡化的方式來:

* 根據工作負載需求佈建節點。
* 使用靈活的 NodePool 選項,透過執行個體類型建立多樣化的節點配置。不需要管理許多特定的自訂節點群組,Karpenter 可以讓您使用單一靈活的 NodePool 來管理多樣化的工作負載容量。
* 透過快速啟動節點和調度 Pod,達到大規模 Pod 調度的改善。

有關使用 Karpenter 的資訊和文件,請訪問 [karpenter.sh](https://karpenter.sh/) 網站。

## 建議

最佳實踐分為 Karpenter 本身、NodePool 和 Pod 調度等部分。

## Karpenter 最佳實踐

以下最佳實踐涵蓋與 Karpenter 本身相關的主題。

### 對於容量需求變化的工作負載使用 Karpenter

Karpenter 將擴展管理更接近 Kubernetes 原生 API,而不是 [Autoscaling 群組](https://aws.amazon.com/blogs/containers/amazon-eks-cluster-multi-zone-auto-scaling-groups/) (ASG) 和 [Managed Node 群組](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) (MNG)。ASG 和 MNG 是 AWS 原生抽象,其中擴展是根據 AWS 層級的指標(如 EC2 CPU 負載)觸發的。[Cluster Autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html#cluster-autoscaler) 將 Kubernetes 抽象與 AWS 抽象連接,但由於這種連接而失去了一些靈活性,例如針對特定可用區域進行調度。

Karpenter 移除了一層 AWS 抽象,將部分靈活性直接帶入 Kubernetes。Karpenter 最適合用於遇到高峰期或具有多樣化計算需求的叢集工作負載。MNG 和 ASG 適用於執行趨於靜態和一致的工作負載的叢集。根據您的需求,您可以混合使用動態和靜態管理的節點。

### 在以下情況考慮其他自動擴展專案...

如果您需要 Karpenter 尚未開發的功能。由於 Karpenter 是一個相對較新的專案,如果您目前需要 Karpenter 尚未包含的功能,請考慮使用其他自動擴展專案。

### 在 EKS Fargate 或屬於節點群組的工作節點上執行 Karpenter 控制器

Karpenter 是使用 [Helm 圖表](https://karpenter.sh/docs/getting-started/) 安裝的。Helm 圖表會安裝 Karpenter 控制器和一個 Webhook Pod,作為一個需要在使用 Karpenter 進行擴展之前執行的部署。我們建議至少有一個小型節點群組,其中至少有一個工作節點。或者,您可以透過為 `karpenter` 命名空間建立 Fargate 設定檔,在 EKS Fargate 上執行這些 Pod。這樣做會導致部署到此命名空間的所有 Pod 都在 EKS Fargate 上執行。請勿在由 Karpenter 管理的節點上執行 Karpenter。

### 避免使用自訂啟動範本與 Karpenter

Karpenter 強烈建議不要使用自訂啟動範本。使用自訂啟動範本會阻止多架構支援、自動升級節點的能力以及安全群組探索。使用啟動範本也可能造成混淆,因為某些欄位在 Karpenter 的 NodePool 中是重複的,而其他則被 Karpenter 忽略,例如子網和執行個體類型。

您通常可以透過使用自訂使用者資料和/或直接在 AWS 節點範本中指定自訂 AMI,來避免使用啟動範本。如何執行的更多資訊,請參閱 [NodeClasses](https://karpenter.sh/docs/concepts/nodeclasses/)。

### 排除不符合您工作負載的執行個體類型

如果某些執行個體類型不符合您叢集中執行的工作負載需求,請考慮使用 [node.kubernetes.io/instance-type](http://node.kubernetes.io/instance-type) 鍵來排除特定執行個體類型。

以下範例顯示如何避免佈建大型 Graviton 執行個體。

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

### 啟用中斷處理時使用 Spot

Karpenter 支援透過 `--interruption-queue-name` CLI 引數和 SQS 佇列名稱啟用 [原生中斷處理](https://karpenter.sh/docs/concepts/disruption/#interruption)。中斷處理會監視即將發生的非自願中斷事件,這些事件會導致您的工作負載中斷,例如:

* Spot 中斷警告
* 排程變更健康狀態事件 (維護事件)
* 執行個體終止事件
* 執行個體停止事件

當 Karpenter 偵測到這些事件將發生在您的節點上時,它會自動封鎖、清空和終止節點,以在中斷事件發生前提供最長的時間來進行工作負載清理。不建議與 Karpenter 一起使用 AWS Node Termination Handler,如 [這裡](https://karpenter.sh/docs/faq/#interruption-handling) 所解釋。

需要檢查點或其他形式的正常排空的 Pod,在關機前需要 2 分鐘,應在其叢集中啟用 Karpenter 中斷處理。

### **沒有對外網際網路存取的 Amazon EKS 私有叢集**

當在沒有路由到網際網路的 VPC 中佈建 EKS 叢集時,您必須確保已根據 EKS 文件中出現的私有叢集 [需求](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html#private-cluster-requirements) 配置您的環境。此外,您需要確保已在 VPC 中建立 STS VPC 區域端點。否則,您將看到類似以下的錯誤。

```console
{"level":"FATAL","time":"2024-02-29T14:28:34.392Z","logger":"controller","message":"Checking EC2 API connectivity, WebIdentityErr: failed to retrieve credentials\ncaused by: RequestError: send request failed\ncaused by: Post \"https://sts.<region>.amazonaws.com/\": dial tcp 54.239.32.126:443: i/o timeout","commit":"596ea97"}
```

在私有叢集中需要進行這些變更,因為 Karpenter 控制器使用服務帳戶的 IAM 角色 (IRSA)。配置了 IRSA 的 Pod 會透過呼叫 AWS 安全權杖服務 (AWS STS) API 來獲取憑證。如果沒有對外網際網路存取,您必須在 VPC 中建立和使用 ***AWS STS VPC 端點***。

私有叢集還需要您為 SSM 建立 ***VPC 端點***。當 Karpenter 嘗試佈建新節點時,它會查詢啟動範本配置和 SSM 參數。如果您的 VPC 中沒有 SSM VPC 端點,將會導致以下錯誤:

```console
{"level":"ERROR","time":"2024-02-29T14:28:12.889Z","logger":"controller","message":"Unable to hydrate the AWS launch template cache, RequestCanceled: request context canceled\ncaused by: context canceled","commit":"596ea97","tag-key":"karpenter.k8s.aws/cluster","tag-value":"eks-workshop"}
...
{"level":"ERROR","time":"2024-02-29T15:08:58.869Z","logger":"controller.nodeclass","message":"discovering amis from ssm, getting ssm parameter \"/aws/service/eks/optimized-ami/1.27/amazon-linux-2/recommended/image_id\", RequestError: send request failed\ncaused by: Post \"https://ssm.<region>.amazonaws.com/\": dial tcp 67.220.228.252:443: i/o timeout","commit":"596ea97","ec2nodeclass":"default","query":"/aws/service/eks/optimized-ami/1.27/amazon-linux-2/recommended/image_id"}
```

沒有 ***[價格清單查詢 API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-pelong.html) 的 VPC 端點***。
因此,隨著時間的推移,定價資料將會過期。
Karpenter 透過在其二進位檔中包含隨需付費定價資料來解決這個問題,但只有在升級 Karpenter 時才會更新該資料。
對定價資料的失敗請求將導致以下錯誤訊息:

```console
{"level":"ERROR","time":"2024-02-29T15:08:58.522Z","logger":"controller.pricing","message":"retreiving on-demand pricing data, RequestError: send request failed\ncaused by: Post \"https://api.pricing.<region>.amazonaws.com/\": dial tcp 18.196.224.8:443: i/o timeout; RequestError: send request failed\ncaused by: Post \"https://api.pricing.<region>.amazonaws.com/\": dial tcp 18.185.143.117:443: i/o timeout","commit":"596ea97"}
```

總之,要在完全私有的 EKS 叢集中使用 Karpenter,您需要建立以下 VPC 端點:

```console
com.amazonaws.<region>.ec2
com.amazonaws.<region>.ecr.api
com.amazonaws.<region>.ecr.dkr
com.amazonaws.<region>.s3 – 用於拉取容器映像
com.amazonaws.<region>.sts – 用於服務帳戶的 IAM 角色
com.amazonaws.<region>.ssm - 用於解析預設 AMI
com.amazonaws.<region>.sqs - 用於存取 SQS (如果使用中斷處理)
```

!!! 注意
    Karpenter (控制器和 Webhook 部署) 容器映像必須在 Amazon ECR 私有或其他可從 VPC 內部存取的私有登錄中。原因是 Karpenter 控制器和 Webhook Pod 目前使用公開 ECR 映像。如果這些映像無法從 VPC 內部或與 VPC 對等的網路存取,您將會在 Kubernetes 嘗試從 ECR 公開拉取這些映像時遇到映像拉取錯誤。

有關更多資訊,請參閱 [Issue 988](https://github.com/aws/karpenter/issues/988) 和 [Issue 1157](https://github.com/aws/karpenter/issues/1157)。

## 建立 NodePool

以下最佳實踐涵蓋與建立 NodePool 相關的主題。

### 在以下情況下建立多個 NodePool...

當不同團隊共用一個叢集並需要在不同的工作節點上執行他們的工作負載,或者有不同的作業系統或執行個體類型需求時,請建立多個 NodePool。例如,一個團隊可能想要使用 Bottlerocket,而另一個團隊可能想要使用 Amazon Linux。同樣地,一個團隊可能可以存取昂貴的 GPU 硬體,而另一個團隊則不需要。使用多個 NodePool 可確保每個團隊都可獲得最適合的資源。

### 建立相互排斥或加權的 NodePool

建議建立相互排斥或加權的 NodePool,以提供一致的調度行為。如果它們不是,並且多個 NodePool 都符合條件,Karpenter 將隨機選擇使用哪一個,導致意外的結果。建立多個 NodePool 的有用範例包括以下:

建立一個具有 GPU 的 NodePool,並只允許特殊工作負載在這些(昂貴的)節點上運行:

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

部署具有容忍度的工作負載:

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

對於另一個團隊的一般部署,NodePool 規格可以包含 nodeAffinify。部署可以使用 nodeSelectorTerms 來匹配 `billing-team`。

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

使用 nodeAffinity 的部署:

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

### 使用計時器 (TTL) 自動從叢集刪除節點

您可以為佈建的節點設置計時器,以設定何時刪除沒有工作負載 Pod 或已到期的節點。節點到期可用作升級的一種方式,以便淘汰節點並用更新版本替換。請參閱 Karpenter 文件中的 [到期](https://karpenter.sh/docs/concepts/disruption/) 以獲取有關使用 `spec.disruption.expireAfter` 配置節點到期的資訊。

### 避免過度限制 Karpenter 可以佈建的執行個體類型,尤其是在使用 Spot 時

在使用 Spot 時,Karpenter 使用 [Price Capacity Optimized](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-fleet-allocation-strategy.html) 分配策略來佈建 EC2 執行個體。此策略指示 EC2 從最深的池中佈建您要啟動的執行個體數量,並且具有最低的中斷風險。然後 EC2 Fleet 會從這些池中最低價格的池中請求 Spot 執行個體。您允許 Karpenter 使用的執行個體類型越多,EC2 就越能優化您的 Spot 執行個體的運行時間。預設情況下,Karpenter 將使用 EC2 在您的叢集所在區域和可用區域中提供的所有執行個體類型。Karpenter 會根據待處理的 Pod 智慧地從所有執行個體類型中進行選擇,以確保您的 Pod 調度到適當大小和配備的執行個體上。例如,如果您的 Pod 不需要 GPU,Karpenter 將不會將您的 Pod 調度到支援 GPU 的 EC2 執行個體類型。當您不確定要使用哪些執行個體類型時,您可以運行 Amazon [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector) 來生成符合您計算需求的執行個體類型列表。例如,該 CLI 採用記憶體、vCPU、架構和區域作為輸入參數,並為您提供符合這些約束條件的 EC2 執行個體列表。

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

在使用 Spot 執行個體時,您不應對 Karpenter 施加太多約束,因為這樣做可能會影響您應用程式的可用性。例如,如果某個特定類型的所有執行個體都被回收,而沒有合適的替代品可以替換它們,您的 Pod 將保持待處理狀態,直到為配置的執行個體類型重新補充 Spot 容量。您可以透過在不同的可用區域分散您的執行個體來降低不足容量錯誤的風險,因為不同可用區域的 Spot 池是不同的。不過,一般最佳實踐是在使用 Spot 時允許 Karpenter 使用多樣化的執行個體類型。

## 調度 Pod

以下最佳實踐與在使用 Karpenter 進行節點佈建的叢集中部署 Pod 有關。

### 遵循 EKS 高可用性最佳實踐

如果您需要運行高度可用的應用程式,請遵循一般 EKS 最佳實踐 [建議](https://aws.github.io/aws-eks-best-practices/reliability/docs/application/#recommendations)。請參閱 Karpenter 文件中的 [拓撲擴展](https://karpenter.sh/docs/concepts/scheduling/#topology-spread) 以獲取有關跨節點和區域分散 Pod 的詳細資訊。使用 [中斷預算](https://karpenter.sh/docs/troubleshooting/#disruption-budgets) 來設置在嘗試驅逐或刪除 Pod 時需要維護的最小可用 Pod 數量。

### 使用分層約束來限制您從雲端提供商獲得的計算功能

Karpenter 的分層約束模型允許您建立一組複雜的 NodePool 和 Pod 部署約束,以獲得 Pod 調度的最佳匹配。Pod 規格可以請求的約束範例包括以下:

* 需要在特定應用程式可用的可用區域中運行。例如,您有一個 Pod 需要與在特定可用區域中的 EC2 執行個體上運行的另一個應用程式進行通信。如果您的目標是減少 VPC 中的跨可用區域流量,您可能希望將 Pod 與 EC2 執行個體共置在同一可用區域。這種定位通常是使用節點選擇器來實現的。有關 [節點選擇器](https://karpenter.sh/docs/concepts/scheduling/#selecting-nodes) 的更多資訊,請參閱 Kubernetes 文件。
* 需要特定類型的處理器或其他硬體。請參閱 Karpenter 文件中的 [加速器](https://karpenter.sh/docs/concepts/scheduling/#acceleratorsgpu-resources) 部分以獲取需要在 GPU 上運行的 Pod 規格範例。

### 建立計費警報以監控您的計算支出

當您配置叢集自動擴展時,您應該建立計費警報來警告您當支出超過閾值時,並在 Karpenter 配置中添加資源限制。使用 Karpenter 設置資源限制類似於設置 AWS 自動擴展群組的最大容量,它表示 Karpenter NodePool 可以佈建的最大計算資源量。

!!! 注意
    無法為整個叢集設置全域限制。限制適用於特定的 NodePool。

下面的代碼片段告訴 Karpenter 只佈建最多 1000 個 CPU 核心和 1000Gi 的記憶體。只有在達到或超過限制時,Karpenter 才會停止添加容量。當超過限制時,Karpenter 控制器將在控制器的日誌中寫入 `memory resource usage of 1001 exceeds limit of 1000` 或類似的消息。如果您將容器日誌路由到 CloudWatch 日誌,您可以建立 [指標篩選器](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html) 來查找日誌中的特定模式或術語,然後建立 [CloudWatch 警報](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) 來在您配置的指標閾值被觸發時通知您。

有關使用 Karpenter 的限制的更多資訊,請參閱 Karpenter 文件中的 [設置資源限制](https://karpenter.sh/docs/concepts/nodepools/#speclimits)。

```yaml
spec:
  limits:
    cpu: 1000
    memory: 1000Gi
```

如果您不使用限制或限制 Karpenter 可以佈建的執行個體類型,Karpenter 將根據需要繼續為您的叢集添加計算容量。雖然以這種方式配置 Karpenter 允許您的叢集自由擴展,但它也可能會產生重大的成本影響。這就是我們建議配置計費警報的原因。計費警報允許您在您的帳戶中的估計費用超過定義的閾值時得到主動通知。有關更多資訊,請參閱 [設置 Amazon CloudWatch 計費警報以主動監控估計費用](https://aws.amazon.com/blogs/mt/setting-up-an-amazon-cloudwatch-billing-alarm-to-proactively-monitor-estimated-charges/)。

您還可能希望啟用成本異常檢測,這是 AWS 成本管理的一項功能,使用機器學習持續監控您的成本和使用情況,以檢測異常支出。更多資訊可以在 [AWS 成本異常檢測入門](https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html) 指南中找到。如果您已經在 AWS Budgets 中建立了預算,您還可以配置一個動作來在特定閾值被觸發時通知您。使用預算動作,您可以發送電子郵件、發布消息到 SNS 主題或向 Slack 等聊天機器人發送消息。有關更多資訊,請參閱 [配置 AWS Budgets 動作](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)。

### 使用 karpenter.sh/do-not-disrupt 註釋來防止 Karpenter 取消佈建節點

如果您在由 Karpenter 佈建的節點上運行關鍵應用程式,例如 *長時間運行* 的批處理作業或有狀態的應用程式,*且* 節點的 TTL 已過期,則當執行個體終止時,應用程式將被中斷。通過將 `karpenter.sh/karpenter.sh/do-not-disrupt` 註釋添加到 Pod 中,您指示 Karpenter 保留該節點,直到 Pod 終止或移除 `karpenter.sh/do-not-disrupt` 註釋為止。請參閱 [中斷](https://karpenter.sh/docs/concepts/disruption/#node-level-controls) 文件以獲取更多資訊。

如果節點上剩下的唯一非 daemonset Pod 與作業相關聯,只要作業狀態為 succeed 或 failed,Karpenter 就能夠定位並終止這些節點。

### 在使用合併時為所有非 CPU 資源配置 requests=limits

合併和調度通常是通過比較 Pod 的資源請求與節點上的可分配資源量來工作的。不考慮資源限制。例如,具有比記憶體請求更大的記憶體限制的 Pod 可以超過請求。如果同一節點上的多個 Pod 同時突發,這可能會導致某些 Pod 由於記憶體不足 (OOM) 條件而被終止。合併會增加這種可能性,因為它只考慮 Pod 的請求來將 Pod 打包到節點上。

### 使用 LimitRanges 為資源請求和限制配置預設值

由於 Kubernetes 不設置默認請求或限制,容器從底層主機消耗資源的 CPU 和記憶體是無限制的。Kubernetes 調度器查看 Pod 的總請求(來自 Pod 容器或 Pod 的 Init 容器的總請求中較高的那個)來確定將 Pod 調度到哪個工作節點上。同樣,Karpenter 也考慮 Pod 的請求來確定佈建哪種類型的執行個體。您可以使用限制範圍為命名空間應用合理的默認值,以防某些 Pod 未指定資源請求。

請參閱 [為命名空間配置默認記憶體請求和限制](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/)

### 為所有工作負載應用精確的資源請求

當 Karpenter 對您的工作負載需求的資訊準確時,它就能夠啟動最適合您的工作負載的節點。如果使用 Karpenter 的合併功能,這一點尤其重要。

請參閱 [為所有工作負載配置和調整資源請求/限制](https://aws.github.io/aws-eks-best-practices/reliability/docs/dataplane/#configure-and-size-resource-requestslimits-for-all-workloads)

## CoreDNS 建議

### 更新 CoreDNS 配置以維護可靠性
在將 CoreDNS Pod 部署到由 Karpenter 管理的節點上時,鑑於 Karpenter 快速終止/建立新節點以符合需求的動態特性,建議遵循以下最佳實踐:

[CoreDNS lameduck 持續時間](https://aws.github.io/aws-eks-best-practices/scalability/docs/cluster-services/#coredns-lameduck-duration)

[CoreDNS 就緒探針](https://aws.github.io/aws-eks-best-practices/scalability/docs/cluster-services/#coredns-readiness-probe)

這將確保不會將 DNS 查詢定向到尚未就緒或已終止的 CoreDNS Pod。

## Karpenter 藍圖
由於 Karpenter 採用以應用程式為先的方法來為 Kubernetes 資料平面佈建計算容量,您可能想知道如何正確配置一些常見的工作負載場景。[Karpenter 藍圖](https://github.com/aws-samples/karpenter-blueprints)是一個存放庫,其中包含了一系列遵循此處描述的最佳實踐的常見工作負載場景。您將擁有所需的所有資源,甚至可以建立一個配置了 Karpenter 的 EKS 叢集,並測試存放庫中包含的每個藍圖。您可以組合不同的藍圖來最終建立您的工作負載所需的藍圖。

## 其他資源
* [Karpenter/Spot 工作坊](https://ec2spotworkshops.com/karpenter.html)
* [Karpenter 節點佈建器](https://youtu.be/_FXRIKWJWUk)
* [TGIK Karpenter](https://youtu.be/zXqrNJaTCrU)
* [Karpenter 與 Cluster Autoscaler](https://youtu.be/3QsVRHVdOnM)
* [無群組自動擴展與 Karpenter](https://www.youtube.com/watch?v=43g8uPohTgc)
* [教程: 使用 Amazon EC2 Spot 和 Karpenter 以較低成本運行 Kubernetes 叢集](https://community.aws/tutorials/run-kubernetes-clusters-for-less-with-amazon-ec2-spot-and-karpenter#step-6-optional-simulate-spot-interruption)
