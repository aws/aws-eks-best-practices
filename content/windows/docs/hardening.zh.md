# Windows 工作节点加固

操作系统加固是一种组合操作系统配置、打补丁和删除不必要的软件包的做法，旨在锁定系统并减少攻击面。最佳实践是根据公司的要求准备自己的 EKS 优化 Windows AMI 并进行加固配置。

AWS 每月都会提供一个新的 EKS 优化 Windows AMI，其中包含最新的 Windows Server 安全补丁。但是，无论使用自管理还是托管节点组，用户仍有责任通过应用必要的操作系统配置来加固其 AMI。

微软提供了一系列工具，如 [Microsoft Security Compliance Toolkit](https://www.microsoft.com/en-us/download/details.aspx?id=55319) 和 [Security Baselines](https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-security-baselines),可帮助您根据安全策略需求实现加固。在生产环境中，还应在 Amazon EKS 优化 Windows AMI 之上实施 [CIS 基准](https://learn.cisecurity.org/benchmarks?_gl=1*eoog69*_ga*MTgzOTM2NDE0My4xNzA0NDgwNTcy*_ga_3FW1B1JC98*MTcwNDQ4MDU3MS4xLjAuMTcwNDQ4MDU3MS4wLjAuMA..*_ga_N70Z2MKMD7*MTcwNDQ4MDU3MS4xLjAuMTcwNDQ4MDU3MS42MC4wLjA.)。

## 通过 Windows Server Core 减少攻击面

Windows Server Core 是 [EKS 优化 Windows AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html) 中提供的一种最小安装选项。部署 Windows Server Core 有几个好处。首先，它的磁盘占用空间相对较小，Server Core 为 6GB，而 Windows Server 桌面体验版为 10GB。其次，由于代码库和可用 API 较小，因此攻击面也较小。

无论 Amazon EKS 支持哪个版本，AWS 每月都会为客户提供新的 Amazon EKS 优化 Windows AMI，其中包含最新的 Microsoft 安全补丁。作为最佳实践，必须使用基于最新 Amazon EKS 优化 AMI 的新节点替换 Windows 工作节点。任何运行超过 45 天且未更新或未替换节点的做法都不符合安全最佳实践。

## 避免 RDP 连接

远程桌面协议 (RDP) 是一种由 Microsoft 开发的连接协议，用于为用户提供图形界面，以便通过网络连接到另一台 Windows 计算机。

作为最佳实践，您应将 Windows 工作节点视为临时主机。这意味着不允许管理连接、更新和故障排查。任何修改和更新都应作为新的自定义 AMI 实施，并通过更新自动伸缩组进行替换。请参阅**修补 Windows 服务器和容器**和**Amazon EKS 优化 Windows AMI 管理**。

在部署期间通过将 ssh 属性的值设置为 **false** 来禁用 Windows 节点上的 RDP 连接，如下例所示：

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

如果需要访问 Windows 节点，请使用 [AWS System Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) 通过 AWS 控制台和 SSM 代理建立安全的 PowerShell 会话。要了解如何实施此解决方案，请观看 [Securely Access Windows Instances Using AWS Systems Manager Session Manager](https://www.youtube.com/watch?v=nt6NTWQ-h6o)

为了使用 System Manager Session Manager，必须将附加 IAM 策略应用于用于启动 Windows 工作节点的 IAM 角色。下面是一个示例，其中在 `eksctl` 集群清单中指定了 **AmazonSSMManagedInstanceCore**:

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
> [Amazon Inspector](https://aws.amazon.com/inspector/) 是一种自动化安全评估服务，可帮助提高部署在 AWS 上的应用程序的安全性和合规性。Amazon Inspector 会自动评估应用程序是否存在暴露、漏洞和偏离最佳实践的情况。执行评估后，Amazon Inspector 会生成一份详细的安全发现列表，按严重级别排列优先级。您可以直接查看这些发现，也可以作为详细评估报告的一部分查看，这些报告可通过 Amazon Inspector 控制台或 API 获取。

可以使用 Amazon Inspector 在 Windows 工作节点上运行 CIS 基准评估，只需执行以下任务即可在 Windows Server Core 上安装它：

1. 下载以下 .exe 文件：
https://inspector-agent.amazonaws.com/windows/installer/latest/AWSAgentInstall.exe
2. 将代理传输到 Windows 工作节点。
3. 在 PowerShell 上运行以下命令以安装 Amazon Inspector 代理： `.\AWSAgentInstall.exe /install`

下面是首次运行后的输出。如您所见，它根据 [CVE](https://cve.mitre.org/) 数据库生成了发现结果。您可以使用这些结果来加固您的工作节点或基于加固配置创建 AMI。

![](./images/inspector-agent.png)

有关 Amazon Inspector 的更多信息，包括如何安装 Amazon Inspector 代理、设置 CIS 基准评估以及生成报告，请观看 [Improving the security and compliance of Windows Workloads with Amazon Inspector](https://www.youtube.com/watch?v=nIcwiJ85EKU) 视频。

## Amazon GuardDuty
> [Amazon GuardDuty](https://aws.amazon.com/guardduty/) 是一种威胁检测服务，可持续监控恶意活动和未经授权的行为，以保护您的 AWS 账户、工作负载和存储在 Amazon S3 中的数据。借助云，可以简化账户和网络活动的收集和聚合，但安全团队持续分析事件日志数据以查找潜在威胁可能会耗费大量时间。

通过使用 Amazon GuardDuty，您可以了解针对 Windows 工作节点的恶意活动，如 RDP 暴力破解和端口探测攻击。

观看 [Threat Detection for Windows Workloads using Amazon GuardDuty](https://www.youtube.com/watch?v=ozEML585apQ) 视频，了解如何在优化的 EKS Windows AMI 上实施和运行 CIS 基准。

## Amazon EC2 中的 Windows 安全性
阅读 [Security best practices for Amazon EC2 Windows instances](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2-security.html),以在每个层面实施安全控制。