# Amazon EKS 優化的 Windows AMI 管理
Windows Amazon EKS 優化的 AMI 是建立在 Windows Server 2019 和 Windows Server 2022 之上。它們被設定為作為 Amazon EKS 節點的基礎映像。預設情況下,AMI 包括以下元件:
- [kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)
- [kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/)
- [AWS IAM Authenticator for Kubernetes](https://github.com/kubernetes-sigs/aws-iam-authenticator)
- [csi-proxy](https://github.com/kubernetes-csi/csi-proxy)
- [containerd](https://containerd.io/)

您可以透過查詢 AWS Systems Manager Parameter Store API 以程式設計方式取得 Amazon EKS 優化 AMI 的 Amazon Machine Image (AMI) ID。此參數可消除您手動查詢 Amazon EKS 優化 AMI ID 的需求。有關 Systems Manager Parameter Store API 的更多資訊,請參閱 [GetParameter](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_GetParameter.html)。您的使用者帳戶必須擁有 ssm:GetParameter IAM 權限,才能取得 Amazon EKS 優化 AMI 的中繼資料。

以下範例會取得 Windows Server 2019 LTSC Core 最新 Amazon EKS 優化 AMI 的 AMI ID。AMI 名稱中列出的版本號與其準備的對應 Kubernetes 組建版本有關。

```bash    
aws ssm get-parameter --name /aws/service/ami-windows-latest/Windows_Server-2019-English-Core-EKS_Optimized-1.21/image_id --region us-east-1 --query "Parameter.Value" --output text
```

範例輸出:

```
ami-09770b3eec4552d4e
```

## 管理您自己的 Amazon EKS 優化 Windows AMI

對於生產環境而言,一個重要步驟是在 Amazon EKS 叢集中維持相同的 Amazon EKS 優化 Windows AMI 和 kubelet 版本。

在 Amazon EKS 叢集中使用相同版本可減少故障排除時間,並提高叢集一致性。[Amazon EC2 Image Builder](https://aws.amazon.com/image-builder/) 有助於建立和維護自訂的 Amazon EKS 優化 Windows AMI,以便在 Amazon EKS 叢集中使用。

使用 Amazon EC2 Image Builder 可選擇 Windows Server 版本、AWS Windows Server AMI 發行日期和/或 OS 組建版本。組建元件步驟可讓您選擇現有的 EKS 優化 Windows 構件以及 kubelet 版本。更多資訊:https://docs.aws.amazon.com/eks/latest/userguide/eks-custom-ami-windows.html

![](./images/build-components.png)

**注意:** 在選擇基礎映像之前,請先查閱 [Windows Server 版本和授權](licensing.md)一節,瞭解有關發行通道更新的重要詳細資訊。

## 為自訂 EKS 優化 AMI 設定更快的啟動速度 ##

使用自訂 Windows Amazon EKS 優化 AMI 時,可以透過啟用 Fast Launch 功能,使 Windows 工作節點的啟動速度提高高達 65%。此功能維護一組已完成 _Sysprep specialize_、_Windows Out of Box Experience (OOBE)_ 步驟和所需重新啟動的預先佈建快照。這些快照隨後將用於後續啟動,從而減少擴展或替換節點的時間。Fast Launch 僅可透過 EC2 主控台或在 AWS CLI 中為 *您擁有的* AMI 啟用,並且可配置維護的快照數量。

**注意:** Fast Launch 與預設的 Amazon 提供的 EKS 優化 AMI 不相容,請先建立上述自訂 AMI,然後再嘗試啟用它。
 
更多資訊: [AWS Windows AMIs - 設定您的 AMI 以更快啟動](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/windows-ami-version-history.html#win-ami-config-fast-launch)

## 在自訂 AMI 上快取 Windows 基礎層 ##

Windows 容器映像比 Linux 映像大。如果您正在運行任何基於 .NET Framework 的容器化應用程式,平均映像大小約為 8.24GB。在 pod 調度期間,必須在磁碟中完全拉取和解壓縮容器映像,然後 pod 才能達到 Running 狀態。

在此過程中,容器運行時 (containerd) 會並行拉取和解壓縮磁碟中的整個容器映像。拉取操作是一個並行過程,這意味著容器運行時會並行拉取容器映像層。相反,解壓縮操作是一個順序過程,而且是 I/O 密集型的。因此,容器映像可能需要超過 8 分鐘才能完全解壓縮並準備好供容器運行時 (containerd) 使用,結果是 pod 啟動時間可能需要數分鐘。

如 **修補 Windows Server 和容器** 主題所述,在準備 AMI 時,有一個選項可以使用 EKS 建立自訂 AMI。在 AMI 準備期間,您可以添加一個額外的 EC2 Image builder 元件,在本地拉取所有必需的 Windows 容器映像,然後生成 AMI。這種策略將大大減少 pod 達到 **Running** 狀態所需的時間。

在 Amazon EC2 Image Builder 上,建立一個 [元件](https://docs.aws.amazon.com/imagebuilder/latest/userguide/manage-components.html) 來下載必需的映像,並將其附加到映像配方。以下示例從 ECR 存放庫拉取特定映像。

```
name: ContainerdPull
description: 此元件拉取快取策略所需的容器映像。
schemaVersion: 1.0

phases:
  - name: build
    steps:
      - name: containerdpull
        action: ExecutePowerShell
        inputs:
          commands:
            - Set-ExecutionPolicy Unrestricted -Force
            - (Get-ECRLoginCommand).Password | docker login --username AWS --password-stdin 111000111000.dkr.ecr.us-east-1.amazonaws.com
            - ctr image pull mcr.microsoft.com/dotnet/framework/aspnet:latest
            - ctr image pull 111000111000.dkr.ecr.us-east-1.amazonaws.com/myappcontainerimage:latest
```

要確保以下元件能正常工作,請檢查 EC2 Image builder 使用的 IAM 角色 (EC2InstanceProfileForImageBuilder) 是否附加了以下政策:

![](./images/permissions-policies.png)

## 部落格文章 ##
在以下部落格文章中,您將找到如何為自訂 Amazon EKS Windows AMI 實現快取策略的分步指南:

[使用 EC2 Image builder 和映像快取策略加速 Windows 容器啟動時間](https://aws.amazon.com/blogs/containers/speeding-up-windows-container-launch-times-with-ec2-image-builder-and-image-cache-strategy/)