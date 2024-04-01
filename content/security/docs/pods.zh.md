# Pod 安全性

Pod 规范包括各种不同的属性，可以加强或削弱您的整体安全态势。作为 Kubernetes 从业人员，您的主要关注点应该是防止在容器运行时中运行的进程逃离容器隔离边界并获得对底层主机的访问权限。

## Linux 功能

默认情况下，在容器中运行的进程在 [Linux] 根用户的上下文中运行。尽管根在容器内的操作部分受到容器运行时分配给容器的 Linux 功能集的约束，但这些默认权限可能允许攻击者升级他们的权限和/或访问绑定到主机的敏感信息，包括 Secret 和 ConfigMap。下面是分配给容器的默认功能列表。有关每个功能的更多信息，请参阅 [http://man7.org/linux/man-pages/man7/capabilities.7.html](http://man7.org/linux/man-pages/man7/capabilities.7.html)。

`CAP_AUDIT_WRITE, CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FOWNER, CAP_FSETID, CAP_KILL, CAP_MKNOD, CAP_NET_BIND_SERVICE, CAP_NET_RAW, CAP_SETGID, CAP_SETUID, CAP_SETFCAP, CAP_SETPCAP, CAP_SYS_CHROOT`

!!! 信息

  EC2 和 Fargate pod 默认分配了上述功能。此外，只能从 Fargate pod 中删除 Linux 功能。

以特权模式运行的 Pod 继承了主机上与 root 相关的所有 Linux 功能。如果可能的话，应该避免这种情况。

### 节点授权

所有 Kubernetes 工作节点都使用一种称为 [节点授权](https://kubernetes.io/docs/reference/access-authn-authz/node/) 的授权模式。节点授权允许来自 kubelet 的所有 API 请求，并允许节点执行以下操作：

读取操作：

- 服务
- 端点
- 节点
- pod
- 与绑定到 kubelet 节点的 pod 相关的 secret、configmap、持久卷声明和持久卷

写入操作：

- 节点和节点状态(启用 `NodeRestriction` 准入插件以限制 kubelet 仅修改自己的节点)
- pod 和 pod 状态(启用 `NodeRestriction` 准入插件以限制 kubelet 仅修改绑定到自身的 pod)
- 事件

与身份验证相关的操作：

- 读/写访问 CertificateSigningRequest (CSR) API 以进行 TLS 引导
- 创建 TokenReview 和 SubjectAccessReview 的能力，用于委托身份验证/授权检查

EKS 使用 [节点限制准入控制器](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction),它只允许节点修改有限的节点属性和绑定到该节点的 pod 对象。然而，如果攻击者设法访问主机，他们仍然可以从 Kubernetes API 获取有关环境的敏感信息，从而允许他们在集群内进行横向移动。

## Pod 安全解决方案

### Pod 安全策略 (PSP)

过去，使用 [Pod 安全策略 (PSP)](https://kubernetes.io/docs/concepts/policy/pod-security-policy/) 资源来指定 pod 在创建之前必须满足的一组要求。从 Kubernetes 版本 1.21 开始，PSP 已被弃用。它们计划在 Kubernetes 版本 1.25 中被删除。

!!! 注意

  [PSP 在 Kubernetes 版本 1.21 中已被弃用](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/)。您将有大约 2 年的时间来过渡到替代方案，直到版本 1.25。[这个文档](https://github.com/kubernetes/enhancements/blob/master/keps/sig-auth/2579-psp-replacement/README.md#motivation)解释了弃用 PSP 的动机。

### 迁移到新的 pod 安全解决方案

由于 PSP 在 Kubernetes v1.25 中已被删除，集群管理员和操作员必须用其他安全控制来替换。两种解决方案可以满足这种需求：

- Kubernetes 生态系统中的策略即代码 (PAC) 解决方案
- Kubernetes [Pod 安全标准 (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

PAC 和 PSS 解决方案都可以与 PSP 共存;在 PSP 被删除之前，它们可以在集群中使用。这有助于在从 PSP 迁移时采用。在考虑从 PSP 迁移到 PSS 时，请参阅[此文档](https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/)。

Kyverno 是下面概述的 PAC 解决方案之一，在[博客文章](https://kyverno.io/blog/2023/05/24/podsecuritypolicy-migration-with-kyverno/)中概述了从 PSP 迁移到其解决方案的具体指导，包括类似的策略、功能比较和迁移程序。关于使用 Kyverno 迁移到 Pod 安全准入 (PSA) 的更多信息和指导已在 AWS 博客 [此处](https://aws.amazon.com/blogs/containers/managing-pod-security-on-amazon-eks-with-kyverno/) 发布。

### 策略即代码 (PAC)

策略即代码 (PAC) 解决方案提供了保护措施，通过规定和自动化控制来指导集群用户，并防止不希望的行为。PAC 使用 [Kubernetes 动态准入控制器](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)通过 webhook 调用拦截 Kubernetes API 服务器请求流，并根据以代码形式编写和存储的策略对请求负载进行变更和验证。变更和验证发生在 API 服务器请求导致集群发生更改之前。PAC 解决方案使用策略来匹配和处理 API 服务器请求负载，基于分类和值。

Kubernetes 生态系统中有几种开源 PAC 解决方案可用。这些解决方案不是 Kubernetes 项目的一部分;它们来自 Kubernetes 生态系统。下面列出了一些 PAC 解决方案。

- [OPA/Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/)
- [Open Policy Agent (OPA)](https://www.openpolicyagent.org/)
- [Kyverno](https://kyverno.io/)
- [Kubewarden](https://www.kubewarden.io/)
- [jsPolicy](https://www.jspolicy.com/)

有关 PAC 解决方案的更多信息以及如何帮助您选择适合您需求的合适解决方案，请参阅下面的链接。

- [Kubernetes 的基于策略的对策 – 第 1 部分](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-1/)
- [Kubernetes 的基于策略的对策 – 第 2 部分](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-2/)

### Pod 安全标准 (PSS) 和 Pod 安全准入 (PSA)

为了应对 PSP 弃用和对开箱即用的 Kubernetes 内置解决方案控制 pod 安全性的持续需求，Kubernetes [Auth 特别兴趣小组](https://github.com/kubernetes/community/tree/master/sig-auth)创建了 [Pod 安全标准 (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) 和 [Pod 安全准入 (PSA)](https://kubernetes.io/docs/concepts/security/pod-security-admission/)。PSA 工作包括一个 [准入控制器 webhook 项目](https://github.com/kubernetes/pod-security-admission#pod-security-admission),它实现了 PSS 中定义的控制。这种准入控制器方法类似于 PAC 解决方案中使用的方法。

根据 Kubernetes 文档，PSS _"定义了三种不同的策略，广泛涵盖了安全范围。这些策略是累积的，范围从高度宽松到高度限制。"_

这些策略定义如下：

- **特权：** 不受限制(不安全)的策略，提供最广泛的权限级别。此策略允许已知的权限升级。这是没有策略的情况。这对于需要特权访问的应用程序(如日志代理、CNI、存储驱动程序和其他系统范围的应用程序)很有用。

- **基线：** 最小限制性策略，可防止已知的权限升级。允许默认(最小指定)的 Pod 配置。基线策略禁止使用 hostNetwork、hostPID、hostIPC、hostPath、hostPort,无法添加 Linux 功能，以及其他几个限制。

- **受限：** 高度限制的策略，遵循当前的 Pod 强化最佳实践。该策略继承自基线并添加了进一步的限制，例如无法以 root 或 root 组身份运行。受限策略可能会影响应用程序的功能。它们主要针对运行安全关键应用程序。

这些策略定义了 [pod 执行配置文件](https://kubernetes.io/docs/concepts/security/pod-security-standards/#profile-details),分为三个特权与受限访问级别。

为了实现 PSS 定义的控制，PSA 以三种模式运行：

- **enforce:** 违反策略将导致 pod 被拒绝。

- **audit:** 违反策略将触发在审计日志中添加审计注释到记录的事件，但其他情况下允许。

- **warn:** 违反策略将触发面向用户的警告，但其他情况下允许。

这些模式和配置文件(限制)级别使用标签在 Kubernetes 命名空间级别进行配置，如下例所示。

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/enforce: restricted
```

当单独使用时，这些操作模式会产生不同的响应，从而导致不同的用户体验。_enforce_ 模式将阻止创建违反配置限制级别的 pod。但是，在这种模式下，创建 pod 的非 pod Kubernetes 对象(如 Deployment)将不会被阻止应用到集群，即使其中的 podSpec 违反了应用的 PSS。在这种情况下，Deployment 将被应用，而 pod 将被阻止应用。

这是一种困难的用户体验，因为没有立即的迹象表明成功应用的 Deployment 对象掩盖了 pod 创建失败。违规的 podSpec 将不会创建 pod。使用 `kubectl get deploy <DEPLOYMENT_NAME> -oyaml` 检查 Deployment 资源将暴露失败 pod 的 `.status.conditions` 元素中的消息，如下所示。

```yaml
...
status:
  conditions:
    - lastTransitionTime: "2022-01-20T01:02:08Z"
      lastUpdateTime: "2022-01-20T01:02:08Z"
      message: 'pods "test-688f68dc87-tw587" is forbidden: violates PodSecurity "restricted:latest":
        allowPrivilegeEscalation != false (container "test" must set securityContext.allowPrivilegeEscalation=false),
        unrestricted capabilities (container "test" must set securityContext.capabilities.drop=["ALL"]),
        runAsNonRoot != true (pod or container "test" must set securityContext.runAsNonRoot=true),
        seccompProfile (pod or container "test" must set securityContext.seccompProfile.type
        to "RuntimeDefault" or "Localhost")'
      reason: FailedCreate
      status: "True"
      type: ReplicaFailure
...
```

在 _audit_ 和 _warn_ 模式下，pod 限制不会阻止违规 pod 被创建和启动。但是，在这些模式下，当 pod 以及创建 pod 的对象包含违规 podSpec 时，会分别触发 API 服务器审计日志事件的审计注释和向 API 服务器客户端(如 _kubectl_)发出警告。下面是 `kubectl` _Warning_ 消息。

```bash
Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "test" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "test" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "test" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "test" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
deployment.apps/test created
```

PSA _audit_ 和 _warn_ 模式在引入 PSS 时不会对集群操作产生负面影响，因此很有用。

PSA 操作模式不是互斥的，可以以累积的方式使用。如下所示，多个模式可以在单个命名空间中配置。

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
```

在上面的示例中，在应用 Deployment 时提供了友好的警告和审计注释，同时还提供了违规的强制执行。事实上，多个 PSA 标签可以使用不同的配置文件级别，如下所示。

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/warn: restricted
```

在上面的示例中，PSA 被配置为允许创建满足 _baseline_ 配置文件级别的所有 pod，然后对违反 _restricted_ 配置文件级别的 pod(和创建 pod 的对象)发出警告。这是一种有用的方法，可以确定从 _baseline_ 到 _restricted_ 配置文件时可能产生的影响。

#### 现有 Pod

如果使用更严格的 PSS 配置文件修改了包含现有 pod 的命名空间，_audit_ 和 _warn_ 模式将产生适当的消息;但是，_enforce_ 模式不会删除 pod。下面是警告消息。

```bash
Warning: existing pods in namespace "policy-test" violate the new PodSecurity enforce level "restricted:latest"
Warning: test-688f68dc87-htm8x: allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile
namespace/policy-test configured
```

#### 豁免

PSA 使用 _Exemptions_ 来排除对本应应用的 pod 的违规执行。这些豁免如下所列。

- **用户名：** 来自具有豁免的经过身份验证(或模拟)用户名的请求将被忽略。

- **RuntimeClassName:** 指定了豁免的运行时类名的 pod 和工作负载资源将被忽略。

- **命名空间：** 位于豁免命名空间中的 pod 和工作负载资源将被忽略。

这些豁免作为 API 服务器配置的一部分静态应用于 [PSA 准入控制器配置](https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-admission-controller/#configure-the-admission-controller)。

在 _Validating Webhook_ 实现中，豁免可以在 Kubernetes [ConfigMap](https://github.com/kubernetes/pod-security-admission/blob/master/webhook/manifests/20-configmap.yaml) 资源中配置，该资源作为卷被挂载到 [pod-security-webhook](https://github.com/kubernetes/pod-security-admission/blob/master/webhook/manifests/50-deployment.yaml) 容器中。

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pod-security-webhook
  namespace: pod-security-webhook
data:
  podsecurityconfiguration.yaml: |
    apiVersion: pod-security.admission.config.k8s.io/v1
    kind: PodSecurityConfiguration
    defaults:
      enforce: "restricted"
      enforce-version: "latest"
      audit: "restricted"
      audit-version: "latest"
      warn: "restricted"
      warn-version: "latest"
    exemptions:
      # Array of authenticated usernames to exempt.
      usernames: []
      # Array of runtime class names to exempt.
      runtimeClasses: []
      # Array of namespaces to exempt.
      namespaces: ["kube-system","policy-test1"]
```

如上面的 ConfigMap YAML 所示，已将集群范围的默认 PSS 级别设置为所有 PSA 模式(_audit_、_enforce_ 和 _warn_)的 _restricted_。这影响所有命名空间，除了那些被豁免的命名空间： `namespaces: ["kube-system","policy-test1"]`。此外，在下面的 _ValidatingWebhookConfiguration_ 资源中，_pod-security-webhook_ 命名空间也被豁免于配置的 PSS。

```yaml
...
webhooks:
  # Audit annotations will be prefixed with this name
  - name: "pod-security-webhook.kubernetes.io"
    # Fail-closed admission webhooks can present operational challenges.
    # You may want to consider using a failure policy of Ignore, but should 
    # consider the security tradeoffs.
    failurePolicy: Fail
    namespaceSelector:
      # Exempt the webhook itself to avoid a circular dependency.
      matchExpressions:
        - key: kubernetes.io/metadata.name
          operator: NotIn
          values: ["pod-security-webhook"]
...
```

!!! 注意

  Pod 安全准入在 Kubernetes v1.25 中已经毕业为稳定版本。如果您想在默认启用该功能之前使用 Pod 安全准入功能，您需要安装动态准入控制器(变更 webhook)。安装和配置 webhook 的说明可以在[这里](https://github.com/kubernetes/pod-security-admission/tree/master/webhook)找到。

### 在策略即代码和 Pod 安全标准之间做出选择

Pod 安全标准 (PSS) 的开发是为了取代 Pod 安全策略 (PSP)，通过提供一个内置于 Kubernetes 的解决方案，而不需要使用来自 Kubernetes 生态系统的解决方案。不过，策略即代码 (PAC) 解决方案要灵活得多。

以下优缺点列表旨在帮助您就 pod 安全解决方案做出更明智的决定。

#### 策略即代码(与 Pod 安全标准相比)

优点：

- 更灵活、更细粒度(如果需要，可以细化到资源的属性)
- 不仅仅局限于 pod，可以用于不同的资源和操作
- 不仅仅在命名空间级别应用
- 比 Pod 安全标准更成熟
- 决策可以基于 API 服务器请求负载中的任何内容，以及现有集群资源和外部数据(取决于解决方案)
- 支持在验证之前变更 API 服务器请求(取决于解决方案)
- 可以生成补充策略和 Kubernetes 资源(取决于解决方案 - 从 pod 策略开始，Kyverno 可以 [自动生成](https://kyverno.io/docs/writing-policies/autogen/)更高级控制器(如 Deployment)的策略。Kyverno 还可以通过使用 [Generate Rules](https://kyverno.io/docs/writing-policies/generate/) 在创建新资源或更新源时生成其他 Kubernetes 资源。)
- 可以向左移动，进入 CICD 管道，在调用 Kubernetes API 服务器之前(取决于解决方案)
- 可以用于实现与安全无关的行为，例如最佳实践、组织标准等
- 可以在非 Kubernetes 用例中使用(取决于解决方案)
- 由于灵活性，用户体验可以根据用户需求进行调整

缺点：

- 不是内置于 Kubernetes 中
- 更复杂，学习、配置和支持都更加困难
- 编写策略可能需要新的技能/语言/能力

#### Pod 安全准入(与策略即代码相比)

优点：

- 内置于 Kubernetes 中
- 配置更简单
- 无需使用新语言或编写策略
- 如果集群默认准入级别配置为 _privileged_，则可以使用命名空间标签将命名空间选入 pod 安全配置文件。

缺点：

- 不如策略即代码那么灵活或细粒度
- 只有 3 个限制级别
- 主要关注 pod

#### 总结

如果您目前还没有除 PSP 之外的 pod 安全解决方案，并且您所需的 pod 安全态势符合 Pod 安全标准 (PSS) 定义的模型，那么采用 PSS 而不是策略即代码解决方案可能是一条更简单的路径。但是，如果您的 pod 安全态势不符合 PSS 模型，或者您预计将添加超出 PSS 定义范围的其他控制，那么策略即代码解决方案似乎更合适。

## 建议

### 为获得更好的用户体验，使用多个 Pod 安全准入 (PSA) 模式

如前所述，PSA _enforce_ 模式可以防止违反 PSS 的 pod 被应用，但不会阻止更高级别的控制器(如 Deployment)。事实上，Deployment 将被成功应用，而没有任何迹象表明 pod 未能被应用。虽然您可以使用 _kubectl_ 检查 Deployment 对象，并发现来自 PSA 的失败 pod 消息，但用户体验可以更好。为了改善用户体验，应该使用多个 PSA 模式(audit、enforce、warn)。

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
```

在上面的示例中，定义了 _enforce_ 模式，当尝试将包含 PSS 违规的 podSpec 的 Deployment 清单应用到 Kubernetes API 服务器时，Deployment 将被成功应用，但 pod 不会。而且，由于 _audit_ 和 _warn_ 模式也已启用，API 服务器客户端将收到警告消息，API 服务器审计日志事件也将被注释消息。

### 限制可以以特权模式运行的容器

如前所述，以特权模式运行的容器继承了主机上与 root 相关的所有 Linux 功能。很少有容器需要这种类型的特权才能正常运行。有多种方法可以用来限制容器的权限和功能。

!!! 注意

  Fargate 是一种启动类型，可让您在 AWS 管理的基础设施上运行"无服务器"容器(pod 中的容器)。使用 Fargate，您无法运行特权容器或配置 pod 使用 hostNetwork 或 hostPort。

### 不要以 root 身份在容器中运行进程

所有容器默认都以 root 身份运行。如果攻击者能够利用应用程序中的漏洞并获得对正在运行的容器的 shell 访问权限，这可能会带来问题。您可以通过多种方式缓解这种风险。首先，从容器镜像中删除 shell。其次，在 Dockerfile 中添加 USER 指令或以非 root 用户身份在 pod 中运行容器。Kubernetes podSpec 包括一组字段，在 `spec.securityContext` 下，让您可以指定运行应用程序的用户和/或组。这些字段分别是 `runAsUser` 和 `runAsGroup`。

要在集群中强制使用 Kubernetes podSpec 中的 `spec.securityContext` 及其关联元素，可以添加策略即代码或 Pod 安全标准。这些解决方案允许您编写和/或使用策略或配置文件，在将请求负载持久化到 etcd 之前，可以验证传入的 Kubernetes API 服务器请求负载。此外，策略即代码解决方案可以变更传入的请求，在某些情况下还可以生成新的请求。

### 永远不要在 Docker 中运行 Docker 或在容器中挂载套接字

虽然这种方式可以方便地让您在 Docker 容器中构建/运行镜像，但您基本上是在放弃对节点的完全控制权，让在容器中运行的进程来控制。如果您需要在 Kubernetes 上构建容器镜像，请使用 [Kaniko](https://github.com/GoogleContainerTools/kaniko)、[buildah](https://github.com/containers/buildah) 或构建服务(如 [CodeBuild](https://docs.aws.amazon.com/codebuild/latest/userguide/welcome.html))。

!!! 提示

  用于 CICD 处理(如构建容器镜像)的 Kubernetes 集群应与运行更通用工作负载的集群隔离。

### 限制 hostPath 的使用，或者如果必须使用 hostPath，则限制可以使用的前缀并将卷配置为只读

`hostPath` 是一种卷，直接将主机上的目录挂载到容器中。很少有 pod 需要这种类型的访问权限，但如果需要，您需要意识到风险。默认情况下，以 root 身份运行的 pod 将对 hostPath 暴露的文件系统具有写入权限。这可能允许攻击者修改 kubelet 设置、创建指向未直接暴露的目录或文件(例如 /etc/shadow)的符号链接、安装 ssh 密钥、读取挂载到主机的 secret 以及执行其他恶意操作。为了减轻 hostPath 带来的风险，请将 `spec.containers.volumeMounts` 配置为 `readOnly`,例如：

```yaml
volumeMounts:
- name: hostPath-volume
    readOnly: true
    mountPath: /host-path
```

您还应该使用策略即代码解决方案来限制可以使用 `hostPath` 卷的目录，或者完全阻止使用 `hostPath`。您可以使用 Pod 安全标准的 _Baseline_ 或 _Restricted_ 策略来防止使用 `hostPath`。

有关特权升级的危险性的更多信息，请阅读 Seth Art 的博客 [Bad Pods: Kubernetes Pod Privilege Escalation](https://labs.bishopfox.com/tech-blog/bad-pods-kubernetes-pod-privilege-escalation)。

### 为每个容器设置请求和限制，以避免资源争用和 DoS 攻击

没有请求或限制的 pod 理论上可以消耗主机上的所有可用资源。当额外的 pod 被调度到节点时，节点可能会遇到 CPU 或内存压力，这可能会导致 Kubelet 终止或从节点中逐出 pod。虽然您无法完全防止这种情况发生，但设置请求和限制将有助于最小化资源争用并减轻编写不佳的应用程序消耗过多资源的风险。

`podSpec` 允许您为 CPU 和内存指定请求和限制。CPU 被视为可压缩资源，因为它可以过度使用。内存是不可压缩的，即不能在多个容器之间共享。

当您为 CPU 或内存指定 _requests_ 时，您实际上是在指定容器保证获得的 _内存_ 量。Kubernetes 汇总 pod 中所有容器的请求，以确定将 pod 调度到哪个节点。如果容器超过请求的内存量，如果节点上存在内存压力，它可能会被终止。

_Limits_ 是容器允许消耗的最大 CPU 和内存资源量，直接对应于为容器创建的 cgroup 的 `memory.limit_in_bytes` 值。超过内存限制的容器将被 OOM 终止。如果容器超过其 CPU 限制，它将被节流。

!!! 提示

  使用容器 `resources.limits` 时，强烈建议基于负载测试来确定精确的容器资源使用情况(也称为资源占用)。如果没有准确可信的资源占用，可以适当填充容器 `resources.limits`。例如，`resources.limits.memory` 可以比可观察到的最大值高出 20-30%,以考虑潜在的内存资源限制不准确性。

Kubernetes 使用三个服务质量 (QoS) 类来确定在节点上运行的工作负载的优先级。这些包括：

- guaranteed
- burstable
- best-effort

如果未设置限制和请求，则 pod 被配置为 _best-effort_(最低优先级)。当内存不足时，best-effort pod 将是第一个被终止的。如果在 pod 内的所有容器上设置了限制，或者请求和限制设置为相同的值且不等于 0，则 pod 被配置为 _guaranteed_(最高优先级)。guaranteed pod 不会被终止，除非它们超过配置的内存限制。如果限制和请求配置为不同的值且不等于 0，或者 pod 内的一个容器设置了限制而其他容器没有设置或为不同资源设置了限制，则 pod 被配置为 _burstable_(中等优先级)。这些 pod 有一些资源保证，但一旦超过请求的内存就可能被终止。

!!! 注意

  请求不会影响容器 cgroup 的 `memory_limit_in_bytes` 值;cgroup 限制设置为主机上可用的内存量。但是，如果将请求值设置得太低，当节点遇到内存压力时，kubelet 可能会将 pod 列为终止目标。

| 类别 | 优先级 | 条件 | 终止条件 |
| :-- | :-- | :-- | :-- |
| Guaranteed | 最高 | limit = request != 0  | 仅在超过内存限制时 |
| Burstable  | 中等  | limit != request != 0 | 如果超过请求内存，可能会被终止 |
| Best-Effort| 最低  | limit & request 未设置 | 当内存不足时首先被终止 |

有关资源 QoS 的更多信息，请参阅 [Kubernetes 文档](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/)。

您可以通过在命名空间上设置 [资源配额](https://kubernetes.io/docs/concepts/policy/resource-quotas/)或创建 [限制范围](https://kubernetes.io/docs/concepts/policy/limit-range/)来强制使用请求和限制。资源配额允许您指定分配给命名空间的总资源量，例如 CPU 和 RAM。当应用到命名空间时，它会强制您为部署到该命名空间的所有容器指定请求和限制。相比之下，限制范围让您可以更精细地控制命名空间内的资源分配。使用限制范围，您可以为 pod 或命名空间内的每个容器设置 CPU 和内存资源的最小/最大值。您还可以使用它们来设置默认的请求/限制值，如果没有提供的话。

策略即代码解决方案可用于强制执行请求和限制，或者在创建命名空间时甚至创建资源配额和限制范围。

### 不要允许特权升级

特权升级允许进程更改其运行的安全上下文。Sudo 就是一个很好的例子，具有 SUID 或 SGID 位的二进制文件也是如此。特权升级基本上是一种让用户以另一个用户或组的权限执行文件的方式。您可以通过实现变更策略即代码策略将 `allowPrivilegeEscalation` 设置为 `false`,或者在 `podSpec` 中设置 `securityContext.allowPrivilegeEscalation`,来防止容器使用特权升级。策略即代码策略还可以用于防止 API 服务器请求在检测到错误设置时成功。Pod 安全标准也可以用于防止 pod 使用特权升级。

### 禁用 ServiceAccount 令牌挂载

对于不需要访问 Kubernetes API 的 pod，您可以在 pod 规范或对于使用特定 ServiceAccount 的所有 pod 上禁用自动挂载 ServiceAccount 令牌。

!!! 注意

  禁用 ServiceAccount 挂载并不会阻止 pod 通过网络访问 Kubernetes API。要防止 pod 通过网络访问 Kubernetes API，您需要修改 [EKS 集群端点访问](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)并使用 [NetworkPolicy](../network/#network-policy) 阻止 pod 访问。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-automount
spec:
  automountServiceAccountToken: false
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sa-no-automount
automountServiceAccountToken: false
```

### 禁用服务发现

对于不需要查找或调用集群内服务的 pod，您可以减少提供给 pod 的信息量。您可以将 Pod 的 DNS 策略设置为不使用 CoreDNS，并且不将服务暴露为 pod 命名空间中的环境变量。有关服务链接的更多信息，请参阅 [Kubernetes 关于环境变量的文档][k8s-env-var-docs]。pod 的 DNS 策略的默认值为 "ClusterFirst",它使用集群内 DNS，而非默认值 "Default" 使用底层节点的 DNS 解析。有关更多信息，请参阅 [Kubernetes 关于 Pod DNS 策略的文档][dns-policy]。

[k8s-env-var-docs]: https://kubernetes.io/docs/concepts/services-networking/service/#environment-variables
[dns-policy]: https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-s-dns-policy

!!! 注意

  禁用服务链接和更改 pod 的 DNS 策略并不会阻止 pod 通过网络访问集群内 DNS 服务。攻击者仍然可以通过访问集群内 DNS 服务来枚举服务。(例如： `dig SRV *.*.svc.cluster.local @$CLUSTER_DNS_IP`)要防止集群内服务发现，请使用 [NetworkPolicy](../network/#network-policy) 阻止 pod 访问

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-service-info
spec:
    dnsPolicy: Default # "Default" 不是真正的默认值
    enableServiceLinks: false
```

### 将您的镜像配置为只读根文件系统

将您的镜像配置为只读根文件系统可以防止攻击者覆盖您的应用程序使用的文件系统上的二进制文件。如果您的应用程序需要写入文件系统，请考虑写入临时目录或附加并挂载卷。您可以通过设置 pod 的 SecurityContext 来强制执行此操作，如下所示：

```yaml
...
securityContext:
  readOnlyRootFilesystem: true
...
```

策略即代码和 Pod 安全标准可用于强制执行此行为。

!!! 信息

  根据 [Kubernetes 中的 Windows 容器](https://kubernetes.io/docs/concepts/windows/intro/),对于在 Windows 上运行的容器，`securityContext.readOnlyRootFilesystem` 不能设置为 `true`,因为注册表和系统进程需要在容器内部具有写入访问权限才能运行。

## 工具和资源

- [Amazon EKS 安全沉浸式研讨会 - Pod 安全](https://catalog.workshops.aws/eks-security-immersionday/en-US/3-pod-security)
- [open-policy-agent/gatekeeper-library: OPA Gatekeeper 策略库](https://github.com/open-policy-agent/gatekeeper-library),您可以使用这个库作为 PSP 的替代品。
- [Kyverno 策略库](https://kyverno.io/policies/)
- 一组常见的 OPA 和 Kyverno [策略](https://github.com/aws/aws-eks-best-practices/tree/master/policies)用于 EKS。
- [基于策略的对策：第 1 部分](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-1/)
- [基于策略的对策：第 2 部分](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-2/)
- [Pod 安全策略迁移器](https://appvia.github.io/psp-migration/) 一个将 PSP 转换为 OPA/Gatekeeper、KubeWarden 或 Kyverno 策略的工具
- [NeuVector by SUSE](https://www.suse.com/neuvector/) 开源、零信任容器安全平台，提供进程和文件系统策略以及准入控制规则。