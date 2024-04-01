# Windows 网络

## Windows 容器网络概述
Windows 容器与 Linux 容器有根本的不同。Linux 容器使用 Linux 构造，如命名空间、联合文件系统和 cgroups。在 Windows 上，这些构造由 [Host Compute Service (HCS)](https://github.com/microsoft/hcsshim) 从 containerd 抽象出来。HCS 充当位于 Windows 上容器实现之上的 API 层。Windows 容器还利用了 Host Network Service (HNS)，它定义了节点上的网络拓扑。

![](./images/windows-networking.png)

从网络角度来看，HCS 和 HNS 使 Windows 容器的功能类似于虚拟机。例如，如上图所示，每个容器都有一个连接到 Hyper-V 虚拟交换机 (vSwitch) 的虚拟网络适配器 (vNIC)。

## IP 地址管理
Amazon EKS 中的节点使用其弹性网络接口 (ENI) 连接到 AWS VPC 网络。目前，**每个 Windows 工作节点仅支持一个 ENI**。Windows 节点的 IP 地址管理由运行在控制平面上的 [VPC Resource Controller](https://github.com/aws/amazon-vpc-resource-controller-k8s) 执行。有关 Windows 节点 IP 地址管理工作流程的更多详细信息，可以在[这里](https://github.com/aws/amazon-vpc-resource-controller-k8s#windows-ipv4-address-management)找到。

Windows 工作节点可以支持的 Pod 数量取决于节点的大小和可用 IPv4 地址的数量。您可以按如下方式计算节点上可用的 IPv4 地址：
- 默认情况下，只会为 ENI 分配辅助 IPv4 地址。在这种情况下：
  ```
  可用于 Pod 的总 IPv4 地址数 = 主接口支持的 IPv4 地址数 - 1
  ```
  我们从总数中减去 1，因为一个 IPv4 地址将用作 ENI 的主地址，因此无法分配给 Pod。

- 如果集群已配置为通过启用 [前缀委派功能](../../networking/prefix-mode/index_windows.md) 实现高 Pod 密度，则-
  ```
  可用于 Pod 的总 IPv4 地址数 = (主接口支持的 IPv4 地址数 - 1) * 16
  ```
  在这里，VPC Resource Controller 将分配 `/28 前缀`而不是分配辅助 IPv4 地址，因此可用的 IPv4 地址总数将增加 16 倍。

使用上面的公式，我们可以根据 m5.large 实例计算 Windows 工作节点的最大 Pod 数量如下：
- 默认情况下，在辅助 IP 模式下运行时-
  ```
  每个 ENI 10 个辅助 IPv4 地址 - 1 = 9 个可用 IPv4 地址
  ```
- 使用 `prefix delegation` 时-
  ```
  (每个 ENI 10 个辅助 IPv4 地址 - 1) * 16 = 144 个可用 IPv4 地址
  ```

有关每种实例类型可以支持多少 IP 地址的更多信息，请参阅 [每种实例类型的每个网络接口的 IP 地址](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI)。

---

另一个关键考虑因素是网络流量的流动。对于 Windows，如果节点上有超过 100 个服务，就存在端口耗尽的风险。出现这种情况时，节点将开始抛出以下错误消息：

**"Policy creation failed: hcnCreateLoadBalancer failed in Win32: The specified port already exists."**

为了解决这个问题，我们利用了直接服务器返回 (Direct Server Return， DSR)。DSR 是一种非对称网络负载分布的实现。换句话说，请求和响应流量使用不同的网络路径。这一功能加快了 Pod 之间的通信，并降低了端口耗尽的风险。因此，我们建议在 Windows 节点上启用 DSR。

DSR 在 Windows Server SAC EKS 优化 AMI 中默认启用。对于 Windows Server 2019 LTSC EKS 优化 AMI，您需要在实例供应期间使用下面的脚本启用它，并在 `eksctl` nodeGroup 中使用 Windows Server 2019 Full 或 Core 作为 amiFamily。有关更多信息，请参阅 [eksctl 自定义 AMI](https://eksctl.io/usage/custom-ami-support/)。

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
为了在 Windows Server 2019 及更高版本中使用 DSR，您需要在实例启动期间指定以下 [**kube-proxy**](https://kubernetes.io/docs/setup/production-environment/windows/intro-windows-in-kubernetes/#load-balancing-and-services) 标志。您可以通过调整与 [自管理节点组启动模板](https://docs.aws.amazon.com/eks/latest/userguide/launch-windows-workers.html) 关联的 userdata 脚本来实现这一点。

```powershell
<powershell>
[string]$EKSBinDir = "$env:ProgramFiles\Amazon\EKS"
[string]$EKSBootstrapScriptName = 'Start-EKSBootstrap.ps1'
[string]$EKSBootstrapScriptFile = "$EKSBinDir\$EKSBootstrapScriptName"
(Get-Content $EKSBootstrapScriptFile).replace('"--proxy-mode=kernelspace",', '"--proxy-mode=kernelspace", "--feature-gates WinDSR=true", "--enable-dsr",') | Set-Content $EKSBootstrapScriptFile 
& $EKSBootstrapScriptFile -EKSClusterName "eks-windows" -APIServerEndpoint "https://<REPLACE-EKS-CLUSTER-CONFIG-API-SERVER>" -Base64ClusterCA "<REPLACE-EKSCLUSTER-CONFIG-DETAILS-CA>" -DNSClusterIP "172.20.0.10" -KubeletExtraArgs "--node-labels=alpha.eksctl.io/cluster-name=eks-windows,alpha.eksctl.io/nodegroup-name=windows-ng-ltsc2019 --register-with-taints=" 3>&1 4>&1 5>&1 6>&1
</powershell>
```

可以按照 [Microsoft 网络博客](https://techcommunity.microsoft.com/t5/networking-blog/direct-server-return-dsr-in-a-nutshell/ba-p/693710) 和 [Windows Containers on AWS 实验室](https://catalog.us-east-1.prod.workshops.aws/workshops/1de8014a-d598-4cb5-a119-801576492564/en-US/module1-eks/lab3-handling-mixed-clusters)中的说明验证 DSR 的启用情况。

![](./images/dsr.png)

## 容器网络接口 (CNI) 选项
AWSVPC CNI 是 Windows 和 Linux 工作节点的事实上的 CNI 插件。虽然 AWSVPC CNI 满足了许多客户的需求，但在某些情况下，您可能需要考虑使用覆盖网络等替代方案来避免 IP 耗尽。在这种情况下，可以使用 Calico CNI 代替 AWSVPC CNI。[Project Calico](https://www.projectcalico.org/) 是由 [Tigera](https://www.tigera.io/) 开发的开源软件。该软件包括一个与 EKS 兼容的 CNI。有关在 EKS 中安装 Calico CNI 的说明，可以在 [Project Calico EKS 安装](https://docs.projectcalico.org/getting-started/kubernetes/managed-public-cloud/eks)页面上找到。

## 网络策略
将 Kubernetes 集群中 Pod 之间的默认开放通信模式更改为基于网络策略限制访问被认为是最佳实践。开源的 [Project Calico](https://www.tigera.io/tigera-products/calico/) 对适用于 Linux 和 Windows 节点的网络策略提供了强大支持。此功能独立于使用 Calico CNI。因此，我们建议安装 Calico 并将其用于网络策略管理。

有关在 EKS 中安装 Calico 的说明，可以在 [在 Amazon EKS 上安装 Calico](https://docs.aws.amazon.com/eks/latest/userguide/calico.html) 页面上找到。

此外，[Amazon EKS 安全最佳实践指南 - 网络部分](https://aws.github.io/aws-eks-best-practices/security/docs/network/)中提供的建议同样适用于具有 Windows 工作节点的 EKS 集群，但目前 Windows 不支持某些功能，如"Pod 的安全组"。