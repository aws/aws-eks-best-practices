# Pod 安全性上下文

**Pod 安全政策 (PSP)** 和 **Pod 安全標準 (PSS)** 是在 Kubernetes 中實施安全性的兩種主要方式。請注意,從 Kubernetes v1.21 開始,PodSecurityPolicy 已被棄用,並將在 v1.25 中被移除,而 Pod 安全標準 (PSS) 是 Kubernetes 推薦用於實施安全性的方法。

Pod 安全政策 (PSP) 是 Kubernetes 中實施安全政策的原生解決方案。PSP 是一種集群級別的資源,用於控制 Pod 規格的安全敏感方面。使用 Pod 安全政策,您可以定義一組 Pod 必須滿足的條件,才能被集群接受。
PSP 功能從 Kubernetes 的早期就已經存在,旨在阻止錯誤配置的 Pod 在給定集群上被創建。

有關 Pod 安全政策的更多資訊,請參閱 Kubernetes [文檔](https://kubernetes.io/docs/concepts/policy/pod-security-policy/)。根據 [Kubernetes 棄用政策](https://kubernetes.io/docs/reference/using-api/deprecation-policy/),在功能被棄用後的九個月,舊版本將停止獲得支援。

另一方面,Pod 安全標準 (PSS) 是推薦的安全方法,通常使用安全上下文在 Pod 清單中的 Pod 和容器規格中定義。PSS 是 Kubernetes 項目團隊定義的官方標準,用於解決 Pod 的安全相關最佳實踐。它定義了諸如基線 (最小限制性,預設)、特權 (無限制) 和受限 (最嚴格) 等政策。

我們建議從基線配置文件開始。PSS 基線配置文件在安全性和潛在阻力之間提供了良好的平衡,只需要最少的例外清單,它是工作負載安全的良好起點。如果您目前正在使用 PSP,我們建議切換到 PSS。有關 PSS 政策的更多詳細資訊,可以在 Kubernetes [文檔](https://kubernetes.io/docs/concepts/security/pod-security-standards/)中找到。這些政策可以使用多種工具來實施,包括來自 [OPA](https://www.openpolicyagent.org/) 和 [Kyverno](https://kyverno.io/) 的工具。例如,Kyverno 提供了完整的 PSS 政策集合,可在[這裡](https://kyverno.io/policies/pod-security/)找到。

安全上下文設置允許您為選定的進程授予特權、使用程序配置文件來限制單個程序的功能、允許權限提升、過濾系統調用等。

在安全上下文方面,Kubernetes 中的 Windows Pod 與標準的基於 Linux 的工作負載相比存在一些限制和區別。

Windows 使用每個容器的作業對象和系統命名空間過濾器來包含容器中的所有進程,並從主機中邏輯隔離。沒有辦法在沒有命名空間過濾的情況下運行 Windows 容器。這意味著系統特權無法在主機上下文中被斷言,因此在 Windows 上不提供特權容器。

以下 `windowsOptions` 是唯一記錄的 [Windows 安全上下文選項](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#windowssecuritycontextoptions-v1-core),而其餘則是一般的 [安全上下文選項](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.21/#securitycontext-v1-core)

有關在 Windows 與 linux 中支援的安全上下文屬性清單,請參閱官方文檔[這裡](https://kubernetes.io/docs/setup/production-environment/windows/_print/#v1-container)。

Pod 特定設置適用於所有容器。如果未指定,將使用 PodSecurityContext 中的選項。如果在 SecurityContext 和 PodSecurityContext 中都設置了,則 SecurityContext 中指定的值優先。

例如,Pod 和容器的 runAsUserName 設置是 Windows 選項,大致相當於 Linux 特定的 runAsUser 設置,在以下清單中,Pod 特定的安全上下文應用於所有容器

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: run-as-username-pod-demo
spec:
  securityContext:
    windowsOptions:
      runAsUserName: "ContainerUser"
  containers:
  - name: run-as-username-demo
    ...
  nodeSelector:
    kubernetes.io/os: windows
```

而在以下情況下,容器級別的安全上下文覆蓋了 Pod 級別的安全上下文。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: run-as-username-container-demo
spec:
  securityContext:
    windowsOptions:
      runAsUserName: "ContainerUser"
  containers:
  - name: run-as-username-demo
    ..
    securityContext:
        windowsOptions:
            runAsUserName: "ContainerAdministrator"
  nodeSelector:
    kubernetes.io/os: windows
```

runAsUserName 字段的可接受值示例:ContainerAdministrator、ContainerUser、NT AUTHORITY\NETWORK SERVICE、NT AUTHORITY\LOCAL SERVICE

通常,對於 Windows Pod 來說,使用 ContainerUser 運行容器是一個好主意。用戶不在容器和主機之間共享,但 ContainerAdministrator 確實在容器內擁有額外的特權。請注意,需要注意一些用戶名[限制](https://kubernetes.io/docs/tasks/configure-pod-container/configure-runasusername/#windows-username-limitations)。

使用 ContainerAdministrator 的一個好例子是設置 PATH。您可以使用 USER 指令來實現,如下所示:

```bash
USER ContainerAdministrator
RUN setx /M PATH "%PATH%;C:/your/path"
USER ContainerUser
```

另請注意,秘密以明文形式寫入節點的卷 (與 linux 上的 tmpfs/內存不同)。這意味著您必須做兩件事

* 使用文件 ACL 來保護秘密文件位置
* 使用 [BitLocker](https://docs.microsoft.com/en-us/windows/security/information-protection/bitlocker/bitlocker-how-to-deploy-on-windows-server) 進行卷級加密