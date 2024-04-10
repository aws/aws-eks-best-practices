# 執行異質工作負載¶

Kubernetes 支援異質叢集,您可以在同一個叢集中混合使用 Linux 和 Windows 節點。在該叢集中,您可以混合使用在 Linux 上運行的 Pod 和在 Windows 上運行的 Pod。您甚至可以在同一個叢集中運行多個版本的 Windows。但是,在做出這個決定時,需要考慮一些因素(如下所述)。

# 將 POD 分配給節點的最佳實踐

為了將 Linux 和 Windows 工作負載保留在各自的特定操作系統節點上,您需要使用節點選擇器和污點/容忍度的組合。在異質環境中調度工作負載的主要目標是避免破壞現有 Linux 工作負載的兼容性。

## 確保特定操作系統的工作負載落在適當的容器主機上

使用者可以使用 nodeSelectors 確保 Windows 容器可以在適當的主機上調度。今天所有的 Kubernetes 節點都有以下默認標籤:

    kubernetes.io/os = [windows|linux]
    kubernetes.io/arch = [amd64|arm64|...]

如果 Pod 規範不包含像 ``"kubernetes.io/os": windows`` 這樣的 nodeSelector,則該 Pod 可能會被調度到任何主機,無論是 Windows 還是 Linux。這可能會有問題,因為 Windows 容器只能在 Windows 上運行,而 Linux 容器只能在 Linux 上運行。

在企業環境中,擁有大量現有的 Linux 容器部署以及現成的配置生態系統(如 Helm 圖表)是很常見的。在這種情況下,您可能不願意更改部署的 nodeSelectors。**替代方案是使用污點**。

例如: `--register-with-taints='os=windows:NoSchedule'`

如果您正在使用 EKS,eksctl 提供了通過 clusterConfig 應用污點的方式:

```yaml
NodeGroups:
  - name: windows-ng
    amiFamily: WindowsServer2022FullContainer
    ...
    labels:
      nodeclass: windows2022
    taints:
      os: "windows:NoSchedule"
```

為所有 Windows 節點添加污點,調度器將不會將 Pod 調度到這些節點,除非它們容忍該污點。Pod 清單示例:

```yaml
nodeSelector:
    kubernetes.io/os: windows
tolerations:
    - key: "os"
      operator: "Equal"
      value: "windows"
      effect: "NoSchedule"
```

## 在同一個叢集中處理多個 Windows 版本

每個 Pod 使用的 Windows 容器基礎映像必須與節點的相同內核版本匹配。如果您想在同一個叢集中使用多個 Windows Server 版本,那麼您應該設置額外的節點標籤、nodeSelectors 或利用名為 **windows-build** 的標籤。

Kubernetes 1.17 自動為 Windows 節點添加了一個新的標籤 **node.kubernetes.io/windows-build**,以簡化同一個叢集中多個 Windows 版本的管理。如果您正在運行較舊的版本,則建議手動為 Windows 節點添加此標籤。

該標籤反映了需要匹配以實現兼容性的 Windows 主版本號、次版本號和版本號。下面是今天每個 Windows Server 版本使用的值。

重要的是要注意,Windows Server 正在將 Long-Term Servicing Channel (LTSC) 作為主要發佈渠道。Windows Server Semi-Annual Channel (SAC) 已於 2022 年 8 月 9 日停止。將不會有未來的 Windows Server SAC 版本。


| 產品名稱 | 版本號 |
| -------- | -------- |
| Server full 2022 LTSC    | 10.0.20348    |
| Server core 2019 LTSC    | 10.0.17763    |

可以通過以下命令檢查操作系統版本號:

```bash    
kubectl get nodes -o wide
```

KERNEL-VERSION 輸出與 Windows 操作系統版本號匹配。

```bash 
NAME                          STATUS   ROLES    AGE   VERSION                INTERNAL-IP   EXTERNAL-IP     OS-IMAGE                         KERNEL-VERSION                  CONTAINER-RUNTIME
ip-10-10-2-235.ec2.internal   Ready    <none>   23m   v1.24.7-eks-fb459a0    10.10.2.235   3.236.30.157    Windows Server 2022 Datacenter   10.0.20348.1607                 containerd://1.6.6
ip-10-10-31-27.ec2.internal   Ready    <none>   23m   v1.24.7-eks-fb459a0    10.10.31.27   44.204.218.24   Windows Server 2019 Datacenter   10.0.17763.4131                 containerd://1.6.6
ip-10-10-7-54.ec2.internal    Ready    <none>   31m   v1.24.11-eks-a59e1f0   10.10.7.54    3.227.8.172     Amazon Linux 2                   5.10.173-154.642.amzn2.x86_64   containerd://1.6.19
```

下面的示例將額外的 nodeSelector 應用於 Pod 清單,以便在運行不同 Windows 節點組操作系統版本時匹配正確的 Windows 版本號。

```yaml
nodeSelector:
    kubernetes.io/os: windows
    node.kubernetes.io/windows-build: '10.0.20348'
tolerations:
    - key: "os"
    operator: "Equal"
    value: "windows"
    effect: "NoSchedule"
```

## 使用 RuntimeClass 簡化 Pod 清單中的 NodeSelector 和 Toleration

您還可以使用 RuntimeClass 來簡化使用污點和容忍度的過程。這可以通過創建一個 RuntimeClass 對象來實現,該對象用於封裝這些污點和容忍度。

通過運行以下清單創建一個 RuntimeClass:

```yaml
apiVersion: node.k8s.io/v1beta1
kind: RuntimeClass
metadata:
  name: windows-2022
handler: 'docker'
scheduling:
  nodeSelector:
    kubernetes.io/os: 'windows'
    kubernetes.io/arch: 'amd64'
    node.kubernetes.io/windows-build: '10.0.20348'
  tolerations:
  - effect: NoSchedule
    key: os
    operator: Equal
    value: "windows"
```

一旦創建了 Runtimeclass,就可以在 Pod 清單中將其指定為 Spec:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iis-2022
  labels:
    app: iis-2022
spec:
  replicas: 1
  template:
    metadata:
      name: iis-2022
      labels:
        app: iis-2022
    spec:
      runtimeClassName: windows-2022
      containers:
      - name: iis
```

## 托管節點組支持
為了幫助客戶以更流暢的方式運行其 Windows 應用程序,AWS 於 2022 年 12 月 15 日推出了對 Amazon [EKS 托管節點組 (MNG) 支持 Windows 容器](https://aws.amazon.com/about-aws/whats-new/2022/12/amazon-eks-automated-provisioning-lifecycle-management-windows-containers/)的支持。為了幫助統一運營團隊,[Windows MNG](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 使用與 [Linux MNG](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 相同的工作流和工具啟用。支持 Windows Server 2019 和 2022 的完整和核心 AMI (Amazon Machine Image) 版本。

以下 AMI 系列支持托管節點組 (MNG):

| AMI 系列 |
| ---------   | 
| WINDOWS_CORE_2019_x86_64    | 
| WINDOWS_FULL_2019_x86_64    | 
| WINDOWS_CORE_2022_x86_64    | 
| WINDOWS_FULL_2022_x86_64    | 

## 其他文檔


AWS 官方文檔:
https://docs.aws.amazon.com/eks/latest/userguide/windows-support.html

要更好地理解 Pod 網絡 (CNI) 的工作原理,請查看以下鏈接: https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html

AWS 關於在 EKS 上部署 Windows 托管節點組的博客:
https://aws.amazon.com/blogs/containers/deploying-amazon-eks-windows-managed-node-groups/