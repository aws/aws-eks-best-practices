# 租戶隔離

當我們思考多租戶時,我們通常希望將用戶或應用程序與在共享基礎設施上運行的其他用戶或應用程序隔離開來。

Kubernetes 是一個 _單租戶編排器_,即控制平面的單個實例在集群中由所有租戶共享。但是,您可以使用各種 Kubernetes 對象來創建多租戶的外觀。例如,可以實現命名空間和基於角色的訪問控制 (RBAC) 來在邏輯上隔離租戶。同樣,配額和限制範圍可用於控制每個租戶可以消耗的集群資源量。儘管如此,集群是提供強大安全邊界的唯一構造。這是因為一旦攻擊者設法訪問集群中的主機,就可以檢索掛載在該主機上的 _所有_ 密鑰、ConfigMap 和卷。他們還可以冒充 Kubelet,從而允許他們操縱節點的屬性和/或在集群內橫向移動。

以下幾節將解釋如何實現租戶隔離,同時減輕使用 Kubernetes 等單租戶編排器的風險。

## 軟多租戶

通過軟多租戶,您可以使用本機 Kubernetes 構造,例如命名空間、角色和角色綁定以及網路策略,在租戶之間創建邏輯分離。例如,RBAC 可以防止租戶訪問或操縱彼此的資源。配額和限制範圍可控制每個租戶可以消耗的集群資源量,而網路策略可幫助防止部署到不同命名空間中的應用程序相互通信。

但是,這些控制都無法防止來自不同租戶的 pod 共享節點。如果需要更強的隔離,您可以使用節點選擇器、反親和性規則和/或污點和容忍度,將來自不同租戶的 pod 強制調度到單獨的節點上;通常稱為 _單租戶節點_。在有許多租戶的環境中,這可能會變得相當複雜且成本高昂。

!!! 注意
    使用命名空間實現的軟多租戶不允許您向租戶提供已篩選的命名空間列表,因為命名空間是全局作用域類型。如果租戶有能力查看特定命名空間,它就可以查看集群中的所有命名空間。

!!! 警告
    使用軟多租戶,租戶默認保留查詢 CoreDNS 以獲取集群中運行的所有服務的能力。攻擊者可以通過從集群中的任何 pod 運行 `dig SRV *.*.svc.cluster.local` 來利用這一點。如果您需要限制訪問集群中運行的服務的 DNS 記錄的權限,請考慮使用 CoreDNS 的防火牆或策略插件。有關更多信息,請參閱 [https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy](https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy)。

[Kiosk](https://github.com/kiosk-sh/kiosk) 是一個開源項目,可以幫助實現軟多租戶。它是作為一系列 CRD 和控制器實現的,提供以下功能:

- **帳戶和帳戶用戶** 用於在共享 Kubernetes 集群中分離租戶
- **自助命名空間供應** 供帳戶用戶使用
- **帳戶限制** 確保在共享集群時的服務質量和公平性
- **命名空間模板** 用於安全的租戶隔離和自助命名空間初始化
  
[Loft](https://loft.sh) 是 Kiosk 和 [DevSpace](https://github.com/devspace-cloud/devspace) 維護者提供的商業產品,增加了以下功能:

- **多集群訪問** 用於授予對不同集群中空間的訪問權限
- **睡眠模式** 在空閒期間縮減空間中的部署
- **單點登錄** 與 GitHub 等 OIDC 身份驗證提供程序集成

軟多租戶可以解決三個主要用例。

### 企業環境

第一個是企業環境,其中"租戶"是半信任的,即他們是員工、承包商或由組織授權的其他人員。每個租戶通常與管理部門(如部門或團隊)相對應。

在這種環境中,集群管理員通常負責創建命名空間和管理策略。他們還可能實施委派管理模型,其中某些個人被授予對命名空間的監督權,允許他們對非策略相關對象(如部署、服務、pod、作業等)執行 CRUD 操作。

在這種環境中,容器運行時提供的隔離可能是可接受的,或者可能需要使用其他控制來增強 pod 安全性。如果需要更嚴格的隔離,也可能需要限制不同命名空間中服務之間的通信。

### Kubernetes 作為服務

相反,軟多租戶可用於希望提供 Kubernetes 作為服務 (KaaS) 的環境。使用 KaaS,您的應用程序托管在共享集群中,其中包含一組控制器和 CRD,提供一組 PaaS 服務。租戶直接與 Kubernetes API 服務器交互,並被允許對非策略對象執行 CRUD 操作。還有一個自助服務的元素,即租戶可能被允許創建和管理自己的命名空間。在這種類型的環境中,假設租戶運行的是不可信代碼。

要在這種類型的環境中隔離租戶,您可能需要實施嚴格的網路策略以及 _pod 沙箱_。沙箱是在微型虛擬機(如 Firecracker)或用戶空間內核中運行 pod 的容器。今天,您可以使用 EKS Fargate 創建沙箱 pod。

### 軟件即服務 (SaaS)

軟多租戶的最後一個用例是軟件即服務 (SaaS) 環境。在這種環境中,每個租戶都與集群中運行的應用程序的特定 _實例_ 相關聯。每個實例通常都有自己的數據,並使用與 Kubernetes RBAC 獨立的單獨訪問控制。

與其他用例不同,SaaS 環境中的租戶不直接與 Kubernetes API 交互。相反,SaaS 應用程序負責與 Kubernetes API 交互,以創建支持每個租戶所需的對象。

## Kubernetes 構造

在這些實例中,使用以下構造來隔離租戶:

### 命名空間

命名空間是實現軟多租戶的基礎。它們允許您將集群劃分為邏輯分區。配額、網路策略、服務帳戶和實現多租戶所需的其他對象都在命名空間範圍內。

### 網路策略

默認情況下,集群中的所有 pod 都可以相互通信。可以使用網路策略更改此行為。

網路策略使用標籤或 IP 地址範圍來限制 pod 之間的通信。在需要在租戶之間實現嚴格網路隔離的多租戶環境中,我們建議從一個拒絕 pod 之間通信的默認規則開始,以及另一個允許所有 pod 查詢 DNS 服務器進行名稱解析的規則。有了這個基礎,您就可以開始添加更多允許在命名空間內通信的規則。根據需要,可以進一步細化這些規則。

!!! 注意
    Amazon [VPC CNI 現在支持 Kubernetes 網路策略](https://aws.amazon.com/blogs/containers/amazon-vpc-cni-now-supports-kubernetes-network-policies/),可以在 AWS 上運行 Kubernetes 時創建策略,以隔離敏感工作負載並保護它們免受未經授權的訪問。這意味著您可以在 Amazon EKS 集群中使用網路策略 API 的所有功能。這種細粒度的控制使您能夠實施最小特權原則,確保只有經過授權的 pod 才能相互通信。

!!! 注意
    網路策略是必要的,但不足以實現隔離。網路策略的執行需要策略引擎,如 Calico 或 Cilium。

### 基於角色的訪問控制 (RBAC)

角色和角色綁定是用於在 Kubernetes 中實施基於角色的訪問控制 (RBAC) 的對象。**角色** 包含可對集群中對象執行的操作列表。**角色綁定** 指定角色適用的個人或組。在企業和 KaaS 環境中,RBAC 可用於允許選定的組或個人管理對象。

### 配額

配額用於定義托管在集群中的工作負載的限制。使用配額,您可以指定 pod 可以消耗的最大 CPU 和內存量,或者可以限制可在集群或命名空間中分配的資源數量。**限制範圍** 允許您聲明每個限制的最小、最大和默認值。

在共享集群中過度使用資源通常是有利的,因為它允許您最大化利用資源。但是,無限制地訪問集群可能會導致資源耗盡,從而導致性能下降和應用程序可用性損失。如果 pod 的請求設置過低,實際資源利用率超過節點的容量,節點將開始經歷 CPU 或內存壓力。發生這種情況時,pod 可能會在節點上重新啟動和/或被逐出。

為了防止這種情況發生,您應該計劃對多租戶環境中的命名空間實施配額,以強制租戶在集群上調度 pod 時指定請求和限制。它還將減輕 pod 可能消耗的資源量的潛在拒絕服務。

您還可以使用配額來按照租戶的支出分配集群資源。這在 KaaS 場景中特別有用。

### Pod 優先級和抢占

當您希望相對於其他 Pod 為某個 Pod 提供更高的重要性時,Pod 優先級和抢占可能很有用。例如,通過 pod 優先級,您可以配置客戶 A 的 pod 以比客戶 B 的 pod 具有更高的優先級。當可用容量不足時,調度器將逐出客戶 B 的較低優先級 pod,以容納客戶 A 的較高優先級 pod。在客戶願意支付更高費用以獲得更高優先級的 SaaS 環境中,這可能特別有用。

!!! 注意
    Pod 優先級可能會對其他較低優先級的 Pod 產生意外影響。例如,儘管受害 pod 會被正常終止,但 PodDisruptionBudget 不能保證,這可能會破壞依賴 Pod 組中的多數 Pod 的較低優先級應用程序,請參閱 [抢占的限制](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/#limitations-of-preemption)。

## 緩解控制

作為多租戶環境的管理員,您最主要的擔憂是防止攻擊者訪問底層主機。應考慮以下控制措施來減輕此風險:

### 容器的沙箱執行環境

沙箱是一種技術,每個容器都在自己的隔離虛擬機中運行。執行 pod 沙箱的技術包括 [Firecracker](https://firecracker-microvm.github.io/) 和 Weave 的 [Firekube](https://www.weave.works/blog/firekube-fast-and-secure-kubernetes-clusters-using-weave-ignite)。

有關將 Firecracker 作為 EKS 支持的運行時的工作的更多信息,請參閱
[https://threadreaderapp.com/thread/1238496944684597248.html](https://threadreaderapp.com/thread/1238496944684597248.html)。

### Open Policy Agent (OPA) 和 Gatekeeper

[Gatekeeper](https://github.com/open-policy-agent/gatekeeper) 是一個 Kubernetes 准入控制器,它強制執行使用 [OPA](https://www.openpolicyagent.org/) 創建的策略。使用 OPA,您可以創建一個策略,將來自租戶的 pod 在單獨的實例上運行,或比其他租戶具有更高的優先級。本項目的 GitHub [存儲庫](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa)中包含了一些常見的 OPA 策略集合。

還有一個實驗性的 [OPA CoreDNS 插件](https://github.com/coredns/coredns-opa),允許您使用 OPA 過濾/控制 CoreDNS 返回的記錄。

### Kyverno

[Kyverno](https://kyverno.io) 是一個本機 Kubernetes 策略引擎,可以使用作為 Kubernetes 資源的策略來驗證、變更和生成配置。Kyverno 使用 Kustomize 樣式的覆蓋進行驗證,支持 JSON Patch 和策略合併修補進行變更,並且可以根據靈活的觸發器在命名空間之間克隆資源。

您可以使用 Kyverno 隔離命名空間、強制執行 pod 安全性和其他最佳實踐,以及生成默認配置(如網路策略)。本項目的 GitHub [存儲庫](https://github.com/aws/aws-eks-best-practices/tree/master/policies/kyverno)中包含了一些示例。Kyverno 網站上的 [策略庫](https://kyverno.io/policies/)中還包含了許多其他示例。

### 將租戶工作負載隔離到特定節點

將租戶工作負載限制在特定節點上運行可用於增加軟多租戶模型中的隔離。使用這種方法,特定於租戶的工作負載僅在為各自租戶配置的節點上運行。為實現此隔離,使用本機 Kubernetes 屬性(節點親和性、污點和容忍度)來針對特定節點進行 pod 調度,並防止來自其他租戶的 pod 被調度到特定於租戶的節點上。

#### 第 1 部分 - 節點親和性

Kubernetes [節點親和性](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)用於基於節點 [標籤](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)針對調度目標節點。使用節點親和性規則,pod 會被吸引到與選擇器條件匹配的特定節點。在下面的 pod 規範中,`requiredDuringSchedulingIgnoredDuringExecution` 節點親和性被應用於相應的 pod。結果是,pod 將針對帶有以下鍵/值的節點: `node-restriction.kubernetes.io/tenant: tenants-x`。

``` yaml
...
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node-restriction.kubernetes.io/tenant
            operator: In
            values:
            - tenants-x
...
```

使用此節點親和性,標籤在調度期間是必需的,但在執行期間不是必需的;如果底層節點的標籤發生變化,pod 不會僅因標籤更改而被逐出。但是,未來的調度可能會受到影響。

!!! 警告
    標籤前綴 `node-restriction.kubernetes.io/` 在 Kubernetes 中有特殊含義。[NodeRestriction](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction) 在 EKS 集群上啟用,防止 `kubelet` 添加/刪除/更新此前綴的標籤。攻擊者無法使用 `kubelet` 的憑證來更新節點對象或修改系統設置以將這些標籤傳遞給 `kubelet`,因為 `kubelet` 不允許修改這些標籤。如果對所有 pod 到節點的調度使用此前綴,它可以防止攻擊者希望通過修改節點標籤來吸引不同的工作負載集合到節點的情況。

!!! 信息
    我們可以使用 [節點選擇器](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector)而不是節點親和性。但是,節點親和性更具表現力,並允許在 pod 調度期間考慮更多條件。有關差異和更高級調度選擇的更多信息,請參閱 CNCF 博客文章 [Advanced Kubernetes pod to node scheduling](https://www.cncf.io/blog/2021/07/27/advanced-kubernetes-pod-to-node-scheduling/)。

#### 第 2 部分 - 污點和容忍度

將 pod 吸引到節點只是這個三部分方法的第一部分。為了使這種方法有效,我們必須阻止未經授權的 pod 調度到不允許它們的節點上。為了阻止不需要或未經授權的 pod,Kubernetes 使用節點 [污點](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)。污點用於在節點上放置條件,以防止 pod 被調度。下面的污點使用鍵值對 `tenant: tenants-x`。

``` yaml
...
    taints:
      - key: tenant
        value: tenants-x
        effect: NoSchedule
...
```

給定上述節點 `taint`,只有 _容忍_ 該污點的 pod 才能被允許調度到該節點。為了允許授權的 pod 調度到節點,相應的 pod 規範必須包含對該污點的 `toleration`,如下所示。

``` yaml
...
  tolerations:
  - effect: NoSchedule
    key: tenant
    operator: Equal
    value: tenants-x
...
```

具有上述 `toleration` 的 pod 不會因為該特定污點而被阻止調度到節點。污點也被 Kubernetes 用於在某些條件下(如節點資源壓力)暫時停止 pod 調度。使用節點親和性、污點和容忍度,我們可以有效地將所需的 pod 吸引到特定節點,並阻止不需要的 pod。租戶工作負載實際上是隔離的。

!!! 注意
    某些 Kubernetes pod 需要在所有節點上運行。這些 pod 的示例包括由 [容器網路接口 (CNI)](https://github.com/containernetworking/cni) 和 [kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) [daemonset](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) 啟動的 pod。為此,這些 pod 的規範包含非常寬鬆的容忍度,以容忍不同的污點。應該注意不要更改這些容忍度。更改這些容忍度可能會導致集群操作不正確。此外,策略管理工具(如 [OPA/Gatekeeper](https://github.com/open-policy-agent/gatekeeper) 和 [Kyverno](https://kyverno.io/))可用於編寫驗證策略,以防止未經授權的 pod 使用這些寬鬆的容忍度。

#### 第 3 部分 - 基於策略的節點選擇管理

有幾種工具可用於幫助管理 pod 規範的節點親和性和容忍度,包括在 CICD 管道中實施規則。但是,隔離的實施也應該在 Kubernetes 集群級別進行。為此,可以使用策略管理工具來 _變更_ 基於請求負載的入站 Kubernetes API 服務器請求,以應用上述相應的節點親和性規則和容忍度。

例如,目標為 _tenants-x_ 命名空間的 pod 可以使用 _stamp_ 正確的節點親和性和容忍度,以允許在 _tenants-x_ 節點上調度。利用配置為使用 Kubernetes [變更準入 Webhook](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#mutatingadmissionwebhook) 的策略管理工具,可以使用策略來變更入站 pod 規範。變更會添加所需的元素以允許所需的調度。下面是一個使用 OPA/Gatekeeper 添加節點親和性的策略示例。

``` yaml
apiVersion: mutations.gatekeeper.sh/v1alpha1
kind: Assign
metadata:
  name: mutator-add-nodeaffinity-pod
  annotations:
    aws-eks-best-practices/description: >-
      Adds Node affinity - https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#node-affinity
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    namespaces: ["tenants-x"]
  location: "spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms"
  parameters:
    assign:
      value: 
        - matchExpressions:
          - key: "tenant"
            operator: In
            values:
            - "tenants-x"
```

上述策略應用於 Kubernetes API 服務器請求,以將 pod 應用到 _tenants-x_ 命名空間。該策略添加了 `requiredDuringSchedulingIgnoredDuringExecution` 節點親和性規則,以便 pod 被吸引到帶有 `tenant: tenants-x` 標籤的節點。

第二個策略(如下所示)使用相同的目標命名空間和組、種類和版本匹配條件,將容忍度添加到相同的 pod 規範中。

``` yaml
apiVersion: mutations.gatekeeper.sh/v1alpha1
kind: Assign
metadata:
  name: mutator-add-toleration-pod
  annotations:
    aws-eks-best-practices/description: >-
      Adds toleration - https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    namespaces: ["tenants-x"]
  location: "spec.tolerations"
  parameters:
    assign:
      value: 
      - key: "tenant"
        operator: "Equal"
        value: "tenants-x"
        effect: "NoSchedule"
```

上述策略專門針對 pod;這是由於策略中 `location` 元素中變更元素的路徑。可以編寫其他策略來處理創建 pod 的資源,如 Deployment 和 Job 資源。可以在本指南的配套 [GitHub 項目](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa/gatekeeper/node-selector)中看到列出的策略和其他示例。

這兩種變更的結果是,pod 被吸引到所需的節點,同時也不被特定節點的污點排斥。為了驗證這一點,我們可以看看兩個 `kubectl` 調用的輸出片段,以獲取帶有 `tenant=tenants-x` 標籤的節點,以及在 `tenants-x` 命名空間中的 pod。

``` bash
kubectl get nodes -l tenant=tenants-x
NAME                                        
ip-10-0-11-255...
ip-10-0-28-81...
ip-10-0-43-107...

kubectl -n tenants-x get pods -owide
NAME                                  READY   STATUS    RESTARTS   AGE   IP            NODE
tenant-test-deploy-58b895ff87-2q7xw   1/1     Running   0          13s   10.0.42.143   ip-10-0-43-107...
tenant-test-deploy-58b895ff87-9b6hg   1/1     Running   0          13s   10.0.18.145   ip-10-0-28-81...
tenant-test-deploy-58b895ff87-nxvw5   1/1     Running   0          13s   10.0.30.117   ip-10-0-28-81...
tenant-test-deploy-58b895ff87-vw796   1/1     Running   0          13s   10.0.3.113    ip-10-0-11-255...
tenant-test-pod                       1/1     Running   0          13s   10.0.35.83    ip-10-0-43-107...
```

如我們所見,所有 pod 都調度在帶有 `tenant=tenants-x` 標籤的節點上。簡而言之,pod 只會在所需的節點上運行,而其他 pod(沒有所需的親和性和容忍度)則不會。租戶工作負載實際上是隔離的。

下面是一個變更後的 pod 規範示例。

``` yaml
apiVersion: v1
kind: Pod
metadata:
  name: tenant-test-pod
  namespace: tenants-x
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: tenant
            operator: In
            values:
            - tenants-x
...
  tolerations:
  - effect: NoSchedule
    key: tenant
    operator: Equal
    value: tenants-x
...
```

!!! 注意
    集成到 Kubernetes API 服務器請求流程的策略管理工具(使用變更和驗證準入 Webhook)被設計為在指定的時間內響應 API 服務器的請求。這通常是 3 秒或更短。如果 Webhook 調用無法在配置的時間內返回響應,則入站 API 服務器請求的變更和/或驗證可能會或可能不會發生。這種行為取決於準入 Webhook 配置是設置為 [Fail Open 或 Fail Close](https://open-policy-agent.github.io/gatekeeper/website/docs/#admission-webhook-fail-open-by-default)。

在上面的示例中,我們使用了為 OPA/Gatekeeper 編寫的策略。但是,也有其他策略管理工具可以處理我們的節點選擇用例。例如,可以使用此 [Kyverno 策略](https://kyverno.io/policies/other/add_node_affinity/add_node_affinity/)來處理節點親和性變更。

!!! 提示
    如果正確操作,變更策略將對入站 API 服務器請求負載產生所需的更改。但是,也應該包括驗證策略,以在允許更改持續之前驗證所需的更改是否發生。在使用這些策略進行租戶到節點隔離時,這一點尤其重要。定期檢查集群是否存在不需要的配置也是一個好主意,可以包括 _審計_ 策略。

### 參考資料

- [k-rail](https://github.com/cruise-automation/k-rail) 旨在通過實施某些策略來幫助您保護多租戶環境。

- [使用 Amazon EKS 的多租戶 SaaS 應用程序的安全實踐](https://d1.awsstatic.com/whitepapers/security-practices-for-multi-tenant-saas-apps-using-eks.pdf)

## 硬多租戶

可以通過為每個租戶配置單獨的集群來實現硬多租戶。雖然這在租戶之間提供了非常強的隔離,但也有幾個缺點。

首先,當您有許多租戶時,這種方法很快就會變得昂貴。您不僅需要為每個集群支付控制平面成本,而且無法在集群之間共享計算資源。最終會導致碎片化,其中一部分集群利用不足,而另一部分集群則過度利用。

其次,您可能需要購買或構建特殊工具來管理所有這些集群。隨著時間的推移,管理數百或數千個集群可能會變得過於困難。

最後,為每個租戶創建集群將比創建命名空間慢。儘管如此,在高度監管的行業或需要強隔離的 SaaS 環境中,可能需要採用硬租戶方法。

## 未來方向

Kubernetes 社區已經認識到軟多租戶的當前缺陷以及硬多租戶的挑戰。[多租戶特殊興趣小組 (SIG)](https://github.com/kubernetes-sigs/multi-tenancy) 正試圖通過幾個孵化項目(包括分層命名空間控制器 (HNC) 和虛擬集群)來解決這些缺陷。

HNC 提案 (KEP) 描述了在命名空間之間創建父子關係的方式,包括 \[policy\] 對象繼承以及租戶管理員創建子命名空間的能力。

虛擬集群提案描述了為每個租戶在集群內創建單獨控制平面服務實例(也稱為"Kubernetes on Kubernetes")的機制,包括 API 服務器、控制器管理器和調度器。

[多租戶基準](https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/README.md)提案提供了使用命名空間進行隔離和分段共享集群的指導方針,以及 [kubectl-mtb](https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/kubectl-mtb/README.md) 命令行工具來驗證對這些指導方針的符合性。

## 多集群管理工具和資源

- [Banzai Cloud](https://banzaicloud.com/)
- [Kommander](https://d2iq.com/solutions/ksphere/kommander)
- [Lens](https://github.com/lensapp/lens)
- [Nirmata](https://nirmata.com)
- [Rafay](https://rafay.co/)
- [Rancher](https://rancher.com/products/rancher/)
- [Weave Flux](https://www.weave.works/oss/flux/)
