# Windows 網路

## Windows 容器網路概述
Windows 容器與 Linux 容器有根本的不同。Linux 容器使用 Linux 構造如命名空間、聯合檔案系統和 cgroup。在 Windows 上，這些構造由 [Host Compute Service (HCS)](https://github.com/microsoft/hcsshim) 從 containerd 抽象化。HCS 充當位於 Windows 上容器實現之上的 API 層。Windows 容器還利用 Host Network Service (HNS) 來定義節點上的網路拓撲。

![](./images/windows-networking.png)

從網路角度來看，HCS 和 HNS 使 Windows 容器的功能類似於虛擬機器。例如，每個容器都有一個連接到 Hyper-V 虛擬交換機 (vSwitch) 的虛擬網路介面卡 (vNIC)，如上圖所示。

## IP 位址管理
Amazon EKS 中的節點使用其彈性網路介面 (ENI) 連接到 AWS VPC 網路。目前 **僅支援每個 Windows 工作節點一個 ENI**。Windows 節點的 IP 位址管理由在控制平面中運行的 [VPC Resource Controller](https://github.com/aws/amazon-vpc-resource-controller-k8s) 執行。有關 Windows 節點 IP 位址管理工作流程的更多詳細資訊，可以在[這裡](https://github.com/aws/amazon-vpc-resource-controller-k8s#windows-ipv4-address-management)找到。

Windows 工作節點可以支援的 Pod 數量取決於節點的大小和可用的 IPv4 位址數量。您可以按如下方式計算節點上可用的 IPv4 位址:
- 預設情況下，只會將次要 IPv4 位址分配給 ENI。在這種情況下:
  ```
  可用於 Pod 的總 IPv4 位址數 = 主要介面中支援的 IPv4 位址數 - 1
  ```
  我們從總數中減去 1，因為一個 IPv4 位址將用作 ENI 的主要位址，因此無法分配給 Pod。

- 如果集群已配置為通過啟用 [prefix delegation 功能](../../networking/prefix-mode/index_windows.md)來實現高 Pod 密度，則-
  ```
  可用於 Pod 的總 IPv4 位址數 = (主要介面中支援的 IPv4 位址數 - 1) * 16
  ```
  在這裡，VPC Resource Controller 將分配 `/28 前綴`而不是分配次要 IPv4 位址，因此可用的 IPv4 位址總數將增加 16 倍。

使用上面的公式，我們可以根據 m5.large 實例計算 Windows 工作節點的最大 Pod 數量如下:
- 預設情況下，在次要 IP 模式下運行時-
  ```
  每個 ENI 10 個次要 IPv4 位址 - 1 = 9 個可用 IPv4 位址
  ```
- 使用 `prefix delegation` 時-
  ```
  (每個 ENI 10 個次要 IPv4 位址 - 1) * 16 = 144 個可用 IPv4 位址
  ```

有關每種實例類型可以支援多少 IP 位址的更多資訊，請參閱 [每種實例類型的網路介面的 IP 位址數](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI)。

---

另一個關鍵考慮因素是網路流量的流向。對於 Windows，如果節點上有超過 100 個服務，就存在端口耗盡的風險。出現這種情況時，節點將開始拋出帶有以下消息的錯誤:

**"Policy creation failed: hcnCreateLoadBalancer failed in Win32: The specified port already exists."**

為了解決這個問題，我們利用直接服務器返回 (Direct Server Return, DSR)。DSR 是非對稱網路負載分佈的一種實現。換句話說，請求和響應流量使用不同的網路路徑。這個功能加快了 Pod 之間的通信，並降低了端口耗盡的風險。因此，我們建議在 Windows 節點上啟用 DSR。

Windows Server SAC EKS 優化 AMI 預設啟用了 DSR。對於 Windows Server 2019 LTSC EKS 優化 AMI，您需要在實例配置期間使用下面的腳本啟用它，並在 `eksctl` nodeGroup 中使用 Windows Server 2019 Full 或 Core 作為 amiFamily。有關詳細資訊，請參閱 [eksctl custom AMI](https://eksctl.io/usage/custom-ami-support/)。

```yaml
nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2019CoreContainer
  ssh:
    allow: false
```
為了在 Windows Server 2019 及更高版本中使用 DSR，您需要在實例啟動期間指定以下 [**kube-proxy**](https://kubernetes.io/docs/setup/production-environment/windows/intro-windows-in-kubernetes/#load-balancing-and-services) 標誌。您可以通過調整與 [自行管理節點組啟動模板](https://docs.aws.amazon.com/eks/latest/userguide/launch-windows-workers.html) 關聯的 userdata 腳本來實現這一點。

```powershell
<powershell>
[string]$EKSBinDir = "$env:ProgramFiles\Amazon\EKS"
[string]$EKSBootstrapScriptName = 'Start-EKSBootstrap.ps1'
[string]$EKSBootstrapScriptFile = "$EKSBinDir\$EKSBootstrapScriptName"
(Get-Content $EKSBootstrapScriptFile).replace('"--proxy-mode=kernelspace",', '"--proxy-mode=kernelspace", "--feature-gates WinDSR=true", "--enable-dsr",') | Set-Content $EKSBootstrapScriptFile 
& $EKSBootstrapScriptFile -EKSClusterName "eks-windows" -APIServerEndpoint "https://<REPLACE-EKS-CLUSTER-CONFIG-API-SERVER>" -Base64ClusterCA "<REPLACE-EKSCLUSTER-CONFIG-DETAILS-CA>" -DNSClusterIP "172.20.0.10" -KubeletExtraArgs "--node-labels=alpha.eksctl.io/cluster-name=eks-windows,alpha.eksctl.io/nodegroup-name=windows-ng-ltsc2019 --register-with-taints=" 3>&1 4>&1 5>&1 6>&1
</powershell>
```

可以按照 [Microsoft Networking 博客](https://techcommunity.microsoft.com/t5/networking-blog/direct-server-return-dsr-in-a-nutshell/ba-p/693710) 和 [Windows Containers on AWS Lab](https://catalog.us-east-1.prod.workshops.aws/workshops/1de8014a-d598-4cb5-a119-801576492564/en-US/module1-eks/lab3-handling-mixed-clusters) 中的說明來驗證 DSR 的啟用情況。

![](./images/dsr.png)

## 容器網路介面 (CNI) 選項
AWSVPC CNI 是 Windows 和 Linux 工作節點的事實上的 CNI 插件。儘管 AWSVPC CNI 滿足了許多客戶的需求，但有時您可能需要考慮使用覆蓋網路等替代方案來避免 IP 耗盡。在這種情況下，可以使用 Calico CNI 代替 AWSVPC CNI。[Project Calico](https://www.projectcalico.org/) 是由 [Tigera](https://www.tigera.io/) 開發的開源軟體。該軟體包括一個與 EKS 兼容的 CNI。有關在 EKS 中安裝 Calico CNI 的說明，可以在 [Project Calico EKS 安裝](https://docs.projectcalico.org/getting-started/kubernetes/managed-public-cloud/eks) 頁面上找到。

## 網路策略
將 Kubernetes 集群上的 Pod 之間的默認開放通信模式更改為基於網路策略限制訪問被認為是最佳實踐。開源的 [Project Calico](https://www.tigera.io/tigera-products/calico/) 對於與 Linux 和 Windows 節點兼容的網路策略有很好的支援。這個功能與使用 Calico CNI 是分開的，不依賴於它。因此，我們建議安裝 Calico 並使用它進行網路策略管理。

有關在 EKS 中安裝 Calico 的說明，可以在 [在 Amazon EKS 上安裝 Calico](https://docs.aws.amazon.com/eks/latest/userguide/calico.html) 頁面上找到。

此外，[Amazon EKS 安全最佳實踐指南 - 網路部分](https://aws.github.io/aws-eks-best-practices/security/docs/network/) 中提供的建議同樣適用於包含 Windows 工作節點的 EKS 集群，但目前 Windows 不支援某些功能如 "Pod 的安全組"。