# 保護基礎設施 (主機)

雖然確保您的容器映像安全很重要,但保護運行它們的基礎設施同樣重要。本節探討了不同的方法來減輕直接針對主機發起的攻擊帶來的風險。這些指導方針應與 [運行時安全性](runtime.md) 一節中概述的指導方針一併使用。

## 建議

### 使用針對運行容器進行優化的作業系統

考慮使用 Flatcar Linux、Project Atomic、RancherOS 和 [Bottlerocket](https://github.com/bottlerocket-os/bottlerocket/)。Bottlerocket 是 AWS 設計用於運行 Linux 容器的特殊用途作業系統。它包括減少的攻擊面、在啟動時驗證的磁碟映像,以及使用 SELinux 實施的權限邊界。

或者,對於您的 Kubernetes 工作節點,使用 [EKS 優化的 AMI][eks-ami]。EKS 優化的 AMI 定期發佈,並包含運行容器化工作負載所需的最小操作系統軟件包和二進制文件。

[eks-ami]: https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html

請參閱 [Amazon EKS AMI RHEL 構建規範](https://github.com/aws-samples/amazon-eks-ami-rhel),該規範提供了一個示例配置腳本,可用於使用 Hashicorp Packer 在 Red Hat Enterprise Linux 上構建自定義 Amazon EKS AMI。該腳本可以進一步用於構建符合 STIG 合規性的 EKS 自定義 AMI。

### 保持工作節點作業系統的最新狀態

無論您使用容器優化的主機作業系統 (如 Bottlerocket) 還是更大但仍然簡約的 Amazon Machine Image (如 EKS 優化的 AMI),最佳做法是使這些主機作業系統映像保持最新的安全補丁。

對於 EKS 優化的 AMI,請定期檢查 [變更日誌][eks-ami-changes] 和/或 [發佈說明頻道][eks-ami-releases],並自動將更新的工作節點映像部署到您的集群中。

[eks-ami-changes]: https://github.com/awslabs/amazon-eks-ami/blob/master/CHANGELOG.md
[eks-ami-releases]: https://github.com/awslabs/amazon-eks-ami/releases

### 將您的基礎設施視為不可變的,並自動替換工作節點

與執行就地升級不同,當有新的補丁或更新可用時,請替換您的工作節點。可以通過以下兩種方式之一來實現這一點。您可以在現有的自動擴展組中添加使用最新 AMI 的實例,同時按順序隔離和清空節點,直到該組中的所有節點都已使用最新 AMI 進行了替換。或者,您可以在新的節點組中添加實例,同時按順序從舊的節點組中隔離和清空節點,直到所有節點都已被替換。EKS [託管節點組](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 使用第一種方法,並且在有新的 AMI 可用時,將在控制台中顯示一條消息以升級您的工作節點。`eksctl` 還提供了一種機制,用於使用最新的 AMI 創建節點組,並在終止實例之前優雅地隔離和清空節點組中的 Pod。如果您決定使用其他方法來替換工作節點,強烈建議您自動化該過程,以最小化人工監督,因為您可能需要定期替換工作節點,因為會發佈新的更新/補丁,並且在升級控制平面時也需要這樣做。

對於 EKS Fargate,AWS 將在有更新可用時自動更新底層基礎設施。通常情況下,這可以無縫完成,但有時更新可能會導致您的 Pod 被重新調度。因此,我們建議您在運行 Fargate Pod 時為應用程序創建多個副本的部署。

### 定期運行 kube-bench 以驗證是否符合 [Kubernetes 的 CIS 基準](https://www.cisecurity.org/benchmark/kubernetes/)

kube-bench 是 Aqua 的一個開源項目,用於根據 Kubernetes 的 CIS 基準評估您的集群。該基準描述了確保非托管 Kubernetes 集群安全的最佳實踐。CIS Kubernetes 基準包括控制平面和數據平面。由於 Amazon EKS 提供了完全托管的控制平面,因此並非 CIS Kubernetes 基準中的所有建議都適用。為了確保此範圍反映了 Amazon EKS 的實現方式,AWS 創建了 *CIS Amazon EKS 基準*。EKS 基準繼承自 CIS Kubernetes 基準,並結合了社區對 EKS 集群的特定配置考慮因素提供的其他輸入。

在 EKS 集群上運行 [kube-bench](https://github.com/aquasecurity/kube-bench) 時,請按照 Aqua Security 提供的 [這些說明](https://github.com/aquasecurity/kube-bench/blob/main/docs/running.md#running-cis-benchmark-in-an-eks-cluster) 操作。有關進一步信息,請參閱 [介紹 CIS Amazon EKS 基準](https://aws.amazon.com/blogs/containers/introducing-cis-amazon-eks-benchmark/)。

### 最小化對工作節點的訪問

與啟用 SSH 訪問不同,當您需要遠程訪問主機時,請使用 [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)。與可能丟失、複製或共享的 SSH 密鑰不同,Session Manager 允許您使用 IAM 控制對 EC2 實例的訪問。此外,它還提供了審計跡蹟和在實例上運行的命令的日誌。

從 2020 年 8 月 19 日起,托管節點組支持自定義 AMI 和 EC2 啟動模板。這允許您將 SSM 代理嵌入到 AMI 中,或在啟動引導工作節點時安裝它。如果您不想修改優化的 AMI 或 ASG 的啟動模板,您可以使用 DaemonSet 安裝 SSM 代理,如 [此示例](https://github.com/aws-samples/ssm-agent-daemonset-installer) 所示。

#### 基於 SSM 的 SSH 訪問的最小 IAM 策略

`AmazonSSMManagedInstanceCore` AWS 托管策略包含許多權限,如果您只是想避免使用 SSH 訪問,這些權限是不需要的。具體而言,令人關注的是對 `ssm:GetParameter(s)` 的 `*` 權限,這將允許該角色訪問 Parameter Store 中的所有參數 (包括使用配置的 AWS 托管 KMS 密鑰的 SecureStrings)。

以下 IAM 策略包含啟用通過 SSM Systems Manager 訪問節點所需的最小權限集。

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

在設置了此策略並安裝了 [Session Manager 插件](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) 後,您可以運行

```bash
aws ssm start-session --target [INSTANCE_ID_OF_EKS_NODE]
```

來訪問節點。

!!! note
    您也可以考慮添加權限以 [啟用 Session Manager 日誌記錄](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-create-iam-instance-profile.html#create-iam-instance-profile-ssn-logging)。

### 將工作節點部署到私有子網

通過將工作節點部署到私有子網,您可以最小化它們暴露在互聯網上的風險,而攻擊通常就是從那裡發起的。從 2020 年 4 月 22 日開始,將公共 IP 地址分配給托管節點組中的節點將由它們部署到的子網控制。在此之前,托管節點組中的節點會自動分配公共 IP。如果您選擇將工作節點部署到公共子網,請實施嚴格的 AWS 安全組規則以限制它們的暴露。

### 運行 Amazon Inspector 以評估主機的暴露、漏洞和偏離最佳實踐的情況

您可以使用 [Amazon Inspector](https://docs.aws.amazon.com/inspector/latest/user/what-is-inspector.html) 來檢查是否存在對節點的意外網絡訪問以及底層 Amazon EC2 實例上的漏洞。

只有在安裝和啟用 Amazon EC2 Systems Manager (SSM) 代理時,Amazon Inspector 才能為您的 Amazon EC2 實例提供常見漏洞和暴露 (CVE) 數據。該代理預裝在多個 [Amazon Machine Images (AMI)](https://docs.aws.amazon.com/systems-manager/latest/userguide/ami-preinstalled-agent.html) 上,包括 [EKS 優化的 Amazon Linux AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html)。無論 SSM 代理狀態如何,都將對您的所有 Amazon EC2 實例進行網絡可訪問性問題掃描。有關為 Amazon EC2 配置掃描的更多信息,請參閱 [掃描 Amazon EC2 實例](https://docs.aws.amazon.com/inspector/latest/user/enable-disable-scanning-ec2.html)。

!!! attention
    Inspector 無法在用於運行 Fargate Pod 的基礎設施上運行。

## 替代方案

### 運行 SELinux

!!! info
    適用於 Red Hat Enterprise Linux (RHEL)、CentOS、Bottlerocket 和 Amazon Linux 2023

SELinux 提供了一個額外的安全層,用於隔離容器與主機以及容器之間的隔離。SELinux 允許管理員對每個用戶、應用程序、進程和文件強制執行強制訪問控制 (MAC)。可以將其視為一個後備措施,根據一組標籤限制對特定資源執行的操作。在 EKS 上,SELinux 可用於防止容器訪問彼此的資源。

容器 SELinux 策略在 [container-selinux](https://github.com/containers/container-selinux) 包中定義。Docker CE 需要此包 (及其依賴項),以便由 Docker (或其他容器運行時) 創建的進程和文件以有限的系統訪問權限運行。容器利用 `container_t` 標籤,這是 `svirt_lxc_net_t` 的別名。這些策略有效地防止容器訪問主機的某些功能。

當您為 Docker 配置 SELinux 時,Docker 會自動將工作負載標記為 `container_t` 類型,並為每個容器分配一個唯一的 MCS 級別。這將隔離容器彼此之間。如果您需要更寬鬆的限制,您可以在 SElinux 中創建自己的配置文件,該配置文件授予容器訪問文件系統特定區域的權限。這類似於 PSP,您可以為不同的容器/Pod 創建不同的配置文件。例如,您可以為一般工作負載設置一組嚴格的控制,為需要特權訪問的工作負載設置另一組控制。

容器的 SELinux 有一組可以配置的選項,用於修改默認限制。可以根據您的需求啟用或禁用以下 SELinux 布爾值:

| 布爾值 | 默認值 | 描述 |
|---|:--:|---|
| `container_connect_any` | `off` | 允許容器訪問主機上的特權端口。例如,如果您有一個需要將端口映射到主機上的 443 或 80 的容器。|
| `container_manage_cgroup` | `off` | 允許容器管理 cgroup 配置。例如,運行 systemd 的容器將需要啟用此選項。|
| `container_use_cephfs` | `off` | 允許容器使用 ceph 文件系統。|

默認情況下,容器被允許在 `/usr` 下讀/執行,並從 `/etc` 讀取大部分內容。`/var/lib/docker` 和 `/var/lib/containers` 下的文件具有 `container_var_lib_t` 標籤。要查看完整的默認標籤列表,請參閱 [container.fc](https://github.com/containers/container-selinux/blob/master/container.fc) 文件。

```bash
docker container run -it \
  -v /var/lib/docker/image/overlay2/repositories.json:/host/repositories.json \
  centos:7 cat /host/repositories.json
# cat: /host/repositories.json: 權限被拒絕

docker container run -it \
  -v /etc/passwd:/host/etc/passwd \
  centos:7 cat /host/etc/passwd
# cat: /host/etc/passwd: 權限被拒絕
```

標記為 `container_file_t` 的文件是容器唯一可寫的文件。如果您希望掛載的卷是可寫的,您將需要在末尾指定 `:z` 或 `:Z`。

- `:z` 將重新標記文件,以便容器可以讀/寫
- `:Z` 將重新標記文件,以便 **只有** 容器可以讀/寫

```bash
ls -Z /var/lib/misc
# -rw-r--r--. root root system_u:object_r:var_lib_t:s0   postfix.aliasesdb-stamp

docker container run -it \
  -v /var/lib/misc:/host/var/lib/misc:z \
  centos:7 echo "重新標記!"

ls -Z /var/lib/misc
#-rw-r--r--. root root system_u:object_r:container_file_t:s0 postfix.aliasesdb-stamp
```

```bash
docker container run -it \
  -v /var/log:/host/var/log:Z \
  fluentbit:latest
```

在 Kubernetes 中,重新標記略有不同。與讓 Docker 自動重新標記文件不同,您可以指定一個自定義的 MCS 標籤來運行 Pod。支持重新標記的卷將自動重新標記,以便可以訪問它們。具有匹配的 MCS 標籤的 Pod 將能夠訪問該卷。如果您需要嚴格的隔離,請為每個 Pod 設置不同的 MCS 標籤。

```yaml
securityContext:
  seLinuxOptions:
    # 為每個容器提供唯一的 MCS 標籤
    # 您也可以指定用戶、角色和類型
    # 基於類型和級別 (svert) 的強制執行
    level: s0:c144:c154
```

在此示例中,`s0:c144:c154` 對應於分配給容器允許訪問的文件的 MCS 標籤。

在 EKS 上,您可以創建策略以允許運行特權容器 (如 FluentD),並創建 SELinux 策略以允許它從主機上的 /var/log 讀取,而無需重新標記主機目錄。具有相同標籤的 Pod 將能夠訪問相同的主機卷。

我們已經為 Amazon EKS 實現了 [示例 AMI](https://github.com/aws-samples/amazon-eks-custom-amis),其中在 CentOS 7 和 RHEL 7 上配置了 SELinux。這些 AMI 是為了演示滿足高度受監管客戶 (如 STIG、CJIS 和 C2S) 要求的示例實現而開發的。

!!! caution
    SELinux 將忽略類型為 unconfined 的容器。

## 工具和資源

- [SELinux Kubernetes RBAC 和為內部部署應用程序發佈安全策略](https://platform9.com/blog/selinux-kubernetes-rbac-and-shipping-security-policies-for-on-prem-applications/)
- [Kubernetes 的迭代強化](https://jayunit100.blogspot.com/2019/07/iterative-hardening-of-kubernetes-and.html)
- [Audit2Allow](https://linux.die.net/man/1/audit2allow)
- [SEAlert](https://linux.die.net/man/8/sealert)
- [使用 Udica 為容器生成 SELinux 策略](https://www.redhat.com/en/blog/generate-selinux-policies-containers-with-udica) 描述了一個工具,該工具查看容器規範文件中的 Linux 功能、端口和掛載點,並生成一組 SELinux 規則,允許容器正常運行
- [AMI 強化](https://github.com/aws-samples/amazon-eks-custom-amis#hardening) 用於滿足不同監管要求的作業系統強化劇本
- [Keiko Upgrade Manager](https://github.com/keikoproj/upgrade-manager) 是 Intuit 的一個開源項目,用於編排工作節點的輪換
- [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
- [eksctl](https://eksctl.io/)
