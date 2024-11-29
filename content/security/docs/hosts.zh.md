# 保护基础设施（主机）

保护容器镜像很重要，同样重要的是要保护运行它们的基础设施。本节探讨了缓解针对主机发起的攻击风险的不同方式。这些指导方针应与 [运行时安全](runtime.md) 一节中概述的指导方针一起使用。

## 建议

### 使用针对运行容器进行了优化的操作系统

考虑使用 Flatcar Linux、Project Atomic、RancherOS 和 [Bottlerocket](https://github.com/bottlerocket-os/bottlerocket/)，这是 AWS 专门为运行 Linux 容器而设计的特殊操作系统。它包括减小的攻击面、在启动时验证的磁盘映像以及使用 SELinux 实施的权限边界。

或者，为您的 Kubernetes 工作节点使用 [EKS 优化的 AMI][eks-ami]。EKS 优化的 AMI 会定期发布，并包含运行容器化工作负载所需的最小操作系统包和二进制文件集。

[eks-ami]: https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html

请参阅 [Amazon EKS AMI RHEL 构建规范](https://github.com/aws-samples/amazon-eks-ami-rhel)，了解一个示例配置脚本，该脚本可用于使用 Hashicorp Packer 在 Red Hat Enterprise Linux 上构建自定义 Amazon EKS AMI。此脚本可以进一步用于构建符合 STIG 的 EKS 自定义 AMI。

### 保持工作节点操作系统的更新

无论您使用容器优化的主机操作系统（如 Bottlerocket）还是更大但仍然简约的 Amazon 机器映像（如 EKS 优化的 AMI），最佳做法是使这些主机操作系统映像保持最新的安全补丁。

对于 EKS 优化的 AMI，请定期查看 [CHANGELOG][eks-ami-changes] 和/或 [发布说明频道][eks-ami-releases]，并自动化将更新的工作节点映像部署到您的集群中。

[eks-ami-changes]: https://github.com/awslabs/amazon-eks-ami/blob/master/CHANGELOG.md
[eks-ami-releases]: https://github.com/awslabs/amazon-eks-ami/releases

### 将您的基础设施视为不可变的，并自动化工作节点的替换

当新的补丁或更新可用时，请替换您的工作节点，而不是执行就地升级。可以通过以下两种方式之一来实现这一点。您可以使用最新的 AMI 将实例添加到现有的自动伸缩组中，同时依次隔离和排空节点，直到该组中的所有节点都已使用最新的 AMI 进行了替换。或者，您可以将实例添加到新的节点组中，同时依次隔离和排空旧节点组中的节点，直到所有节点都已替换。EKS [托管节点组](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)使用第一种方法，并且在新的 AMI 可用时会在控制台中显示一条消息以升级您的工作节点。`eksctl` 也有一种机制，可以使用最新的 AMI 创建节点组，并在终止实例之前优雅地隔离和排空节点组中的 Pod。如果您决定使用其他方法来替换工作节点，我们强烈建议您自动化该过程，以最小化人工监督，因为您可能需要定期替换工作节点，因为会发布新的更新/补丁，并且在升级控制平面时也需要这样做。

对于 EKS Fargate，AWS 将在更新可用时自动更新底层基础设施。通常情况下，这可以无缝完成，但有时更新会导致您的 Pod 被重新调度。因此，我们建议您在以 Fargate Pod 运行应用程序时创建具有多个副本的部署。

### 定期运行 kube-bench 以验证是否符合 [Kubernetes 的 CIS 基准](https://www.cisecurity.org/benchmark/kubernetes/)

kube-bench 是 Aqua 的一个开源项目，用于根据 Kubernetes 的 CIS 基准评估您的集群。该基准描述了保护非托管 Kubernetes 集群的最佳实践。CIS Kubernetes 基准涵盖了控制平面和数据平面。由于 Amazon EKS 提供了完全托管的控制平面，因此并非 CIS Kubernetes 基准中的所有建议都适用。为了确保此范围反映了 Amazon EKS 的实现方式，AWS 创建了 *CIS Amazon EKS 基准*。EKS 基准继承自 CIS Kubernetes 基准，并结合了来自社区的其他输入，特别考虑了 EKS 集群的配置。

在 EKS 集群上运行 [kube-bench](https://github.com/aquasecurity/kube-bench) 时，请按照 Aqua Security 的[这些说明](https://github.com/aquasecurity/kube-bench/blob/main/docs/running.md#running-cis-benchmark-in-an-eks-cluster)进行操作。有关更多信息，请参阅 [介绍 CIS Amazon EKS 基准](https://aws.amazon.com/blogs/containers/introducing-cis-amazon-eks-benchmark/)。

### 最小化对工作节点的访问

与其启用 SSH 访问，不如在需要远程访问主机时使用 [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)。与可能丢失、复制或共享的 SSH 密钥不同，Session Manager 允许您使用 IAM 控制对 EC2 实例的访问。此外，它还提供了审计跟踪和在实例上运行的命令的日志。

从 2020 年 8 月 19 日起，托管节点组支持自定义 AMI 和 EC2 启动模板。这允许您将 SSM 代理嵌入到 AMI 中或在引导工作节点时安装它。如果您不想修改优化的 AMI 或 ASG 的启动模板，您可以使用 DaemonSet 安装 SSM 代理，如[此示例](https://github.com/aws-samples/ssm-agent-daemonset-installer)所示。

#### 用于基于 SSM 的 SSH 访问的最小 IAM 策略

`AmazonSSMManagedInstanceCore` AWS 托管策略包含许多不需要 SSM Session Manager / SSM RunCommand 的权限（如果您只是想避免 SSH 访问）。特别令人关注的是对 `ssm:GetParameter(s)` 的 `*` 权限，这将允许该角色访问参数存储中的所有参数（包括使用配置的 AWS 托管 KMS 密钥的 SecureStrings）。

以下 IAM 策略包含启用通过 SSM Systems Manager 访问节点所需的最小权限集。

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnableAccessViaSSMSessionManager",
      "Effect": "Allow",
      "Action": [
        "ssmmessages:OpenDataChannel",
        "ssmmessages:OpenControlChannel",
        "ssmmessages:CreateDataChannel",
        "ssmmessages:CreateControlChannel",
        "ssm:UpdateInstanceInformation"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EnableSSMRunCommand",
      "Effect": "Allow",
      "Action": [
        "ssm:UpdateInstanceInformation",
        "ec2messages:SendReply",
        "ec2messages:GetMessages",
        "ec2messages:GetEndpoint",
        "ec2messages:FailMessage",
        "ec2messages:DeleteMessage",
        "ec2messages:AcknowledgeMessage"
      ],
      "Resource": "*"
    }
  ]
}
```

使用此策略并安装 [Session Manager 插件](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)后，您就可以运行

```bash
aws ssm start-session --target [INSTANCE_ID_OF_EKS_NODE]
```

来访问节点。

!!! note
    您也可以考虑添加权限以[启用 Session Manager 日志记录](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-create-iam-instance-profile.html#create-iam-instance-profile-ssn-logging)。

### 将工作节点部署到私有子网

通过将工作节点部署到私有子网，可以最小化它们暴露在互联网上的风险，而攻击通常就是从互联网发起的。从 2020 年 4 月 22 日开始，在托管节点组中分配给节点的公有 IP 地址将由它们部署到的子网控制。在此之前，托管节点组中的节点会自动分配公有 IP。如果您选择将工作节点部署到公有子网，请实施限制性的 AWS 安全组规则来限制它们的暴露。

### 运行 Amazon Inspector 以评估主机的暴露、漏洞和偏离最佳实践的情况

您可以使用 [Amazon Inspector](https://docs.aws.amazon.com/inspector/latest/user/what-is-inspector.html) 来检查是否存在意外的网络访问到您的节点以及底层 Amazon EC2 实例上的漏洞。

只有在安装和启用 Amazon EC2 Systems Manager (SSM) 代理的情况下，Amazon Inspector 才能为您的 Amazon EC2 实例提供常见漏洞和暴露 (CVE) 数据。此代理预先安装在多个 [Amazon Machine Images (AMIs)](https://docs.aws.amazon.com/systems-manager/latest/userguide/ami-preinstalled-agent.html) 上，包括 [EKS 优化的 Amazon Linux AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html)。无论 SSM 代理状态如何，都会扫描您所有的 Amazon EC2 实例以检查网络可达性问题。有关为 Amazon EC2 配置扫描的更多信息，请参阅[扫描 Amazon EC2 实例](https://docs.aws.amazon.com/inspector/latest/user/enable-disable-scanning-ec2.html)。

!!! attention
    无法在用于运行 Fargate Pod 的基础设施上运行 Inspector。

## 替代方案

### 运行 SELinux

!!! info
    可用于 Red Hat Enterprise Linux (RHEL)、CentOS、Bottlerocket 和 Amazon Linux 2023

SELinux 提供了一层额外的安全性，可以将容器与彼此和主机隔离。SELinux 允许管理员对每个用户、应用程序、进程和文件实施强制访问控制 (MAC)。可以将其视为一个后备机制，根据一组标签限制对特定资源执行的操作。在 EKS 上，SELinux 可用于防止容器访问彼此的资源。

容器 SELinux 策略在 [container-selinux](https://github.com/containers/container-selinux) 包中定义。Docker CE 需要此包（及其依赖项），以便由 Docker（或其他容器运行时）创建的进程和文件以有限的系统访问权限运行。容器利用 `container_t` 标签，这是 `svirt_lxc_net_t` 的别名。这些策略有效地防止容器访问主机的某些功能。

当您为 Docker 配置 SELinux 时，Docker 会自动将工作负载标记为 `container_t` 类型，并为每个容器分配一个唯一的 MCS 级别。这将隔离容器彼此之间。如果您需要更宽松的限制，您可以在 SElinux 中创建自己的配置文件，该配置文件授予容器访问文件系统特定区域的权限。这类似于 PSP，您可以为不同的容器/Pod 创建不同的配置文件。例如，您可以为一般工作负载设置一组限制性控制的配置文件，为需要特权访问的工作负载设置另一个配置文件。

容器的 SELinux 有一组可以配置的选项，用于修改默认限制。可以根据需要启用或禁用以下 SELinux 布尔值：

| 布尔值 | 默认值 | 描述|
|---|:--:|---|
| `container_connect_any` | `off` | 允许容器访问主机上的特权端口。例如，如果您有一个需要将端口映射到主机上的 443 或 80 的容器。 |
| `container_manage_cgroup` | `off` | 允许容器管理 cgroup 配置。例如，运行 systemd 的容器将需要启用此选项。 |
| `container_use_cephfs` | `off` | 允许容器使用 ceph 文件系统。 |

默认情况下，容器被允许在 `/usr` 下读/执行，并从 `/etc` 读取大部分内容。`/var/lib/docker` 和 `/var/lib/containers` 下的文件具有 `container_var_lib_t` 标签。要查看默认标签的完整列表，请参阅 [container.fc](https://github.com/containers/container-selinux/blob/master/container.fc) 文件。

```bash
docker container run -it \
  -v /var/lib/docker/image/overlay2/repositories.json:/host/repositories.json \
  
  centos:7 cat /host/repositories.json
# cat: /host/repositories.json: 权限被拒绝

docker container run -it \
  -v /etc/passwd:/host/etc/passwd \
  centos:7 cat /host/etc/passwd
# cat: /host/etc/passwd: 权限被拒绝
```

标记为 `container_file_t` 的文件是容器唯一可写的文件。如果您希望卷挂载可写，您将需要在末尾指定 `:z` 或 `:Z`。

- `:z` 将重新标记文件，以便容器可以读/写
- `:Z` 将重新标记文件，以便**只有**容器可以读/写

```bash
ls -Z /var/lib/misc
# -rw-r--r--. root root system_u:object_r:var_lib_t:s0   postfix.aliasesdb-stamp

docker container run -it \
  -v /var/lib/misc:/host/var/lib/misc:z \
  centos:7 echo "重新标记!"

ls -Z /var/lib/misc
#-rw-r--r--. root root system_u:object_r:container_file_t:s0 postfix.aliasesdb-stamp
```

```bash
docker container run -it \
  -v /var/log:/host/var/log:Z \
  fluentbit:latest
```

在 Kubernetes 中，重新标记略有不同。不是让 Docker 自动重新标记文件，而是可以指定一个自定义的 MCS 标签来运行 Pod。支持重新标记的卷将自动重新标记，以便可以访问它们。具有匹配的 MCS 标签的 Pod 将能够访问该卷。如果您需要严格的隔离，请为每个 Pod 设置不同的 MCS 标签。

```yaml
securityContext:
  seLinuxOptions:
    # 为每个容器提供唯一的 MCS 标签
    # 您也可以指定用户、角色和类型
    # 基于类型和级别 (svert) 的强制执行
    level: s0:c144:c154
```

在此示例中，`s0:c144:c154` 对应于容器被允许访问的文件分配的 MCS 标签。

在 EKS 上，您可以创建策略以允许运行特权容器（如 FluentD），并创建 SELinux 策略以允许它从主机上的 /var/log 读取，而无需重新标记主机目录。具有相同标签的 Pod 将能够访问相同的主机卷。

我们已经实现了 [Amazon EKS 的示例 AMI](https://github.com/aws-samples/amazon-eks-custom-amis)，其中在 CentOS 7 和 RHEL 7 上配置了 SELinux。这些 AMI 是为满足高度监管客户（如 STIG、CJIS 和 C2S）的要求而开发的示例实现。

!!! caution
    SELinux 将忽略类型为 unconfined 的容器。

## 工具和资源

- [SELinux Kubernetes RBAC 和为本地应用程序发布安全策略](https://platform9.com/blog/selinux-kubernetes-rbac-and-shipping-security-policies-for-on-prem-applications/)
- [Kubernetes 的迭代强化](https://jayunit100.blogspot.com/2019/07/iterative-hardening-of-kubernetes-and.html)
- [Audit2Allow](https://linux.die.net/man/1/audit2allow)
- [SEAlert](https://linux.die.net/man/8/sealert)
- [使用 Udica 为容器生成 SELinux 策略](https://www.redhat.com/en/blog/generate-selinux-policies-containers-with-udica) 描述了一个工具，它查看容器规范文件中的 Linux 功能、端口和挂载点，并生成一组 SELinux 规则，允许容器正常运行
- [AMI 强化](https://github.com/aws-samples/amazon-eks-custom-amis#hardening) 用于满足不同监管要求的操作系统强化剧本
- [Keiko Upgrade Manager](https://github.com/keikoproj/upgrade-manager) 是 Intuit 的一个开源项目，用于协调工作节点的轮换。
- [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
- [eksctl](https://eksctl.io/)