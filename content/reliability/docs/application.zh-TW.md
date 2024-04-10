# 運行高度可用的應用程式

您的客戶期望您的應用程式隨時可用,包括在進行更改時,尤其是在流量高峰期間。可擴展和有彈性的架構可以確保您的應用程式和服務在沒有中斷的情況下持續運行,從而讓您的用戶滿意。可擴展的基礎設施可根據業務需求而增長和縮減。消除單點故障是提高應用程式可用性和使其具有彈性的關鍵步驟。

使用 Kubernetes,您可以以高度可用和有彈性的方式運行和操作您的應用程式。它的聲明式管理可確保一旦設置了應用程式,Kubernetes 將不斷嘗試 [將當前狀態與期望狀態相匹配](https://kubernetes.io/docs/concepts/architecture/controller/#desired-vs-current)。

## 建議

### 避免運行單個 Pod

如果您的整個應用程式在單個 Pod 中運行,則該 Pod 終止時,您的應用程式將無法使用。不要使用單個 Pod 部署應用程式,而是創建 [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)。如果由 Deployment 創建的 Pod 失敗或被終止,Deployment [控制器](https://kubernetes.io/docs/concepts/architecture/controller/) 將啟動新的 Pod 以確保指定數量的副本 Pod 始終在運行。

### 運行多個副本

使用 Deployment 運行應用程式的多個副本 Pod 有助於以高度可用的方式運行。如果一個副本失敗,其餘副本仍將繼續運行,儘管容量會降低,直到 Kubernetes 創建另一個 Pod 來彌補損失。此外,您可以使用 [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) 根據工作負載需求自動擴展副本。

### 跨節點調度副本

如果所有副本都在同一個節點上運行,而該節點變得不可用,則運行多個副本將不會很有用。考慮使用 Pod 反親和性或 Pod 拓撲擴散約束來跨多個工作節點分佈 Deployment 的副本。

您可以進一步提高典型應用程式的可靠性,方法是跨多個可用區域運行它。

#### 使用 Pod 反親和性規則

下面的清單告訴 Kubernetes 調度器 *優先* 將 Pod 放置在單獨的節點和可用區域。它不需要不同的節點或可用區域,因為如果需要,則一旦每個可用區域都有一個 Pod 在運行,Kubernetes 就無法再調度任何 Pod。如果您的應用程式只需要三個副本,您可以對 `topologyKey: topology.kubernetes.io/zone` 使用 `requiredDuringSchedulingIgnoredDuringExecution`,Kubernetes 調度器將不會在同一個可用區域調度兩個 Pod。

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spread-host-az
  labels:
    app: web-server
spec:
  replicas: 4
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-server
              topologyKey: topology.kubernetes.io/zone
            weight: 100
          - podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-server
              topologyKey: kubernetes.io/hostname 
            weight: 99
      containers:
      - name: web-app
        image: nginx:1.16-alpine
```

#### 使用 Pod 拓撲擴散約束

與 Pod 反親和性規則類似,Pod 拓撲擴散約束允許您在不同的故障域(或拓撲域)如主機或可用區域中使您的應用程式可用。當您試圖確保容錯以及可用性時,這種方法非常有效,因為您可以在不同的拓撲域中擁有多個副本。另一方面,具有相互反親和性的 Pod 具有相互排斥的效果,因此很容易產生在拓撲域中只有單個副本的結果。在這種情況下,在專用節點上只有單個副本對於容錯和資源利用都不理想。使用拓撲擴散約束,您可以更好地控制調度器應該嘗試在拓撲域之間應用的擴散或分佈。在這種方法中,有一些重要的屬性可以使用:
1. `maxSkew` 用於控制或確定可以在拓撲域之間的不均勻程度的最大點。例如,如果應用程式有 10 個副本並部署在 3 個可用區域中,您無法獲得均勻的分佈,但您可以影響分佈的不均勻程度。在這種情況下,`maxSkew` 可以是 1 到 10 之間的任何值。值為 1 意味著您可能最終會在 3 個可用區域中獲得 `4,3,3`、`3,4,3` 或 `3,3,4` 的分佈。相比之下,值為 10 意味著您可能最終會在 3 個可用區域中獲得 `10,0,0`、`0,10,0` 或 `0,0,10` 的分佈。
2. `topologyKey` 是節點標籤之一的鍵,定義了應該用於 Pod 分佈的拓撲域類型。例如,區域擴散將具有以下鍵值對:
```
topologyKey: "topology.kubernetes.io/zone"
```
3. `whenUnsatisfiable` 屬性用於確定如果無法滿足所需的約束,您希望調度器如何響應。
4. `labelSelector` 用於查找匹配的 Pod,以便調度器在根據您指定的約束決定放置 Pod 的位置時可以知道它們。

除了上述內容外,您還可以在 [Kubernetes 文檔](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)中進一步閱讀其他字段。

![跨 3 個可用區域的 Pod 拓撲擴散約束](./images/pod-topology-spread-constraints.jpg)

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spread-host-az
  labels:
    app: web-server
spec:
  replicas: 10
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: "topology.kubernetes.io/zone"
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: express-test
      containers:
      - name: web-app
        image: nginx:1.16-alpine
```

### 運行 Kubernetes Metrics Server

安裝 Kubernetes [metrics server](https://github.com/kubernetes-sigs/metrics-server) 以幫助擴展您的應用程式。Kubernetes 自動擴展器插件如 [HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) 和 [VPA](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) 需要跟踪應用程式指標以對其進行擴展。metrics-server 從 kubelet 收集資源指標,並以 [Metrics API 格式](https://github.com/kubernetes/metrics)提供服務。

metrics-server 不保留任何數據,它也不是監控解決方案。它的目的是向其他系統公開 CPU 和內存使用情況指標。如果您想跟踪應用程式的狀態隨時間的變化,您需要一個監控工具,如 Prometheus 或 Amazon CloudWatch。

請按照 [EKS 文檔](https://docs.aws.amazon.com/eks/latest/userguide/metrics-server.html)在您的 EKS 集群中安裝 metrics-server。

## Horizontal Pod Autoscaler (HPA)

HPA 可以根據需求自動擴展您的應用程式,並幫助您在流量高峰期間避免影響客戶。它是 Kubernetes 中實現為一個控制循環,定期從提供資源指標的 API 查詢指標。

HPA 可以從以下 API 獲取指標:
1. `metrics.k8s.io`,也稱為資源指標 API - 提供 Pod 的 CPU 和內存使用情況
2. `custom.metrics.k8s.io` - 從其他指標收集器(如 Prometheus)提供指標;這些指標 __內部__ 在您的 Kubernetes 集群中。
3. `external.metrics.k8s.io` - 提供 __外部__ 於您的 Kubernetes 集群的指標(例如,SQS 隊列深度、ELB 延遲)。

您必須使用這三個 API 中的一個來提供指標,以擴展您的應用程式。

### 根據自定義或外部指標擴展應用程式

您可以使用自定義或外部指標根據 CPU 或內存利用率以外的指標來擴展您的應用程式。[自定義指標](https://github.com/kubernetes-sigs/custom-metrics-apiserver) API 服務器提供 HPA 可以用於自動擴展應用程式的 `custom-metrics.k8s.io` API。

您可以使用 [Prometheus Adapter for Kubernetes Metrics APIs](https://github.com/directxman12/k8s-prometheus-adapter) 從 Prometheus 收集指標並與 HPA 一起使用。在這種情況下,Prometheus 適配器將以 [Metrics API 格式](https://github.com/kubernetes/metrics/blob/master/pkg/apis/metrics/types.go)公開 Prometheus 指標。

一旦部署了 Prometheus Adapter,您就可以使用 kubectl 查詢自定義指標。
`kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/`

外部指標,顧名思義,為 Horizontal Pod Autoscaler 提供了根據外部於 Kubernetes 集群的指標擴展部署的能力。例如,在批處理工作負載中,通常需要根據 SQS 隊列中的作業數量來擴展副本數量。

要根據 CloudWatch 指標(例如 [根據 SQS 隊列深度擴展批處理器應用程式](https://github.com/awslabs/k8s-cloudwatch-adapter/blob/master/samples/sqs/README.md))自動擴展 Deployment,您可以使用 [`k8s-cloudwatch-adapter`](https://github.com/awslabs/k8s-cloudwatch-adapter)。`k8s-cloudwatch-adapter` 是一個社區項目,不由 AWS 維護。

## Vertical Pod Autoscaler (VPA)

VPA 自動調整 Pod 的 CPU 和內存預留,以幫助您為應用程式 "調整大小"。對於需要垂直擴展的應用程式 - 通過增加資源分配來實現 - 您可以使用 [VPA](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) 自動擴展 Pod 副本或提供擴展建議。

如果 VPA 需要擴展它,您的應用程式可能會暫時無法使用,因為 VPA 的當前實現不會對 Pod 進行就地調整;相反,它將重新創建需要擴展的 Pod。

[EKS 文檔](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html)包括設置 VPA 的分步指南。

[Fairwinds Goldilocks](https://github.com/FairwindsOps/goldilocks/) 項目提供了一個儀表板,用於可視化 VPA 對 CPU 和內存請求和限制的建議。它的 VPA 更新模式允許您根據 VPA 建議自動擴展 Pod。

## 更新應用程式

現代應用程式需要快速創新,同時具有高度的穩定性和可用性。Kubernetes 為您提供了工具,可以不中斷客戶的情況下持續更新應用程式。

讓我們看看一些使您能夠快速部署更改而不犧牲可用性的最佳實踐。

### 具有執行回滾的機制

擁有一個撤銷按鈕可以避免災難。最佳做法是在更新生產集群之前,在單獨的較低環境(測試或開發環境)中測試部署。使用 CI/CD 管道可以幫助您自動化和測試部署。通過持續部署管道,如果升級發生故障,您可以快速恢復到舊版本。

您可以使用 Deployment 來更新正在運行的應用程式。這通常是通過更新容器映像來完成。您可以使用 `kubectl` 更新 Deployment,如下所示:

```bash
kubectl --record deployment.apps/nginx-deployment set image nginx-deployment nginx=nginx:1.16.1
```

`--record` 參數記錄對 Deployment 的更改,如果您需要執行回滾,這將很有幫助。`kubectl rollout history deployment` 顯示您集群中對 Deployment 的記錄更改。您可以使用 `kubectl rollout undo deployment <DEPLOYMENT_NAME>` 回滾更改。

默認情況下,當您更新需要重新創建 Pod 的 Deployment 時,Deployment 將執行 [滾動更新](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)。換句話說,Kubernetes 將只更新 Deployment 中運行的部分 Pod,而不是所有 Pod。您可以通過 `RollingUpdateStrategy` 屬性控制 Kubernetes 執行滾動更新的方式。

在執行 Deployment 的 *滾動更新* 時,您可以使用 [`Max Unavailable`](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#max-unavailable) 屬性指定在更新期間可以不可用的最大 Pod 數量。Deployment 的 `Max Surge` 屬性允許您設置可以超過所需 Pod 數量的最大 Pod 數。

考慮調整 `max unavailable` 以確保滾動更新不會中斷您的客戶。例如,Kubernetes 默認設置 25% `max unavailable`,這意味著如果您有 100 個 Pod,在滾動更新期間可能只有 75 個 Pod 處於活動狀態。如果您的應用程式需要至少 80 個 Pod,這種滾動更新可能會造成中斷。相反,您可以將 `max unavailable` 設置為 20%,以確保在整個滾動更新過程中至少有 80 個功能 Pod。

### 使用藍/綠部署

變更本身是有風險的,但無法撤銷的變更可能是災難性的。允許您有效地通過 *回滾* 撤消更改的變更程序使增強和實驗更加安全。藍/綠部署為您提供了一種快速撤銷更改的方法,如果出現問題。在這種部署策略中,您為新版本創建一個環境。這個環境與正在更新的應用程式的當前版本相同。一旦新環境被佈建,流量就會被路由到新環境。如果新版本產生了預期的結果而沒有生成錯誤,則終止舊環境。否則,將流量恢復到舊版本。

您可以在 Kubernetes 中通過創建與現有版本的 Deployment 相同的新 Deployment 來執行藍/綠部署。一旦您驗證新 Deployment 中的 Pod 正在無錯誤運行,您就可以通過更改路由到您應用程式 Pod 的 Service 中的 `selector` 規範開始將流量發送到新 Deployment。

許多持續集成工具如 [Flux](https://fluxcd.io)、[Jenkins](https://www.jenkins.io) 和 [Spinnaker](https://spinnaker.io) 都允許您自動化藍/綠部署。AWS Containers Blog 包括使用 AWS Load Balancer Controller 的分步指南: [使用 AWS Load Balancer Controller 進行藍/綠部署、金絲雀部署和 A/B 測試](https://aws.amazon.com/blogs/containers/using-aws-load-balancer-controller-for-blue-green-deployment-canary-deployment-and-a-b-testing/)

### 使用金絲雀部署

金絲雀部署是藍/綠部署的一種變體,可以顯著降低變更的風險。在這種部署策略中,您在旧 Deployment 旁邊創建一個新的具有較少 Pod 的 Deployment,並將少量流量分流到新的 Deployment。如果指標表明新版本的性能與現有版本一樣好或更好,您就可以逐步增加到新 Deployment 的流量,同時擴展它,直到所有流量都被分流到新 Deployment。如果出現問題,您可以將所有流量路由到舊 Deployment,並停止將流量發送到新 Deployment。

儘管 Kubernetes 沒有原生的方式來執行金絲雀部署,但您可以使用諸如 [Flagger](https://github.com/weaveworks/flagger) 與 [Istio](https://docs.flagger.app/tutorials/istio-progressive-delivery) 或 [App Mesh](https://docs.flagger.app/install/flagger-install-on-eks-appmesh) 等工具。


## 健康檢查和自我修復

沒有軟件是沒有錯誤的,但 Kubernetes 可以幫助您盡量減少軟件故障的影響。過去,如果應用程式崩潰,有人必須手動重新啟動應用程式來解決問題。Kubernetes 使您能夠檢測 Pod 中的軟件故障,並自動用新副本替換它們。使用 Kubernetes,您可以監控應用程式的健康狀況,並自動替換不健康的實例。

Kubernetes 支持三種 [健康檢查](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/):

1. 存活探測器
2. 啟動探測器(在 Kubernetes 1.16+ 版本中支持)
3. 就緒探測器

[Kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) 是 Kubernetes 代理,負責運行所有上述檢查。Kubelet 可以通過三種方式檢查 Pod 的健康狀況:kubelet 可以在 Pod 的容器內運行 shell 命令、向其容器發送 HTTP GET 請求或在指定端口打開 TCP 套接字。

如果您選擇基於 `exec` 的探測器(在容器內運行 shell 腳本),請確保 shell 命令在 `timeoutSeconds` 值過期之前退出。否則,您的節點將有 `<defunct>` 進程,導致節點故障。

## 建議
### 使用存活探測器移除不健康的 Pod

存活探測器可以檢測 *死鎖* 情況,在這種情況下,進程繼續運行,但應用程式變得無響應。例如,如果您正在運行一個在端口 80 上監聽的 Web 服務,您可以配置一個存活探測器在 Pod 的端口 80 上發送 HTTP GET 請求。Kubelet 將定期向 Pod 發送 GET 請求並期望響應;如果 Pod 響應在 200-399 之間,則 kubelet 認為該 Pod 是健康的;否則,該 Pod 將被標記為不健康。如果一個 Pod 連續失敗健康檢查,kubelet 將終止它。

您可以使用 `initialDelaySeconds` 來延遲第一次探測。

使用存活探測器時,請確保您的應用程式不會出現所有 Pod 同時失敗存活探測器的情況,因為 Kubernetes 將嘗試替換所有 Pod,這將使您的應用程式離線。此外,Kubernetes 將繼續創建新的 Pod,這些 Pod 也將失敗存活探測器,從而給控制平面帶來不必要的壓力。避免將存活探測器配置為依賴於 Pod 外部的因素,例如外部數據庫。換句話說,無響應的外部數據庫不應使您的 Pod 失敗其存活探測器。

Sandor Szücs 的文章 [LIVENESS PROBES ARE DANGEROUS](https://srcco.de/posts/kubernetes-liveness-probes-are-dangerous.html) 描述了由於配置不當的探測器可能導致的問題。

### 對於需要更長時間啟動的應用程式使用啟動探測器

當您的應用程式需要額外的時間啟動時,您可以使用啟動探測器來延遲存活探測器和就緒探測器。例如,需要從數據庫加載緩存的 Java 應用程式可能需要長達兩分鐘才能完全可用。在它完全可用之前執行的任何存活或就緒探測器都可能會失敗。配置啟動探測器將允許 Java 應用程式在存活或就緒探測器執行之前變為 *健康*。

在啟動探測器成功之前,所有其他探測器都將被禁用。您可以定義 Kubernetes 應該等待應用程式啟動的最長時間。如果在配置的最長時間後,Pod 仍然失敗啟動探測器,它將被終止,並創建一個新的 Pod。

啟動探測器類似於存活探測器 - 如果它們失敗,Pod 將被重新創建。正如 Ricardo A. 在他的文章 [Fantastic Probes And How To Configure Them](https://medium.com/swlh/fantastic-probes-and-how-to-configure-them-fef7e030bd2f) 中解釋的那樣,當應用程式的啟動時間不可預測時,應該使用啟動探測器。如果您知道您的應用程式需要十秒鐘才能啟動,您應該使用具有 `initialDelaySeconds` 的存活/就緒探測器。

### 使用就緒探測器檢測部分不可用

存活探測器檢測應用程式中可以通過終止 Pod(因此重新啟動應用程式)來解決的故障,而就緒探測器則檢測應用程式可能 *暫時* 不可用的情況。在這些情況下,應用程式可能會暫時無響應;但是,一旦此操作完成,它就會再次變為健康。

例如,在密集的磁盤 I/O 操作期間,應用程式可能暫時無法處理請求。在這種情況下,終止應用程式的 Pod 不是一種補救措施;同時,發送到該 Pod 的任何其他請求都可能會失敗。

您可以使用就緒探測器檢測應用程式中的暫時不可用情況,並停止將請求發送到其 Pod,直到它再次可用為止。*與存活探測器不同,失敗的就緒探測器意味著 Pod 將不會從 Kubernetes Service 接收任何流量*。當就緒探測器成功時,Pod 將恢復從 Service 接收流量。

就像存活探測器一樣,避免將就緒探測器配置為依賴於 Pod 外部的資源(如數據庫)。這裡有一個場景說明了配置不當的就緒探測器如何使應用程式無法運行 - 如果當應用程式的數據庫無法訪問時,Pod 的就緒探測器失敗,則共享相同健康檢查標準的其他 Pod 副本也將同時失敗。以這種方式設置探測器將確保無論何時數據庫不可用,Pod 的就緒探測器都將失敗,Kubernetes 將停止向 *所有* Pod 發送流量。

使用就緒探測器的一個副作用是它們可能會增加更新 Deployment 所需的時間。新副本將不會接收流量,除非就緒探測器成功;在此之前,舊副本將繼續接收流量。

---

## 處理中斷

Pod 有有限的生命週期 - 即使您有長期運行的 Pod,也應該確保 Pod 在到期時正確終止。根據您的升級策略,Kubernetes 集群升級可能需要您創建新的工作節點,這需要在較新的節點上重新創建所有 Pod。正確的終止處理和 Pod 中斷預算可以幫助您避免在從舊節點移除 Pod 並在較新節點上重新創建它們時出現服務中斷。

升級工作節點的首選方式是創建新的工作節點並終止舊節點。在終止工作節點之前,您應該 `drain` 它。當工作節點被排空時,它上面的所有 Pod 都會被 *安全地* 逐出。安全是一個關鍵詞;當工作節點上的 Pod 被逐出時,它們不會簡單地收到 `SIGKILL` 信號。相反,`SIGTERM` 信號將發送到每個被逐出 Pod 中容器的主進程(PID 1)。發送 `SIGTERM` 信號後,Kubernetes 將給予進程一些時間(寬限期),然後再發送 `SIGKILL` 信號。默認寬限期為 30 秒;您可以使用 kubectl 中的 `grace-period` 標誌或在您的 Podspec 中聲明 `terminationGracePeriodSeconds` 來覆蓋默認值。

`kubectl delete pod <pod name> --grace-period=<seconds>`

通常情況下,容器中的主進程沒有 PID 1。考慮這個基於 Python 的示例容器:

```
$ kubectl exec python-app -it ps
 PID USER TIME COMMAND
 1   root 0:00 {script.sh} /bin/sh ./script.sh
 5   root 0:00 python app.py
```

在這個示例中,shell 腳本接收到 `SIGTERM`,主進程(在這個示例中是 Python 應用程式)沒有收到 `SIGTERM` 信號。當 Pod 被終止時,Python 應用程式將被突然殺死。這可以通過更改容器的 [`ENTRYPOINT`](https://docs.docker.com/engine/reference/builder/#entrypoint) 來啟動 Python 應用程式來補救。或者,您可以使用像 [dumb-init](https://github.com/Yelp/dumb-init) 這樣的工具來確保您的應用程式可以處理信號。

您還可以使用 [Container hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/#container-hooks) 在容器啟動或停止時執行腳本或 HTTP 請求。`PreStop` 鉤子操作在容器收到 `SIGTERM` 信號之前運行,並且必須在發送此信號之前完成。`terminationGracePeriodSeconds` 值適用於 `PreStop` 鉤子操作開始執行時,而不是發送 `SIGTERM` 信號時。

## 建議

### 使用 Pod 中斷預算保護關鍵工作負載

Pod 中斷預算或 PDB 可以暫時暫停逐出過程,如果應用程式的副本數量低於聲明的閾值。一旦可用副本的數量超過閾值,逐出過程將繼續。您可以使用 PDB 聲明 `minAvailable` 和 `maxUnavailable` 副本數量。例如,如果您希望至少有三個應用程式副本可用,您可以創建一個 PDB。

```
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: my-svc-pdb
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: my-svc
```

上面的 PDB 策略告訴 Kubernetes 暫停逐出過程,直到有三個或更多副本可用。節點排空遵守 `PodDisruptionBudgets`。在 EKS 托管節點組升級期間,[節點在十五分鐘超時後被排空](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-update-behavior.html)。十五分鐘後,如果不強制更新(在 EKS 控制台中稱為滾動更新),更新將失敗。如果強制更新,Pod 將被刪除。

對於自管理節點,您還可以使用像 [AWS Node Termination Handler](https://github.com/aws/aws-node-termination-handler) 這樣的工具,它可以確保 Kubernetes 控制平面對可能導致您的 EC2 實例變得不可用的事件做出適當響應,例如 [EC2 維護](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-instances-status-check_sched.html) 事件和 [EC2 Spot 中斷](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html)。它使用 Kubernetes API 來隔離節點,以確保不會調度新的 Pod,然後將其排空,終止任何正在運行的 Pod。

您可以使用 Pod 反親和性在不同節點上調度 Deployment 的 Pod,並避免在節點升級期間出現與 PDB 相關的延遲。

### 實踐混沌工程
> 混沌工程是在分佈式系統上進行實驗的學科,目的是建立對系統在生產環境中承受動盪條件的能力的信心。

在他的博客中,Dominik Tornow 解釋說 [Kubernetes 是一個聲明式系統](https://medium.com/@dominik.tornow/the-mechanics-of-kubernetes-ac8112eaa302),*"用戶向系統提供所需系統狀態的表示。然後,系統考慮當前狀態和所需狀態,以確定從當前狀態過渡到所需狀態的命令序列。"* 這意味著 Kubernetes 始終存儲 *所需狀態*,如果系統偏離,Kubernetes 將採取行動來恢復狀態。例如,如果工作節點變得不可用,Kubernetes 將在另一個工作節點上重新調度 Pod。類似地,如果 `replica` 崩潰,則 [Deployment Controller](https://kubernetes.io/docs/concepts/architecture/controller/#design) 將創建一個新的 `replica`。通過這種方式,Kubernetes 控制器會自動修復故障。

像 [Gremlin](https://www.gremlin.com) 這樣的混沌工程工具可以幫助您測試 Kubernetes 集群的彈性並識別單點故障。在受控環境中引入人為混亂的工具可以揭示系統性弱點,提供一個機會來識別瓶頸和錯誤配置,並糾正問題。混沌工程理念提倡有意破壞並對基礎設施進行壓力測試,以盡量減少意外停機。

### 使用服務網格

您可以使用服務網格來提高應用程式的彈性。服務網格支持服務間通信,並增加了微服務網絡的可觀察性。大多數服務網格產品的工作方式是在每個服務旁運行一個小型網絡代理,它攔截並檢查應用程式的網絡流量。您可以將應用程式放入網格中,而無需修改應用程式。使用服務代理的內置功能,您可以讓它生成網絡統計信息、創建訪問日誌以及為分佈式跟踪向外bound請求添加 HTTP 標頭。

服務網格可以幫助您通過自動請求重試、超時、斷路器和速率限制等功能使您的微服務更加彈性。

如果您運行多個集群,您可以使用服務網格啟用跨集群的服務間通信。

### 服務網格
+ [AWS App Mesh](https://aws.amazon.com/app-mesh/)
+ [Istio](https://istio.io)
+ [LinkerD](http://linkerd.io)
+ [Consul](https://www.consul.io)

---

## 可觀察性

可觀察性是一個包括監控、日誌記錄和跟踪的總稱。基於微服務的應用程式本質上是分佈式的。與只需監控單個系統的單體應用程式不同,在分佈式應用程式架構中,您需要監控每個組件的性能。您可以使用集群級監控、日誌記錄和分佈式跟踪系統來識別集群中的問題,從而在它們中斷客戶之前解決。

Kubernetes 內置的故障排除和監控工具有限。metrics-server 收集資源指標並將其存儲在內存中,但不會持久化它們。您可以使用 kubectl 查看 Pod 的日誌,但 Kubernetes 不會自動保留日誌。分佈式跟踪的實現要麼在應用程式代碼級別完成,要麼使用服務網格。

Kubernetes 的可擴展性在這裡展現出來。Kubernetes 允許您引入首選的集中式監控、日誌記錄和跟踪解決方案。

## 建議

### 監控您的應用程式

您需要監控的指標數量在現代應用程式中不斷增長。如果您有一種自動化的方式來跟踪您的應用程式,您就可以專注於解決客戶的挑戰。像 [Prometheus](https://prometheus.io) 或 [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html) 這樣的集群範圍監控工具可以監控您的集群和工作負載,並在出現問題之前或之後為您提供信號。

監控工具允許您創建運營團隊可以訂閱的警報。考慮為可能在加劇時導致中斷或影響應用程式性能的事件激活警報的規則。

如果您不確定應該監控哪些指標,您可以從這些方法中獲取靈感:

- [RED 方法](https://www.weave.works/blog/a-practical-guide-from-instrumenting-code-to-specifying-alerts-with-the-red-method)。代表請求、錯誤和持續時間。
- [USE 方法](http://www.brendangregg.com/usemethod.html)。代表利用率、飽和度和錯誤。

Sysdig 的文章 [Best practices for alerting on Kubernetes](https://sysdig.com/blog/alerting-kubernetes/) 包括了可能影響應用程式可用性的組件的全面列表。

### 使用 Prometheus 客戶端庫公開應用程式指標

除了監控應用程式狀態和聚合標準指標外,您還可以使用 [Prometheus 客戶端庫](https://prometheus.io/docs/instrumenting/clientlibs/)公開應用程式特定的自定義指標,以提高應用程式的可觀察性。

### 使用集中式日誌工具收集和持久化日誌

在 EKS 中,日誌分為兩類:控制平面日誌和應用程式日誌。EKS 控制平面日誌直接從控制平面提供審計和診斷日誌到您帳戶中的 CloudWatch Logs。應用程式日誌是由集群內運行的 Pod 產生的日誌。應用程式日誌包括由運行業務邏輯應用程式的 Pod 以及 Kubernetes 系統組件(如 CoreDNS、Cluster Autoscaler、Prometheus 等)產生的日誌。

[EKS 提供五種類型的控制平面日誌](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html):

1. Kubernetes API 服務器組件日誌
2. 審計
3. 身份驗證器
4. 控制器管理器
5. 調度器

控制器管理器和調度器日誌可以幫助診斷控制平面問題,如瓶頸和錯誤。默認情況下,EKS 控制平面日誌不會發送到 CloudWatch Logs。您可以為您帳戶中的每個集群啟用控制平面日誌記錄,並選擇要捕獲的 EKS 控制平面日誌類型

收集應用程式日誌需要在集群中安裝日誌聚合工具,如 [Fluent Bit](http://fluentbit.io)、[Fluentd](https://www.fluentd.org) 或 [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html)。

Kubernetes 日誌聚合工具作為 DaemonSet 運行,從節點刮取容器日誌。然後,應用程式日誌被發送到集中式目的地進行存儲。例如,CloudWatch Container Insights 可以使用 Fluent Bit 或 Fluentd 收集日誌並將它們發送到 CloudWatch Logs 進行存儲。Fluent Bit 和 Fluentd 支持許多流行的日誌分析系統,如 Elasticsearch 和 InfluxDB,這使您能夠通過修改 Fluent bit 或 Fluentd 的日誌配置來更改日誌的存儲後端。


### 使用分佈式跟踪系統識別瓶頸

典型的現代應用程式的組件分佈在網絡上,其可靠性取決於組成應用程式的每個組件的正常運行。您可以使用分佈式跟踪解決方案來了解請求的流動方式以及系統如何通信。跟踪可以向您展示應用程式網絡中存在瓶頸的位置,並防止可能導致級聯故障的問題。

您有兩種選擇來在應用程式中實現跟踪:您可以在代碼級別使用共享庫實現分佈式跟踪,或者使用服務網格。

在代碼級別實現跟踪可能是不利的。在這種方法中,您必須修改代碼。如果您有多語言應用程式,這將進一步複雜化。您還要負責維護跨服務的另一個庫。

像 [LinkerD](http://linkerd.io)、[Istio](http://istio.io) 和 [AWS App Mesh](https://aws.amazon.com/app-mesh/) 這樣的服務網格可以用於在您的應用程式中實現分佈式跟踪,而幾乎不需要修改應用程式代碼。您可以使用服務網格來標準化指標生成、日誌記錄和跟踪。

跟踪工具如 [AWS X-Ray](https://aws.amazon.com/xray/) 和 [Jaeger](https://www.jaegertracing.io) 支持共享庫和服務網格實現。

考慮使用支持這兩種實現的跟踪工具,如 [AWS X-Ray](https://aws.amazon.com/xray/) 或 [Jaeger](https://www.jaegertracing.io),這樣如果您以後採用服務網格,就不必切換工具。
