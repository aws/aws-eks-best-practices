# 審核和記錄

收集和分析 \[audit\] 日誌對於各種不同的原因都很有用。日誌可以幫助根本原因分析和歸因,即將更改歸因於特定用戶。當收集了足夠的日誌後,它們也可以用於檢測異常行為。在 EKS 上,審核日誌被發送到 Amazon Cloudwatch Logs。EKS 的審核策略如下:

```yaml
apiVersion: audit.k8s.io/v1beta1
kind: Policy
rules:
  # 記錄 aws-auth configmap 更改
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
  # Secrets、ConfigMaps 和 TokenReviews 可能包含敏感和二進制數據,
  # 因此只在元數據級別記錄。
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
  # 已知 API 的默認級別
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
  # 所有其他請求的默認級別。
  - level: Metadata
    omitStages:
      - "RequestReceived"
```

## 建議

### 啟用審核日誌

審核日誌是 EKS 管理的 Kubernetes 控制平面日誌的一部分,由 EKS 管理。啟用/禁用控制平面日誌的說明(包括 Kubernetes API 服務器、控制器管理器和調度器的日誌,以及審核日誌)可以在這裡找到, [https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html#enabling-control-plane-log-export](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html#enabling-control-plane-log-export)。

!!! info
    啟用控制平面日誌記錄時,您將為在 CloudWatch 中存儲日誌產生 [成本](https://aws.amazon.com/cloudwatch/pricing/)。這提出了一個更廣泛的問題,即安全性的持續成本。最終,您將不得不權衡這些成本與安全漏洞的成本,例如財務損失、聲譽損失等。您可能會發現,通過實施本指南中的部分建議,您可以充分保護您的環境。

!!! warning
    CloudWatch Logs 條目的最大大小為 [256KB](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html),而 Kubernetes API 請求的最大大小為 1.5MiB。大於 256KB 的日誌條目將被截斷或僅包含請求元數據。

### 利用審核元數據

Kubernetes 審核日誌包括兩個註釋,表示請求是否獲得授權 `authorization.k8s.io/decision` 和決策原因 `authorization.k8s.io/reason`。使用這些屬性來確定為什麼允許特定的 API 調用。

### 為可疑事件創建警報

創建一個警報,在 403 Forbidden 和 401 Unauthorized 響應增加時自動提醒您,然後使用屬性如 `host`、`sourceIPs` 和 `k8s_user.username` 來找出這些請求來自哪裡。

### 使用 Log Insights 分析日誌

使用 CloudWatch Log Insights 監控對 RBAC 對象的更改,例如 Roles、RoleBindings、ClusterRoles 和 ClusterRoleBindings。以下是一些示例查詢:

列出對 `aws-auth` ConfigMap 的更新:

```bash
fields @timestamp, @message
| filter @logStream like "kube-apiserver-audit"
| filter verb in ["update", "patch"]
| filter objectRef.resource = "configmaps" and objectRef.name = "aws-auth" and objectRef.namespace = "kube-system"
| sort @timestamp desc
```

列出新建或更改驗證 webhooks:

```bash
fields @timestamp, @message
| filter @logStream like "kube-apiserver-audit"
| filter verb in ["create", "update", "patch"] and responseStatus.code = 201
| filter objectRef.resource = "validatingwebhookconfigurations"
| sort @timestamp desc
```

列出對 Roles 的創建、更新、刪除操作:

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="roles" and verb in ["create", "update", "patch", "delete"]
```

列出對 RoleBindings 的創建、更新、刪除操作:

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="rolebindings" and verb in ["create", "update", "patch", "delete"]
```

列出對 ClusterRoles 的創建、更新、刪除操作:

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="clusterroles" and verb in ["create", "update", "patch", "delete"]
```

列出對 ClusterRoleBindings 的創建、更新、刪除操作:

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="clusterrolebindings" and verb in ["create", "update", "patch", "delete"]
```

繪製對 Secrets 的未經授權讀取操作:

```bash
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="secrets" and verb in ["get", "watch", "list"] and responseStatus.code="401"
| stats count() by bin(1m)
```

失敗的匿名請求列表:

```bash
fields @timestamp, @message, sourceIPs.0
| sort @timestamp desc
| limit 100
| filter user.username="system:anonymous" and responseStatus.code in ["401", "403"]
```

### 審核您的 CloudTrail 日誌

由利用 IAM Roles for Service Accounts (IRSA) 的 pod 調用的 AWS API 會自動記錄到 CloudTrail,並附帶服務帳戶的名稱。如果日誌中出現了一個未明確授權調用 API 的服務帳戶名稱,這可能表示 IAM 角色的信任策略配置錯誤。總的來說,Cloudtrail 是將 AWS API 調用歸因於特定 IAM 主體的一個很好的方式。

### 使用 CloudTrail Insights 發現可疑活動

CloudTrail insights 自動分析來自 CloudTrail 跟蹤的寫入管理事件,並在發生異常活動時向您發出警報。這可以幫助您識別您的 AWS 帳戶中寫入 API 的調用量增加,包括來自使用 IRSA 承擔 IAM 角色的 pod。有關更多信息,請參閱 [Announcing CloudTrail Insights: Identify and Response to Unusual API Activity](https://aws.amazon.com/blogs/aws/announcing-cloudtrail-insights-identify-and-respond-to-unusual-api-activity/)。

### 其他資源

隨著日誌量的增加,使用 Log Insights 或其他日誌分析工具解析和過濾它們可能會變得無效。作為替代方案,您可能需要考慮運行 [Sysdig Falco](https://github.com/falcosecurity/falco) 和 [ekscloudwatch](https://github.com/sysdiglabs/ekscloudwatch)。Falco 分析審核日誌並標記長期的異常或濫用行為。ekscloudwatch 項目將審核日誌事件從 CloudWatch 轉發到 Falco 進行分析。Falco 提供了一組 [默認審核規則](https://github.com/falcosecurity/plugins/blob/master/plugins/k8saudit/rules/k8s_audit_rules.yaml) 以及添加您自己規則的能力。

另一個選擇可能是將審核日誌存儲在 S3 中,並使用 SageMaker [Random Cut Forest](https://docs.aws.amazon.com/sagemaker/latest/dg/randomcutforest.html) 算法來檢測需要進一步調查的異常行為。

## 工具和資源

以下商業和開源項目可用於評估您的集群與既定最佳實踐的一致性:

- [Amazon EKS Security Immersion Workshop - Detective Controls](https://catalog.workshops.aws/eks-security-immersionday/en-US/5-detective-controls)
- [kubeaudit](https://github.com/Shopify/kubeaudit)
- [kube-scan](https://github.com/octarinesec/kube-scan) 根據 Kubernetes 通用配置評分系統框架為您的集群中運行的工作負載分配風險分數
- [kubesec.io](https://kubesec.io/)
- [polaris](https://github.com/FairwindsOps/polaris)
- [Starboard](https://github.com/aquasecurity/starboard)
- [Snyk](https://support.snyk.io/hc/en-us/articles/360003916138-Kubernetes-integration-overview)
- [Kubescape](https://github.com/kubescape/kubescape) Kubescape 是一個開源的 kubernetes 安全工具,可以掃描集群、YAML 文件和 Helm 圖表。它根據多個框架檢測錯誤配置(包括 [NSA-CISA](https://www.armosec.io/blog/kubernetes-hardening-guidance-summary-by-armo/?utm_source=github&utm_medium=repository) 和 [MITRE ATT&CK®](https://www.microsoft.com/security/blog/2021/03/23/secure-containerized-environments-with-updated-threat-matrix-for-kubernetes/))。
