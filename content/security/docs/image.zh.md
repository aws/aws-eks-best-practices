# 镜像安全

您应该将容器镜像视为防御攻击的第一道防线。不安全、构建不当的镜像可能会允许攻击者逃脱容器的限制并访问主机。一旦进入主机，攻击者就可以访问敏感信息或在集群或您的 AWS 账户中横向移动。以下最佳实践将有助于降低发生这种情况的风险。

## 建议

### 创建最小镜像

首先从容器镜像中删除所有多余的二进制文件。如果您正在使用来自 Dockerhub 的不熟悉的镜像，请使用诸如 [Dive](https://github.com/wagoodman/dive) 之类的应用程序检查镜像，它可以向您显示容器每一层的内容。删除所有带有 SETUID 和 SETGID 位的二进制文件，因为它们可用于权限提升，并考虑删除所有 shell 和实用程序，如 nc 和 curl，它们可用于不正当目的。您可以使用以下命令找到带有 SETUID 和 SETGID 位的文件：

```bash
find / -perm /6000 -type f -exec ls -ld {} \;
```

要从这些文件中删除特殊权限，请在容器镜像中添加以下指令：

```docker
RUN find / -xdev -perm /6000 -type f -exec chmod a-s {} \; || true
```

俗称，这被称为"去除镜像的牙齿"。

### 使用多阶段构建

使用多阶段构建是创建最小镜像的一种方式。通常，多阶段构建用于自动化持续集成周期的某些部分。例如，多阶段构建可用于 lint 您的源代码或执行静态代码分析。这为开发人员提供了一个机会，可以获得近乎即时的反馈，而不必等待管道执行。从安全角度来看，多阶段构建很有吸引力，因为它们允许您最小化推送到容器注册表的最终镜像的大小。不包含构建工具和其他多余二进制文件的容器镜像可以通过减小镜像的攻击面来改善您的安全态势。有关多阶段构建的更多信息，请参阅 [Docker 的多阶段构建文档](https://docs.docker.com/develop/develop-images/multistage-build/)。

### 为您的容器镜像创建软件材料清单 (SBOM)

"软件材料清单"(SBOM) 是构成您的容器镜像的软件工件的嵌套清单。
SBOM 是软件安全和软件供应链风险管理的关键组成部分。[生成、在中央存储库中存储 SBOM 并扫描 SBOM 以查找漏洞](https://anchore.com/sbom/)有助于解决以下问题：

- **可见性**: 了解构成您的容器镜像的组件。在中央存储库中存储可以让 SBOM 随时被审计和扫描，即使在部署后也可以检测和响应新的漏洞，如零日漏洞。
- **来源验证**: 确保现有假设关于工件的来源地和方式是真实的，以及工件或其附带的元数据在构建或交付过程中没有被篡改。
- **可信度**: 确保给定工件及其内容可以被信任，即可以执行其声称的功能。这涉及对代码是否安全执行的判断，以及对执行代码的风险做出明智决定。可信度是通过创建经过认证的管道执行报告以及经过认证的 SBOM 和经过认证的 CVE 扫描报告来确保的，以向镜像的消费者保证该镜像确实是通过安全方式(管道)使用安全组件创建的。
- **依赖信任验证**: 递归检查工件的依赖树，以验证其使用的工件的可信度和来源。SBOM 中的偏差可以帮助检测恶意活动，包括未经授权、不受信任的依赖项、渗透尝试。

以下工具可用于生成 SBOM：

- [Amazon Inspector](https://docs.aws.amazon.com/inspector) 可用于[创建和导出 SBOM](https://docs.aws.amazon.com/inspector/latest/user/sbom-export.html)。
- 也可以使用 [Anchore 的 Syft](https://github.com/anchore/syft) 进行 SBOM 生成。为了更快地进行漏洞扫描，为容器镜像生成的 SBOM 可以用作扫描的输入。然后，SBOM 和扫描报告[经过认证并附加](https://github.com/sigstore/cosign/blob/main/doc/cosign_attach_attestation.md)到镜像上，然后将镜像推送到中央 OCI 存储库(如 Amazon ECR)以供审查和审计。

通过查看 [CNCF 软件供应链最佳实践指南](https://project.linuxfoundation.org/hubfs/CNCF_SSCP_v1.pdf) 了解更多关于保护您的软件供应链的信息。

### 定期扫描镜像以查找漏洞

与其虚拟机对应物一样，容器镜像也可能包含有漏洞的二进制文件和应用程序库，或随着时间的推移而产生漏洞。防范漏洞利用的最佳方式是使用镜像扫描器定期扫描您的镜像。存储在 Amazon ECR 中的镜像可以在推送或按需(在 24 小时内一次)进行扫描。ECR 目前支持[两种类型的扫描 - 基本和增强](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)。基本扫描利用 [Clair](https://github.com/quay/clair) 这个开源镜像扫描解决方案，无需付费。[增强扫描](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning-enhanced.html)使用 Amazon Inspector 提供自动持续扫描[需要额外付费](https://aws.amazon.com/inspector/pricing/)。扫描镜像后，结果将记录到 EventBridge 中 ECR 的事件流中。您也可以从 ECR 控制台查看扫描结果。具有高或关键漏洞的镜像应该被删除或重建。如果已部署的镜像出现漏洞，应尽快替换。

了解部署了哪些有漏洞的镜像对于保持环境安全至关重要。虽然您可以自己构建镜像跟踪解决方案，但已经有几种商业产品可以开箱即用地提供此功能和其他高级功能，包括：

- [Grype](https://github.com/anchore/grype)
- [Palo Alto - Prisma Cloud (twistcli)](https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/tools/twistcli_scan_images)
- [Aqua](https://www.aquasec.com/)
- [Kubei](https://github.com/Portshift/kubei)
- [Trivy](https://github.com/aquasecurity/trivy)
- [Snyk](https://support.snyk.io/hc/en-us/articles/360003946917-Test-images-with-the-Snyk-Container-CLI)

Kubernetes 验证 webhook 也可用于验证镜像是否没有关键漏洞。验证 webhook 在 Kubernetes API 之前被调用。它们通常用于拒绝不符合 webhook 中定义的验证标准的请求。[这](https://aws.amazon.com/blogs/containers/building-serverless-admission-webhooks-for-kubernetes-with-aws-sam/)是一个无服务器 webhook 的示例，它调用 ECR describeImageScanFindings API 来确定 pod 是否正在拉取有关键漏洞的镜像。如果发现漏洞，pod 将被拒绝，并返回一个带有 CVE 列表的事件消息。

### 使用认证来验证工件完整性

认证是一个加密签名的"声明",声明某些事情 - 一个"谓词",例如管道运行或 SBOM 或漏洞扫描报告，关于另一件事 - 一个"主题"即容器镜像是真实的。

认证帮助用户验证工件是否来自软件供应链中的可信来源。例如，我们可能会使用容器镜像而不知道该镜像中包含了哪些软件组件或依赖项。但是，如果我们信任容器镜像的生产者所说的关于存在哪些软件的内容，我们就可以使用生产者的认证来依赖该工件。这意味着我们可以安全地在工作流中使用该工件，而不必自己进行分析。

- 可以使用 [AWS Signer](https://docs.aws.amazon.com/signer/latest/developerguide/Welcome.html) 或 [Sigstore cosign](https://github.com/sigstore/cosign/blob/main/doc/cosign_attest.md) 创建认证。
- Kubernetes 准入控制器如 [Kyverno](https://kyverno.io/) 可用于[验证认证](https://kyverno.io/docs/writing-policies/verify-images/sigstore/)。
- 参考这个[研讨会](https://catalog.us-east-1.prod.workshops.aws/workshops/49343bb7-2cc5-4001-9d3b-f6a33b3c4442/en-US/0-introduction)了解有关在 AWS 上使用开源工具的软件供应链管理最佳实践的更多信息，包括为容器镜像创建和附加认证的主题。

### 为 ECR 存储库创建 IAM 策略

如今，在共享 AWS 账户中有多个开发团队独立运作并不罕见。如果这些团队不需要共享资产，您可能希望创建一组 IAM 策略来限制每个团队可以与之交互的存储库。实现这一点的一个好方法是使用 ECR [命名空间](https://docs.aws.amazon.com/AmazonECR/latest/userguide/Repositories.html#repository-concepts)。命名空间是将类似的存储库分组在一起的一种方式。例如，团队 A 的所有注册表可以使用 team-a/ 前缀，而团队 B 的注册表可以使用 team-b/ 前缀。限制访问的策略可能如下所示：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": [
        "arn:aws:ecr:<region>:<account_id>:repository/team-a/*"
      ]
    }
  ]
}
```

### 考虑使用 ECR 私有端点

ECR API 有一个公共端点。因此，只要请求已通过 IAM 进行身份验证和授权，就可以从互联网访问 ECR 注册表。对于那些需要在没有互联网网关 (IGW) 的沙盒环境中运行的人，您可以为 ECR 配置私有端点。创建私有端点可以让您通过私有 IP 地址而不是通过互联网路由流量来私密访问 ECR API。有关此主题的更多信息，请参阅 [Amazon ECR 接口 VPC 端点](https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html)。

### 为 ECR 实施端点策略

默认的 ECR 端点策略允许访问该区域内的所有 ECR 存储库。这可能会允许攻击者/内部人员将数据打包为容器镜像并将其推送到另一个 AWS 账户中的注册表，从而导致数据外泄。缓解这种风险涉及创建一个端点策略，限制对 ECR 存储库的 API 访问。例如，以下策略允许您账户中的所有 AWS 主体对您的 ECR 存储库执行所有操作：

```json
{
  "Statement": [
    {
      "Sid": "LimitECRAccess",
      "Principal": "*",
      "Action": "*",
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:<region>:<account_id>:repository/*"
    }
  ]
}
```

您可以通过设置使用新的 `PrincipalOrgID` 属性的条件来进一步增强，这将防止不属于您的 AWS 组织的 IAM 主体推送/拉取镜像。有关详细信息，请参阅 [aws:PrincipalOrgID](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid)。
我们建议将相同的策略应用于 `com.amazonaws.<region>.ecr.dkr` 和 `com.amazonaws.<region>.ecr.api` 两个端点。
由于 EKS 从 ECR 为 kube-proxy、coredns 和 aws-node 拉取镜像，您需要将注册表的账户 ID (例如 `602401143452.dkr.ecr.us-west-2.amazonaws.com/*`) 添加到端点策略中资源列表中，或修改策略以允许从 "*" 拉取并限制推送到您的账户 ID。下表显示了 EKS 镜像所在的 AWS 账户与集群区域之间的映射关系。

|账户号码 |区域 |
|--- |--- |
|602401143452 |除下面列出的区域外的所有商业区域 |
|--- |--- |
|800184023465 |ap-east-1 - 亚太地区(香港) |
|558608220178 |me-south-1 - 中东(巴林) |
|918309763551 |cn-north-1 - 中国(北京) |
|961992271922 |cn-northwest-1 - 中国(宁夏) |

有关使用端点策略的更多信息，请参阅[使用 VPC 端点策略控制对 Amazon ECR 的访问](https://aws.amazon.com/blogs/containers/using-vpc-endpoint-policies-to-control-amazon-ecr-access/)。

### 为 ECR 实施生命周期策略

[NIST 应用程序容器安全指南](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)警告了"注册表中陈旧镜像"的风险，指出随着时间的推移，应该删除包含有漏洞、过时软件包的旧镜像，以防止意外部署和暴露。
每个 ECR 存储库都可以有一个生命周期策略，用于设置镜像过期的规则。[AWS 官方文档](https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html)描述了如何设置测试规则、评估它们并应用它们。官方文档中有几个[生命周期策略示例](https://docs.aws.amazon.com/AmazonECR/latest/userguide/lifecycle_policy_examples.html),显示了在存储库中过滤镜像的不同方式：

- 按镜像年龄或计数过滤
- 按标记或未标记镜像过滤
- 按镜像标签过滤，可以在多个规则或单个规则中进行

???+ warning
    如果长期运行的应用程序的镜像从 ECR 中被清除，在重新部署或水平扩展应用程序时可能会导致镜像拉取错误。使用镜像生命周期策略时，请确保您有良好的 CI/CD 实践来保持部署和它们引用的镜像的最新状态，并始终创建[镜像]过期规则以考虑您的发布/部署频率。

### 创建一组精选镜像

与允许开发人员创建自己的镜像不同，请考虑为您组织中的不同应用程序堆栈创建一组经过审查的镜像。这样做，开发人员就可以避免学习如何编写 Dockerfile，而专注于编写代码。随着更改合并到主分支，CI/CD 管道可以自动编译资产、将其存储在工件存储库中，然后将工件复制到适当的镜像中，再将其推送到 Docker 注册表(如 ECR)。至少，您应该为开发人员创建一组基础镜像，以便他们创建自己的 Dockerfile。理想情况下，您希望避免从 Dockerhub 拉取镜像，因为 1/ 您并不总是知道镜像中包含什么，2/ 大约[五分之一](https://www.kennasecurity.com/blog/one-fifth-of-the-most-used-docker-containers-have-at-least-one-critical-vulnerability/)的前 1000 个镜像存在漏洞。这些镜像及其漏洞的列表可以在[这里](https://vulnerablecontainers.org/)找到。

### 在 Dockerfile 中添加 USER 指令以非 root 用户身份运行

正如在 pod 安全部分中提到的，您应该避免以 root 用户身份运行容器。虽然您可以将此配置为 podSpec 的一部分，但在 Dockerfile 中使用 `USER` 指令是一个良好的习惯。`USER` 指令设置在 USER 指令之后出现的 `RUN`、`ENTRYPOINT` 或 `CMD` 指令时要使用的 UID。

### 对 Dockerfile 进行 lint 检查

Lint 检查可用于验证您的 Dockerfile 是否符合创建安全镜像的一组预定义准则，例如包含 `USER` 指令或要求所有镜像都被标记。[dockerfile_lint](https://github.com/projectatomic/dockerfile_lint) 是 RedHat 的一个开源项目，它可以验证常见的最佳实践，并包含一个规则引擎，您可以使用它来构建自己的规则来对 Dockerfile 进行 lint 检查。它可以被纳入 CI 管道，因此违反规则的 Dockerfile 构建将自动失败。

### 从 Scratch 构建镜像

减小容器镜像的攻击面应该是构建镜像时的主要目标。实现这一点的理想方式是创建最小镜像，这些镜像不包含可用于利用漏洞的二进制文件。幸运的是，Docker 有一种从 [`scratch`](https://docs.docker.com/develop/develop-images/baseimages/#create-a-simple-parent-image-using-scratch) 创建镜像的机制。对于像 Go 这样的语言，您可以创建一个静态链接的二进制文件，并在 Dockerfile 中引用它，如下例所示：

```docker
############################
# 步骤 1 构建可执行二进制文件
############################
FROM golang:alpine AS builder# 安装 git。
# 获取依赖项需要 Git。
RUN apk update && apk add --no-cache gitWORKDIR $GOPATH/src/mypackage/myapp/COPY . . # 获取依赖项。
# 使用 go get。
RUN go get -d -v# 构建二进制文件。
RUN go build -o /go/bin/hello

############################
# 步骤 2 构建小型镜像
############################
FROM scratch# 复制我们的静态可执行文件。
COPY --from=builder /go/bin/hello /go/bin/hello# 运行 hello 二进制文件。
ENTRYPOINT ["/go/bin/hello"]
```

这将创建一个只包含您的应用程序的容器镜像，使其极其安全。

### 使用 ECR 的不可变标签

[不可变标签](https://aws.amazon.com/about-aws/whats-new/2019/07/amazon-ecr-now-supports-immutable-image-tags/)会强制您在每次推送到镜像存储库时更新镜像标签。这可以阻止攻击者在不更改镜像标签的情况下用恶意版本覆盖镜像。此外，它为您提供了一种轻松、唯一地标识镜像的方式。

### 为镜像、SBOM、管道运行和漏洞报告签名

当 Docker 刚推出时，没有加密模型来验证容器镜像。在 v2 中，Docker 为镜像清单添加了摘要。这允许对镜像配置进行哈希运算，并使用哈希生成镜像 ID。启用镜像签名后，Docker 引擎将验证清单的签名，确保内容是由可信来源生成的，并且没有发生任何篡改。下载每一层后，引擎都会验证该层的摘要，确保内容与清单中指定的内容相匹配。镜像签名实际上允许您创建一个安全的供应链，通过验证与镜像关联的数字签名。

我们可以使用 [AWS Signer](https://docs.aws.amazon.com/signer/latest/developerguide/Welcome.html) 或 [Sigstore Cosign](https://github.com/sigstore/cosign) 为容器镜像签名，为 SBOM、漏洞扫描报告和管道运行报告创建认证。这些认证确保了镜像的可信度和完整性，确实是由可信管道创建的，没有任何干扰或篡改，并且只包含由镜像发布者验证和信任的软件组件(在 SBOM 中记录)。这些认证可以附加到容器镜像上并推送到存储库。

在下一节中，我们将看到如何使用经过认证的工件进行审计和准入控制器验证。

### 使用 Kubernetes 准入控制器进行镜像完整性验证

我们可以使用[动态准入控制器](https://kubernetes.io/blog/2019/03/21/a-guide-to-kubernetes-admission-controllers/)以自动化方式在将镜像部署到目标 Kubernetes 集群之前验证镜像签名、经过认证的工件，并且仅在工件的安全元数据符合准入控制器策略时才允许部署。

例如，我们可以编写一个策略来加密验证镜像签名、经过认证的 SBOM、经过认证的管道运行报告或经过认证的 CVE 扫描报告。我们可以在策略中编写条件来检查报告中的数据，例如 CVE 扫描不应该有任何关键 CVE。只有满足这些条件的镜像才会被准入控制器允许部署，所有其他部署都将被拒绝。

准入控制器的示例包括：

- [Kyverno](https://kyverno.io/)
- [OPA Gatekeeper](https://github.com/open-policy-agent/gatekeeper)
- [Portieris](https://github.com/IBM/portieris)
- [Ratify](https://github.com/deislabs/ratify)
- [Kritis](https://github.com/grafeas/kritis)
- [Grafeas 教程](https://github.com/kelseyhightower/grafeas-tutorial)
- [Voucher](https://github.com/Shopify/voucher)

### 更新容器镜像中的软件包

您应该在 Dockerfile 中包含 RUN `apt-get update && apt-get upgrade` 来升级镜像中的软件包。虽然升级需要以 root 用户身份运行，但这发生在镜像构建阶段。应用程序不需要以 root 用户身份运行。您可以安装更新，然后切换到其他用户使用 USER 指令。如果您的基础镜像以非 root 用户身份运行，请切换到 root 用户，然后切换回来;不要完全依赖基础镜像的维护者来安装最新的安全更新。

运行 `apt-get clean` 可以从 `/var/cache/apt/archives/` 中删除安装程序文件。安装软件包后，您还可以运行 `rm -rf /var/lib/apt/lists/*`。这将删除可安装软件包的索引文件或列表。请注意，对于每个软件包管理器，这些命令可能会有所不同。例如：

```docker
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libsqlite3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
```

## 工具和资源

- [Amazon EKS 安全沉浸式研讨会 - 镜像安全](https://catalog.workshops.aws/eks-security-immersionday/en-US/12-image-security)
- [docker-slim](https://github.com/docker-slim/docker-slim) 构建安全的最小镜像
- [dockle](https://github.com/goodwithtech/dockle) 验证您的 Dockerfile 是否符合创建安全镜像的最佳实践
- [dockerfile-lint](https://github.com/projectatomic/dockerfile_lint) Dockerfile 的基于规则的 lint 工具
- [hadolint](https://github.com/hadolint/hadolint) 一个智能 dockerfile lint 工具
- [Gatekeeper 和 OPA](https://github.com/open-policy-agent/gatekeeper) 基于策略的准入控制器
- [Kyverno](https://kyverno.io/) 一个原生 Kubernetes 策略引擎
- [in-toto](https://in-toto.io/) 允许用户验证供应链中的步骤是否有意执行，以及步骤是否由正确的参与者执行
- [Notary](https://github.com/theupdateframework/notary) 一个用于签名容器镜像的项目
- [Notary v2](https://github.com/notaryproject/nv2)
- [Grafeas](https://grafeas.io/) 一个开放的工件元数据 API，用于审计和管理您的软件供应链
- [SUSE 的 NeuVector](https://www.suse.com/neuvector/) 开源、零信任容器安全平台，提供容器、镜像和注册表扫描以查找漏洞、机密和合规性问题。