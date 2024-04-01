# 运行时安全

运行时安全为您的容器在运行时提供主动保护。其理念是检测和/或防止在容器内部发生恶意活动。这可以通过Linux内核或与Kubernetes集成的内核扩展中的多种机制来实现，例如Linux功能、安全计算(seccomp)、AppArmor或SELinux。还有一些选项，如Amazon GuardDuty和第三方工具，可以帮助建立基线并检测异常活动，而无需手动配置Linux内核机制。

!!! attention
    Kubernetes目前没有任何本地机制将seccomp、AppArmor或SELinux配置文件加载到节点上。它们要么必须手动加载，要么在引导节点时安装。这必须在引用它们之前完成，因为调度程序不知道哪些节点有配置文件。请参阅下面如何使用工具(如Security Profiles Operator)来帮助自动将配置文件配置到节点上。

## 安全上下文和Kubernetes内置控制

许多Linux运行时安全机制与Kubernetes紧密集成，可以通过Kubernetes [安全上下文](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)进行配置。其中一个选项是`privileged`标志，默认情况下为`false`,如果启用，基本相当于主机上的root。在生产工作负载中启用特权模式几乎总是不合适的，但还有许多其他控制可以根据需要为容器提供更细粒度的特权。

### Linux功能

Linux功能允许您在不提供root用户的所有能力的情况下，将某些功能授予Pod或容器。示例包括`CAP_NET_ADMIN`,允许配置网络接口或防火墙，或`CAP_SYS_TIME`,允许操作系统时钟。

### Seccomp

使用安全计算(seccomp)，您可以防止容器化应用程序向底层主机操作系统内核发出某些系统调用。虽然Linux操作系统有几百个系统调用，但大部分都不是运行容器所必需的。通过限制容器可以发出的系统调用，您可以有效地减小应用程序的攻击面。

Seccomp通过拦截系统调用并只允许通过已允许列表的系统调用来工作。Docker有一个[默认](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json)seccomp配置文件，适用于大多数通用工作负载，其他容器运行时(如containerd)也提供了可比的默认值。您可以通过在Pod规范的`securityContext`部分添加以下内容，将容器或Pod配置为使用容器运行时的默认seccomp配置文件：

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

从1.22版本开始(alpha版，1.27版本稳定)，上面的`RuntimeDefault`可以使用[单个kubelet标志](https://kubernetes.io/docs/tutorials/security/seccomp/#enable-the-use-of-runtimedefault-as-the-default-seccomp-profile-for-all-workloads)(`--seccomp-default`)用于节点上的所有Pod。然后，只有在需要其他配置文件时，才需要在`securityContext`中指定配置文件。

也可以为需要额外权限的内容创建自己的配置文件。手动执行这一操作可能非常繁琐，但有一些工具(如[Inspektor Gadget](https://github.com/inspektor-gadget/inspektor-gadget)(也在[网络安全部分](../network/)中推荐用于生成网络策略)和[Security Profiles Operator](https://github.com/inspektor-gadget/inspektor-gadget))支持使用eBPF或日志记录基线特权要求作为seccomp配置文件。Security Profiles Operator进一步允许自动将记录的配置文件部署到节点，以供Pod和容器使用。

### AppArmor和SELinux

AppArmor和SELinux被称为[强制访问控制或MAC系统](https://en.wikipedia.org/wiki/Mandatory_access_control)。它们在概念上与seccomp类似，但具有不同的API和功能，允许对特定文件系统路径或网络端口进行访问控制。对这些工具的支持取决于Linux发行版，Debian/Ubuntu支持AppArmor，RHEL/CentOS/Bottlerocket/Amazon Linux 2023支持SELinux。另请参阅[基础设施安全部分](../hosts/#run-selinux)以进一步讨论SELinux。

AppArmor和SELinux都与Kubernetes集成，但截至Kubernetes 1.28,AppArmor配置文件必须通过[注解](https://kubernetes.io/docs/tutorials/security/apparmor/#securing-a-pod)指定，而SELinux标签可以通过安全上下文中的[SELinuxOptions](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/#selinuxoptions-v1-core)字段直接设置。

与seccomp配置文件一样，上面提到的Security Profiles Operator可以帮助将配置文件部署到集群中的节点上。(未来，该项目还旨在为AppArmor和SELinux生成配置文件，就像它为seccomp所做的那样。)

## 建议

### 使用Amazon GuardDuty进行运行时监控并检测对您的EKS环境的威胁

如果您目前没有持续监控EKS运行时和分析EKS审计日志、扫描恶意软件和其他可疑活动的解决方案，Amazon强烈建议希望以简单、快速、安全、可扩展和经济高效的一键方式保护其AWS环境的客户使用[Amazon GuardDuty](https://aws.amazon.com/guardduty/)。Amazon GuardDuty是一种安全监控服务，可分析和处理基础数据源，如AWS CloudTrail管理事件、AWS CloudTrail事件日志、VPC流日志(来自Amazon EC2实例)、Kubernetes审计日志和DNS日志。它还包括EKS运行时监控。它使用不断更新的威胁情报源(如恶意IP地址和域名列表)，并使用机器学习来识别您的AWS环境中意外、可能未经授权和恶意的活动。这可能包括特权升级、使用暴露的凭证或与恶意IP地址、域名通信、您的Amazon EC2实例和EKS容器工作负载上存在恶意软件，或发现可疑的API活动等问题。GuardDuty通过在GuardDuty控制台或通过Amazon EventBridge生成安全发现来通知您AWS环境的状态。GuardDuty还支持将您的发现导出到Amazon简单存储服务(S3)存储桶，并与其他服务(如AWS Security Hub和Detective)集成。

观看此AWS在线技术讨论["使用Amazon GuardDuty增强对Amazon EKS的威胁检测 - AWS在线技术讨论"](https://www.youtube.com/watch?v=oNHGRRroJuE),了解如何分步在几分钟内启用这些额外的EKS安全功能。

### 可选：使用第三方解决方案进行运行时监控

如果您不熟悉Linux安全，创建和管理seccomp和Apparmor配置文件可能会很困难。如果您没有时间成为专家，可以考虑使用第三方商业解决方案。许多解决方案已经超越了静态配置文件(如Apparmor和seccomp)，开始使用机器学习来阻止或发出可疑活动的警报。其中一些解决方案可以在下面的[工具](#tools-and-resources)部分找到。更多选项可以在[AWS Marketplace for Containers](https://aws.amazon.com/marketplace/features/containers)上找到。

### 在编写seccomp策略之前，考虑添加/删除Linux功能

功能涉及可通过系统调用访问的内核函数中的各种检查。如果检查失败，系统调用通常会返回错误。该检查可以在特定系统调用的开头立即执行，也可以在可能通过多个不同系统调用访问的内核的更深层次执行(例如写入特定的特权文件)。另一方面，seccomp是一个系统调用过滤器，在运行任何系统调用之前都会应用。进程可以设置一个过滤器，允许它们撤销运行某些系统调用或某些系统调用的特定参数的权限。

在使用seccomp之前，请考虑添加/删除Linux功能是否可以为您提供所需的控制。有关更多信息，请参阅[为容器设置功能](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container)。

### 查看是否可以通过使用Pod安全策略(PSP)来实现您的目标

Pod安全策略提供了许多不同的方式来改善您的安全态势，而不会引入过多的复杂性。在开始构建seccomp和Apparmor配置文件之前，请探索PSP中提供的选项。

!!! warning
    从Kubernetes 1.25开始，PSP已被删除并替换为[Pod安全准入](https://kubernetes.io/docs/concepts/security/pod-security-admission/)控制器。第三方替代方案包括OPA/Gatekeeper和Kyverno。用于实现PSP中常见策略的Gatekeeper约束和约束模板集合可以从GitHub上的[Gatekeeper库](https://github.com/open-policy-agent/gatekeeper-library/tree/master/library/pod-security-policy)存储库中提取。而且，PSP的许多替代方案都可以在[Kyverno策略库](https://main.kyverno.io/policies/)中找到，包括完整的[Pod安全标准](https://kubernetes.io/docs/concepts/security/pod-security-standards/)集合。

## 工具和资源

- [在开始之前你应该知道的7件事](https://itnext.io/seccomp-in-kubernetes-part-i-7-things-you-should-know-before-you-even-start-97502ad6b6d6)
- [AppArmor Loader](https://github.com/kubernetes/kubernetes/tree/master/test/images/apparmor-loader)
- [使用配置文件设置节点](https://kubernetes.io/docs/tutorials/clusters/apparmor/#setting-up-nodes-with-profiles)
- [Security Profiles Operator](https://github.com/kubernetes-sigs/security-profiles-operator)是一个Kubernetes增强功能，旨在让用户更容易在Kubernetes集群中使用SELinux、seccomp和AppArmor。它提供了从正在运行的工作负载生成配置文件以及将配置文件加载到Kubernetes节点以供Pod和容器使用的功能。
- [Inspektor Gadget](https://github.com/inspektor-gadget/inspektor-gadget)允许检查、跟踪和分析Kubernetes上许多运行时行为方面，包括协助生成seccomp配置文件。
- [Aqua](https://www.aquasec.com/products/aqua-cloud-native-security-platform/)
- [Qualys](https://www.qualys.com/apps/container-security/)
- [Stackrox](https://www.stackrox.com/use-cases/threat-detection/)
- [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
- [Prisma](https://docs.paloaltonetworks.com/cn-series)
- [NeuVector by SUSE](https://www.suse.com/neuvector/) 开源的零信任容器安全平台，提供进程配置文件规则和文件访问规则。