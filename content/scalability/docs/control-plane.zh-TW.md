# Kubernetes 控制平面

Kubernetes 控制平面包括 Kubernetes API 伺服器、Kubernetes 控制器管理器、調度器和 Kubernetes 運作所需的其他元件。這些元件的可擴展性限制取決於您在叢集中運行的內容,但對擴展影響最大的領域包括 Kubernetes 版本、使用率和個別節點的擴展。

## 使用 EKS 1.24 或更高版本

EKS 1.24 引入了許多變更,並將容器運行時切換為 [containerd](https://containerd.io/) 而非 docker。containerd 通過限制容器運行時功能以緊密符合 Kubernetes 的需求,從而幫助叢集擴展並提高個別節點的性能。containerd 在每個受支援的 EKS 版本中都可用,如果您希望在 1.24 之前的版本中切換到 containerd,請使用 [`--container-runtime` 引導旗標](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html#containerd-bootstrap)。

## 限制工作負載和節點突發

!!! 注意
    為了避免觸及控制平面的 API 限制,您應該限制會增加叢集規模 10% 以上的擴展尖峰 (例如一次從 1000 個節點擴展到 1100 個節點或從 4000 個 Pod 擴展到 4500 個 Pod)。

隨著叢集的增長,EKS 控制平面將自動擴展,但對於擴展速度有限制。當您首次建立 EKS 叢集時,控制平面一開始無法立即擴展到數百個節點或數千個 Pod。要閱讀更多有關 EKS 如何進行擴展改進的資訊,請參閱 [此部落格文章](https://aws.amazon.com/blogs/containers/amazon-eks-control-plane-auto-scaling-enhancements-improve-speed-by-4x/)。

擴展大型應用程式需要基礎架構適應並完全就緒 (例如預熱負載平衡器)。為了控制擴展速度,請確保您根據應用程式的正確指標進行擴展。CPU 和記憶體擴展可能無法準確預測您的應用程式限制,在 Kubernetes 水平 Pod 自動擴展器 (HPA) 中使用自訂指標 (例如每秒請求數) 可能是更好的擴展選擇。

要使用自訂指標,請參閱 [Kubernetes 文件](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/#autoscaling-on-multiple-metrics-and-custom-metrics) 中的示例。如果您有更高級的擴展需求或需要根據外部來源 (例如 AWS SQS 佇列) 進行擴展,請使用 [KEDA](https://keda.sh) 進行基於事件的工作負載擴展。

## 安全地縮減節點和 Pod

### 替換長期運行的實例

定期替換節點可以保持叢集的健康狀態,避免配置漂移和僅在長時間運行後才會發生的問題 (例如緩慢的記憶體洩漏)。自動化替換將為您提供良好的流程和實踐,用於節點升級和安全性修補。如果叢集中的每個節點都定期替換,那麼維護單獨的流程進行持續維護所需的工作量就會減少。

使用 Karpenter 的 [存活時間 (TTL)](https://aws.github.io/aws-eks-best-practices/karpenter/#use-timers-ttl-to-automatically-delete-nodes-from-the-cluster) 設定,在實例運行指定時間後將其替換。自行管理的節點組可以使用 `max-instance-lifetime` 設定自動循環節點。目前受管理的節點組沒有此功能,但您可以在 [GitHub 上追蹤此請求](https://github.com/aws/containers-roadmap/issues/1190)。

### 移除利用率低的節點

當節點上沒有正在運行的工作負載時,您可以使用 Kubernetes 叢集自動擴展器中的 [`--scale-down-utilization-threshold`](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-does-scale-down-work) 縮減閾值或在 Karpenter 中使用 `ttlSecondsAfterEmpty` 配置器設定來移除節點。

### 使用 Pod 干擾預算和安全的節點關閉

從 Kubernetes 叢集中移除 Pod 和節點需要控制器對多個資源 (例如 EndpointSlices) 進行更新。如果頻繁或太快地執行此操作,可能會導致 API 伺服器節流和應用程式中斷,因為變更需要傳播到控制器。[Pod 干擾預算](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) 是一種最佳實踐,可在從叢集中移除或重新調度節點時減緩變更速度,以保護工作負載的可用性。

## 在運行 Kubectl 時使用用戶端緩存

如果使用不當,kubectl 命令可能會為 Kubernetes API 伺服器增加額外負載。您應該避免運行重複使用 kubectl 的腳本或自動化 (例如在 for 迴圈中) 或在沒有本地緩存的情況下運行命令。

`kubectl` 有一個用戶端緩存,可以緩存來自叢集的探索資訊,從而減少所需的 API 呼叫數量。預設會啟用緩存,並每 10 分鐘重新整理一次。

如果您從容器運行 kubectl 或在沒有用戶端緩存的情況下運行,您可能會遇到 API 節流問題。建議您保留叢集緩存,方法是掛載 `--cache-dir` 以避免進行不必要的 API 呼叫。

## 停用 kubectl 壓縮

在您的 kubeconfig 檔案中停用 kubectl 壓縮可以減少 API 和用戶端 CPU 使用量。預設情況下,伺服器會壓縮傳送到用戶端的資料以優化網路頻寬。這會為每個請求在用戶端和伺服器上增加 CPU 負載,停用壓縮可以減少開銷和延遲 (如果您有足夠的頻寬)。要停用壓縮,您可以使用 `--disable-compression=true` 旗標或在 kubeconfig 檔案中設定 `disable-compression: true`。

```
apiVersion: v1
clusters:
- cluster:
    server: serverURL
    disable-compression: true
  name: cluster
```

## 分片叢集自動擴展器

[Kubernetes 叢集自動擴展器已經過測試](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/proposals/scalability_tests.md),可以擴展到 1000 個節點。在擁有超過 1000 個節點的大型叢集上,建議以分片模式運行多個叢集自動擴展器實例。每個叢集自動擴展器實例都配置為擴展一組節點組。以下示例顯示了兩個叢集自動擴展配置,每個配置都設置為擴展 4 個節點組。

ClusterAutoscaler-1

```
autoscalingGroups:
- name: eks-core-node-grp-20220823190924690000000011-80c1660e-030d-476d-cb0d-d04d585a8fcb
  maxSize: 50
  minSize: 2
- name: eks-data_m1-20220824130553925600000011-5ec167fa-ca93-8ca4-53a5-003e1ed8d306
  maxSize: 450
  minSize: 2
- name: eks-data_m2-20220824130733258600000015-aac167fb-8bf7-429d-d032-e195af4e25f5
  maxSize: 450
  minSize: 2
- name: eks-data_m3-20220824130553914900000003-18c167fa-ca7f-23c9-0fea-f9edefbda002
  maxSize: 450
  minSize: 2
```

ClusterAutoscaler-2

```
autoscalingGroups:
- name: eks-data_m4-2022082413055392550000000f-5ec167fa-ca86-6b83-ae9d-1e07ade3e7c4
  maxSize: 450
  minSize: 2
- name: eks-data_m5-20220824130744542100000017-02c167fb-a1f7-3d9e-a583-43b4975c050c
  maxSize: 450
  minSize: 2
- name: eks-data_m6-2022082413055392430000000d-9cc167fa-ca94-132a-04ad-e43166cef41f
  maxSize: 450
  minSize: 2
- name: eks-data_m7-20220824130553921000000009-96c167fa-ca91-d767-0427-91c879ddf5af
  maxSize: 450
  minSize: 2
```

## API 優先順序和公平性

![](../images/APF.jpg)

### 概述

<iframe width="560" height="315" src="https://www.youtube.com/embed/YnPPHBawhE0" title="YouTube 視頻播放器" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

為了在請求增加期間保護自身免受過載,API 伺服器會限制其可以同時處理的請求數量。一旦超過此限制,API 伺服器將開始拒絕請求,並向用戶端返回 429 HTTP 響應代碼 "Too Many Requests"。伺服器拋棄請求並讓用戶端稍後重試,比沒有伺服器端對請求數量的限制而導致控制平面過載 (可能會導致性能下降或不可用) 更可取。

Kubernetes 用於配置不同請求類型的請求配額劃分方式的機制稱為 [API 優先順序和公平性](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/)。API 伺服器通過將 `--max-requests-inflight` 和 `--max-mutating-requests-inflight` 旗標指定的值相加來配置可以接受的總請求數量。EKS 使用這些旗標的預設值 400 和 200 個請求,允許同時分派總共 600 個請求。但是,隨著它根據使用率和工作負載變化的增加而擴展控制平面,它也相應地將請求配額增加到 2000 (可能會更改)。APF 指定如何將這些請求配額進一步細分為不同的請求類型。請注意,EKS 控制平面是高度可用的,每個叢集至少註冊了 2 個 API 伺服器。這意味著您的叢集可以處理的總請求數量是每個 kube-apiserver 設定的請求配額的兩倍或更高 (如果進一步水平擴展的話)。這相當於最大的 EKS 叢集每秒可以處理數千個請求。

兩種 Kubernetes 物件稱為 PriorityLevelConfigurations 和 FlowSchemas,用於配置總請求數量在不同請求類型之間的劃分方式。這些物件由 API 伺服器自動維護,EKS 使用給定 Kubernetes 次要版本的預設配置。PriorityLevelConfigurations 代表允許請求總數的一部分。例如,workload-high PriorityLevelConfiguration 被分配了總共 600 個請求中的 98 個。所有 PriorityLevelConfigurations 分配的請求總和將等於 600 (或略高於 600,因為如果給定級別被授予一個請求的一部分,API 伺服器將進位)。要檢查叢集中的 PriorityLevelConfigurations 以及分配給每個級別的請求數量,您可以運行以下命令。這些是 EKS 1.24 上的預設值:

```
$ kubectl get --raw /metrics | grep apiserver_flowcontrol_request_concurrency_limit
apiserver_flowcontrol_request_concurrency_limit{priority_level="catch-all"} 13
apiserver_flowcontrol_request_concurrency_limit{priority_level="global-default"} 49
apiserver_flowcontrol_request_concurrency_limit{priority_level="leader-election"} 25
apiserver_flowcontrol_request_concurrency_limit{priority_level="node-high"} 98
apiserver_flowcontrol_request_concurrency_limit{priority_level="system"} 74
apiserver_flowcontrol_request_concurrency_limit{priority_level="workload-high"} 98
apiserver_flowcontrol_request_concurrency_limit{priority_level="workload-low"} 245
```

第二種物件是 FlowSchemas。具有給定一組屬性的 API 伺服器請求將被歸類為同一 FlowSchema。這些屬性包括經過身份驗證的用戶或請求的屬性,例如 API 組、命名空間或資源。FlowSchema 還指定此類請求應映射到哪個 PriorityLevelConfiguration。這兩個物件一起說明 "我希望這種類型的請求計入這部分請求配額"。當請求到達 API 伺服器時,它將檢查每個 FlowSchema,直到找到一個與所有必需屬性相匹配的 FlowSchema。如果多個 FlowSchemas 與請求相匹配,API 伺服器將選擇具有最小匹配優先順序的 FlowSchema,優先順序作為物件中的一個屬性指定。

可以使用以下命令查看 FlowSchemas 到 PriorityLevelConfigurations 的映射:

```
$ kubectl get flowschemas
NAME                           PRIORITYLEVEL     MATCHINGPRECEDENCE   DISTINGUISHERMETHOD   AGE     MISSINGPL
exempt                         exempt            1                    <none>                7h19m   False
eks-exempt                     exempt            2                    <none>                7h19m   False
probes                         exempt            2                    <none>                7h19m   False
system-leader-election         leader-election   100                  ByUser                7h19m   False
endpoint-controller            workload-high     150                  ByUser                7h19m   False
workload-leader-election       leader-election   200                  ByUser                7h19m   False
system-node-high               node-high         400                  ByUser                7h19m   False
system-nodes                   system            500                  ByUser                7h19m   False
kube-controller-manager        workload-high     800                  ByNamespace           7h19m   False
kube-scheduler                 workload-high     800                  ByNamespace           7h19m   False
kube-system-service-accounts   workload-high     900                  ByNamespace           7h19m   False
eks-workload-high              workload-high     1000                 ByUser                7h14m   False
service-accounts               workload-low      9000                 ByUser                7h19m   False
global-default                 global-default    9900                 ByUser                7h19m   False
catch-all                      catch-all         10000                ByUser                7h19m   False
```

PriorityLevelConfigurations 可以是 Queue、Reject 或 Exempt 類型。對於 Queue 和 Reject 類型,將對該優先級別的最大請求數量實施限制,但當達到該限制時,行為會有所不同。例如,workload-high PriorityLevelConfiguration 使用 Queue 類型,並為控制器管理器、端點控制器、調度器、EKS 相關控制器和從 kube-system 命名空間中的 Pod 運行的請求提供 98 個可用請求。由於使用了 Queue 類型,API 伺服器將嘗試將請求保留在記憶體中,並希望在這些請求超時之前,請求數量下降到低於 98。如果給定請求在佇列中超時或已有太多請求佇列,API 伺服器別無選擇,只能拋棄該請求並向用戶端返回 429。請注意,佇列可能會防止請求收到 429,但代價是請求的端到端延遲會增加。

現在考慮映射到 Reject 類型的 catch-all PriorityLevelConfiguration 的 catch-all FlowSchema。如果用戶端達到 13 個請求的限制,API 伺服器將不會進行佇列,而是立即以 429 響應代碼拋棄請求。最後,映射到 Exempt 類型 PriorityLevelConfiguration 的請求將永遠不會收到 429,並將立即分派。這用於高優先級請求,例如 healthz 請求或來自 system:masters 組的請求。

### 監控 APF 和拋棄的請求

要確認是否有任何請求由於 APF 而被拋棄,可以監控 API 伺服器的 `apiserver_flowcontrol_rejected_requests_total` 指標,以檢查受影響的 FlowSchemas 和 PriorityLevelConfigurations。例如,此指標顯示由於請求在 workload-low 佇列中超時,而拋棄了來自 service-accounts FlowSchema 的 100 個請求:

```
% kubectl get --raw /metrics | grep apiserver_flowcontrol_rejected_requests_total
apiserver_flowcontrol_rejected_requests_total{flow_schema="service-accounts",priority_level="workload-low",reason="time-out"} 100
```

要檢查給定 PriorityLevelConfiguration 離收到 429 或由於佇列而導致延遲增加有多近,您可以比較請求配額與正在使用的請求配額之間的差異。在此示例中,我們有 100 個請求的緩衝區。

```
% kubectl get --raw /metrics | grep 'apiserver_flowcontrol_request_concurrency_limit.*workload-low'
apiserver_flowcontrol_request_concurrency_limit{priority_level="workload-low"} 245

% kubectl get --raw /metrics | grep 'apiserver_flowcontrol_request_concurrency_in_use.*workload-low'
apiserver_flowcontrol_request_concurrency_in_use{flow_schema="service-accounts",priority_level="workload-low"} 145
```

要檢查給定 PriorityLevelConfiguration 是否正在發生佇列但尚未拋棄請求,可以參考 `apiserver_flowcontrol_current_inqueue_requests` 指標:

```
% kubectl get --raw /metrics | grep 'apiserver_flowcontrol_current_inqueue_requests.*workload-low'
apiserver_flowcontrol_current_inqueue_requests{flow_schema="service-accounts",priority_level="workload-low"} 10
```

其他有用的 Prometheus 指標包括:

- apiserver_flowcontrol_dispatched_requests_total
- apiserver_flowcontrol_request_execution_seconds
- apiserver_flowcontrol_request_wait_duration_seconds

有關完整 [APF 指標](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/#observability) 列表,請參閱上游文件。

### 防止請求被拋棄

#### 通過更改工作負載防止 429

當 APF 由於給定 PriorityLevelConfiguration 超過其允許的最大請求數量而拋棄請求時,受影響 FlowSchemas 中的用戶端可以減少同時執行的請求數量。這可以通過在發生 429 的時間段內減少總請求數量來實現。請注意,長時間運行的請求 (例如耗時的列表呼叫) 特別成問題,因為它們在整個執行期間都被視為一個請求。減少這些耗時請求的數量或優化這些列表呼叫的延遲 (例如,通過減少每個請求獲取的物件數量或切換到使用監視請求) 可以幫助減少給定工作負載所需的總並發量。

#### 通過更改 APF 設定防止 429

!!! 警告
    僅在您確實知道自己在做什麼的情況下才更改預設 APF 設定。錯誤配置的 APF 設定可能會導致 API 伺服器請求被拋棄和嚴重的工作負載中斷。

防止請求被拋棄的另一種方法是更改 EKS 叢集上安裝的預設 FlowSchemas 或 PriorityLevelConfigurations。EKS 為給定 Kubernetes 次要版本安裝上游預設的 FlowSchemas 和 PriorityLevelConfigurations 設定。除非在這些物件上設置了以下註釋為 false,否則 API 伺服器將自動將這些物件與其預設值進行協調:

```
  metadata:
    annotations:
      apf.kubernetes.io/autoupdate-spec: "false"
```

從高層次來看,APF 設定可以進行修改以:

- 為您關心的請求分配更多請求配額。
- 隔離非必需或耗時的請求,這些請求可能會耗盡其他請求類型的容量。

這可以通過更改預設 FlowSchemas 和 PriorityLevelConfigurations 或創建這些類型的新物件來實現。操作員可以增加相關 PriorityLevelConfigurations 物件的 assuredConcurrencyShares 值,以增加分配給它們的請求配額比例。此外,還可以增加一次可以佇列的請求數量,如果應用程式可以處理由於請求在分派之前被佇列而導致的額外延遲。

或者,可以創建特定於客戶工作負載的新 FlowSchema 和 PriorityLevelConfigurations 物件。請注意,無論是為現有 PriorityLevelConfigurations 還是為新 PriorityLevelConfigurations 分配更多 assuredConcurrencyShares,都會導致其他存放區可處理的請求數量減少,因為總限制將保持在每個 API 伺服器 600 個請求。

在更改 APF 預設值時,應在非生產叢集上監控這些指標,以確保更改設定不會導致意外的 429:

1. 應監控所有 FlowSchemas 的 `apiserver_flowcontrol_rejected_requests_total` 指標,以確保沒有存放區開始拋棄請求。
2. 應比較 `apiserver_flowcontrol_request_concurrency_limit` 和 `apiserver_flowcontrol_request_concurrency_in_use` 的值,以確保正在使用的請求配額不會有觸及該優先級別限制的風險。

定義新 FlowSchema 和 PriorityLevelConfiguration 的一個常見用例是隔離。假設我們希望將來自 Pod 的長時間列表事件呼叫與其他請求隔離到自己的請求配額中。這將防止使用現有 service-accounts FlowSchema 的重要 Pod 請求收到 429 並被剝奪請求容量。請回憶一下,總請求數量是有限的,但此示例顯示可以修改 APF 設定以更好地為給定工作負載劃分請求容量:

用於隔離列表事件請求的示例 FlowSchema 物件:

```
apiVersion: flowcontrol.apiserver.k8s.io/v1beta1
kind: FlowSchema
metadata:
  name: list-events-default-service-accounts
spec:
  distinguisherMethod:
    type: ByUser
  matchingPrecedence: 8000
  priorityLevelConfiguration:
    name: catch-all
  rules:
  - resourceRules:
    - apiGroups:
      - '*'
      namespaces:
      - default
      resources:
      - events
      verbs:
      - list
    subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: default
        namespace: default
```

- 此 FlowSchema 捕獲來自 default 命名空間中服務帳戶的所有列表事件呼叫。
- 匹配優先順序 8000 低於現有 service-accounts FlowSchema 使用的 9000 值,因此這些列表事件呼叫將匹配 list-events-default-service-accounts 而不是 service-accounts。
- 我們使用 catch-all PriorityLevelConfiguration 來隔離這些請求。此存放區只允許這些長時間列表事件呼叫使用 13 個請求配額。一旦 Pod 嘗試同時發出超過 13 個此類請求,它們就會開始收到 429。

## 從 API 伺服器檢索資源

從 API 伺服器獲取資訊是任何規模的叢集的預期行為。隨著叢集中資源數量的增加,請求頻率和資料量可能很快就會成為控制平面的瓶頸,並將導致 API 延遲和緩慢。根據延遲的嚴重程度,如果不小心的話,它可能會導致意外的停機。

了解您正在請求什麼以及請求的頻率是避免這類問題的第一步。根據擴展最佳實踐,以下是限制查詢量的指導原則。本節中的建議按照已知的最佳擴展順序提供。

### 使用共享資訊器

在構建與 Kubernetes API 集成的控制器和自動化時,您通常需要從 Kubernetes 資源獲取資訊。如果您定期輪詢這些資源,可能會給 API 伺服器帶來大量負載。

使用 client-go 庫中的 [資訊器](https://pkg.go.dev/k8s.io/client-go/informers) 將使您能夠根據事件而不是輪詢來監視資源變更。資訊器通過為事件和變更使用共享緩存,進一步減少了負載,因此監視相同資源的多個控制器不會增加額外負載。

控制器應避免在大型叢集中輪詢沒有標籤和欄位選擇器的整個叢集資源。每次未過濾的輪詢都需要從 etcd 通過 API 伺服器傳送大量不必要的資料,然後由用戶端進行過濾。通過基於標籤和命名空間進行過濾,您可以減少 API 伺服器為滿足請求所需執行的工作量和傳送到用戶端的資料量。

### 優化 Kubernetes API 使用

在使用自定義控制器或自動化呼叫 Kubernetes API 時,重要的是您只限制對所需資源的呼叫。如果沒有限制,您可能會給 API 伺服器和 etcd 帶來不必要的負載。

建議您盡可能使用 watch 參數。如果不使用任何參數,預設行為是列出物件。要改用 watch 而不是 list,您可以在 API 請求的末尾附加 `?watch=true`。例如,要使用 watch 獲取 default 命名空間中的所有 Pod,請使用:

```
/api/v1/namespaces/default/pods?watch=true
```

如果您正在列出物件,您應該限制列出範圍和返回的資料量。您可以通過在請求中添加 `limit=500` 參數來限制返回的資料。`fieldSelector` 參數和 `/namespace/` 路徑可用於確保您的列表範圍盡可能窄。例如,要僅列出 default 命名空間中正在運行的 Pod,請使用以下 API 路徑和參數。

```
/api/v1/namespaces/default/pods?fieldSelector=status.phase=Running&limit=500
```

或列出所有正在運行的 Pod:

```
/api/v1/pods?fieldSelector=status.phase=Running&limit=500
```

限制 watch 呼叫或列出物件的另一個選項是使用 [`resourceVersions`,您可以在 Kubernetes 文件中閱讀相關內容](https://kubernetes.io/docs/reference/using-api/api-concepts/#resource-versions)。如果不使用 `resourceVersion` 參數,您將收到最新可用的版本,這需要對 etcd 進行仲裁讀取,這是資料庫中最昂貴和最慢的讀取操作。resourceVersion 取決於您嘗試查詢的資源,可以在 `metadata.resourseVersion` 欄位中找到。對於使用 watch 呼叫而不僅僅是 list 呼叫,也建議這樣做

有一個特殊的 `resourceVersion=0` 可用,它將從 API 伺服器緩存返回結果。這可以減少 etcd 的負載,但不支援分頁。

```
/api/v1/namespaces/default/pods?resourceVersion=0
```
建議使用 watch 並將 resourceVersion 設置為從前一個 list 或 watch 收到的最新已知值。這在 client-go 中會自動處理。但如果您在其他語言中使用 k8s 用戶端,建議您仔細檢查。

```
/api/v1/namespaces/default/pods?watch=true&resourceVersion=362812295
```
如果您在不使用任何參數的情況下呼叫 API,這將對 API 伺服器和 etcd 造成最大的資源影響。此呼叫將獲取所有命名空間中的所有 Pod,而不進行分頁或限制範圍,並需要從 etcd 進行仲裁讀取。

```
/api/v1/pods
```
