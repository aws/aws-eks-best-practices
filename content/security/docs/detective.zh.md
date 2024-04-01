# 审计和日志记录

收集和分析[审计]日志对于各种不同的原因都是有用的。日志可以帮助进行根本原因分析和归因，即将某个变更归因于特定用户。当收集了足够多的日志后，它们也可以用于检测异常行为。在 EKS 上，审计日志被发送到 Amazon Cloudwatch Logs。EKS 的审计策略如下：

```yaml
apiVersion: audit.k8s.io/v1beta1
kind: Policy
rules:
  # 记录 aws-auth configmap 的更改
  - level: RequestResponse
    namespaces: ["kube-system"]
    verbs: ["update", "patch", "delete"]
    resources:
      - group: "" # core
        resources: ["configmaps"]
        resourceNames: ["aws-auth"]
    omitStages:
      - "RequestReceived"
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
      - group: "" # core
        resources: ["endpoints", "services", "services/status"]
  - level: None
    users: ["kubelet"] # legacy kubelet identity
    verbs: ["get"]
    resources:
      - group: "" # core
        resources: ["nodes", "nodes/status"]
  - level: None
    userGroups: ["system:nodes"]
    verbs: ["get"]
    resources:
      - group: "" # core
        resources: ["nodes", "nodes/status"]
  - level: None
    users:
      - system:kube-controller-manager
      - system:kube-scheduler
      - system:serviceaccount:kube-system:endpoint-controller
    verbs: ["get", "update"]
    namespaces: ["kube-system"]
    resources:
      - group: "" # core
        resources: ["endpoints"]
  - level: None
    users: ["system:apiserver"]
    verbs: ["get"]
    resources:
      - group: "" # core
        resources: ["namespaces", "namespaces/status", "namespaces/finalize"]
  - level: None
    users:
      - system:kube-controller-manager
    verbs: ["get", "list"]
    resources:
      - group: "metrics.k8s.io"
  - level: None
    nonResourceURLs:
      - /healthz*
      - /version
      - /swagger*
  - level: None
    resources:
      - group: "" # core
        resources: ["events"]
  - level: Request
    users: ["kubelet", "system:node-problem-detector", "system:serviceaccount:kube-system:node-problem-detector"]
    verbs: ["update","patch"]
    resources:
      - group: "" # core
        resources: ["nodes/status", "pods/status"]
    omitStages:
      - "RequestReceived"
  - level: Request
    userGroups: ["system:nodes"]
    verbs: ["update","patch"]
    resources:
      - group: "" # core
        resources: ["nodes/status", "pods/status"]
    omitStages:
      - "RequestReceived"
  - level: Request
    users: ["system:serviceaccount:kube-system:namespace-controller"]
    verbs: ["deletecollection"]
    omitStages:
      - "RequestReceived"
  # Secrets、ConfigMaps 和 TokenReviews 可能包含敏感和二进制数据，
  # 因此只在元数据级别记录。
  - level: Metadata
    resources:
      - group: "" # core
        resources: ["secrets", "configmaps"]
      - group: authentication.k8s.io
        resources: ["tokenreviews"]
    omitStages:
      - "RequestReceived"
  - level: Request
    resources:
      - group: ""
        resources: ["serviceaccounts/token"]
  - level: Request
    verbs: ["get", "list", "watch"]
    resources: 
      - group: "" # core
      - group: "admissionregistration.k8s.io"
      - group: "apiextensions.k8s.io"
      - group: "apiregistration.k8s.io"
      - group: "apps"
      - group: "authentication.k8s.io"
      - group: "authorization.k8s.io"
      - group: "autoscaling"
      - group: "batch"
      - group: "certificates.k8s.io"
      - group: "extensions"
      - group: "metrics.k8s.io"
      - group: "networking.k8s.io"
      - group: "policy"
      - group: "rbac.authorization.k8s.io"
      - group: "scheduling.k8s.io"
      - group: "settings.k8s.io"
      - group: "storage.k8s.io"
    omitStages:
      - "RequestReceived"
  # 已知 API 的默认级别
  - level: RequestResponse
    resources: 
      - group: "" # core
      - group: "admissionregistration.k8s.io"
      - group: "apiextensions.k8s.io"
      - group: "apiregistration.k8s.io"
      - group: "apps"
      - group: "authentication.k8s.io"
      - group: "authorization.k8s.io"
      - group: "autoscaling"
      - group: "batch"
      - group: "certificates.k8s.io"
      - group: "extensions"
      - group: "metrics.k8s.io"
      - group: "networking.k8s.io"
      - group: "policy"
      - group: "rbac.authorization.k8s.io"
      - group: "scheduling.k8s.io"
      - group: "settings.k8s.io"
      - group: "storage.k8s.io"
    omitStages:
      - "RequestReceived"
  # 所有其他请求的默认级别。
  - level: Metadata
    omitStages:
      - "RequestReceived"
```

## 建议

### 启用审计日志

审计日志是 EKS 管理的 Kubernetes 控制平面日志的一部分，由 EKS 管理。启用/禁用控制平面日志(包括 Kubernetes API 服务器、控制器管理器和调度器的日志以及审计日志)的说明可以在这里找到，[https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html#enabling-control-plane-log-export](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html#enabling-control-plane-log-export)。

!!! info
    启用控制平面日志记录时，您将为在 CloudWatch 中存储日志而产生[成本](https://aws.amazon.com/cloudwatch/pricing/)。这引出了一个更广泛的问题，即安全性的持续成本。最终，您必须权衡这些成本与安全漏洞的成本，例如财务损失、声誉损害等。您可能会发现，通过实施本指南中的部分建议，您就可以充分保护您的环境。

!!! warning
    CloudWatch Logs 条目的最大大小为 [256KB](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html),而 Kubernetes API 请求的最大大小为 1.5MiB。大于 256KB 的日志条目将被截断或仅包含请求元数据。

### 利用审计元数据

Kubernetes 审计日志包括两个注释，用于指示请求是否被授权 `authorization.k8s.io/decision` 以及决策的原因 `authorization.k8s.io/reason`。使用这些属性来确定为什么允许特定的 API 调用。

### 为可疑事件创建警报

创建一个警报，在 403 Forbidden 和 401 Unauthorized 响应增加时自动提醒您，然后使用诸如 `host`、`sourceIPs` 和 `k8s_user.username` 等属性来找出这些请求来自何处。
  
### 使用 Log Insights 分析日志

使用 CloudWatch Log Insights 监控对 RBAC 对象的更改，例如 Roles、RoleBindings、ClusterRoles 和 ClusterRoleBindings。下面是一些示例查询：

列出对 `aws-auth` ConfigMap 的更新：

```bash
fields @timestamp, @message
| filter @logStream like "kube-apiserver-audit"
| filter verb in ["update", "patch"]
| filter objectRef.resource = "configmaps" and objectRef.name = "aws-auth" and objectRef.namespace = "kube-system"
| sort @timestamp desc
```

列出新创建的或对验证 Webhook 的更改：

```bash
fields @timestamp, @message
| filter @logStream like "kube-apiserver-audit"
| filter verb in ["create", "update", "patch"] and responseStatus.code = 201
| filter objectRef.resource = "validatingwebhookconfigurations"
| sort @timestamp desc
```

列出对 Roles 的创建、更新、删除操作：

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="roles" and verb in ["create", "update", "patch", "delete"]
```

列出对 RoleBindings 的创建、更新、删除操作：

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="rolebindings" and verb in ["create", "update", "patch", "delete"]
```

列出对 ClusterRoles 的创建、更新、删除操作：

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="clusterroles" and verb in ["create", "update", "patch", "delete"]
```

列出对 ClusterRoleBindings 的创建、更新、删除操作：

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="clusterrolebindings" and verb in ["create", "update", "patch", "delete"]
```

绘制对 Secrets 的未授权读取操作：

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="secrets" and verb in ["get", "watch", "list"] and responseStatus.code="401"
| stats count() by bin(1m)
```

列出失败的匿名请求：

```bash
fields @timestamp, @message, sourceIPs.0
| sort @timestamp desc
| limit 100
| filter user.username="system:anonymous" and responseStatus.code in ["401", "403"]
```

### 审计您的 CloudTrail 日志

由利用 IAM Roles for Service Accounts (IRSA) 的 pod 调用的 AWS API 会自动记录到 CloudTrail，并附带服务账户的名称。如果日志中出现未明确授权调用 API 的服务账户名称，则可能表示 IAM 角色的信任策略配置错误。总的来说，Cloudtrail 是将 AWS API 调用归因于特定 IAM 主体的一种很好的方式。

### 使用 CloudTrail Insights 发现可疑活动

CloudTrail Insights 会自动分析来自 CloudTrail 跟踪的写入管理事件，并在发现异常活动时向您发出警报。这可以帮助您识别您的 AWS 账户中写入 API 的调用量增加的情况，包括使用 IRSA 来承担 IAM 角色的 pod。有关更多信息，请参阅[宣布推出 CloudTrail Insights：识别和响应异常 API 活动](https://aws.amazon.com/blogs/aws/announcing-cloudtrail-insights-identify-and-respond-to-unusual-api-activity/)。

### 其他资源

随着日志量的增加，使用 Log Insights 或其他日志分析工具进行解析和过滤可能会变得无效。作为替代方案，您可能需要考虑运行 [Sysdig Falco](https://github.com/falcosecurity/falco) 和 [ekscloudwatch](https://github.com/sysdiglabs/ekscloudwatch)。Falco 分析审计日志并标记长期的异常或滥用行为。ekscloudwatch 项目将 CloudWatch 中的审计日志事件转发给 Falco 进行分析。Falco 提供了一组[默认审计规则](https://github.com/falcosecurity/plugins/blob/master/plugins/k8saudit/rules/k8s_audit_rules.yaml)以及添加您自己规则的能力。

另一个选择可能是将审计日志存储在 S3 中，并使用 SageMaker [Random Cut Forest](https://docs.aws.amazon.com/sagemaker/latest/dg/randomcutforest.html) 算法来检测需要进一步调查的异常行为。

## 工具和资源

以下商业和开源项目可用于评估您的集群与既定最佳实践的一致性：

- [Amazon EKS 安全沉浸式研讨会 - 检测控制](https://catalog.workshops.aws/eks-security-immersionday/en-US/5-detective-controls)
- [kubeaudit](https://github.com/Shopify/kubeaudit)
- [kube-scan](https://github.com/octarinesec/kube-scan) 根据 Kubernetes 通用配置评分系统框架为集群中运行的工作负载分配风险评分
- [kubesec.io](https://kubesec.io/)
- [polaris](https://github.com/FairwindsOps/polaris)
- [Starboard](https://github.com/aquasecurity/starboard)
- [Snyk](https://support.snyk.io/hc/en-us/articles/360003916138-Kubernetes-integration-overview)
- [Kubescape](https://github.com/kubescape/kubescape) Kubescape 是一个开源的 kubernetes 安全工具，可扫描集群、YAML 文件和 Helm 图表。它根据多个框架(包括 [NSA-CISA](https://www.armosec.io/blog/kubernetes-hardening-guidance-summary-by-armo/?utm_source=github&utm_medium=repository) 和 [MITRE ATT&CK®](https://www.microsoft.com/security/blog/2021/03/23/secure-containerized-environments-with-updated-threat-matrix-for-kubernetes/))检测错误配置。