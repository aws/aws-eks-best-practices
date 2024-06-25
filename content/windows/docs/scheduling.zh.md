＃ 运行异构工作负载¶

Kubernetes 支持异构集群，在同一个集群中可以混合使用 Linux 和 Windows 节点。在该集群中，您可以混合运行在 Linux 上的 Pod 和在 Windows 上的 Pod。您甚至可以在同一个集群中运行多个版本的 Windows。但是，在做出这个决定时，需要考虑以下几个因素(如下所述)。

＃ 将 POD 分配给节点的最佳实践

为了将 Linux 和 Windows 工作负载保留在各自特定操作系统的节点上，您需要使用节点选择器和污点/容忍度的组合。在异构环境中调度工作负载的主要目标是避免破坏现有 Linux 工作负载的兼容性。

## 确保特定操作系统的工作负载落在适当的容器主机上

用户可以使用 nodeSelectors 确保 Windows 容器可以在适当的主机上调度。当今所有 Kubernetes 节点都具有以下默认标签：

    kubernetes.io/os = [windows|linux]
    kubernetes.io/arch = [amd64|arm64|...]

如果 Pod 规范不包含诸如 ``"kubernetes.io/os": windows`` 之类的 nodeSelector，则该 Pod 可能会被调度到任何主机，无论是 Windows 还是 Linux。这可能会有问题，因为 Windows 容器只能在 Windows 上运行，而 Linux 容器只能在 Linux 上运行。

在企业环境中，拥有大量预先存在的 Linux 容器部署以及现成的配置(如 Helm 图表)的生态系统是很常见的。在这种情况下，您可能不愿意更改部署的 nodeSelectors。**替代方案是使用污点**。

例如： `--register-with-taints='os=windows:NoSchedule'`

如果您使用 EKS，eksctl 提供了通过 clusterConfig 应用污点的方式：

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

为所有 Windows 节点添加污点后，调度程序将不会在这些节点上调度 Pod，除非它们容忍该污点。Pod 清单示例：

```yaml
nodeSelector:
    kubernetes.io/os: windows
tolerations:
    - key: "os"
      operator: "Equal"
      value: "windows"
      effect: "NoSchedule"
```

## 在同一集群中处理多个 Windows 版本

每个 Pod 使用的 Windows 容器基础映像必须与节点使用的相同内核版本匹配。如果您想在同一集群中使用多个 Windows Server 版本，那么您应该设置额外的节点标签、nodeSelectors 或利用名为 **windows-build** 的标签。

Kubernetes 1.17 自动为 Windows 节点添加了一个新的标签 **node.kubernetes.io/windows-build**,以简化同一集群中多个 Windows 版本的管理。如果您运行的是旧版本，则建议手动为 Windows 节点添加此标签。

该标签反映了需要匹配以实现兼容性的 Windows 主版本号、次版本号和内部版本号。下面是当前每个 Windows Server 版本使用的值。

重要的是要注意，Windows Server 正在将 Long-Term Servicing Channel (LTSC) 作为主要发布渠道。Windows Server Semi-Annual Channel (SAC) 已于 2022 年 8 月 9 日停止使用。将不会有未来的 Windows Server SAC 版本。


| 产品名称 | 内部版本号 |
| -------- | -------- |
| Server full 2022 LTSC    | 10.0.20348    |
| Server core 2019 LTSC    | 10.0.17763    |

可以通过以下命令检查操作系统内部版本号：

```bash    
kubectl get nodes -o wide
```

KERNEL-VERSION 输出与 Windows 操作系统内部版本号匹配。

```bash 
NAME                          STATUS   ROLES    AGE   VERSION                INTERNAL-IP   EXTERNAL-IP     OS-IMAGE                         KERNEL-VERSION                  CONTAINER-RUNTIME
ip-10-10-2-235.ec2.internal   Ready    <none>   23m   v1.24.7-eks-fb459a0    10.10.2.235   3.236.30.157    Windows Server 2022 Datacenter   10.0.20348.1607                 containerd://1.6.6
ip-10-10-31-27.ec2.internal   Ready    <none>   23m   v1.24.7-eks-fb459a0    10.10.31.27   44.204.218.24   Windows Server 2019 Datacenter   10.0.17763.4131                 containerd://1.6.6
ip-10-10-7-54.ec2.internal    Ready    <none>   31m   v1.24.11-eks-a59e1f0   10.10.7.54    3.227.8.172     Amazon Linux 2                   5.10.173-154.642.amzn2.x86_64   containerd://1.6.19
```

下面的示例在 Pod 清单中应用了额外的 nodeSelector，以便在运行不同 Windows 节点组操作系统版本时匹配正确的 Windows 内部版本号。

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

## 使用 RuntimeClass 简化 Pod 清单中的 NodeSelector 和 Toleration

您还可以利用 RuntimeClass 来简化使用污点和容忍度的过程。这可以通过创建一个 RuntimeClass 对象来实现，该对象用于封装这些污点和容忍度。

通过运行以下清单创建 RuntimeClass：

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

创建 Runtimeclass 后，使用 Pod 清单中的 Spec 分配它：

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

## 托管节点组支持
为了帮助客户以更加流畅的方式运行其 Windows 应用程序，AWS 于 2022 年 12 月 15 日推出了对 Amazon [EKS 托管节点组 (MNG) 支持 Windows 容器](https://aws.amazon.com/about-aws/whats-new/2022/12/amazon-eks-automated-provisioning-lifecycle-management-windows-containers/)的支持。为了帮助统一运维团队，[Windows MNG](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 使用与 [Linux MNG](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 相同的工作流程和工具启用。支持 Windows Server 2019 和 2022 的完整和核心 AMI (Amazon Machine Image) 版本。

托管节点组 (MNG) 支持以下 AMI 系列。

| AMI 系列 |
| ---------   | 
| WINDOWS_CORE_2019_x86_64    | 
| WINDOWS_FULL_2019_x86_64    | 
| WINDOWS_CORE_2022_x86_64    | 
| WINDOWS_FULL_2022_x86_64    | 

## 其他文档


AWS 官方文档：
https://docs.aws.amazon.com/eks/latest/userguide/windows-support.html

要更好地了解 Pod 网络 (CNI) 的工作原理，请查看以下链接： https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html

AWS 博客关于在 EKS 上部署 Windows 托管节点组：
https://aws.amazon.com/blogs/containers/deploying-amazon-eks-windows-managed-node-groups/