---
日期: 2023-09-22
作者:
  - Shane Corbett
---
# 控制平面監控

## API 伺服器
在查看我們的 API 伺服器時,重要的是要記住它的其中一個功能是限制傳入的請求,以防止控制平面過載。在 API 伺服器層級看似瓶頸的情況,實際上可能是在保護它免受更嚴重問題的影響。我們需要權衡增加通過系統的請求量的利弊。為了確定是否應該增加 API 伺服器的值,以下是我們需要注意的一些事項:

1. 通過系統的請求延遲是多少?
2. 這種延遲是來自 API 伺服器本身,還是來自下游的東西,如 etcd?
3. API 伺服器的佇列深度是否是這種延遲的因素?
4. API 優先級和公平性 (APF) 佇列是否根據我們想要的 API 呼叫模式正確設置?

## 問題出在哪裡?
首先,我們可以使用 API 延遲的指標來了解 API 伺服器為請求服務所需的時間。讓我們使用下面的 PromQL 和 Grafana 熱圖來顯示這些數據。

```
max(increase(apiserver_request_duration_seconds_bucket{subresource!="status",subresource!="token",subresource!="scale",subresource!="/healthz",subresource!="binding",subresource!="proxy",verb!="WATCH"}[$__rate_interval])) by (le)
```

!!! tip
    有關如何使用本文中使用的 API 儀表板監控 API 伺服器的深入介紹,請參閱以下 [blog](https://aws.amazon.com/blogs/containers/troubleshooting-amazon-eks-api-servers-with-prometheus/)

![API 請求持續時間熱圖](../images/api-request-duration.png)

這些請求都在一秒以內,這是一個很好的跡象,表明控制平面正在及時處理請求。但是,如果情況並非如此呢?

我們在上面使用的 API 請求持續時間的格式是熱圖。熱圖格式的好處是,它默認告訴我們 API 的超時值 (60 秒)。但是,我們真正需要知道的是,在達到超時閾值之前,什麼閾值應該引起關注。對於可接受閾值的粗略指南,我們可以使用上游 Kubernetes SLO,可以在 [這裡](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md#steady-state-slisslos) 找到

!!! tip
    注意這個語句上的 max 函數嗎? 在使用聚合多個伺服器 (默認情況下 EKS 上有兩個 API 伺服器) 的指標時,重要的是不要將這些伺服器平均在一起。

### 不對稱流量模式
如果一個 API 伺服器 [pod] 負載很輕,而另一個負載很重怎麼辦? 如果我們將這兩個數字平均在一起,我們可能會誤解正在發生的情況。例如,這裡我們有三個 API 伺服器,但所有的負載都在其中一個 API 伺服器上。作為規則,任何具有多個伺服器的東西,如 etcd 和 API 伺服器,在研究規模和性能問題時都應該被分解。

![總飛行請求](../images/inflight-requests.png)

隨著 API 優先級和公平性的推出,系統上的總請求數只是檢查 API 伺服器是否過度訂閱的一個因素。由於系統現在基於一系列佇列工作,我們必須查看是否有任何佇列已滿,以及該佇列的流量是否被丟棄。

讓我們使用以下查詢來查看這些佇列:

```
max without(instance)(apiserver_flowcontrol_request_concurrency_limit{})
```

!!! note
    有關 API A&F 工作原理的更多信息,請參閱以下 [最佳實踐指南](https://aws.github.io/aws-eks-best-practices/scalability/docs/control-plane/#api-priority-and-fairness)

在這裡,我們看到了集群上默認的七個不同優先級組

![共享並發](../images/shared-concurrency.png)

接下來,我們想看看該優先級組的使用百分比,以便我們可以了解是否有某個優先級級別已經飽和。在工作負載低級別節流請求可能是可取的,但在領導者選舉級別丟棄就不可取了。

API 優先級和公平性 (APF) 系統有許多複雜的選項,其中一些選項可能會產生意想不到的後果。我們在現場看到的一個常見問題是,增加佇列深度到一個程度,它開始增加不必要的延遲。我們可以使用 `apiserver_flowcontrol_current_inqueue_request` 指標來監控這個問題。我們可以使用 `apiserver_flowcontrol_rejected_requests_total` 檢查丟棄。如果任何存儲桶超過其並發性,這些指標將是非零值。

![使用中的請求](../images/requests-in-use.png)

增加佇列深度可能會使 API 伺服器成為延遲的重要來源,因此應該小心使用。我們建議審慎地設置要創建的佇列數量。例如,EKS 系統上的份額數量是 600,如果我們創建太多佇列,這可能會減少需要吞吐量的重要佇列中的份額,如領導者選舉佇列或系統佇列。創建太多額外的佇列可能會使正確調整這些佇列的大小變得更加困難。

要專注於您可以在 APF 中進行的簡單有影響的更改,您只需從未充分利用的存儲桶中取出份額,並增加使用率達到最大值的存儲桶的大小。通過智能地在這些存儲桶之間重新分配份額,您可以減少丟棄的可能性。

有關更多信息,請訪問 EKS 最佳實踐指南中的 [API 優先級和公平性設置](https://aws.github.io/aws-eks-best-practices/scalability/docs/control-plane/#api-priority-and-fairness)。

### API 與 etcd 延遲
我們如何利用 API 伺服器的指標/日誌來確定是 API 伺服器出現問題,還是 API 伺服器上游/下游出現問題,或者兩者都有問題。為了更好地理解這一點,讓我們看看 API 伺服器和 etcd 之間是如何相關的,以及在錯誤的系統上進行故障排除是多麼容易。

在下圖中,我們看到 API 伺服器延遲,但我們還看到這種延遲很大程度上與 etcd 伺服器相關,因為圖中的條形圖顯示大部分延遲都在 etcd 級別。如果在 API 伺服器延遲 20 秒的同時,etcd 延遲 15 秒,那麼大部分延遲實際上是在 etcd 級別。

通過查看整個流程,我們看到專注於 API 伺服器是明智的,但也要尋找表明 etcd 處於困境 (即慢應用計數器增加) 的信號。能夠一眼就找到正確的問題區域,這就是儀表板強大的原因。

!!! tip
    本節中的儀表板可在 https://github.com/RiskyAdventure/Troubleshooting-Dashboards/blob/main/api-troubleshooter.json 找到

![ETCD 困境](../images/etcd-duress.png)

### 控制平面與客戶端問題
在此圖中,我們正在尋找在該時間段內完成時間最長的 API 呼叫。在這種情況下,我們看到在 05:40 時間範圍內,一個自定義資源 (CRD) 正在呼叫一個延遲最高的 APPLY 函數。

![最慢的請求](../images/slowest-requests.png)

有了這些數據,我們可以使用 Ad-Hoc PromQL 或 CloudWatch Insights 查詢來從該時間段的審計日誌中提取 LIST 請求,以查看這可能是哪個應用程式。

### 使用 CloudWatch 找到來源
指標最好用於找到我們要查看的問題區域,並縮小問題的時間範圍和搜索參數。一旦我們有了這些數據,我們就希望轉向日誌以獲得更詳細的時間和錯誤。為此,我們將使用 [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html) 將日誌轉換為指標。

例如,要調查上述問題,我們將使用以下 CloudWatch Logs Insights 查詢來提取 userAgent 和 requestURI,以便我們可以確定是哪個應用程式導致了這種延遲。

!!! tip
    需要使用適當的 Count 以避免提取 Watch 上的正常 List/Resync 行為。

```
fields *@timestamp*, *@message*
| filter *@logStream* like "kube-apiserver-audit"
| filter ispresent(requestURI)
| filter verb = "list"
| parse requestReceivedTimestamp /\d+-\d+-(?<StartDay>\d+)T(?<StartHour>\d+):(?<StartMinute>\d+):(?<StartSec>\d+).(?<StartMsec>\d+)Z/
| parse stageTimestamp /\d+-\d+-(?<EndDay>\d+)T(?<EndHour>\d+):(?<EndMinute>\d+):(?<EndSec>\d+).(?<EndMsec>\d+)Z/
| fields (StartHour * 3600 + StartMinute * 60 + StartSec + StartMsec / 1000000) as StartTime, (EndHour * 3600 + EndMinute * 60 + EndSec + EndMsec / 1000000) as EndTime, (EndTime - StartTime) as DeltaTime
| stats avg(DeltaTime) as AverageDeltaTime, count(*) as CountTime by requestURI, userAgent
| filter CountTime >=50
| sort AverageDeltaTime desc
```

使用此查詢,我們發現有兩個不同的代理正在運行大量高延遲的 list 操作。Splunk 和 CloudWatch 代理。有了這些數據,我們可以決定移除、更新或用另一個項目替換此控制器。

![查詢結果](../images/query-results.png)

!!! tip
    有關此主題的更多詳細信息,請參閱以下 [blog](https://aws.amazon.com/blogs/containers/troubleshooting-amazon-eks-api-servers-with-prometheus/)

## 調度器
由於 EKS 控制平面實例是在單獨的 AWS 帳戶中運行的,因此我們將無法為這些組件抓取指標 (API 伺服器除外)。但是,由於我們可以訪問這些組件的審計日誌,我們可以將這些日誌轉換為指標,以查看是否有任何子系統導致了擴展瓶頸。讓我們使用 CloudWatch Logs Insights 來查看調度器佇列中有多少未調度的 pod。

### 調度器日誌中的未調度 pod
如果我們可以直接在自我管理的 Kubernetes (如 Kops) 上抓取調度器指標,我們將使用以下 PromQL 來了解調度器積壓情況。

```
max without(instance)(scheduler_pending_pods)
```

由於我們無法在 EKS 中訪問上述指標,因此我們將使用下面的 CloudWatch Logs Insights 查詢來查看特定時間段內無法調度的 pod 數量,從而了解積壓情況。然後,我們可以進一步深入研究峰值時間段的消息,以了解瓶頸的性質。例如,節點無法及時啟動,或者調度器本身的速率限制器。

```
fields timestamp, pod, err, *@message*
| filter *@logStream* like "scheduler"
| filter *@message* like "Unable to schedule pod"
| parse *@message*  /^.(?<date>\d{4})\s+(?<timestamp>\d+:\d+:\d+\.\d+)\s+\S*\s+\S+\]\s\"(.*?)\"\s+pod=(?<pod>\"(.*?)\")\s+err=(?<err>\"(.*?)\")/
| count(*) as count by pod, err
| sort count desc
```

在這裡,我們看到調度器的錯誤說明 pod 未部署是因為存儲 PVC 不可用。

![CloudWatch Logs 查詢](../images/cwl-query.png)

!!! note
    必須在控制平面上啟用審計日誌記錄,才能啟用此功能。限制日誌保留期也是一種最佳實踐,以免隨著時間的推移而產生不必要的成本。以下是使用 EKSCTL 工具啟用所有日誌記錄功能的示例。

```yaml
cloudWatch:
  clusterLogging:
    enableTypes: ["*"]
    logRetentionInDays: 10
```

## Kube 控制器管理器
與所有其他控制器一樣,Kube 控制器管理器也有限制它一次可以執行多少操作。讓我們通過查看 KOPS 配置來查看一些這些標誌,在 KOPS 配置中我們可以設置這些參數。

```yaml
  kubeControllerManager:
    concurrentEndpointSyncs: 5
    concurrentReplicasetSyncs: 5
    concurrentNamespaceSyncs: 10
    concurrentServiceaccountTokenSyncs: 5
    concurrentServiceSyncs: 5
    concurrentResourceQuotaSyncs: 5
    concurrentGcSyncs: 20
    kubeAPIBurst: 20
    kubeAPIQPS: "30"
```

這些控制器在集群高度變化的時候有佇列會填滿。在這種情況下,我們看到 replicaset 控制器在其佇列中有大量積壓。

![佇列](../images/queues.png)

我們有兩種不同的方式來解決這種情況。如果運行自我管理,我們可以簡單地增加並行 goroutine,但這將影響 etcd 的性能,因為它需要處理更多數據。另一種選擇是使用部署上的 `.spec.revisionHistoryLimit` 減少 replicaset 對象的數量,從而減少對此控制器的壓力。

```yaml
spec:
  revisionHistoryLimit: 2
```

其他 Kubernetes 功能可以進行調整或關閉,以減少高變化率系統中的壓力。例如,如果我們的 pod 中的應用程序不需要直接與 k8s API 通信,那麼關閉將投影密鑰注入到這些 pod 中將減少對 ServiceaccountTokenSyncs 的負載。如果可能的話,這是解決此類問題的更可取的方式。

```yaml
kind: Pod
spec:
  automountServiceAccountToken: false
```

在我們無法獲取指標的系統中,我們可以再次查看日誌以檢測爭用情況。如果我們想查看每個控制器或總體級別上正在處理的請求數量,我們將使用以下 CloudWatch Logs Insights 查詢。

### KCM 處理的總體量

```
# 查詢計算來自 kube-controller-manager 的 API qps,按控制器類型分開。
# 如果您看到任何特定控制器的值接近 20/秒,它很可能遇到了客戶端 API 節流。
fields @timestamp, @logStream, @message
| filter @logStream like /kube-apiserver-audit/
| filter userAgent like /kube-controller-manager/
# 排除與租約相關的呼叫 (不計入 kcm qps)
| filter requestURI not like "apis/coordination.k8s.io/v1/namespaces/kube-system/leases/kube-controller-manager"
# 排除 API 發現呼叫 (不計入 kcm qps)
| filter requestURI not like "?timeout=32s"
# 排除 watch 呼叫 (不計入 kcm qps)
| filter verb != "watch"
# 如果您想獲取來自特定控制器的 API 呼叫計數,請取消註釋下面適當的行:
# | filter user.username like "system:serviceaccount:kube-system:job-controller"
# | filter user.username like "system:serviceaccount:kube-system:cronjob-controller"
# | filter user.username like "system:serviceaccount:kube-system:deployment-controller"
# | filter user.username like "system:serviceaccount:kube-system:replicaset-controller"
# | filter user.username like "system:serviceaccount:kube-system:horizontal-pod-autoscaler"
# | filter user.username like "system:serviceaccount:kube-system:persistent-volume-binder"
# | filter user.username like "system:serviceaccount:kube-system:endpointslice-controller"
# | filter user.username like "system:serviceaccount:kube-system:endpoint-controller"
# | filter user.username like "system:serviceaccount:kube-system:generic-garbage-controller"
| stats count(*) as count by user.username
| sort count desc
```

關鍵要點是,在研究可擴展性問題時,要查看路徑中的每一步 (API、調度器、KCM、etcd),然後再進入詳細的故障排除階段。通常在生產環境中,您會發現需要對 Kubernetes 的多個部分進行調整,才能使系統發揮最佳性能。很容易無意中對症狀 (如節點超時) 進行故障排除,而不是更大的瓶頸。

## ETCD
etcd 使用內存映射文件來有效地存儲鍵值對。有一種保護機制可以設置可用內存空間的大小,通常設置為 2、4 和 8GB 限制。數據庫中的對象越少,etcd 在更新對象並需要清除舊版本時需要清理的工作就越少。清除對象舊版本的過程稱為壓實。經過一定次數的壓實操作後,會有一個後續的過程來恢復可用空間,稱為碎片整理,這在超過某個閾值或固定的時間間隔後發生。

我們可以做一些與用戶相關的事情來限制 Kubernetes 中的對象數量,從而減少壓實和碎片整理過程的影響。例如,Helm 保留了高 `revisionHistoryLimit`。這會將較舊的對象 (如 ReplicaSets) 保留在系統上,以便能夠進行回滾。通過將歷史記錄限制設置為 2,我們可以將對象數量 (如 ReplicaSets) 從十個減少到兩個,從而減少系統負載。

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  revisionHistoryLimit: 2
```

從監控的角度來看,如果系統延遲出現固定模式的尖峰,則檢查這個碎片整理過程是否是源頭會很有幫助。我們可以通過使用 CloudWatch Logs 來查看這一點。

如果您想查看碎片整理的開始/結束時間,請使用以下查詢:

```
fields *@timestamp*, *@message*
| filter *@logStream* like /etcd-manager/
| filter *@message* like /defraging|defraged/
| sort *@timestamp* asc
```

![碎片整理查詢](../images/defrag.png)