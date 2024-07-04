# 租户隔离

当我们考虑多租户时，我们通常希望将一个用户或应用程序与在共享基础设施上运行的其他用户或应用程序隔离开来。

Kubernetes 是一个 _单租户编排器_，即控制平面的单个实例在集群内的所有租户之间共享。但是，您可以使用各种 Kubernetes 对象来创建多租户的外观。例如，可以实现命名空间和基于角色的访问控制 (RBAC) 来在逻辑上将租户相互隔离。同样，可以使用配额和限制范围来控制每个租户可以消耗的集群资源量。然而，集群是提供强大安全边界的唯一构造。这是因为一旦攻击者设法访问集群中的主机，他们就可以检索该主机上安装的 _所有_ Secret、ConfigMap 和卷。他们还可以伪装 Kubelet，从而允许他们操纵节点的属性和/或在集群内横向移动。

以下几节将解释如何实现租户隔离，同时缓解使用 Kubernetes 等单租户编排器的风险。

## 软多租户

使用软多租户，您可以使用本地 Kubernetes 构造(例如命名空间、角色和角色绑定以及网络策略)在租户之间创建逻辑分离。例如，RBAC 可以防止租户访问或操纵彼此的资源。配额和限制范围可以控制每个租户可以消耗的集群资源量，而网络策略可以帮助防止部署到不同命名空间中的应用程序相互通信。

然而，这些控制都无法防止来自不同租户的 pod 共享节点。如果需要更强的隔离，您可以使用节点选择器、反亲和规则和/或污点和容忍度来强制将来自不同租户的 pod 调度到单独的节点上;通常称为 _单租户节点_。在有许多租户的环境中，这可能会变得相当复杂和成本高昂。

!!! attention
    使用命名空间实现的软多租户不允许您向租户提供已过滤的命名空间列表，因为命名空间是全局作用域类型。如果租户有能力查看特定命名空间，它就可以查看集群中的所有命名空间。

!!! warning
    在软多租户环境中，租户默认保留查询 CoreDNS 以获取集群内运行的所有服务的能力。攻击者可以通过从集群中的任何 pod 运行 dig SRV `*.*.svc.cluster.local` 来利用这一点。如果您需要限制访问集群内运行的服务的 DNS 记录，请考虑使用 CoreDNS 的 Firewall 或 Policy 插件。有关更多信息，请参阅 [https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy](https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy)。

[Kiosk](https://github.com/kiosk-sh/kiosk) 是一个开源项目，可以帮助实现软多租户。它是作为一系列 CRD 和控制器实现的，提供以下功能：

- **账户和账户用户**用于在共享 Kubernetes 集群中分离租户
- **自助命名空间供应**供账户用户使用
- **账户限制**确保在共享集群时的服务质量和公平性
- **命名空间模板**用于安全的租户隔离和自助命名空间初始化

[Loft](https://loft.sh) 是 Kiosk 和 [DevSpace](https://github.com/devspace-cloud/devspace) 维护者提供的商业产品，增加了以下功能：

- **多集群访问**用于授予对不同集群中空间的访问权限
- **睡眠模式**在空闲期间缩减空间中的部署
- **单点登录**与 GitHub 等 OIDC 身份验证提供商集成

软多租户可以解决三个主要用例。

### 企业环境

第一个是企业环境，其中"租户"是半信任的，即他们是组织授权的员工、承包商或其他人员。每个租户通常与行政部门或团队等管理部门相对应。

在这种环境中，通常由集群管理员负责创建命名空间和管理策略。他们还可能实施委派管理模型，其中某些个人被授予对命名空间的监督权，允许他们对非策略相关对象(如部署、服务、pod、作业等)执行 CRUD 操作。

在这种环境中，容器运行时提供的隔离可能是可接受的，或者可能需要通过额外的 pod 安全性控制来增强。如果需要更严格的隔离，也可能需要限制不同命名空间中服务之间的通信。

### Kubernetes 作为服务

相比之下，软多租户可以用于希望提供 Kubernetes 作为服务 (KaaS) 的环境。使用 KaaS，您的应用程序托管在共享集群中，与一组控制器和 CRD 一起提供一组 PaaS 服务。租户直接与 Kubernetes API 服务器交互，并被允许对非策略对象执行 CRUD 操作。还有一个自助服务元素，租户可能被允许创建和管理自己的命名空间。在这种环境中，假设租户运行的是不受信任的代码。

要在这种环境中隔离租户，您可能需要实施严格的网络策略以及 _pod 沙箱化_。沙箱化是指在微虚拟机(如 Firecracker)或用户空间内核中运行 pod 的容器。今天，您可以使用 EKS Fargate 创建沙箱化的 pod。

### 软件即服务 (SaaS)

软多租户的最后一个用例是软件即服务 (SaaS) 环境。在这种环境中，每个租户都与运行在集群中的应用程序的特定 _实例_ 相关联。每个实例通常都有自己的数据，并使用独立于 Kubernetes RBAC 的单独访问控制。

与其他用例不同，SaaS 环境中的租户不直接与 Kubernetes API 交互。相反，SaaS 应用程序负责与 Kubernetes API 交互，以创建支持每个租户所需的对象。

## Kubernetes 构造

在每个实例中，都使用以下构造来隔离租户：

### 命名空间

命名空间是实现软多租户的基础。它们允许您将集群划分为逻辑分区。配额、网络策略、服务账户和实现多租户所需的其他对象都在命名空间范围内。

### 网络策略

默认情况下，集群中的所有 pod 都可以相互通信。可以使用网络策略来改变这种行为。

网络策略使用标签或 IP 地址范围来限制 pod 之间的通信。在需要在租户之间实现严格网络隔离的多租户环境中，我们建议从一个拒绝 pod 之间通信的默认规则开始，以及另一个允许所有 pod 查询 DNS 服务器进行名称解析的规则。有了这个基础，您就可以开始添加更多允许在命名空间内通信的规则。根据需要，可以进一步细化这些规则。

!!! note
    Amazon [VPC CNI 现在支持 Kubernetes 网络策略](https://aws.amazon.com/blogs/containers/amazon-vpc-cni-now-supports-kubernetes-network-policies/),可以创建策略来隔离敏感工作负载并保护它们免受未经授权访问，当在 AWS 上运行 Kubernetes 时。这意味着您可以在 Amazon EKS 集群中使用网络策略 API 的所有功能。这种细粒度的控制使您能够实现最小特权原则，确保只有经过授权的 pod 才能相互通信。

!!! attention
    网络策略是必要的，但不足以实现隔离。网络策略的执行需要策略引擎，如 Calico 或 Cilium。

### 基于角色的访问控制 (RBAC)

角色和角色绑定是用于在 Kubernetes 中实施基于角色的访问控制 (RBAC) 的对象。**角色**包含可以对集群中对象执行的操作列表。**角色绑定**指定应用角色的个人或组。在企业和 KaaS 环境中，RBAC 可用于允许选定的组或个人管理对象。

### 配额

配额用于定义托管在集群中的工作负载的限制。使用配额，您可以指定 pod 可以消耗的最大 CPU 和内存量，或者限制可以在集群或命名空间中分配的资源数量。**限制范围**允许您为每个限制声明最小、最大和默认值。

在共享集群中过度使用资源通常是有益的，因为它允许您最大限度地利用资源。但是，对集群的无限制访问可能会导致资源耗尽，从而导致性能下降和应用程序可用性丢失。如果 pod 的请求设置过低，实际资源利用率超过了节点的容量，节点将开始经历 CPU 或内存压力。发生这种情况时，pod 可能会在节点上重新启动和/或被驱逐。

为了防止这种情况发生，您应该计划在多租户环境中对命名空间实施配额，以强制租户在集群上调度 pod 时指定请求和限制。它还将缓解潜在的拒绝服务攻击，限制 pod 可以消耗的资源量。

您还可以使用配额来按照租户的支出来分配集群资源。这在 KaaS 场景中特别有用。

### Pod 优先级和抢占

当您希望为 Pod 相对于其他 Pod 提供更高的重要性时，Pod 优先级和抢占可能会很有用。例如，使用 pod 优先级，您可以配置来自客户 A 的 pod 以比来自客户 B 的 pod 更高的优先级运行。当可用容量不足时，调度器将驱逐来自客户 B 的较低优先级 pod，以容纳来自客户 A 的较高优先级 pod。在客户愿意支付更高费用以获得更高优先级的 SaaS 环境中，这可能特别方便。

!!! attention
    Pod 优先级可能会对较低优先级的其他 Pod 产生意外影响。例如，虽然受害 pod 会被正常终止，但 PodDisruptionBudget 不能得到保证，这可能会破坏依赖于 Pod 仲裁的较低优先级应用程序，请参阅 [抢占的限制](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/#limitations-of-preemption)。

## 缓解控制

作为多租户环境的管理员，您的主要关注点是防止攻击者访问底层主机。应考虑以下控制措施来缓解这种风险：

### 容器的沙箱化执行环境

沙箱化是一种技术，每个容器都在自己的隔离虚拟机中运行。执行 pod 沙箱化的技术包括 [Firecracker](https://firecracker-microvm.github.io/) 和 Weave 的 [Firekube](https://www.weave.works/blog/firekube-fast-and-secure-kubernetes-clusters-using-weave-ignite)。

有关将 Firecracker 作为 EKS 支持的运行时的工作的更多信息，请参阅 [https://threadreaderapp.com/thread/1238496944684597248.html](https://threadreaderapp.com/thread/1238496944684597248.html)。

### 开放策略代理 (OPA) 和 Gatekeeper

[Gatekeeper](https://github.com/open-policy-agent/gatekeeper) 是一个 Kubernetes 准入控制器，用于执行使用 [OPA](https://www.openpolicyagent.org/) 创建的策略。使用 OPA，您可以创建一个策略，将来自租户的 pod 在单独的实例上运行，或以比其他租户更高的优先级运行。该项目的 GitHub [存储库](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa)中包含了一些常见的 OPA 策略集合。

还有一个实验性的 [OPA CoreDNS 插件](https://github.com/coredns/coredns-opa),允许您使用 OPA 来过滤/控制 CoreDNS 返回的记录。

### Kyverno

[Kyverno](https://kyverno.io) 是一个 Kubernetes 原生策略引擎，可以使用作为 Kubernetes 资源的策略来验证、变更和生成配置。Kyverno 使用 Kustomize 风格的覆盖进行验证，支持 JSON Patch 和策略合并修补进行变更，并且可以根据灵活的触发器在命名空间之间克隆资源。

您可以使用 Kyverno 隔离命名空间、实施 pod 安全性和其他最佳实践，以及生成默认配置(如网络策略)。该项目的 GitHub [存储库](https://github.com/aws/aws-eks-best-practices/tree/master/policies/kyverno)中包含了一些示例。Kyverno 网站上的 [策略库](https://kyverno.io/policies/)中也包含了许多其他示例。

### 将租户工作负载隔离到特定节点

在软多租户模型中，将租户工作负载限制在特定节点上运行可以增加隔离。使用这种方法，特定租户的工作负载只在为该租户配置的节点上运行。为实现此隔离，使用本地 Kubernetes 属性(节点亲和性、污点和容忍度)来针对特定节点进行 pod 调度，并防止来自其他租户的 pod 被调度到特定租户的节点上。

#### 第 1 部分 - 节点亲和性

Kubernetes [节点亲和性](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)用于基于节点 [标签](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)针对节点进行调度。使用节点亲和性规则，pod 会被吸引到与选择器项匹配的特定节点。在下面的 pod 规范中，`requiredDuringSchedulingIgnoredDuringExecution` 节点亲和性被应用于相应的 pod。结果是 pod 将针对带有以下键/值标签的节点： `node-restriction.kubernetes.io/tenant: tenants-x`。

``` yaml
...
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node-restriction.kubernetes.io/tenant
            operator: In
            values:
            - tenants-x
...
```

使用此节点亲和性，标签在调度期间是必需的，但在执行期间不是必需的;如果底层节点的标签发生变化，pod 不会仅因为该标签更改而被驱逐。但是，未来的调度可能会受到影响。

!!! Warning
    标签前缀 `node-restriction.kubernetes.io/` 在 Kubernetes 中有特殊含义。[NodeRestriction](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction) 在 EKS 集群中启用，防止 `kubelet` 添加/删除/更新具有此前缀的标签。攻击者无法使用 `kubelet` 的凭据来更新节点对象或修改系统设置以将这些标签传递给 `kubelet`,因为 `kubelet` 不允许修改这些标签。如果为 pod 到节点调度使用了此前缀，它可以防止攻击者通过修改节点标签来吸引不同的工作负载集到节点的情况。

!!! Info
    我们也可以使用 [节点选择器](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector)而不是节点亲和性。但是，节点亲和性更具表现力，并允许在 pod 调度期间考虑更多条件。有关差异和更高级调度选择的更多信息，请参阅 CNCF 博客文章 [高级 Kubernetes pod 到节点调度](https://www.cncf.io/blog/2021/07/27/advanced-kubernetes-pod-to-node-scheduling/)。

#### 第 2 部分 - 污点和容忍度

吸引 pod 到节点只是这种三部曲方法的第一部分。为了使这种方法有效，我们必须阻止未经授权的 pod 调度到它们不被授权的节点上。为了阻止不需要或未经授权的 pod，Kubernetes 使用节点 [污点](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)。污点用于在节点上设置条件，以防止 pod 被调度。下面的污点使用键值对 `tenant: tenants-x`。

``` yaml
...
    taints:
      - key: tenant
        value: tenants-x
        effect: NoSchedule
...
```

给定上述节点 `taint`,只有 _容忍_ 该污点的 pod 才能被允许调度到该节点。为了允许授权的 pod 被调度到节点，相应的 pod 规范必须包含对该污点的 `toleration`,如下所示。

``` yaml
...
  tolerations:
  - effect: NoSchedule
    key: tenant
    operator: Equal
    value: tenants-x
...
```

具有上述 `toleration` 的 pod 不会因为该特定污点而被阻止调度到节点。污点也被 Kubernetes 用于在某些条件下(如节点资源压力)临时停止 pod 调度。使用节点亲和性、污点和容忍度，我们可以有效地将所需的 pod 吸引到特定节点，并阻止不需要的 pod。

!!! attention
    某些 Kubernetes pod 需要在所有节点上运行。这些 pod 的示例包括由 [容器网络接口 (CNI)](https://github.com/containernetworking/cni) 和 [kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) [daemonsets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) 启动的 pod。为此，这些 pod 的规范包含非常宽松的容忍度，以容忍不同的污点。应当注意不要更改这些容忍度。更改这些容忍度可能会导致集群操作不正确。此外，策略管理工具(如 [OPA/Gatekeeper](https://github.com/open-policy-agent/gatekeeper) 和 [Kyverno](https://kyverno.io/))可用于编写验证策略，以防止未经授权的 pod 使用这些宽松的容忍度。

#### 第 3 部分 - 基于策略的节点选择管理

有几种工具可用于帮助管理 pod 规范的节点亲和性和容忍度，包括在 CICD 管道中实施规则。但是，隔离的实施也应该在 Kubernetes 集群级别进行。为此，可以使用策略管理工具来 _变更_ 传入的 Kubernetes API 服务器请求，根据请求负载应用上述节点亲和性规则和容忍度。

例如，可以为 _tenants-x_ 命名空间中的 pod _添加标记_，以允许在 _tenants-x_ 节点上进行调度。利用配置为使用 Kubernetes [变更准入 Webhook](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#mutatingadmissionwebhook) 的策略管理工具，可以使用策略来变更传入的 pod 规范。变更会添加所需的元素以允许所需的调度。下面是一个使用 OPA/Gatekeeper 添加节点亲和性的策略示例。

``` yaml
apiVersion: mutations.gatekeeper.sh/v1alpha1
kind: Assign
metadata:
  name: mutator-add-nodeaffinity-pod
  annotations:
    aws-eks-best-practices/description: >-
      Adds Node affinity - https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#node-affinity
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    namespaces: ["tenants-x"]
  location: "spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms"
  parameters:
    assign:
      value: 
        - matchExpressions:
          - key: "tenant"
            operator: In
            values:
            - "tenants-x"
```

上述策略应用于 Kubernetes API 服务器请求，以将 pod 应用于 _tenants-x_ 命名空间。该策略添加了 `requiredDuringSchedulingIgnoredDuringExecution` 节点亲和性规则，以便将 pod 吸引到带有 `tenant: tenants-x` 标签的节点。

下面的第二个策略使用相同的目标命名空间和组、种类和版本匹配条件，将容忍度添加到同一 pod 规范中。

``` yaml
apiVersion: mutations.gatekeeper.sh/v1alpha1
kind: Assign
metadata:
  name: mutator-add-toleration-pod
  annotations:
    aws-eks-best-practices/description: >-
      Adds toleration - https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    namespaces: ["tenants-x"]
  location: "spec.tolerations"
  parameters:
    assign:
      value: 
      - key: "tenant"
        operator: "Equal"
        value: "tenants-x"
        effect: "NoSchedule"
```

上述策略专门针对 pod;这是由于策略中 `location` 元素中变更元素的路径。可以编写其他策略来处理创建 pod 的资源，如 Deployment 和 Job 资源。列出的策略和其他示例可以在本指南的配套 [GitHub 项目](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa/gatekeeper/node-selector)中查看。

这两个变更的结果是，pod 被吸引到所需的节点，同时也不会被特定节点的污点排斥。为了验证这一点，我们可以看到两个 `kubectl` 调用的输出片段，用于获取带有 `tenant=tenants-x` 标签的节点，以及获取 `tenants-x` 命名空间中的 pod。

``` bash
kubectl get nodes -l tenant=tenants-x
NAME                                        
ip-10-0-11-255...
ip-10-0-28-81...
ip-10-0-43-107...

kubectl -n tenants-x get pods -owide
NAME                                  READY   STATUS    RESTARTS   AGE   IP            NODE
tenant-test-deploy-58b895ff87-2q7xw   1/1     Running   0          13s   10.0.42.143   ip-10-0-43-107...
tenant-test-deploy-58b895ff87-9b6hg   1/1     Running   0          13s   10.0.18.145   ip-10-0-28-81...
tenant-test-deploy-58b895ff87-nxvw5   1/1     Running   0          13s   10.0.30.117   ip-10-0-28-81...
tenant-test-deploy-58b895ff87-vw796   1/1     Running   0          13s   10.0.3.113    ip-10-0-11-255...
tenant-test-pod                       1/1     Running   0          13s   10.0.35.83    ip-10-0-43-107...
```

正如我们从上面的输出中看到的，所有 pod 都被调度到带有 `tenant=tenants-x` 标签的节点上。简单地说，这些 pod 只会在所需的节点上运行，而其他没有所需亲和性和容忍度的 pod 则不会。租户工作负载实际上是隔离的。

下面是一个变更后的 pod 规范示例。

``` yaml
apiVersion: v1
kind: Pod
metadata:
  name: tenant-test-pod
  namespace: tenants-x
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: tenant
            operator: In
            values:
            - tenants-x
...
  tolerations:
  - effect: NoSchedule
    key: tenant
    operator: Equal
    value: tenants-x
...
```

!!! attention
    集成到 Kubernetes API 服务器请求流程的策略管理工具，使用变更和验证准入 Webhook，旨在在指定的时间内响应 API 服务器的请求。这通常是 3 秒或更短。如果 Webhook 调用未能在配置的时间内返回响应，则传入 API 服务器请求的变更和/或验证可能会或可能不会发生。这种行为取决于准入 Webhook 配置是设置为 [Fail Open 还是 Fail Close](https://open-policy-agent.github.io/gatekeeper/website/docs/#admission-webhook-fail-open-by-default)。

在上面的示例中，我们使用了为 OPA/Gatekeeper 编写的策略。但是，也有其他策略管理工具可以处理我们的节点选择用例。例如，可以使用这个 [Kyverno 策略](https://kyverno.io/policies/other/add_node_affinity/add_node_affinity/)来处理节点亲和性变更。

!!! tip
    如果操作正确，变更策略将对传入的 API 服务器请求负载产生所需的更改。但是，也应该包括验证策略，以在更改持久化之前验证所需的更改是否发生。在使用这些策略进行租户到节点隔离时，这一点尤其重要。定期检查集群是否存在不需要的配置也是个好主意。

### 参考资料

- [k-rail](https://github.com/cruise-automation/k-rail) 旨在帮助您通过实施某些策略来保护多租户环境。

- [使用 Amazon EKS 的多租户 SaaS 应用程序的安全实践](https://d1.awsstatic.com/whitepapers/security-practices-for-multi-tenant-saas-apps-using-eks.pdf)

## 硬多租户

可以通过为每个租户配置单独的集群来实现硬多租户。虽然这在租户之间提供了非常强大的隔离，但也有几个缺点。

首先，当您有许多租户时，这种方法很快就会变得昂贵。不仅您必须为每个集群支付控制平面成本，而且您将无法在集群之间共享计算资源。最终，您将遇到资源碎片化的情况，其中一部分集群利用不足，而另一部分集群则过度利用。

其次，您可能需要购买或构建特殊工具来管理所有这些集群。随着时间的推移，管理数百或数千个集群可能会变得过于繁重。

最后，为每个租户创建一个集群将比创建一个命名空间慢。但是，在高度监管的行业或需要强隔离的 SaaS 环境中，可能需要采用硬租户方法。

## 未来方向

Kubernetes 社区已经认识到软多租户的当前缺陷以及硬多租户的挑战。[多租户特别兴趣小组 (SIG)](https://github.com/kubernetes-sigs/multi-tenancy) 正试图通过几个孵化项目(包括分层命名空间控制器 (HNC) 和虚拟集群)来解决这些缺陷。

HNC 提案 (KEP) 描述了一种在命名空间之间创建父子关系的方式，具有 \[policy\] 对象继承以及租户管理员创建子命名空间的能力。

虚拟集群提案描述了为每个租户在集群内创建单独的控制平面服务实例(也称为"Kubernetes on Kubernetes")的机制，包括 API 服务器、控制器管理器和调度器。

[多租户基准](https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/README.md)提案提供了使用命名空间进行隔离和分段共享集群的指南，以及一个命令行工具 [kubectl-mtb](https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/kubectl-mtb/README.md) 来验证对这些指南的遵从性。

## 多集群管理工具和资源

- [Banzai Cloud](https://banzaicloud.com/)
- [Kommander](https://d2iq.com/solutions/ksphere/kommander)
- [Lens](https://github.com/lensapp/lens)
- [Nirmata](https://nirmata.com)
- [Rafay](https://rafay.co/)
- [Rancher](https://rancher.com/products/rancher/)
- [Weave Flux](https://www.weave.works/oss/flux/)