# 效能效率支柱

效能效率支柱專注於有效利用計算資源來滿足需求,以及在需求變化和技術演進時如何維持效率。本節提供了在 AWS 上架構效能效率的深入最佳實踐指南。

## 定義

為確保有效利用 EKS 容器服務,您應收集有關架構各個方面的數據,從高層次設計到選擇 EKS 資源類型。透過定期檢視您的選擇,您可確保利用不斷演進的 Amazon EKS 和容器服務。監控將確保您知悉任何偏離預期效能的情況,以便您可採取行動。

EKS 容器的效能效率由三個領域組成:

- 優化您的容器

- 資源管理

- 可擴展性管理

## 最佳實踐

### 優化您的容器

您可以在 Docker 容器中運行大多數應用程式而不會遇到太多麻煩。但是,為了確保它在生產環境中有效運行,您需要做一些事情,包括簡化構建過程。以下最佳實踐將有助於您實現這一目標。

#### 建議

- **使您的容器映像無狀態:** 使用 Docker 映像創建的容器應該是短暫和不可變的。換句話說,容器應該是可處置和獨立的,即可以構建和放置新的容器而無需進行任何配置更改。設計無狀態容器。如果您想使用持久數據,請使用 [volumes](https://docs.docker.com/engine/admin/volumes/volumes/)。如果您想存儲服務使用的密鑰或敏感應用程式數據,您可以使用 AWS [Systems Manager](https://aws.amazon.com/systems-manager/)[Parameter Store](https://aws.amazon.com/ec2/systems-manager/parameter-store/) 或第三方產品或開源解決方案(如 [HashiCorp Valut](https://www.vaultproject.io/) 和 [Consul](https://www.consul.io/))進行運行時配置。
- [**最小基礎映像**](https://docs.docker.com/develop/develop-images/baseimages/): 從小型基礎映像開始。Dockerfile 中的每個其他指令都是在此映像之上構建的。基礎映像越小,生成的映像就越小,下載速度也就越快。例如,映像 [alpine:3.7](https://hub.docker.com/r/library/alpine/tags/) 比 [centos:7](https://hub.docker.com/r/library/centos/tags/) 小 71 MB。您甚至可以使用 [scratch](https://hub.docker.com/r/library/scratch/) 基礎映像,這是一個空映像,您可以在其上構建自己的運行時環境。
- **避免不必要的包:** 在構建容器映像時,只包括您的應用程式所需的依賴項,避免安裝不必要的包。例如,如果您的應用程式不需要 SSH 服務器,請不要包括它。這將減少複雜性、依賴項、文件大小和構建時間。要排除與構建無關的文件,請使用 .dockerignore 文件。
- [**使用多階段構建**](https://docs.docker.com/v17.09/engine/userguide/eng-image/multistage-build/#use-multi-stage-builds):多階段構建允許您在第一個 "構建" 容器中構建應用程式,並在另一個容器中使用結果,同時使用相同的 Dockerfile。稍作解釋,在多階段構建中,您在 Dockerfile 中使用多個 FROM 語句。每個 FROM 指令可以使用不同的基礎,每個指令都開始構建的新階段。您可以選擇性地從一個階段複製構件到另一個階段,同時捨棄最終映像中不需要的所有內容。這種方法大大減小了最終映像的大小,而無需努力減少中間層和文件的數量。
- **最小化層數:** Dockerfile 中的每個指令都會為 Docker 映像添加一個額外的層。應將指令和層數保持在最小,因為這會影響構建效能和時間。例如,第一條指令將創建多個層,而使用 && (鏈接)的第二條指令則減少了層數,這將有助於提供更好的效能。這是減少 Dockerfile 中將創建的層數的最佳方式。
- 
    ```
            RUN apt-get -y update
            RUN apt-get install -y python
            RUN apt-get -y update && apt-get install -y python
    ```
            
- **正確標記您的映像:** 在構建映像時,請始終使用有用和有意義的標記對它們進行標記。這是組織和記錄描述映像的元數據的好方法,例如,包括來自 CI 服務器 (如 CodeBuild 或 Jenkins) 的唯一計數器(如構建 ID),有助於識別正確的映像。如果您在 Docker 命令中沒有提供標記,則默認使用 latest 標記。我們建議不要使用自動創建的 latest 標記,因為使用此標記,您將自動運行未來的主要版本,其中可能包括對您的應用程式的重大更改。最佳實踐是避免使用 latest 標記,而是使用由您的 CI 服務器創建的唯一摘要。
- **使用 [構建緩存](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/) 提高構建速度:** 緩存允許您利用現有的緩存映像,而不是從頭開始構建每個映像。例如,您應該盡可能晚地將應用程式的源代碼添加到 Dockerfile 中,以便基礎映像和應用程式的依賴項被緩存,並且不會在每次構建時重建。要重用已緩存的映像,在 Amazon EKS 中,kubelet 默認將嘗試從指定的註冊表中拉取每個映像。但是,如果容器的 imagePullPolicy 屬性設置為 IfNotPresent 或 Never,則將使用本地映像(優先或專用)。
- **映像安全性:** 使用公共映像可能是開始使用容器和將其部署到 Kubernetes 的好方法。但是,在生產環境中使用它們可能會帶來一些挑戰,尤其是在安全性方面。請確保遵循打包和分發容器/應用程式的最佳實踐。例如,不要在構建容器時內置密碼,您可能還需要控制它們的內容。建議使用私有存儲庫(如 [Amazon ECR](https://aws.amazon.com/ecr/))並利用內置的 [映像掃描](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)功能來識別容器映像中的軟體漏洞。  

- **正確調整容器大小:** 在開發和運行容器應用程式時,有一些關鍵領域需要考慮。您調整容器大小和管理應用程式部署的方式可能會對您提供的服務的最終用戶體驗產生負面影響。為了幫助您取得成功,以下最佳實踐將有助於您正確調整容器大小。在確定應用程式所需的資源數量後,您應該在 Kubernetes 中設置請求和限制,以確保您的應用程式正常運行。 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*(a) 對應用程式進行測試*: 收集重要統計數據和其他效能數據。根據這些數據,您可以計算出容器的最佳配置,即內存和 CPU。重要統計數據包括: __*CPU、延遲、I/O、內存使用量、網絡*__。通過單獨進行負載測試(如有必要),確定預期、平均和峰值容器內存和 CPU 使用量。還要考慮容器中可能並行運行的所有進程。 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;建議使用 [CloudWatch Container insights](https://aws.amazon.com/blogs/mt/introducing-container-insights-for-amazon-ecs/) 或合作夥伴產品,這將為您提供正確調整容器和 Worker 節點的信息。


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*(b)獨立測試服務:* 由於許多應用程式在真正的微服務架構中相互依賴,您需要以高度獨立的方式對它們進行測試,這意味著服務能夠正常獨立運行,也能作為一個協調的系統正常運行。

### 資源管理 

在採用 Kubernetes 時,最常見的問題之一是 "我應該將什麼放在 Pod 中?"。例如,一個三層 LAMP 應用程式容器。我們應該將此應用程式保留在同一個 Pod 中嗎?這確實有效地作為單個 Pod 工作,但這是 Pod 創建的反模式示例。有兩個原因

***(a)*** 如果您將兩個容器都放在同一個 Pod 中,您將被迫使用相同的擴展策略,這對於生產環境來說是不理想的,您也無法根據使用情況有效管理或限制資源。*例如:* 您可能只需要擴展前端而不是前端和後端 (MySQL) 作為一個單元,如果您想增加僅專用於後端的資源,您也無法這樣做。

***(b)*** 如果您有兩個單獨的 Pod,一個用於前端,另一個用於後端。擴展將非常容易,並且您將獲得更好的可靠性。

上述情況可能不適用於所有用例。在上面的示例中,前端和後端可能會落在不同的機器上,它們將通過網絡相互通信,因此您需要問自己這個問題:"如果它們被放置並在不同的機器上運行,我的應用程式是否能正常工作?"如果答案是"否",可能是因為應用程式設計或其他技術原因,那麼在單個 Pod 中分組容器就有意義。如果答案是"是",那麼多個 Pod 就是正確的方法。

#### 建議

+ **每個容器打包一個應用程式:**
容器最適合在其中運行單個應用程式。該應用程式應該有一個單一的父進程。例如,不要在同一個容器中運行 PHP 和 MySQL:它更難調試,而且您無法單獨水平擴展 PHP 容器。這種分離允許您更好地將應用程式的生命週期與容器的生命週期關聯起來。您的容器應該是無狀態和不可變的。無狀態意味著任何狀態(任何類型的持久數據)都存儲在容器外部,例如,您可以使用不同類型的外部存儲(如持久磁盤、Amazon EBS 和 Amazon EFS(如有需要))或托管數據庫(如 Amazon RDS)。不可變意味著容器在其生命週期內不會被修改:沒有更新、修補或配置更改。要更新應用程式代碼或應用修補程式,您需要構建新的映像並部署它。

+ **為 Kubernetes 對象使用標籤:**
[標籤](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/#labels)允許批量查詢和操作 Kubernetes 對象。它們還可用於識別和組織 Kubernetes 對象組。因此,定義標籤應該是任何 Kubernetes 最佳實踐列表的首要任務。

+ **設置資源請求限制:**
設置請求限制是控制容器可以消耗的系統資源(如 CPU 和內存)數量的機制。這些設置是容器初始啟動時保證獲得的資源。如果容器請求資源,容器編排器(如 Kubernetes)將只在可以提供該資源的節點上調度它。另一方面,限制確保容器永遠不會超過某個值。容器只允許達到限制,然後就會受到限制。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 在下面的 Pod 清單示例中,我們添加了 1.0 CPU 和 256 MB 內存的限制

```
        apiVersion: v1
        kind: Pod
        metadata:
          name: nginx-pod-webserver
          labels:
            name: nginx-pod
        spec:
          containers:
          - name: nginx
            image: nginx:latest
            resources:
              limits:
                memory: "256Mi"
                cpu: "1000m"
              requests:
                memory: "128Mi"
                cpu: "500m"
            ports:
            - containerPort: 80

         
```


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;在 Pod 定義中定義這些請求和限制是最佳實踐。如果您不包括這些值,調度器將無法了解所需的資源。沒有這些信息,調度器可能會將 Pod 調度到沒有足夠資源提供可接受應用程式效能的節點上。

+ **限制並發中斷的數量:**
使用 _PodDisruptionBudget_,此設置允許您在自願驅逐事件期間設置可用和不可用 Pod 的最小和最大數量的策略。驅逐的一個示例是在對節點進行維護或排空節點時。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; _示例:_ 一個 Web 前端可能希望在任何給定時間都有 8 個 Pod 可用。在這種情況下,驅逐可以驅逐任意多個 Pod,只要有八個可用即可。
```
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: frontend-demo
spec:
  minAvailable: 8
  selector:
    matchLabels:
      app: frontend
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**注意:** 您也可以通過使用 maxAvailable 或 maxUnavailable 參數以百分比的形式指定 Pod 中斷預算。

+ **使用命名空間:**
命名空間允許多個團隊共享物理集群。命名空間允許將創建的資源分區到一個邏輯命名組中。這允許您每個命名空間設置資源配額、每個命名空間的基於角色的訪問控制 (RBAC) 以及每個命名空間的網絡策略。它為您提供了軟多租戶功能。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;例如,如果您在單個 Amazon EKS 集群上運行三個應用程式,由三個不同的團隊訪問,需要多個資源約束和不同級別的 QoS,您可以為每個團隊創建一個命名空間,並為每個團隊設置可使用的資源配額,如 CPU 和內存。

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您還可以通過啟用 [LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/) 准入控制器在 Kubernetes 命名空間級別指定默認限制。這些默認限制將限制給定 Pod 可以使用的 CPU 或內存量,除非 Pod 的配置明確覆蓋了默認值。

+ **管理資源配額:** 
每個命名空間都可以分配資源配額。指定配額允許限制在命名空間中的所有資源可以消耗的集群資源量。資源配額可以由 [ResourceQuota](https://kubernetes.io/docs/concepts/policy/resource-quotas/) 對象定義。命名空間中 ResourceQuota 對象的存在確保資源配額得到執行。

+ **為 Pod 配置健康檢查:**
健康檢查是讓系統知道應用程式實例是否正常工作的簡單方法。如果應用程式實例不正常,其他服務就不應該訪問它或向它發送請求。相反,應該將請求發送到正常工作的另一個應用程式實例。系統還應該將您的應用程式恢復到健康狀態。默認情況下,所有正在運行的 Pod 都將重新啟動策略設置為 always,這意味著節點上運行的 kubelet 將在容器遇到錯誤時自動重新啟動 Pod。健康檢查通過 [容器探針](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)的概念擴展了 kubelet 的這一功能。

  Kubernetes 提供兩種 [健康檢查](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/):就緒和存活探針。例如,考慮一下您的應用程式之一,通常會長時間運行,但會轉換為非運行狀態,只能通過重新啟動來恢復。您可以使用存活探針來檢測和補救此類情況。使用健康檢查可以為您的應用程式提供更好的可靠性和更高的正常運行時間。


+ **高級調度技術:**
通常,調度器確保只將 Pod 放置在有足夠可用資源的節點上,並且在節點之間,它們會嘗試平衡資源利用率,例如部署、副本等。但有時您希望控制 Pod 的調度方式。例如,也許您希望確保某些 Pod 只在具有專用硬體(如需要 GPU 機器進行 ML 工作負載)的節點上調度。或者您希望將經常通信的服務放在一起。

  Kubernetes 提供了許多[高級調度功能](https://kubernetes.io/blog/2017/03/advanced-scheduling-in-kubernetes/)和多個過濾器/約束來將 Pod 調度到正確的節點。例如,在使用 Amazon EKS 時,您可以使用[污點和容忍度](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#taints-and-toleations-beta-feature)來限制可以在特定節點上運行的工作負載。您還可以使用 [節點選擇器](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#nodeselector)和[親和性和反親和性](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity)構造來控制 Pod 調度,甚至可以為此目的構建自己的自定義調度器。

#### 可擴展性管理 
  容器是無狀態的。它們出生時,當它們死亡時,它們不會復活。您可以在 Amazon EKS 上利用許多技術,不僅可以擴展容器化應用程式,還可以擴展 Kubernetes worker 節點。
  
#### 建議

  + 在 Amazon EKS 上,您可以配置 [Horizontal pod autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/),它根據觀察到的 CPU 利用率 (或使用[自定義指標](https://git.k8s.io/community/contributors/design-proposals/instrumentation/custom-metrics-api.md)基於應用程式提供的指標)自動擴展複製控制器、部署或副本集中的 Pod 數量。

  + 您可以使用 [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler),它會自動調整 Pod 的 CPU 和內存預留,有助於為您的應用程式"正確調整大小"。這種調整可以提高集群資源利用率,並為其他 Pod 釋放 CPU 和內存。這在您的生產數據庫 "MongoDB" 與無狀態應用程式前端的擴展方式不同的情況下很有用。在這種情況下,您可以使用 VPA 來擴展 MongoDB Pod。

  + 要啟用 VPA,您需要使用 Kubernetes 指標服務器,它是集群中資源使用數據的聚合器。它未在 Amazon EKS 集群中默認部署。在[配置 VPA](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html) 之前,您需要配置它,或者您也可以使用 Prometheus 為 Vertical Pod Autoscaler 提供指標。

  + 雖然 HPA 和 VPA 可擴展部署和 Pod,但 [Cluster Autoscaler](https://github.com/kubernetes/autoscaler) 將擴展和縮減 worker 節點池的大小。它根據當前利用率調整 Kubernetes 集群的大小。當由於資源不足而無法在任何當前節點上調度 Pod 或添加新節點會增加集群資源的整體可用性時,Cluster Autoscaler 會增加集群的大小。請按照此 [逐步](https://eksworkshop.com/scaling/deploy_ca/) 指南設置 Cluster Autoscaler。如果您在 AWS Fargate 上使用 Amazon EKS,AWS 將為您管理控制平面。 

     請查看可靠性支柱以獲取詳細信息。
     
#### 監控 
#### 部署最佳實踐 
#### 權衡
