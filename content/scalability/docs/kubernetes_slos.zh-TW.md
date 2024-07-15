# Kubernetes 上游 SLO

Amazon EKS 運行與上游 Kubernetes 發行版本相同的代碼,並確保 EKS 集群在 Kubernetes 社區定義的 SLO 範圍內運行。Kubernetes [可擴展性特殊興趣小組 (SIG)](https://github.com/kubernetes/community/tree/master/sig-scalability) 定義了可擴展性目標,並通過 SLI 和 SLO 調查性能瓶頸。

SLI 是我們測量系統的方式,例如可用於確定系統運行"良好"的指標或措施,例如請求延遲或計數。SLO 定義了系統運行"良好"時預期的值,例如請求延遲保持在 3 秒以下。Kubernetes SLO 和 SLI 專注於 Kubernetes 組件的性能,並且完全獨立於 Amazon EKS 服務 SLA,後者專注於 EKS 集群端點的可用性。

Kubernetes 有許多功能允許用戶使用自定義插件或驅動程序擴展系統,如 CSI 驅動程序、admission webhook 和自動擴展器。這些擴展可能會以不同的方式極大影響 Kubernetes 集群的性能,即具有 `failurePolicy=Ignore` 的 admission webhook 如果 webhook 目標不可用,可能會增加 K8s API 請求的延遲。Kubernetes 可擴展性 SIG 使用["你承諾,我們承諾"框架](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md#how-we-define-scalability)定義可擴展性:

> 如果你承諾:
>     - 正確配置你的集群
>     - 合理使用可擴展性功能
>     - 將集群中的負載保持在[建議限制](https://github.com/kubernetes/community/blob/master/sig-scalability/configs-and-limits/thresholds.md)內
>
> 那麼我們承諾你的集群可擴展,即:
>     - 所有 SLO 都得到滿足。

## Kubernetes SLO
Kubernetes SLO 不考慮可能影響集群的所有插件和外部限制,例如工作節點擴展或 admission webhook。這些 SLO 專注於 [Kubernetes 組件](https://kubernetes.io/docs/concepts/overview/components/)並確保 Kubernetes 操作和資源在預期範圍內運行。SLO 幫助 Kubernetes 開發人員確保對 Kubernetes 代碼的更改不會降低整個系統的性能。

[Kuberntes 可擴展性 SIG 定義了以下官方 SLO/SLI](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md)。Amazon EKS 團隊定期在 EKS 集群上運行這些 SLO/SLI 的可擴展性測試,以監控隨著變更和新版本發布而可能出現的性能下降。

|目標	|定義	|SLO	|
|---	|---	|---	|
|API 請求延遲 (變更)	|處理單個對象的變更 API 調用的延遲,對於每個 (資源、動詞) 對,以過去 5 分鐘的 99 百分位數測量	|在默認 Kubernetes 安裝中,對於每個 (資源、動詞) 對,排除虛擬和聚合資源以及自定義資源定義,每個集群日 99 百分位數 <= 1 秒	|
|API 請求延遲 (唯讀)	|處理每個 (資源、範圍) 對的非流式唯讀 API 調用的延遲,以過去 5 分鐘的 99 百分位數測量	|在默認 Kubernetes 安裝中,對於每個 (資源、範圍) 對,排除虛擬和聚合資源以及自定義資源定義,每個集群日 99 百分位數: (a) 如果 `scope=resource` 則 <= 1 秒 (b) 否則 (如果 `scope=namespace` 或 `scope=cluster`) <= 30 秒	|
|Pod 啟動延遲	|可調度無狀態 Pod 的啟動延遲,不包括拉取映像和運行初始化容器的時間,從 Pod 創建時間戳開始測量,直到通過監視觀察到所有容器都報告為已啟動,以過去 5 分鐘的 99 百分位數測量	|在默認 Kubernetes 安裝中,每個集群日 99 百分位數 <= 5 秒	|

### API 請求延遲

`kube-apiserver` 默認將 `--request-timeout` 定義為 `1m0s`,這意味著請求可以運行長達一分鐘 (60 秒) 才會超時並被取消。延遲的定義 SLO 根據請求的類型分為變更或唯讀:

#### 變更

Kubernetes 中的變更請求會對資源進行更改,例如創建、刪除或更新。這些請求很昂貴,因為在返回更新的對象之前,這些更改必須寫入 [etcd 後端](https://kubernetes.io/docs/concepts/overview/components/#etcd)。[Etcd](https://etcd.io/) 是用於所有 Kubernetes 集群數據的分佈式鍵值存儲。

該延遲以 5 分鐘內的 99 百分位數測量 Kubernetes 資源的 (資源、動詞) 對,例如這將測量 Create Pod 請求和 Update Node 請求的延遲。要滿足 SLO,請求延遲必須 <= 1 秒。

#### 唯讀

唯讀請求檢索單個資源 (例如 Get Pod X) 或集合 (例如從命名空間 X "Get all Pods")。`kube-apiserver` 維護對象的緩存,因此請求的資源可能來自緩存,也可能需要首先從 etcd 檢索。
這些延遲也是以 5 分鐘內的 99 百分位數測量,但唯讀請求可能具有不同的範圍。SLO 定義了兩個不同的目標:

* 對於針對*單個*資源的請求 (即 `kubectl get pod -n mynamespace my-controller-xxx` ),請求延遲應保持 <= 1 秒。
* 對於在同一命名空間或整個集群中針對多個資源的請求 (例如,`kubectl get pods -A`),延遲應保持 <= 30 秒

SLO 針對不同的請求範圍設置了不同的目標值,因為對 Kubernetes 資源集合的請求預期在 SLO 內返回請求中所有對象的詳細信息。在大型集群或大型資源集合中,這可能會導致大型響應大小,需要一些時間才能返回。例如,在運行數萬個 Pod 的集群中,每個 Pod 在編碼為 JSON 時大約為 1 KiB,返回集群中所有 Pod 將包含 10MB 或更多。Kubernetes 客戶端可以通過使用 APIListChunking 來檢索大型資源集合,從而減少此響應大小。

### Pod 啟動延遲

該 SLO 主要關注從 Pod 創建到該 Pod 中的容器實際開始執行所需的時間。為了測量這一點,計算從記錄在 Pod 上的創建時間戳到 [Pod 的監視](https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes)報告容器已啟動的差值 (不包括拉取映像和運行初始化容器的時間)。要滿足 SLO,每個集群日 Pod 啟動延遲的 99 百分位數必須保持 <=5 秒。

請注意,該 SLO 假設該集群中已經存在處於就緒狀態的工作節點,Pod 可以在其上調度。該 SLO 不考慮映像拉取或初始化容器執行,並且還將測試限制為不利用持久存儲插件的"無狀態 Pod"。

## Kubernetes SLI 指標

Kubernetes 還通過向 Kubernetes 組件添加 [Prometheus 指標](https://prometheus.io/docs/concepts/data_model/)來跟踪這些 SLI 隨時間的變化,從而改善了對 SLI 的可觀察性。使用 [Prometheus 查詢語言 (PromQL)](https://prometheus.io/docs/prometheus/latest/querying/basics/) 我們可以構建查詢,在 Prometheus 或 Grafana 儀表板等工具中顯示 SLI 性能隨時間的變化,下面是上述 SLO 的一些示例。

### API 服務器請求延遲

|指標	|定義	|
|---	|---	|
|apiserver_request_sli_duration_seconds	|針對每個動詞、組、版本、資源、子資源、範圍和組件的響應延遲分佈 (不計算 webhook 持續時間和優先級及公平佇列等待時間) 以秒為單位	|
|apiserver_request_duration_seconds	|針對每個動詞、乾運行值、組、版本、資源、子資源、範圍和組件的響應延遲分佈,以秒為單位	|

*注意: `apiserver_request_sli_duration_seconds` 指標從 Kubernetes 1.27 開始可用。*

你可以使用這些指標來調查 API 服務器響應時間,並查看是否存在 Kubernetes 組件或其他插件/組件中的瓶頸。下面的查詢基於 [社區 SLO 儀表板](https://github.com/kubernetes/perf-tests/tree/master/clusterloader2/pkg/prometheus/manifests/dashboards)。

**API 請求延遲 SLI (變更)** - 這個時間*不*包括 webhook 執行或等待隊列的時間。
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"CREATE|DELETE|PATCH|POST|PUT", subresource!~"proxy|attach|log|exec|portforward"}[5m])) by (resource, subresource, verb, scope, le)) > 0`

**API 請求延遲總計 (變更)** - 這是請求在 API 服務器上花費的總時間,此時間可能比 SLI 時間長,因為它包括 webhook 執行和 API 優先級和公平等待時間。
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"CREATE|DELETE|PATCH|POST|PUT", subresource!~"proxy|attach|log|exec|portforward"}[5m])) by (resource, subresource, verb, scope, le)) > 0`

在這些查詢中,我們排除了不會立即返回的流式 API 請求,例如 `kubectl port-forward` 或 `kubectl exec` 請求 (`subresource!~"proxy|attach|log|exec|portforward"`),並且我們僅過濾修改對象的 Kubernetes 動詞 (`verb=~"CREATE|DELETE|PATCH|POST|PUT"`")。然後,我們計算過去 5 分鐘該延遲的 99 百分位數。

對於唯讀 API 請求,我們可以使用類似的查詢,只需修改我們過濾的動詞以包括唯讀操作 `LIST` 和 `GET`。還有不同的 SLO 閾值,具體取決於請求的範圍,即獲取單個資源還是列出多個資源。

**API 請求延遲 SLI (唯讀)** - 這個時間*不*包括 webhook 執行或等待隊列的時間。
對於單個資源 (scope=resource, threshold=1s)
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"GET", scope=~"resource"}[5m])) by (resource, subresource, verb, scope, le))`

對於同一命名空間中的資源集合 (scope=namespace, threshold=5s)
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"LIST", scope=~"namespace"}[5m])) by (resource, subresource, verb, scope, le))`

對於整個集群中的資源集合 (scope=cluster, threshold=30s)
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"LIST", scope=~"cluster"}[5m])) by (resource, subresource, verb, scope, le))`

**API 請求延遲總計 (唯讀)** - 這是請求在 API 服務器上花費的總時間,此時間可能比 SLI 時間長,因為它包括 webhook 執行和等待時間。
對於單個資源 (scope=resource, threshold=1s)
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"GET", scope=~"resource"}[5m])) by (resource, subresource, verb, scope, le))`

對於同一命名空間中的資源集合 (scope=namespace, threshold=5s)
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"LIST", scope=~"namespace"}[5m])) by (resource, subresource, verb, scope, le))`

對於整個集群中的資源集合 (scope=cluster, threshold=30s)
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"LIST", scope=~"cluster"}[5m])) by (resource, subresource, verb, scope, le))`

SLI 指標通過排除請求在 API 優先級和公平隊列中等待的時間、通過 admission webhook 的時間或其他 Kubernetes 擴展的時間,提供了 Kubernetes 組件性能的見解。總計指標提供了更全面的視圖,因為它反映了你的應用程序等待來自 API 服務器的響應所需的時間。比較這些指標可以提供請求處理延遲引入的位置的見解。

### Pod 啟動延遲

|指標	|定義	|
|---	|---	|
|kubelet_pod_start_sli_duration_seconds	|啟動 Pod 所需的持續時間 (秒),不包括拉取映像和運行初始化容器的時間,從 Pod 創建時間戳開始測量,直到通過監視觀察到所有容器都報告為已啟動	|
|kubelet_pod_start_duration_seconds	|從 kubelet 第一次看到 Pod 到 Pod 開始運行所需的持續時間 (秒)。這不包括調度 Pod 或擴展工作節點容量所需的時間。	|

*注意: `kubelet_pod_start_sli_duration_seconds` 從 Kubernetes 1.27 開始可用。*

與上面的查詢類似,你可以使用這些指標來深入了解節點擴展、映像拉取和初始化容器執行與 Kubelet 操作相比延遲了 Pod 啟動的時間。

**Pod 啟動延遲 SLI -** 這是從 Pod 被創建到應用程序容器報告為正在運行的時間。這包括工作節點容量可用和 Pod 被調度所需的時間,但不包括拉取映像或初始化容器運行所需的時間。
`histogram_quantile(0.99, sum(rate(kubelet_pod_start_sli_duration_seconds_bucket[5m])) by (le))`

**Pod 啟動延遲總計 -** 這是 kubelet 第一次啟動 Pod 所需的時間。這是從 kubelet 通過 WATCH 接收 Pod 開始測量的,不包括節點擴展或調度所需的時間。這包括拉取映像和初始化容器運行所需的時間。
`histogram_quantile(0.99, sum(rate(kubelet_pod_start_duration_seconds_bucket[5m])) by (le))`

## 你的集群上的 SLO

如果你正在從 EKS 集群中的 Kubernetes 資源收集 Prometheus 指標,你可以更深入地了解 Kubernetes 控制平面組件的性能。

[perf-tests 存儲庫](https://github.com/kubernetes/perf-tests/)包括 Grafana 儀表板,用於顯示測試期間集群的延遲和關鍵性能指標。perf-tests 配置利用了 [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack),這是一個開源項目,預先配置為收集 Kubernetes 指標,但你也可以使用 [Amazon Managed Prometheus 和 Amazon Managed Grafana](https://aws-observability.github.io/terraform-aws-observability-accelerator/eks/)。

如果你正在使用 `kube-prometheus-stack` 或類似的 Prometheus 解決方案,你可以安裝相同的儀表板來實時觀察你的集群上的 SLO。

1. 你首先需要使用 `kubectl apply -f prometheus-rules.yaml` 安裝儀表板中使用的 Prometheus 規則。你可以在這裡下載規則的副本: https://github.com/kubernetes/perf-tests/blob/master/clusterloader2/pkg/prometheus/manifests/prometheus-rules.yaml
    1. 確保檔案中的命名空間與你的環境匹配
    2. 如果你正在使用 `kube-prometheus-stack`,請驗證標籤是否與 `prometheus.prometheusSpec.ruleSelector` helm 值匹配
2. 然後你可以在 Grafana 中安裝儀表板。json 儀表板和生成它們的 python 腳本可在這裡找到: https://github.com/kubernetes/perf-tests/tree/master/clusterloader2/pkg/prometheus/manifests/dashboards
    1. [`slo.json` 儀表板](https://github.com/kubernetes/perf-tests/blob/master/clusterloader2/pkg/prometheus/manifests/dashboards/slo.json)顯示了集群相對於 Kubernetes SLO 的性能

請考慮 SLO 專注於你集群中 Kubernetes 組件的性能,但你還可以查看其他指標,它們可以提供不同的視角或對你的集群的見解。像 [Kube-state-metrics](https://github.com/kubernetes/kube-state-metrics/tree/main) 這樣的 Kubernetes 社區項目可以幫助你快速分析集群中的趨勢。Kubernetes 社區中大多數常見的插件和驅動程序也發出 Prometheus 指標,允許你調查自動擴展器或自定義調度器等內容。

[可觀察性最佳實踐指南](https://aws-observability.github.io/observability-best-practices/guides/containers/oss/eks/best-practices-metrics-collection/#control-plane-metrics)有你可以使用的其他 Kubernetes 指標的示例,以獲得進一步的見解。