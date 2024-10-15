# 執行時安全性

執行時安全性為您的容器在運行時提供主動保護。其理念是檢測和/或防止在容器內發生惡意活動。這可以通過 Linux 內核或與 Kubernetes 集成的內核擴展中的多種機制來實現,例如 Linux 功能、安全計算 (seccomp)、AppArmor 或 SELinux。還有像 Amazon GuardDuty 和第三方工具這樣的選擇,可以幫助建立基線並檢測異常活動,而無需手動配置 Linux 內核機制。

!!! attention
    Kubernetes 目前不提供任何將 seccomp、AppArmor 或 SELinux 配置檔案載入到節點的原生機制。它們必須手動載入或在啟動節點時安裝。這必須在引用它們之前完成,因為調度程序不知道哪些節點有配置檔案。請參閱下面如何使用 Security Profiles Operator 等工具來自動將配置檔案佈建到節點。

## 安全上下文和內建的 Kubernetes 控制

許多 Linux 執行時安全機制與 Kubernetes 緊密集成,並且可以通過 Kubernetes [安全上下文](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)進行配置。其中一個選項是 `privileged` 標誌,默認為 `false`,如果啟用則基本等同於主機上的 root。在生產工作負載中啟用特權模式幾乎總是不合適的,但是還有許多其他控制可以根據需要為容器提供更細粒度的特權。

### Linux 功能

Linux 功能允許您在不提供 root 用戶的所有能力的情況下,將某些功能授予 Pod 或容器。示例包括 `CAP_NET_ADMIN`,允許配置網路介面或防火牆,或 `CAP_SYS_TIME`,允許操作系統時鐘。

### Seccomp

通過安全計算 (seccomp),您可以防止容器化應用程序對底層主機操作系統內核發出某些系統調用。儘管 Linux 操作系統有幾百個系統調用,但大部分都不是運行容器所必需的。通過限制容器可以發出的系統調用,您可以有效地減小應用程序的攻擊面。

Seccomp 通過攔截系統調用並僅允許通過已允許列表的系統調用來工作。Docker 有一個 [默認](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json) seccomp 配置檔案,適用於大多數通用工作負載,其他容器運行時(如 containerd)也提供了可比的默認值。您可以通過將以下內容添加到 Pod 規範的 `securityContext` 部分,將您的容器或 Pod 配置為使用容器運行時的默認 seccomp 配置檔案:

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

從 1.22 版本開始(alpha 版,1.27 版本穩定),上述 `RuntimeDefault` 可以使用 [單個 kubelet 標誌](https://kubernetes.io/docs/tutorials/security/seccomp/#enable-the-use-of-runtimedefault-as-the-default-seccomp-profile-for-all-workloads) `--seccomp-default` 用於節點上的所有 Pod。然後,只有在需要其他配置檔案時,才需要在 `securityContext` 中指定配置檔案。

還可以為需要額外權限的內容創建自己的配置檔案。手動執行這一操作可能非常繁瑣,但有像 [Inspektor Gadget](https://github.com/inspektor-gadget/inspektor-gadget) (在 [網路安全部分](../network/) 中也建議用於生成網路策略)和 [Security Profiles Operator](https://github.com/inspektor-gadget/inspektor-gadget) 這樣的工具,可以使用 eBPF 或日誌記錄基線特權要求作為 seccomp 配置檔案。Security Profiles Operator 還允許自動將記錄的配置檔案部署到節點,以供 Pod 和容器使用。

### AppArmor 和 SELinux

AppArmor 和 SELinux 被稱為 [強制訪問控制或 MAC 系統](https://en.wikipedia.org/wiki/Mandatory_access_control)。它們在概念上與 seccomp 類似,但具有不同的 API 和功能,允許對特定文件系統路徑或網路端口進行訪問控制。對這些工具的支持取決於 Linux 發行版,Debian/Ubuntu 支持 AppArmor,而 RHEL/CentOS/Bottlerocket/Amazon Linux 2023 支持 SELinux。另請參閱 [基礎設施安全部分](../hosts/#run-selinux) 對 SELinux 的進一步討論。

AppArmor 和 SELinux 都與 Kubernetes 集成,但截至 Kubernetes 1.28 版本,AppArmor 配置檔案必須通過 [註釋](https://kubernetes.io/docs/tutorials/security/apparmor/#securing-a-pod) 指定,而 SELinux 標籤可以通過安全上下文中的 [SELinuxOptions](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/#selinuxoptions-v1-core) 字段直接設置。

與 seccomp 配置檔案一樣,上面提到的 Security Profiles Operator 可以協助將配置檔案部署到集群中的節點。(未來,該項目還旨在為 AppArmor 和 SELinux 生成配置檔案,就像它為 seccomp 所做的那樣。)

## 建議

### 使用 Amazon GuardDuty 監控執行時間並檢測對您的 EKS 環境的威脅

如果您目前沒有持續監控 EKS 運行時和分析 EKS 審計日誌、掃描惡意軟件和其他可疑活動的解決方案,Amazon 強烈建議希望以簡單、快速、安全、可擴展和經濟高效的一鍵式方式保護其 AWS 環境的客戶使用 [Amazon GuardDuty](https://aws.amazon.com/guardduty/)。Amazon GuardDuty 是一項安全監控服務,可分析和處理基礎數據源,例如 AWS CloudTrail 管理事件、AWS CloudTrail 事件日誌、VPC 流日誌(來自 Amazon EC2 實例)、Kubernetes 審計日誌和 DNS 日誌。它還包括 EKS 運行時監控。它使用不斷更新的威脅情報源(如惡意 IP 地址和域名列表),以及機器學習來識別您的 AWS 環境中意外、可能未經授權和惡意的活動。這可能包括權限提升、使用暴露的憑證或與惡意 IP 地址、域通信、您的 Amazon EC2 實例和 EKS 容器工作負載上存在惡意軟件,或發現可疑的 API 活動等問題。GuardDuty 通過在 GuardDuty 控制台或通過 Amazon EventBridge 生成安全發現來通知您 AWS 環境的狀態。GuardDuty 還支持將發現導出到 Amazon Simple Storage Service (S3) 存儲桶,並與其他服務(如 AWS Security Hub 和 Detective)集成。

觀看此 AWS 線上技術講座 ["Enhanced threat detection for Amazon EKS with Amazon GuardDuty - AWS Online Tech Talks"](https://www.youtube.com/watch?v=oNHGRRroJuE),了解如何分步在幾分鐘內啟用這些額外的 EKS 安全功能。

### 可選: 使用第三方解決方案進行運行時監控

如果您不熟悉 Linux 安全性,創建和管理 seccomp 和 Apparmor 配置檔案可能會很困難。如果您沒有時間成為專家,請考慮使用第三方商業解決方案。許多解決方案已經超越了靜態配置檔案(如 Apparmor 和 seccomp),並開始使用機器學習來阻止或警示可疑活動。其中一些解決方案可以在下面的 [工具](#tools-and-resources) 部分找到。更多選項可以在 [AWS Marketplace for Containers](https://aws.amazon.com/marketplace/features/containers) 上找到。

### 在編寫 seccomp 策略之前,請考慮添加/刪除 Linux 功能

功能涉及可通過系統調用訪問的內核函數中的各種檢查。如果檢查失敗,系統調用通常會返回錯誤。該檢查可以在特定系統調用的開頭立即執行,也可以在可能通過多個不同系統調用到達的內核中的更深層次執行(例如寫入特定的特權文件)。另一方面,seccomp 是一個應用於所有系統調用之前的系統調用過濾器。進程可以設置一個過濾器,允許它們撤銷運行某些系統調用或某些系統調用的特定參數的權限。

在使用 seccomp 之前,請考慮添加/刪除 Linux 功能是否可以為您提供所需的控制。有關進一步資訊,請參閱 [為容器設置功能](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container)。

### 查看是否可以通過使用 Pod 安全策略 (PSP) 來實現您的目標

Pod 安全策略提供了許多不同的方式來改善您的安全態勢,而不會引入過多的複雜性。在著手構建 seccomp 和 Apparmor 配置檔案之前,請探索 PSP 中提供的選項。

!!! warning
    從 Kubernetes 1.25 版本開始,PSP 已被刪除並替換為 [Pod 安全性許可控制器](https://kubernetes.io/docs/concepts/security/pod-security-admission/)。第三方替代方案包括 OPA/Gatekeeper 和 Kyverno。用於實現 PSP 中常見策略的 Gatekeeper 約束和約束模板集合可以從 GitHub 上的 [Gatekeeper 庫](https://github.com/open-policy-agent/gatekeeper-library/tree/master/library/pod-security-policy)存儲庫中提取。並且許多 PSP 的替代方案可以在 [Kyverno 策略庫](https://main.kyverno.io/policies/)中找到,包括完整的 [Pod 安全標準](https://kubernetes.io/docs/concepts/security/pod-security-standards/)集合。

## 工具和資源

- [在您開始之前應該知道的 7 件事](https://itnext.io/seccomp-in-kubernetes-part-i-7-things-you-should-know-before-you-even-start-97502ad6b6d6)
- [AppArmor Loader](https://github.com/kubernetes/kubernetes/tree/master/test/images/apparmor-loader)
- [使用配置檔案設置節點](https://kubernetes.io/docs/tutorials/clusters/apparmor/#setting-up-nodes-with-profiles)
- [Security Profiles Operator](https://github.com/kubernetes-sigs/security-profiles-operator) 是一個 Kubernetes 增強功能,旨在使用戶更容易在 Kubernetes 集群中使用 SELinux、seccomp 和 AppArmor。它提供了從運行中的工作負載生成配置檔案和將配置檔案載入 Kubernetes 節點以供 Pod 和容器使用的功能。
- [Inspektor Gadget](https://github.com/inspektor-gadget/inspektor-gadget) 允許檢查、跟踪和分析 Kubernetes 上許多運行時行為方面,包括協助生成 seccomp 配置檔案。
- [Aqua](https://www.aquasec.com/products/aqua-cloud-native-security-platform/)
- [Qualys](https://www.qualys.com/apps/container-security/)
- [Stackrox](https://www.stackrox.com/use-cases/threat-detection/)
- [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
- [Prisma](https://docs.paloaltonetworks.com/cn-series)
- [NeuVector by SUSE](https://www.suse.com/neuvector/) 開源零信任容器安全平台,提供進程配置檔案規則和文件訪問規則。
