# Pod 安全上下文

**Pod 安全策略 (PSP)** 和 **Pod 安全标准 (PSS)** 是在 Kubernetes 中实施安全性的两种主要方式。请注意，从 Kubernetes v1.21 开始，PodSecurityPolicy 已被弃用，将在 v1.25 中被移除，而 Pod 安全标准 (PSS) 是 Kubernetes 推荐的实施安全性的方法。

Pod 安全策略 (PSP) 是 Kubernetes 中实现安全策略的原生解决方案。PSP 是一种集群级别的资源，用于控制 Pod 规范中与安全相关的方面。使用 Pod 安全策略，您可以定义一组 Pod 必须满足的条件，才能被集群接受。
PSP 功能自 Kubernetes 早期就已存在，旨在阻止错误配置的 Pod 在给定集群上创建。

有关 Pod 安全策略的更多信息，请参考 Kubernetes [文档](https://kubernetes.io/docs/concepts/policy/pod-security-policy/)。根据 [Kubernetes 弃用政策](https://kubernetes.io/docs/reference/using-api/deprecation-policy/),在功能被弃用后九个月，旧版本将停止获得支持。

另一方面，Pod 安全标准 (PSS) 是推荐的安全方法，通常通过安全上下文在 Pod 清单中的 Pod 和容器规范中定义。PSS 是 Kubernetes 项目团队为 Pod 定义的解决安全相关最佳实践的官方标准。它定义了诸如基线(最小限制性，默认)、特权(无限制)和受限(最严格)等策略。

我们建议从基线配置文件开始。PSS 基线配置文件在安全性和潜在摩擦之间提供了良好的平衡，只需要最少的例外列表，因此它是工作负载安全的良好起点。如果您当前正在使用 PSP，我们建议切换到 PSS。有关 PSS 策略的更多详细信息，可以在 Kubernetes [文档](https://kubernetes.io/docs/concepts/security/pod-security-standards/)中找到。这些策略可以通过多种工具(包括来自 [OPA](https://www.openpolicyagent.org/) 和 [Kyverno](https://kyverno.io/) 的工具)来实施。例如，Kyverno 在[这里](https://kyverno.io/policies/pod-security/)提供了完整的 PSS 策略集合。

安全上下文设置允许您为选定进程授予特权、使用程序配置文件限制单个程序的功能、允许特权升级、过滤系统调用等。

在安全上下文方面，Kubernetes 中的 Windows Pod 与基于 Linux 的标准工作负载相比存在一些限制和区别。

Windows 使用每个容器一个作业对象和系统命名空间过滤器来包含容器中的所有进程，并与主机逻辑隔离。无法在没有命名空间过滤的情况下运行 Windows 容器。这意味着无法在主机上下文中断言系统特权，因此 Windows 上不提供特权容器。

以下 `windowsOptions` 是唯一记录的 [Windows 安全上下文选项](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#windowssecuritycontextoptions-v1-core),而其余选项是一般的 [安全上下文选项](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.21/#securitycontext-v1-core)

有关在 Windows 与 Linux 中支持的安全上下文属性列表，请参考官方文档[此处](https://kubernetes.io/docs/setup/production-environment/windows/_print/#v1-container)。

Pod 特定设置适用于所有容器。如果未指定，将使用 PodSecurityContext 中的选项。如果在 SecurityContext 和 PodSecurityContext 中都设置了，则 SecurityContext 中指定的值优先。

例如，Pod 和容器的 runAsUserName 设置是 Linux 特定 runAsUser 设置的粗略等价物，在以下清单中，Pod 级别的安全上下文应用于所有容器

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: run-as-username-pod-demo
spec:
  securityContext:
    windowsOptions:
      runAsUserName: "ContainerUser"
  containers:
  - name: run-as-username-demo
    ...
  nodeSelector:
    kubernetes.io/os: windows
```

而在以下情况下，容器级别的安全上下文会覆盖 Pod 级别的安全上下文。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: run-as-username-container-demo
spec:
  securityContext:
    windowsOptions:
      runAsUserName: "ContainerUser"
  containers:
  - name: run-as-username-demo
    ..
    securityContext:
        windowsOptions:
            runAsUserName: "ContainerAdministrator"
  nodeSelector:
    kubernetes.io/os: windows
```

runAsUserName 字段的可接受值示例：ContainerAdministrator、ContainerUser、NT AUTHORITY\NETWORK SERVICE、NT AUTHORITY\LOCAL SERVICE

通常情况下，以 ContainerUser 身份运行 Windows Pod 中的容器是个好主意。容器和主机之间不共享用户，但 ContainerAdministrator 在容器内确实拥有额外的特权。请注意，需要注意 [限制](https://kubernetes.io/docs/tasks/configure-pod-container/configure-runasusername/#windows-username-limitations)。

使用 ContainerAdministrator 的一个很好的例子是设置 PATH。您可以使用 USER 指令执行此操作，如下所示：

```bash
USER ContainerAdministrator
RUN setx /M PATH "%PATH%;C:/your/path"
USER ContainerUser
```

另请注意，秘密以明文形式写入节点的卷(与 Linux 上的 tmpfs/内存中不同)。这意味着您必须执行以下两项操作：

* 使用文件 ACL 来保护秘密文件位置
* 使用 [BitLocker](https://docs.microsoft.com/en-us/windows/security/information-protection/bitlocker/bitlocker-how-to-deploy-on-windows-server) 进行卷级加密