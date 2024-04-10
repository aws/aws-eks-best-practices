# Windows 工作節點強化

OS 強化是一種結合 OS 配置、修補和移除不必要的軟件包的組合,旨在鎖定系統並減少攻擊面。最佳做法是準備自己的 EKS 優化 Windows AMI,其中包含公司所需的強化配置。

AWS 每月提供一個新的 EKS 優化 Windows AMI,其中包含最新的 Windows Server 安全補丁。但是,無論使用自行管理還是受管節點組,用戶仍有責任通過應用必要的 OS 配置來強化其 AMI。

Microsoft 提供了一系列工具,如 [Microsoft Security Compliance Toolkit](https://www.microsoft.com/en-us/download/details.aspx?id=55319) 和 [Security Baselines](https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-security-baselines),可根據您的安全政策需求實現強化。[CIS 基準](https://learn.cisecurity.org/benchmarks?_gl=1*eoog69*_ga*MTgzOTM2NDE0My4xNzA0NDgwNTcy*_ga_3FW1B1JC98*MTcwNDQ4MDU3MS4xLjAuMTcwNDQ4MDU3MS4wLjAuMA..*_ga_N70Z2MKMD7*MTcwNDQ4MDU3MS4xLjAuMTcwNDQ4MDU3MS42MC4wLjA.) 也可用,並且應在生產環境中在 Amazon EKS 優化 Windows AMI 之上實現。

## 使用 Windows Server Core 減少攻擊面

Windows Server Core 是 [EKS 優化 Windows AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html) 中可用的最小安裝選項。部署 Windows Server Core 有幾個好處。首先,它的磁盤佔用空間相對較小,Server Core 上為 6GB,而 Windows Server 上的桌面體驗為 10GB。其次,由於其較小的代碼庫和可用 API,它具有較小的攻擊面。

無論 Amazon EKS 支持的版本如何,AWS 每月都會為客戶提供新的 Amazon EKS 優化 Windows AMI,其中包含最新的 Microsoft 安全補丁。作為最佳做法,必須使用基於最新 Amazon EKS 優化 AMI 的新節點替換 Windows 工作節點。任何在沒有更新或節點替換的情況下運行超過 45 天的節點都缺乏安全最佳做法。

## 避免 RDP 連接

遠程桌面協議 (RDP) 是 Microsoft 開發的一種連接協議,用於為用戶提供圖形界面,以通過網絡連接到另一台 Windows 計算機。

作為最佳做法,您應將 Windows 工作節點視為臨時主機。這意味著沒有管理連接、更新或故障排除。任何修改和更新都應作為新的自定義 AMI 實現,並通過更新自動擴展組進行替換。請參閱 **修補 Windows 服務器和容器** 和 **Amazon EKS 優化 Windows AMI 管理**。

在部署期間通過將 ssh 屬性的值設置為 **false** 來禁用 Windows 節點上的 RDP 連接,如下例所示:

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

如果需要訪問 Windows 節點,請使用 [AWS System Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) 通過 AWS 控制台和 SSM 代理建立安全的 PowerShell 會話。要查看如何實現該解決方案,請觀看 [使用 AWS Systems Manager Session Manager 安全訪問 Windows 實例](https://www.youtube.com/watch?v=nt6NTWQ-h6o)

為了使用 System Manager Session Manager,必須將附加 IAM 策略應用於用於啟動 Windows 工作節點的 IAM 角色。以下是一個示例,其中 **AmazonSSMManagedInstanceCore** 在 `eksctl` 集群清單中指定:

```yaml
 nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2019CoreContainer
  ssh:
    allow: false
  iam:
    attachPolicyARNs:
      - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
      - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
      - arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess
      - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
      - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
```

## Amazon Inspector
> [Amazon Inspector](https://aws.amazon.com/inspector/) 是一種自動化安全評估服務,可幫助提高部署在 AWS 上的應用程序的安全性和合規性。Amazon Inspector 會自動評估應用程序的暴露、漏洞和偏離最佳做法的情況。執行評估後,Amazon Inspector 會生成一份詳細的安全發現列表,按嚴重程度級別進行優先級排序。可以直接查看這些發現,或者作為詳細評估報告的一部分,通過 Amazon Inspector 控制台或 API 獲取。

可以使用 Amazon Inspector 在 Windows 工作節點上運行 CIS 基準評估,並且可以通過執行以下任務在 Windows Server Core 上安裝:

1. 下載以下 .exe 文件:
https://inspector-agent.amazonaws.com/windows/installer/latest/AWSAgentInstall.exe
2. 將代理傳輸到 Windows 工作節點。
3. 在 PowerShell 上運行以下命令來安裝 Amazon Inspector 代理: `.\AWSAgentInstall.exe /install`

以下是第一次運行後的輸出。如您所見,它根據 [CVE](https://cve.mitre.org/) 數據庫生成了發現。您可以使用它來強化您的工作節點或基於強化配置創建 AMI。

![](./images/inspector-agent.png)

有關 Amazon Inspector 的更多信息,包括如何安裝 Amazon Inspector 代理、設置 CIS 基準評估和生成報告,請觀看 [使用 Amazon Inspector 改善 Windows 工作負載的安全性和合規性](https://www.youtube.com/watch?v=nIcwiJ85EKU) 視頻。

## Amazon GuardDuty
> [Amazon GuardDuty](https://aws.amazon.com/guardduty/) 是一種威脅檢測服務,可持續監控惡意活動和未經授權的行為,以保護您的 AWS 帳戶、工作負載和存儲在 Amazon S3 中的數據。在雲中,收集和聚合帳戶和網絡活動變得簡單,但安全團隊持續分析事件日誌數據以查找潛在威脅可能是耗時的。

通過使用 Amazon GuardDuty,您可以看到針對 Windows 工作節點的惡意活動,如 RDP 暴力破解和端口探測攻擊。

觀看 [使用 Amazon GuardDuty 對 Windows 工作負載進行威脅檢測](https://www.youtube.com/watch?v=ozEML585apQ) 視頻,了解如何在優化的 EKS Windows AMI 上實現和運行 CIS 基準

## Amazon EC2 中的 Windows 安全性
閱讀 [Amazon EC2 Windows 實例的安全最佳做法](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2-security.html),在每一層實現安全控制。
