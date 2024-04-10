# 避免 Kubernetes 應用程式和 AWS 負載平衡器發生錯誤和超時

在建立必要的 Kubernetes 資源（Service、Deployment、Ingress 等）後，您的 Pod 應該能夠透過彈性負載平衡器從客戶端接收流量。但是，當您對應用程式或 Kubernetes 環境進行更改時，可能會發現產生錯誤、超時或連線重置。這些更改可能會觸發應用程式部署或擴展動作（手動或自動）。

不幸的是，即使您的應用程式沒有記錄問題，也可能會產生這些錯誤。這是因為控制集群中資源的 Kubernetes 系統可能比控制負載平衡器目標註冊和健康狀態的 AWS 系統運行得更快。您的 Pod 也可能在應用程式準備好接收請求之前就開始接收流量。

讓我們回顧一下 Pod 成為 Ready 的過程，以及如何將流量路由到 Pod。

## Pod 就緒狀態

這張來自 [2019 年 Kubecon 演講](https://www.youtube.com/watch?v=Vw9GmSeomFg)的圖表顯示了 Pod 成為 Ready 並接收 `LoadBalancer` 服務流量的步驟：
![readiness.png](readiness.png)
*[Ready? A Deep Dive into Pod Readiness Gates for Service Health... - Minhan Xia & Ping Zou](https://www.youtube.com/watch?v=Vw9GmSeomFg)*  
當建立一個屬於 NodePort 服務成員的 Pod 時，Kubernetes 將執行以下步驟：

1. Pod 在 Kubernetes 控制平面上建立（即從 `kubectl` 命令或擴展動作）。
2. `kube-scheduler` 將 Pod 排程並分配給集群中的一個節點。
3. 被分配節點上的 kubelet 將收到更新（透過 `watch`），並將與其本地容器運行時進行通信以啟動 Pod 中指定的容器。
    1. 當容器開始運行（並且選擇性地通過 `ReadinessProbes`）時，kubelet 將通過向 `kube-apiserver` 發送更新來更新 Pod 狀態為 `Ready`。
4. Endpoint Controller 將收到更新（透過 `watch`），表示有一個新的 Pod 準備好被添加到服務的 Endpoints 列表中，並將把 Pod IP/Port 元組添加到適當的 Endpoints 陣列中。
5. `kube-proxy` 收到更新（透過 `watch`），表示有新的 IP/Port 需要添加到服務的 iptables 規則中。
    1. 工作節點上的本地 iptables 規則將使用新的目標 Pod 更新 NodePort 服務。

!!! note
    當使用 Ingress 資源和 Ingress Controller（如 AWS Load Balancer Controller）時，步驟 5 將由相關控制器處理，而不是由 `kube-proxy` 處理。控制器將採取必要的配置步驟（例如向負載平衡器註冊/註銷目標），以允許流量按預期流動。

[當 Pod 終止](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination)或變為非就緒狀態時，將發生類似的過程。API 伺服器將從控制器、kubelet 或 kubectl 客戶端收到終止 Pod 的更新。步驟 3-5 將從那裡繼續，但會從 Endpoints 列表和 iptables 規則中移除 Pod IP/元組，而不是插入。

### 對部署的影響

下圖顯示了應用程式部署觸發替換 Pod 時採取的步驟：
![deployments.png](deployments.png)
*[Ready? A Deep Dive into Pod Readiness Gates for Service Health... - Minhan Xia & Ping Zou](https://www.youtube.com/watch?v=Vw9GmSeomFg)*  
值得注意的是，第二個 Pod 將不會在第一個 Pod 達到「Ready」狀態之前部署。上一節中的步驟 4 和 5 也將與上述部署動作並行進行。

這意味著傳播新 Pod 狀態的動作可能在部署控制器移動到下一個 Pod 時仍在進行中。由於此過程還會終止較舊版本的 Pod，因此可能會導致 Pod 已達到就緒狀態，但這些更改仍在傳播中，而較舊版本的 Pod 已被終止。

當使用來自 AWS 等雲端提供商的負載平衡器時，這個問題會加劇，因為上述 Kubernetes 系統在預設情況下不會考慮負載平衡器的註冊時間或健康檢查。**這意味著部署更新可能完全循環通過 Pod，但負載平衡器尚未完成對新 Pod 的健康檢查或註冊，這可能會導致中斷。**

當 Pod 被終止時也會發生類似的問題。根據負載平衡器的配置，Pod 可能需要一兩分鐘才能註銷並停止接收新請求。**Kubernetes 不會為此註銷而延遲滾動部署，這可能會導致負載平衡器仍將流量發送到已被終止的目標 Pod 的 IP/Port。**

為了避免這些問題，我們可以添加配置以確保 Kubernetes 系統的操作更符合 AWS 負載平衡器的行為。

## 建議

### 使用 IP 目標類型負載平衡器

當建立 `LoadBalancer` 類型服務時，流量將從負載平衡器通過 **Instance 目標類型** 註冊發送到集群中的任何節點。然後，每個節點將把流量從 `NodePort` 重新導向到服務的 Endpoints 陣列中的 Pod/IP 元組，該目標可能在另一個工作節點上運行。

!!! note
    請記住，該陣列應該只包含「Ready」Pod

![nodeport.png](nodeport.png)

這增加了請求的額外跳躍，並增加了負載平衡器配置的複雜性。例如，如果上圖中的負載平衡器配置了會話親和性，則該親和性只能在負載平衡器和後端節點之間保持（取決於親和性配置）。

由於負載平衡器不直接與後端 Pod 通信，因此控制與 Kubernetes 系統的流量流和時間變得更加困難。

當使用 [AWS Load Balancer Controller](https://github.com/kubernetes-sigs/aws-load-balancer-controller) 時，可以使用 **IP 目標類型** 直接將 Pod IP/Port 元組註冊到負載平衡器：
![ip.png](ip.png)  
這簡化了從負載平衡器到目標 Pod 的流量路徑。這意味著當註冊新目標時，我們可以確保該目標是「Ready」Pod IP 和端口，負載平衡器的健康檢查將直接命中 Pod，並且在審查 VPC 流量日誌或監控工具時，負載平衡器與 Pod 之間的流量將易於追蹤。

使用 IP 註冊還允許我們直接針對後端 Pod 控制流量的時間和配置，而不是嘗試通過 `NodePort` 規則來管理連接。

### 利用 Pod 就緒閘道

[Pod 就緒閘道](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-readiness-gate)是在 Pod 被允許達到「Ready」狀態之前必須滿足的額外要求。

>[[...] AWS Load Balancer Controller 可以在構成您的 Ingress 或服務後端的 Pod 上設置就緒條件。只有當 ALB/NLB 目標組中的相應目標顯示「Healthy」健康狀態時，Pod 上的條件狀態才會設置為 `True`。這可以防止部署的滾動更新在新建的 Pod 在 ALB/NLB 目標組中「Healthy」並準備好接收流量之前終止舊的 Pod。](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/pod_readiness_gate/)

就緒閘道確保 Kubernetes 在部署期間創建新副本時不會移動「太快」，並避免了 Kubernetes 已完成部署但新 Pod 尚未完成註冊的情況。

要啟用這些功能，您需要：

1. 部署最新版本的 [AWS Load Balancer Controller](https://github.com/kubernetes-sigs/aws-load-balancer-controller)（**[*如果升級舊版本，請參考文檔*](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/upgrade/migrate_v1_v2/)*）
2. [為目標 Pod 所在的命名空間添加標籤](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/pod_readiness_gate/) `elbv2.k8s.aws/pod-readiness-gate-inject: enabled`，以自動注入 Pod 就緒閘道。
3. 要確保命名空間中的所有 Pod 都獲得就緒閘道配置，您需要在創建 Pod 之前創建 Ingress 或服務並為命名空間添加標籤。

### 確保 Pod 在終止之前從負載平衡器註銷

當 Pod 終止時，Pod 就緒狀態部分的步驟 4 和 5 將與容器進程接收終止信號的時間相同。這意味著如果您的容器能夠快速關閉，它可能會比負載平衡器註銷目標更快。為了避免這種情況，請調整 Pod 規格：

1. 添加 `preStop` 生命週期掛鉤，允許應用程式註銷並優雅地關閉連接。此掛鉤在容器由於 API 請求或管理事件（如活性/啟動探測失敗、搶占、資源競爭等）而終止之前立即被調用，並且允許完成，前提是寬限期足夠長以容納執行。

```
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 180"] 
```

上面這樣一個簡單的 sleep 命令可以用來在 Pod 被標記為 `Terminating`（並開始負載平衡器註銷）和向容器進程發送終止信號之間引入短暫延遲。如果需要，此掛鉤還可用於更高級的應用程式終止/關閉程序。

2. 延長 `terminationGracePeriodSeconds` 以容納整個 `prestop` 執行時間，以及您的應用程式優雅響應終止信號所需的時間。在下面的示例中，寬限期延長到 200 秒，這允許完全執行 `sleep 180` 命令，然後再額外留出 20 秒以確保我的應用程式可以正常關閉。

```
    spec:
      terminationGracePeriodSeconds: 200
      containers:
      - name: webapp
        image: webapp-st:v1.3
        [...]
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 180"] 
```

### 確保 Pod 有就緒探測

在 Kubernetes 中創建 Pod 時，預設的就緒狀態是「Ready」，但大多數應用程式需要一兩秒鐘的時間來實例化並準備好接收請求。[您可以在 Pod 規格中定義 `readinessProbe`](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)，其中包含一個 exec 命令或網絡請求，用於確定應用程式是否已完成啟動並準備好接收流量。

定義了 `readinessProbe` 的 Pod 以「NotReady」狀態開始，並且只有在 `readinessProbe` 成功時才會變為「Ready」。這確保應用程式在完成啟動之前不會被投入「服務」。

建議使用活性探測以允許在應用程式進入損壞狀態（例如死鎖）時重新啟動應用程式，但對於有狀態的應用程式應該小心使用，因為活性探測失敗將觸發應用程式重新啟動。[啟動探測](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#define-startup-probes)也可用於啟動緩慢的應用程式。

下面的探測使用 HTTP 探測針對端口 80 檢查 Web 應用程式何時準備就緒（活性探測也使用相同的探測配置）：

```
        [...]
        ports:
        - containerPort: 80
        livenessProbe:
          httpGet:
            path: /
            port: 80
          failureThreshold: 1
          periodSeconds: 10
          initialDelaySeconds: 5
        readinessProbe:
          httpGet:
            path: /
            port: 80
          periodSeconds: 5
        [...]
```

### 配置 Pod 干擾預算

[Pod 干擾預算 (PDB)](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/#pod-disruption-budgets) 限制了在[自願干擾](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/#voluntary-and-involuntary-disruptions)期間同時停止的複製應用程式 Pod 的數量。例如，基於法定人數的應用程式可能希望確保運行的副本數量永遠不會低於法定人數所需的數量。Web 前端可能希望確保服務負載的副本數量永遠不會低於總數的某個百分比。

PDB 將保護應用程式免受節點耗盡或應用程式部署等影響。PDB 確保在執行這些操作時至少有一定數量或百分比的 Pod 保持可用。

!!! attention
    PDB 不會保護應用程式免受主機操作系統故障或網絡連接中斷等非自願干擾的影響。

下面的示例確保始終至少有一個帶有標籤 `app: echoserver` 的 Pod 可用。[您可以為您的應用程式配置正確的副本數量或使用百分比](https://kubernetes.io/docs/tasks/run-application/configure-pdb/#think-about-how-your-application-reacts-to-disruptions)：

```
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: echoserver-pdb
  namespace: echoserver
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: echoserver
```

### 優雅處理終止信號

當 Pod 被終止時，運行在容器內的應用程式將收到兩個[信號](https://www.gnu.org/software/libc/manual/html_node/Standard-Signals.html)。第一個是 [`SIGTERM` 信號](https://www.gnu.org/software/libc/manual/html_node/Termination-Signals.html)，這是一個「禮貌」請求進程停止執行。此信號可以被阻塞或應用程式可以簡單地忽略此信號，因此在 `terminationGracePeriodSeconds` 過後，應用程式將收到 [`SIGKILL` 信號](https://www.gnu.org/software/libc/manual/html_node/Termination-Signals.html)。`SIGKILL` 用於強制停止進程，它不能被[阻塞、處理或忽略](https://man7.org/linux/man-pages/man7/signal.7.html)，因此總是致命的。

這些信號由容器運行時使用來觸發您的應用程式關閉。`SIGTERM` 信號也將在 `preStop` 掛鉤執行後發送。使用上述配置，`preStop` 掛鉤將確保 Pod 已從負載平衡器註銷，因此應用程式可以在收到 `SIGTERM` 信號時優雅地關閉任何剩餘的開放連接。

!!! note
    [在容器環境中處理信號可能會很複雜，尤其是在使用「包裝器腳本」作為應用程式入口點時](https://petermalmgren.com/signal-handling-docker/)，因為腳本將是 PID 1，可能不會將信號轉發給您的應用程式。


### 注意註銷延遲

彈性負載平衡器停止向正在註銷的目標發送請求。預設情況下，彈性負載平衡器在完成註銷過程之前等待 300 秒，這可以幫助完成對目標的現有請求。要更改彈性負載平衡器等待的時間，請更新註銷延遲值。
正在註銷的目標的初始狀態是 `draining`。註銷延遲過後，註銷過程完成，目標的狀態為 `unused`。如果目標是自動擴展組的一部分，它可以被終止和替換。

如果正在註銷的目標沒有現有請求和活動連接，彈性負載平衡器將立即完成註銷過程，而不等待註銷延遲過期。

!!! attention
    即使目標註銷已完成，目標的狀態仍將顯示為 `draining`，直到註銷延遲超時過期。超時過期後，目標將轉換為 `unused` 狀態。

[如果正在註銷的目標在註銷延遲過期之前終止連接，客戶端將收到 500 級錯誤響應](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html#deregistration-delay)。

可以使用 Ingress 資源上的 [`alb.ingress.kubernetes.io/target-group-attributes` 註釋](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/guide/ingress/annotations/#target-group-attributes)進行配置。示例：

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: echoserver-ip
  namespace: echoserver
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/load-balancer-name: echoserver-ip
    alb.ingress.kubernetes.io/target-group-attributes: deregistration_delay.timeout_seconds=30
spec:
  ingressClassName: alb
  rules:
    - host: echoserver.example.com
      http:
        paths:
          - path: /
            pathType: Exact
            backend:
              service:
                name: echoserver-service
                port:
                  number: 8080
```
