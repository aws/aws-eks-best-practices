# 工作負載

工作負載會影響您的叢集可以擴展的大小。大量使用 Kubernetes API 的工作負載將限制您可以在單一叢集中擁有的工作負載總量,但您可以更改一些預設值來幫助減少負載。

Kubernetes 叢集中的工作負載可以存取與 Kubernetes API 整合的功能 (例如 Secrets 和 ServiceAccounts),但這些功能並非總是必需的,如果不使用應該將其停用。限制工作負載對 Kubernetes 控制平面的存取和依賴性,可增加您在叢集中可以運行的工作負載數量,並透過移除對工作負載的不必要存取權限並實施最小權限實踐來提高您叢集的安全性。請閱讀 [安全最佳實踐](https://aws.github.io/aws-eks-best-practices/security/docs/) 以取得更多資訊。

## 使用 IPv6 進行 Pod 網路

您無法將 VPC 從 IPv4 過渡到 IPv6,因此在佈建叢集之前啟用 IPv6 很重要。如果您在 VPC 中啟用 IPv6,並不意味著您必須使用它,如果您的 Pod 和服務使用 IPv6,您仍然可以將流量路由到和從 IPv4 位址。請參閱 [EKS 網路最佳實踐](https://aws.github.io/aws-eks-best-practices/networking/index/) 以取得更多資訊。

在您的叢集中使用 [IPv6](https://docs.aws.amazon.com/eks/latest/userguide/cni-ipv6.html) 可避免一些最常見的叢集和工作負載擴展限制。IPv6 避免了 IP 位址耗盡的情況,在這種情況下,無法建立 Pod 和節點,因為沒有可用的 IP 位址。它還可以透過減少每個節點的 ENI 連接數量來提高每個節點的效能。您也可以透過在 VPC CNI 中使用 [IPv4 前綴模式](https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/) 來實現類似的節點效能,但您仍需確保 VPC 中有足夠的 IP 位址可用。

## 限制每個命名空間的服務數量

每個 [命名空間的最大服務數量為 5,000,叢集中的最大服務數量為 10,000](https://github.com/kubernetes/community/blob/master/sig-scalability/configs-and-limits/thresholds.md)。為了幫助組織工作負載和服務、提高效能,並避免命名空間範圍內資源的級聯影響,我們建議將每個命名空間的服務數量限制為 500。

隨著叢集中服務總數的增加,kube-proxy 在每個節點上建立的 IP 表規則數量也會增加。生成數千條 IP 表規則並透過這些規則路由封包會對節點產生效能影響並增加網路延遲。

建立包含單一應用程式環境的 Kubernetes 命名空間,只要每個命名空間的服務數量低於 500。這樣可以讓服務探索保持在足夠小的範圍內,以避免服務探索限制,並且還可以幫助您避免服務命名衝突。應用程式環境 (例如開發、測試、生產) 應使用單獨的 EKS 叢集,而不是命名空間。

## 了解 Elastic Load Balancer 配額

建立您的服務時,請考慮將使用哪種類型的負載平衡 (例如 Network Load Balancer (NLB) 或 Application Load Balancer (ALB))。每種負載平衡器類型都提供不同的功能,並且有 [不同的配額](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html)。某些預設配額可以調整,但有些配額上限無法更改。若要查看您的帳戶配額和使用量,請在 AWS 主控台中檢視 [服務配額儀表板](http://console.aws.amazon.com/servicequotas)。

例如,預設 ALB 目標數量為 1000。如果您的服務有超過 1000 個端點,您將需要增加配額或將服務分散到多個 ALB,或使用 Kubernetes Ingress。預設 NLB 目標數量為 3000,但每個可用區域限制為 500 個目標。如果您的叢集為 NLB 服務運行超過 500 個 Pod,您將需要使用多個可用區域或要求增加配額限制。

使用負載平衡器與服務相結合的替代方案是使用 [Ingress 控制器](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)。AWS Load Balancer 控制器可以為 Ingress 資源建立 ALB,但您可以考慮在您的叢集中運行專用控制器。叢集內的 Ingress 控制器允許您從單一負載平衡器公開多個 Kubernetes 服務,方法是在您的叢集內運行反向代理。控制器具有不同的功能,例如支援 [Gateway API](https://gateway-api.sigs.k8s.io/),這可能會根據您的工作負載數量和大小帶來好處。

## 使用 Route 53、Global Accelerator 或 CloudFront

要將使用多個負載平衡器的服務作為單一端點公開,您需要使用 [Amazon CloudFront](https://aws.amazon.com/cloudfront/)、[AWS Global Accelerator](https://aws.amazon.com/global-accelerator/) 或 [Amazon Route 53](https://aws.amazon.com/route53/) 將所有負載平衡器公開為單一客戶端端點。每個選項都有不同的好處,可根據您的需求單獨或一起使用。

Route 53 可以在通用名稱下公開多個負載平衡器,並根據分配的權重將流量發送到每個負載平衡器。您可以在 [文件](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-values-weighted.html#rrsets-values-weighted-weight) 中閱讀有關 DNS 權重的更多資訊,並可以在 [AWS Load Balancer Controller 文件](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/guide/integrations/external_dns/#usage) 中閱讀如何與 [Kubernetes external DNS 控制器](https://github.com/kubernetes-sigs/external-dns)實作它們。

Global Accelerator 可以根據請求 IP 位址將工作負載路由到最近的區域。對於部署到多個區域的工作負載,這可能很有用,但它無法改善對單一區域中單一叢集的路由。將 Route 53 與 Global Accelerator 結合使用可帶來額外的好處,例如健康檢查和自動故障轉移,如果某個可用區域不可用。您可以在 [這篇部落格文章](https://aws.amazon.com/blogs/containers/operating-a-multi-regional-stateless-application-using-amazon-eks/) 中看到使用 Global Accelerator 與 Route 53 的範例。

CloudFront 可與 Route 53 和 Global Accelerator 一起使用,也可單獨使用來路由流量到多個目的地。CloudFront 會快取從來源服務器提供的資產,這可能會減少頻寬需求,具體取決於您正在提供的內容。

## 使用 EndpointSlices 而非 Endpoints

在探索與服務標籤相符的 Pod 時,您應該使用 [EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/) 而非 Endpoints。Endpoints 是一種在小規模上公開服務的簡單方式,但大型服務會自動擴展或更新,這會導致大量 Kubernetes 控制平面流量。EndpointSlices 具有自動分組功能,可啟用諸如拓撲感知提示等功能。

並非所有控制器都預設使用 EndpointSlices。您應該驗證您的控制器設定並在需要時啟用它。對於 [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/configurations/#controller-command-line-flags),您應該啟用 `--enable-endpoint-slices` 選用旗標以使用 EndpointSlices。

## 如果可能的話,使用不可變和外部 Secrets

kubelet 會為該節點上 Pod 中使用的 Volume 的 Secrets 保留目前金鑰和值的快取。kubelet 會對 Secrets 設置監視以偵測變更。隨著叢集擴展,不斷增加的監視可能會對 API 伺服器效能產生負面影響。

有兩種策略可以減少對 Secrets 的監視數量:

* 對於不需要存取 Kubernetes 資源的應用程式,您可以透過設置 automountServiceAccountToken: false 來停用自動掛載服務帳戶 Secrets
* 如果您應用程式的 Secrets 是靜態的且將來不會被修改,請將 [Secret 標記為不可變](https://kubernetes.io/docs/concepts/configuration/secret/#secret-immutable)。kubelet 不會對不可變的 Secrets 維護 API 監視。

要停用自動將服務帳戶掛載到 Pod,您可以在工作負載中使用以下設定。如果特定工作負載需要服務帳戶,您可以覆寫這些設定。

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app
automountServiceAccountToken: true
```

在叢集中的 Secrets 數量超過 10,000 的限制之前,請監控該數量。您可以使用以下命令查看叢集中的 Secrets 總數。您應該透過您的叢集監控工具監控此限制。

```
kubectl get secrets -A | wc -l
```

您應該設置監控,在達到此限制之前向叢集管理員發出警報。請考慮使用外部 Secrets 管理選項,例如 [AWS Key Management Service (AWS KMS)](https://aws.amazon.com/kms/) 或 [Hashicorp Vault](https://www.vaultproject.io/) 搭配 [Secrets Store CSI 驅動程式](https://secrets-store-csi-driver.sigs.k8s.io/)。

## 限制部署歷史記錄

由於叢集中仍在追蹤舊物件,因此在建立、更新或刪除 Pod 時可能會變慢。您可以減少 [部署](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#clean-up-policy) 的 `revisionHistoryLimit`,以清理舊的 ReplicaSet,從而降低 Kubernetes Controller Manager 追蹤的物件總量。部署的預設歷史記錄限制為 10。

如果您的叢集透過 CronJob 或其他機制建立大量 Job 物件,您應該使用 [`ttlSecondsAfterFinished` 設定](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/) 來自動從叢集中清理舊的 Pod。這將在指定的時間後從作業歷史記錄中移除已成功執行的作業。

## 預設停用 enableServiceLinks

當 Pod 在節點上運行時,kubelet 會為每個活動服務新增一組環境變數。Linux 進程對其環境有最大大小限制,如果您的命名空間中有太多服務,可能會達到此限制。每個命名空間的服務數量不應超過 5,000。在此之後,服務環境變數的數量會超過 Shell 限制,導致 Pod 在啟動時當機。

Pod 不應使用服務環境變數進行服務探索還有其他原因。環境變數名稱衝突、洩漏服務名稱和總環境大小就是其中幾個原因。您應該使用 CoreDNS 來探索服務端點。

## 限制每個資源的動態 Admission Webhook 數量

[動態 Admission Webhook](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) 包括 Admission Webhook 和 Mutating Webhook。它們是不屬於 Kubernetes 控制平面的 API 端點,在將資源發送到 Kubernetes API 時會依序呼叫。每個 Webhook 的預設超時時間為 10 秒,如果您有多個 Webhook 或任何一個超時,都可能會增加 API 請求所需的時間。

請確保您的 Webhook 高度可用 (尤其是在可用區域發生事故時),並且 [failurePolicy](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#failure-policy) 設置正確,以拒絕資源或忽略失敗。在不需要時不要呼叫 Webhook,允許 --dry-run kubectl 命令繞過 Webhook。

```
apiVersion: admission.k8s.io/v1
kind: AdmissionReview
request:
  dryRun: False
```

Mutating Webhook 可以連續修改資源。如果您有 5 個 Mutating Webhook,並部署 50 個資源,etcd 將存儲每個資源的所有版本,直到每 5 分鐘運行一次壓縮來移除已修改資源的舊版本。在這種情況下,當 etcd 移除過時的資源時,將從 etcd 中移除 200 個資源版本,並且根據資源的大小,可能會在 etcd 主機上佔用大量空間,直到每 15 分鐘進行一次碎片整理。

這種碎片整理可能會導致 etcd 暫停,從而可能對 Kubernetes API 和控制器產生其他影響。您應該避免頻繁修改大型資源或在短時間內修改數百個資源。
