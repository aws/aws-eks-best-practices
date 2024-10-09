# Pod 安全性

Pod 規格包含各種不同的屬性,可以加強或削弱您的整體安全態勢。作為 Kubernetes 從業人員,您的主要關注點應該是防止在容器運行時內運行的進程逃離容器隔離邊界並獲得對底層主機的訪問權限。

## Linux 功能

在容器內運行的進程默認在 \[Linux\] 根用戶的上下文中運行。儘管根在容器內的操作受到容器運行時分配給容器的 Linux 功能集的部分約束,但這些默認權限可能允許攻擊者提升其權限和/或訪問綁定到主機的敏感信息,包括 Secret 和 ConfigMap。下面是分配給容器的默認功能列表。有關每個功能的更多信息,請參閱 [http://man7.org/linux/man-pages/man7/capabilities.7.html](http://man7.org/linux/man-pages/man7/capabilities.7.html)。

`CAP_AUDIT_WRITE, CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FOWNER, CAP_FSETID, CAP_KILL, CAP_MKNOD, CAP_NET_BIND_SERVICE, CAP_NET_RAW, CAP_SETGID, CAP_SETUID, CAP_SETFCAP, CAP_SETPCAP, CAP_SYS_CHROOT`

!!! 信息

  EC2 和 Fargate pod 默認分配了上述功能。此外,只能從 Fargate pod 中刪除 Linux 功能。

以特權模式運行的 Pod 會繼承主機上與 root 相關的所有 Linux 功能。如果可能,應該避免這種情況。

### 節點授權

所有 Kubernetes 工作節點都使用名為 [Node Authorization](https://kubernetes.io/docs/reference/access-authn-authz/node/) 的授權模式。Node Authorization 授權來自 kubelet 的所有 API 請求,並允許節點執行以下操作:

讀取操作:

- services
- endpoints
- nodes
- pods
- secrets、configmaps、與綁定到 kubelet 節點的 pod 相關的持久性卷聲明和持久性卷

寫入操作:

- nodes 和 node status (啟用 `NodeRestriction` 準入插件以限制 kubelet 只能修改自己的節點)
- pods 和 pod status (啟用 `NodeRestriction` 準入插件以限制 kubelet 只能修改綁定到自己的 pod)
- events

與身份驗證相關的操作:

- 讀/寫訪問 CertificateSigningRequest (CSR) API 以進行 TLS 引導
- 能夠創建 TokenReview 和 SubjectAccessReview 以進行委派身份驗證/授權檢查

EKS 使用 [node restriction admission controller](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction),它只允許節點修改有限的節點屬性和綁定到該節點的 pod 對象。儘管如此,如果攻擊者設法訪問主機,他們仍然可以從 Kubernetes API 獲取有關環境的敏感信息,從而可能在集群內進行橫向移動。

## Pod 安全解決方案

### Pod 安全策略 (PSP)

過去,使用 [Pod 安全策略 (PSP)](https://kubernetes.io/docs/concepts/policy/pod-security-policy/) 資源來指定 pod 在創建之前必須滿足的一組要求。從 Kubernetes 1.21 版開始,PSP 已被棄用。它們計劃在 Kubernetes 1.25 版中被刪除。

!!! 注意

  [PSP 在 Kubernetes 1.21 版中已被棄用](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/)。您將有大約 2 年的時間轉換到替代方案,直到 1.25 版。這 [文檔](https://github.com/kubernetes/enhancements/blob/master/keps/sig-auth/2579-psp-replacement/README.md#motivation) 解釋了此棄用的動機。

### 遷移到新的 pod 安全解決方案

由於 PSP 在 Kubernetes v1.25 中已被刪除,集群管理員和操作員必須使用其他安全控制措施來替代。兩種解決方案可以滿足這種需求:

- Kubernetes 生態系統中的基於策略的代碼 (PAC) 解決方案
- Kubernetes [Pod 安全標準 (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

PAC 和 PSS 解決方案都可以與 PSP 共存;在 PSP 被刪除之前,它們可以在集群中使用。這有助於在遷移 PSP 時採用新解決方案。在考慮從 PSP 遷移到 PSS 時,請參閱此 [文檔](https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/)。

Kyverno 是下面概述的 PAC 解決方案之一,它在一篇 [博客文章](https://kyverno.io/blog/2023/05/24/podsecuritypolicy-migration-with-kyverno/) 中概述了從 PSP 遷移到其解決方案的具體指導,包括類似的策略、功能比較和遷移程序。有關使用 Kyverno 管理 Pod 安全準入 (PSA) 的更多信息和指導,已在 AWS 博客 [此處](https://aws.amazon.com/blogs/containers/managing-pod-security-on-amazon-eks-with-kyverno/) 發布。

### 基於策略的代碼 (PAC)

基於策略的代碼 (PAC) 解決方案提供了指導軌道,通過規定和自動化控制來引導集群用戶並防止不希望的行為。PAC 使用 [Kubernetes 動態準入控制器](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/) 通過 webhook 調用攔截 Kubernetes API 服務器請求流,並根據以代碼形式編寫和存儲的策略來變更和驗證請求有效載荷,在 API 服務器請求導致集群發生變化之前進行這些操作。變更和驗證。PAC 解決方案使用策略來匹配和處理 API 服務器請求有效載荷,根據分類和值進行操作。

Kubernetes 生態系統中有幾種開源 PAC 解決方案可用。這些解決方案不屬於 Kubernetes 項目;它們來自 Kubernetes 生態系統。一些 PAC 解決方案如下所列。

- [OPA/Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/)
- [Open Policy Agent (OPA)](https://www.openpolicyagent.org/)
- [Kyverno](https://kyverno.io/)
- [Kubewarden](https://www.kubewarden.io/)
- [jsPolicy](https://www.jspolicy.com/)

有關 PAC 解決方案的更多信息以及如何幫助您選擇適合您需求的適當解決方案,請參閱下面的鏈接。

- [Kubernetes 的基於策略的對策 – 第 1 部分](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-1/)
- [Kubernetes 的基於策略的對策 – 第 2 部分](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-2/)

### Pod 安全標準 (PSS) 和 Pod 安全準入 (PSA)

為了應對 PSP 棄用以及對內置 Kubernetes 解決方案的持續需求,Kubernetes [Auth 特別興趣小組](https://github.com/kubernetes/community/tree/master/sig-auth)創建了 [Pod 安全標準 (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) 和 [Pod 安全準入 (PSA)](https://kubernetes.io/docs/concepts/security/pod-security-admission/)。PSA 工作包括一個 [admission controller webhook 項目](https://github.com/kubernetes/pod-security-admission#pod-security-admission),它實現了 PSS 中定義的控制措施。這種 admission controller 方法類似於 PAC 解決方案中使用的方法。

根據 Kubernetes 文檔,PSS _"定義了三種不同的策略,廣泛涵蓋了安全範圍。這些策略是累積的,範圍從高度寬鬆到高度限制。"_

這些策略定義如下:

- **特權:** 不受限制(不安全)的策略,提供最廣泛的權限級別。這種策略允許已知的權限提升。這是沒有策略的情況。這對於需要特權訪問的應用程序(如日誌代理、CNI、存儲驅動程序和其他系統範圍的應用程序)很有用。

- **基線:** 最低限制性策略,可防止已知的權限提升。允許默認(最小指定)的 Pod 配置。基線策略禁止使用 hostNetwork、hostPID、hostIPC、hostPath、hostPort,無法添加 Linux 功能,以及其他一些限制。

- **受限:** 嚴格限制的策略,遵循當前 Pod 強化最佳實踐。這種策略繼承自基線並增加了進一步的限制,例如無法以 root 或 root 組身份運行。受限策略可能會影響應用程序的正常運行。它們主要針對運行安全關鍵型應用程序。

這些策略定義了 [pod 執行配置文件](https://kubernetes.io/docs/concepts/security/pod-security-standards/#profile-details),分為三個特權與受限訪問級別。

為了實現 PSS 定義的控制措施,PSA 以三種模式運行:

- **enforce:** 違反策略將導致 pod 被拒絕。

- **audit:** 違反策略將觸發在審計日誌中添加審計註釋到記錄的事件,但其他情況下允許。

- **warn:** 違反策略將觸發面向用戶的警告,但其他情況下允許。

這些模式和配置文件(限制)級別使用標籤在 Kubernetes 命名空間級別進行配置,如下例所示。

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/enforce: restricted
```

如上所示,已將集群範圍的默認 PSS 級別設置為所有 PSA 模式 _audit_、_enforce_ 和 _warn_ 的 _restricted_。這影響所有命名空間,除了那些被豁免的: `namespaces: ["kube-system","policy-test1"]`。此外,在下面顯示的 _ValidatingWebhookConfiguration_ 資源中,_pod-security-webhook_ 命名空間也被豁免於配置的 PSS。

```yaml
...
webhooks:
  # 審計註釋將以此名稱為前綴
  - name: "pod-security-webhook.kubernetes.io"
    # 失敗關閉的準入 webhook 可能會帶來操作挑戰。
    # 您可能需要考慮使用 Ignore 的失敗策略,但應該
    # 考慮安全權衡。
    failurePolicy: Fail
    namespaceSelector:
      # 豁免 webhook 本身以避免循環依賴。
      matchExpressions:
        - key: kubernetes.io/metadata.name
          operator: NotIn
          values: ["pod-security-webhook"]
...
```

!!! 注意

  Pod 安全準入在 Kubernetes v1.25 中已成為穩定版本。如果您想在默認啟用 Pod 安全準入功能之前使用它,您需要安裝動態準入控制器(變更 webhook)。安裝和配置 webhook 的說明可以在 [這裡](https://github.com/kubernetes/pod-security-admission/tree/master/webhook) 找到。

### 選擇基於策略的代碼還是 Pod 安全標準

Pod 安全標準 (PSS) 的開發旨在取代 Pod 安全策略 (PSP),通過提供一種內置於 Kubernetes 且不需要來自 Kubernetes 生態系統的解決方案來實現這一目標。不過,基於策略的代碼 (PAC) 解決方案要靈活得多。

以下優缺點列表旨在幫助您更好地決定 pod 安全解決方案。

#### 基於策略的代碼(與 Pod 安全標準相比)

優點:

- 更靈活、更細粒度(如果需要,可以細化到資源的屬性)
- 不僅僅專注於 pod,可以用於不同的資源和操作
- 不僅在命名空間級別應用
- 比 Pod 安全標準更成熟
- 決策可以基於 API 服務器請求有效載荷中的任何內容,以及現有集群資源和外部數據(取決於解決方案)
- 支持在驗證之前變更 API 服務器請求(取決於解決方案)
- 可以根據 pod 策略生成補充策略和 Kubernetes 資源(取決於解決方案 - 從 pod 策略,Kyverno 可以 [自動生成](https://kyverno.io/docs/writing-policies/autogen/) 更高級控制器的策略,例如 Deployments。Kyverno 還可以通過使用 [生成規則](https://kyverno.io/docs/writing-policies/generate/) 在創建新資源或更新源時"生成額外的 Kubernetes 資源")
- 可以向左移動,進入 CICD 管道,在調用 Kubernetes API 服務器之前(取決於解決方案)
- 可用於實現與安全無關的行為,例如最佳實踐、組織標準等
- 可用於非 Kubernetes 用例(取決於解決方案)
- 由於靈活性,用戶體驗可以根據用戶需求進行調整

缺點:

- 不是 Kubernetes 內置的
- 更複雜,難以學習、配置和支持
- 編寫策略可能需要新的技能/語言/能力

#### Pod 安全準入(與基於策略的代碼相比)

優點:

- 內置於 Kubernetes
- 更簡單的配置
- 不需要使用新語言或編寫策略
- 如果集群默認準入級別配置為 _privileged_,則可以使用命名空間標籤將命名空間選入 pod 安全配置文件。

缺點:

- 沒有基於策略的代碼那麼靈活或細粒度
- 只有 3 個限制級別
- 主要專注於 pod

#### 總結

如果您目前還沒有除 PSP 之外的 pod 安全解決方案,而且您所需的 pod 安全態勢符合 Pod 安全標準 (PSS) 中定義的模型,那麼採用 PSS 而不是基於策略的代碼解決方案可能是一條更簡單的路徑。但是,如果您的 pod 安全態勢不符合 PSS 模型,或者您預期將添加超出 PSS 定義範圍的其他控制措施,那麼基於策略的代碼解決方案似乎更合適。

## 建議

### 為了獲得更好的用戶體驗,使用多個 Pod 安全準入 (PSA) 模式

如前所述,PSA _enforce_ 模式可防止違反 PSS 的 pod 被應用,但不會阻止更高級別的控制器(如 Deployments)。事實上,Deployment 將被成功應用,而不會有任何指示 pod 未能應用的跡象。雖然您可以使用 _kubectl_ 檢查 Deployment 對象,並發現來自 PSA 的失敗 pod 消息,但用戶體驗可能會更好。為了改善用戶體驗,應使用多個 PSA 模式(audit、enforce、warn)。

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
```

在上面的示例中,定義了 _enforce_ 模式,當嘗試將違反 PSS 的 Deployment 清單應用到 Kubernetes API 服務器時,Deployment 將被成功應用,但 pod 不會。而且,由於 _audit_ 和 _warn_ 模式也已啟用,API 服務器客戶端將收到警告消息,API 服務器審計日誌事件也將被註釋消息。

### 限制可以以特權模式運行的容器

如前所述,以特權模式運行的容器會繼承主機上與 root 相關的所有 Linux 功能。很少有容器需要這種類型的特權才能正常運行。有多種方法可用於限制容器的權限和功能。

!!! 注意

  Fargate 是一種啟動類型,可讓您在 AWS 管理的基礎設施上以"無服務器"方式運行容器。使用 Fargate,您無法運行特權容器或將 pod 配置為使用 hostNetwork 或 hostPort。

### 不要以 root 身份在容器中運行進程

所有容器默認以 root 身份運行。如果攻擊者能夠利用應用程序中的漏洞並獲得對正在運行的容器的 shell 訪問權限,這可能會存在問題。您可以通過多種方式緩解這種風險。首先,從容器映像中刪除 shell。其次,在 Dockerfile 中添加 USER 指令或以非 root 用戶身份在 pod 中運行容器。Kubernetes podSpec 包括一組字段,在 `spec.securityContext` 下,可以讓您指定運行應用程序的用戶和/或組。這些字段分別是 `runAsUser` 和 `runAsGroup`。

要在集群中強制使用 Kubernetes podSpec 中的 `spec.securityContext` 及其關聯元素,可以添加基於策略的代碼或 Pod 安全標準。這些解決方案允許您編寫和/或使用策略或配置文件,在 Kubernetes API 服務器請求有效載荷被持久化到 etcd 之前對其進行驗證。此外,基於策略的代碼解決方案還可以變更傳入請求,在某些情況下甚至可以生成新請求。

### 永遠不要在 Docker 中運行 Docker 或在容器中掛載套接字

雖然這種方式可以方便地在 Docker 容器中構建/運行映像,但您基本上是將節點的完全控制權交給了在容器中運行的進程。如果您需要在 Kubernetes 上構建容器映像,請使用 [Kaniko](https://github.com/GoogleContainerTools/kaniko)、[buildah](https://github.com/containers/buildah) 或構建服務(如 [CodeBuild](https://docs.aws.amazon.com/codebuild/latest/userguide/welcome.html))。

!!! 提示

  用於 CICD 處理(如構建容器映像)的 Kubernetes 集群應與運行更一般工作負載的集群隔離。

### 限制 hostPath 的使用,或者如果需要使用 hostPath,請限制可以使用的前綴並將卷配置為只讀

`hostPath` 是一個卷,直接將主機上的目錄掛載到容器。很少有 pod 需要這種訪問權限,但如果需要,您需要了解風險。默認情況下,以 root 身份運行的 pod 將對 hostPath 暴露的文件系統具有寫入訪問權限。這可能允許攻擊者修改 kubelet 設置、創建指向未直接暴露的目錄或文件(例如 /etc/shadow)的符號鏈接、安裝 ssh 密鑰、讀取掛載到主機的 secret 以及其他惡意行為。為了減輕 hostPath 帶來的風險,請將 `spec.containers.volumeMounts` 配置為 `readOnly`,例如:

```yaml
volumeMounts:
- name: hostPath-volume
    readOnly: true
    mountPath: /host-path
```

您還應該使用基於策略的代碼解決方案來限制可以使用 `hostPath` 卷的目錄,或者完全防止使用 `hostPath`。您可以使用 Pod 安全標準 _Baseline_ 或 _Restricted_ 策略來防止使用 `hostPath`。

有關特權提升的危險的更多信息,請閱讀 Seth Art 的博客 [Bad Pods: Kubernetes Pod Privilege Escalation](https://labs.bishopfox.com/tech-blog/bad-pods-kubernetes-pod-privilege-escalation)。

### 為每個容器設置請求和限制,以避免資源競爭和 DoS 攻擊

沒有請求或限制的 pod 理論上可以消耗主機上的所有可用資源。隨著更多 pod 被調度到節點上,節點可能會遇到 CPU 或內存壓力,這可能會導致 Kubelet 從節點終止或逐出 pod。雖然您無法完全防止這種情況發生,但設置請求和限制將有助於最小化資源競爭並減輕編寫不當的應用程序消耗過多資源的風險。

`podSpec` 允許您為 CPU 和內存指定請求和限制。CPU 被視為可壓縮資源,因為它可以過度訂閱。內存是不可壓縮的,即它不能在多個容器之間共享。

當您為 CPU 或內存指定 _requests_ 時,您實際上是指定容器保證獲得的 _memory_ 量。Kubernetes 匯總 pod 中所有容器的請求,以確定將 pod 調度到哪個節點上。如果容器超過了請求的內存量,如果節點上的內存壓力很大,它可能會被終止。

_Limits_ 是容器允許消耗的 CPU 和內存資源的最大量,直接對應於為容器創建的 cgroup 的 `memory.limit_in_bytes` 值。超過內存限制的容器將被 OOM 終止。如果容器超過其 CPU 限制,它將被節流。

!!! 提示

  使用容器 `resources.limits` 時,強烈建議基於負載測試的容器資源使用情況(又稱資源占用)是準確的數據驅動。如果沒有準確可靠的資源占用,容器 `resources.limits` 可以適當填充。例如,`resources.limits.memory` 可以比可觀察到的最大值高出 20-30%,以考慮潛在的內存資源限制不準確性。

Kubernetes 使用三個服務質量 (QoS) 類別來確定節點上運行的工作負載的優先級。這些包括:

- guaranteed
- burstable
- best-effort

如果未設置限制和請求,則 pod 被配置為 _best-effort_(最低優先級)。當內存不足時,best-effort pod 是首先被終止的。如果在 pod 內的所有容器上設置了限制,或者請求和限制設置為相同的值且不等於 0,則 pod 被配置為 _guaranteed_(最高優先級)。guaranteed pod 不會被終止,除非它們超過了配置的內存限制。如果限制和請求被配置為不同的值且不等於 0,或者 pod 內的一個容器設置了限制而其他容器沒有或設置了不同資源的限制,則 pod 被配置為 _burstable_(中等優先級)。這些 pod 有一些資源保證,但一旦超過請求的內存就可能被終止。

!!! 注意

  請求不會影響容器 cgroup 的 `memory_limit_in_bytes` 值;cgroup 限制設置為主機上可用的內存量。不過,如果將請求值設置得太低,當節點遇到內存壓力時,kubelet 可能會將 pod 列為終止目標。

| 類別 | 優先級 | 條件 | 終止條件 |
| :-- | :-- | :-- | :-- |
| Guaranteed | 最高 | limit = request != 0  | 僅超過內存限制 |
| Burstable  | 中等  | limit != request != 0 | 可以在超過請求內存時被終止 |
| Best-Effort| 最低  | limit & request 未設置 | 當內存不足時首先被終止 |

有關資源 QoS 的更多信息,請參閱 [Kubernetes 文檔](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/)。

您可以通過在命名空間上設置 [資源配額](https://kubernetes.io/docs/concepts/policy/resource-quotas/) 或創建 [限制範圍](https://kubernetes.io/docs/concepts/policy/limit-range/) 來強制使用請求和限制。資源配額允許您指定分配給命名空間的總資源量,例如 CPU 和 RAM。當應用到命名空間時,它會強制您為部署到該命名空間的所有容器指定請求和限制。相比之下,限制範圍可以讓您更精細地控制命名空間內的資源分配。使用限制範圍,您可以為 pod 或命名空間內的每個容器設置 CPU 和內存資源的最小/最大值。您還可以使用它們來設置默認的請求/限制值(如果未提供)。

基於策略的代碼解決方案可用於強制使用請求和限制,或者在創建命名空間時甚至可以創建資源配額和限制範圍。

### 不要允許特權提升

特權提升允許進程更改其運行的安全上下文。sudo 就是一個很好的例子,具有 SUID 或 SGID 位的二進制文件也是如此。特權提升基本上是一種讓用戶以另一個用戶或組的權限執行文件的方式。您可以通過實現變更策略來防止容器使用特權提升,該策略將 `allowPrivilegeEscalation` 設置為 `false`,或者在 `podSpec` 中設置 `securityContext.allowPrivilegeEscalation`。基於策略的代碼策略還可以用於防止 API 服務器請求在檢測到不正確設置時成功。Pod 安全標準也可以用於防止 pod 使用特權提升。

### 禁用 ServiceAccount 令牌掛載

對於不需要訪問 Kubernetes API 的 pod,您可以在 pod 規格或對於使用特定 ServiceAccount 的所有 pod 上禁用自動掛載 ServiceAccount 令牌。

!!! 注意

  禁用 ServiceAccount 掛載並不會阻止 pod 通過網絡訪問 Kubernetes API。要防止 pod 通過網絡訪問 Kubernetes API,您需要修改 [EKS 集群端點訪問](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html) 並使用 [NetworkPolicy](../network/#network-policy) 阻止 pod 訪問。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-automount
spec:
  automountServiceAccountToken: false
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sa-no-automount
automountServiceAccountToken: false
```

### 禁用服務發現

對於不需要查找或調用集群內服務的 pod,您可以減少提供給 pod 的信息量。您可以將 Pod 的 DNS 策略設置為不使用 CoreDNS,並且不將服務暴露為 pod 命名空間中的環境變量。有關服務鏈接的更多信息,請參閱 [Kubernetes 環境變量文檔][k8s-env-var-docs]。pod 的 DNS 策略的默認值為 "ClusterFirst",它使用集群內 DNS,而非默認值 "Default" 使用底層節點的 DNS 解析。有關 [Kubernetes Pod DNS 策略][dns-policy]的更多信息,請參閱文檔。

[k8s-env-var-docs]: https://kubernetes.io/docs/concepts/services-networking/service/#environment-variables
[dns-policy]: https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-s-dns-policy

!!! 注意

  禁用服務鏈接和更改 pod 的 DNS 策略並不會阻止 pod 通過網絡訪問集群內 DNS 服務。攻擊者仍然可以通過訪問集群內 DNS 服務來枚舉服務。(例如: `dig SRV *.*.svc.cluster.local @$CLUSTER_DNS_IP`) 要防止集群內服務發現,請使用 [NetworkPolicy](../network/#network-policy) 阻止 pod 訪問

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-service-info
spec:
    dnsPolicy: Default # "Default" 不是真正的默認值
    enableServiceLinks: false
```

### 將您的映像配置為只讀根文件系統

將您的映像配置為只讀根文件系統可以防止攻擊者覆蓋您的應用程序使用的文件系統上的二進制文件。如果您的應用程序需要寫入文件系統,請考慮將其寫入臨時目錄或附加並掛載卷。您可以通過設置 pod 的 SecurityContext 來強制執行此操作:

```yaml
...
securityContext:
  readOnlyRootFilesystem: true
...
```

基於策略的代碼和 Pod 安全標準可用於強制執行此行為。

!!! 信息

  根據 [Kubernetes 中的 Windows 容器](https://kubernetes.io/docs/concepts/windows/intro/) `securityContext.readOnlyRootFilesystem` 不能為在 Windows 上運行的容器設置為 `true`,因為需要寫入訪問權限才能在容器內運行註冊表和系統進程。

## 工具和資源

- [Amazon EKS 安全沉浸式研討會 - Pod 安全](https://catalog.workshops.aws/eks-security-immersionday/en-US/3-pod-security)
- [open-policy-agent/gatekeeper-library: OPA Gatekeeper 策略庫](https://github.com/open-policy-agent/gatekeeper-library),您可以使用這個庫中的 OPA/Gatekeeper 策略作為 PSP 的替代品。
- [Kyverno 策略庫](https://kyverno.io/policies/)
- 一些常見的 OPA 和 Kyverno [策略](https://github.com/aws/aws-eks-best-practices/tree/master/policies)集合,適用於 EKS。
- [基於策略的對策:第 1 部分](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-1/)
- [基於策略的對策:第 2 部分](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-2/)
- [Pod 安全策略遷移器](https://appvia.github.io/psp-migration/) 一個將 PSP 轉換為 OPA/Gatekeeper、KubeWarden 或 Kyverno 策略的工具
- [NeuVector by SUSE](https://www.suse.com/neuvector/) 開源的零信任容器安全平台,提供進程和文件系統策略以及準入控制規則。
