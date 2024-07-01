# 叢集服務

叢集服務在 EKS 叢集內運行，但它們並非使用者工作負載。如果您有 Linux 伺服器，您通常需要運行諸如 NTP、syslog 和容器運行時等服務來支援您的工作負載。叢集服務類似，支援幫助您自動化和操作叢集的服務。在 Kubernetes 中，這些通常在 kube-system 命名空間中運行，有些作為 [DaemonSets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) 運行。

叢集服務預期會有高正常運行時間，並且在發生中斷和故障排除時通常至關重要。如果核心叢集服務無法使用，您可能會失去可用於恢復或預防中斷的數據存取權限（例如高磁碟使用率）。它們應該在專用計算實例上運行，例如單獨的節點群組或 AWS Fargate。這將確保叢集服務不會受到共用實例上可能縮放或使用更多資源的工作負載的影響。

## 擴展 CoreDNS

擴展 CoreDNS 有兩種主要機制。減少對 CoreDNS 服務的呼叫次數，以及增加副本數量。

### 透過降低 ndots 減少外部查詢

ndots 設定指定在域名中被視為足夠避免查詢 DNS 的點數（即「點」）。如果您的應用程式的 ndots 設定為 5（預設值），而您從外部域（如 api.example.com，2 個點）請求資源，則 CoreDNS 將為 /etc/resolv.conf 中定義的每個搜索域查詢更具體的域。預設情況下，將在進行外部請求之前搜索以下域：

```
api.example.<namespace>.svc.cluster.local
api.example.svc.cluster.local
api.example.cluster.local
api.example.<region>.compute.internal
```

`namespace` 和 `region` 值將替換為您的工作負載命名空間和計算區域。根據您的叢集設定，您可能會有其他搜索域。

您可以透過 [降低工作負載的 ndots 選項](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-dns-config) 或透過包含尾隨 . 完全限定您的域請求（例如 `api.example.com.`），來減少對 CoreDNS 的請求次數。如果您的工作負載透過 DNS 連接到外部服務，我們建議將 ndots 設為 2，以便工作負載不會在叢集內進行不必要的叢集 DNS 查詢。您可以設定不同的 DNS 伺服器和搜索域，如果工作負載不需要存取叢集內的服務。

```
spec:
  dnsPolicy: "None"
  dnsConfig:
    options:
      - name: ndots
        value: "2"
      - name: edns0
```

如果您將 ndots 降低到太低的值，或您正在連接的域不包含足夠的特異性（包括尾隨 .），則 DNS 查詢可能會失敗。請確保測試此設定對您的工作負載的影響。

### 水平擴展 CoreDNS

CoreDNS 實例可以透過將更多副本新增至部署來擴展。建議您使用 [NodeLocal DNS](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) 或 [叢集比例自動調整器](https://github.com/kubernetes-sigs/cluster-proportional-autoscaler) 來擴展 CoreDNS。

NodeLocal DNS 將需要在每個節點上運行一個實例（作為 DaemonSet），這需要在叢集中使用更多計算資源，但它將避免 DNS 請求失敗並減少叢集內 DNS 查詢的響應時間。叢集比例自動調整器將根據叢集中的節點或核心數來擴展 CoreDNS。這與請求查詢沒有直接關係，但根據您的工作負載和叢集大小可能很有用。預設的比例擴展是每 256 個核心或 16 個節點（以先發生者為準）新增一個副本。

## 垂直擴展 Kubernetes Metrics Server

Kubernetes Metrics Server 支援水平和垂直擴展。透過水平擴展 Metrics Server，它將具有高可用性，但不會水平擴展以處理更多叢集指標。您將需要根據 [他們的建議](https://kubernetes-sigs.github.io/metrics-server/#scaling) 在新增節點和收集的指標時垂直擴展 Metrics Server。

Metrics Server 將它收集、匯總和服務的數據保存在記憶體中。隨著叢集的增長，Metrics Server 存儲的數據量也會增加。在大型叢集中，Metrics Server 將需要比預設安裝中指定的記憶體和 CPU 預留更多的計算資源。您可以使用 [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)（VPA）或 [Addon Resizer](https://github.com/kubernetes/autoscaler/tree/master/addon-resizer) 來擴展 Metrics Server。Addon Resizer 根據工作節點的比例垂直擴展，而 VPA 則根據 CPU 和記憶體使用量進行擴展。

## CoreDNS lameduck 持續時間

Pod 使用 `kube-dns` 服務進行名稱解析。Kubernetes 使用目的地 NAT（DNAT）將來自節點的 `kube-dns` 流量重新導向到 CoreDNS 後端 Pod。當您擴展 CoreDNS 部署時，`kube-proxy` 會更新節點上的 iptables 規則和鏈，以將 DNS 流量重新導向到 CoreDNS Pod。根據叢集大小，傳播新端點時（擴展時）和刪除規則時（縮減時）可能需要 1 到 10 秒。

此傳播延遲可能會在終止 CoreDNS Pod 但節點的 iptables 規則尚未更新時導致 DNS 查詢失敗。在此情況下，節點可能會繼續將 DNS 查詢發送到已終止的 CoreDNS Pod。

您可以透過在 CoreDNS Pod 中設定 [lameduck](https://coredns.io/plugins/health/) 持續時間來減少 DNS 查詢失敗。在 lameduck 模式下，CoreDNS 將繼續響應正在進行的請求。設定 lameduck 持續時間將延遲 CoreDNS 關閉過程，讓節點有時間更新其 iptables 規則和鏈。

我們建議將 CoreDNS lameduck 持續時間設為 30 秒。

## CoreDNS 就緒探針

我們建議使用 `/ready` 而非 `/health` 作為 CoreDNS 的就緒探針。

根據先前建議將 lameduck 持續時間設為 30 秒，在 Pod 終止前提供充足的時間讓節點的 iptables 規則得以更新，使用 `/ready` 而非 `/health` 作為 CoreDNS 就緒探針可確保 CoreDNS Pod 在啟動時完全準備就緒，可立即回應 DNS 請求。

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8181
    scheme: HTTP
```

有關 CoreDNS Ready 插件的更多資訊，請參閱 [https://coredns.io/plugins/ready/](https://coredns.io/plugins/ready/)

## 日誌和監控代理程式

日誌和監控代理程式可能會對您的叢集控制平面造成重大負載，因為代理程式會查詢 API 伺服器以使用工作負載中繼資料來豐富日誌和指標。節點上的代理程式只能存取本機節點資源以查看容器和程序名稱等資訊。查詢 API 伺服器後，它可以新增更多詳細資料，例如 Kubernetes 部署名稱和標籤。這對於故障排除可能非常有用，但對於擴展來說卻是有害的。

由於日誌和監控的選項有很多種，我們無法為每個提供者顯示範例。使用 [fluentbit](https://docs.fluentbit.io/manual/pipeline/filters/kubernetes) 時，我們建議啟用 Use_Kubelet 從本機 kubelet 而非 Kubernetes API 伺服器獲取中繼資料，並將 `Kube_Meta_Cache_TTL` 設為一個數字，以減少在數據可以緩存時重複呼叫的次數（例如 60）。

擴展監控和日誌記錄有兩個一般選項：

* 停用整合
* 採樣和過濾

停用整合通常不是選項，因為您會失去日誌中繼資料。這將消除 API 擴展問題，但會引入其他問題，因為在需要時無法獲得所需的中繼資料。

採樣和過濾可減少收集的指標和日誌數量。這將降低對 Kubernetes API 的請求數量，並減少存儲收集的指標和日誌所需的空間。減少存儲成本將降低整個系統的成本。

配置採樣的能力取決於代理程式軟體，並且可以在攝取的不同點實現。盡可能在代理程式附近添加採樣非常重要，因為 API 伺服器呼叫可能發生在那裡。請聯繫您的提供者以了解有關採樣支援的更多資訊。

如果您使用 CloudWatch 和 CloudWatch Logs，您可以使用 [文件](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html) 中所述的模式添加代理過濾。

為避免丟失日誌和指標，您應將數據發送到可在接收端發生中斷時暫存數據的系統。使用 fluentbit，您可以使用 [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/pipeline/outputs/firehose) 暫時保留數據，這可以減少過載您最終數據存儲位置的機會。