# 避免 OOM 錯誤

Windows 沒有像 Linux 那樣的記憶體耗盡處理程序殺手。Windows 一直將所有使用者模式記憶體分配視為虛擬的,而且頁面檔案是強制性的。淨效果是 Windows 不會像 Linux 那樣達到記憶體耗盡的情況。進程將換頁到磁碟而不是被記憶體耗盡 (OOM) 終止。如果記憶體超額供應並且所有實體記憶體都已耗盡,則換頁可能會降低性能。

## 保留系統和 kubelet 記憶體
與 Linux 不同,在 Linux 中 `--kubelet-reserve` **捕獲** kubernetes 系統守護程序(如 kubelet、容器運行時等)的資源保留,而 `--system-reserve` **捕獲** 作業系統系統守護程序(如 sshd、udev 等)的資源保留。在 **Windows** 上,這些標誌不會 **捕獲** 和 **設置** **kubelet** 或節點上運行的 **進程** 的記憶體限制。

不過,您可以結合這些標誌來管理 **NodeAllocatable**,以減少節點上的容量,並使用 Pod 清單 **記憶體資源限制** 來控制每個 Pod 的記憶體分配。使用這種策略,您可以更好地控制記憶體分配,並最小化 Windows 節點上的記憶體耗盡 (OOM)。

在 Windows 節點上,最佳做法是至少為作業系統和進程保留 2GB 的記憶體。使用 `--kubelet-reserve` 和/或 `--system-reserve` 來減少 NodeAllocatable。

根據 [Amazon EKS 自管理 Windows 節點](https://docs.aws.amazon.com/eks/latest/userguide/launch-windows-workers.html)文檔,使用 CloudFormation 模板啟動新的 Windows 節點組,並自定義 kubelet 配置。CloudFormation 有一個名為 `BootstrapArguments` 的元素,與 `KubeletExtraArgs` 相同。使用以下標誌和值:

```bash
--kube-reserved memory=0.5Gi,ephemeral-storage=1Gi --system-reserved memory=1.5Gi,ephemeral-storage=1Gi --eviction-hard memory.available<200Mi,nodefs.available<10%"
```

如果是使用 eksctl 進行部署,請查看以下文檔以自定義 kubelet 配置 https://eksctl.io/usage/customizing-the-kubelet/

## Windows 容器記憶體需求
根據 [Microsoft 文檔](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/system-requirements),NANO 的 Windows Server 基礎映像至少需要 30MB,而 Server Core 則需要 45MB。隨著添加 Windows 組件(如 .NET Framework、Web 服務如 IIS 和應用程序),這些數字會增加。

了解您的 Windows 容器映像所需的最小記憶體量(即基礎映像加上其應用層)並在 Pod 規範中將其設置為容器的資源/請求是很重要的。您還應該設置一個限制,以防止 Pod 在應用程序問題的情況下消耗所有可用的節點記憶體。

在下面的示例中,當 Kubernetes 調度器嘗試將 Pod 放置在節點上時,Pod 的請求將用於確定哪個節點有足夠的可用資源進行調度。

```yaml
 spec:
  - name: iis
    image: mcr.microsoft.com/windows/servercore/iis:windowsservercore-ltsc2019
    resources:
      limits:
        cpu: 1
        memory: 800Mi
      requests:
        cpu: .1
        memory: 128Mi
```

## 結論

使用這種方法可以最小化記憶體耗盡的風險,但不能防止它發生。使用 Amazon CloudWatch Metrics,您可以設置警報和補救措施,以防記憶體耗盡發生。