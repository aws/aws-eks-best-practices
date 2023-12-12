# 감사(Audit) 및 로깅
\[감사\] 로그를 수집하고 분석하는 것은 여러 가지 이유로 유용합니다. 로그는 근본 원인 분석(RCA) 및 책임 분석(예: 특정 변경에 대한 사용자 추적)에 도움이 될 수 있습니다. 로그가 충분히 수집되면 이를 사용하여 이상 행동을 탐지할 수도 있습니다. EKS에서는 감사 로그가 Amazon Cloudwatch 로그로 전송됩니다. EKS의 감사 정책은 다음과 같습니다. 

```yaml
apiVersion: audit.k8s.io/v1beta1
kind: Policy
rules:
  # Log aws-auth configmap changes
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
  # Secrets, ConfigMaps, and TokenReviews can contain sensitive & binary data,
  # so only log at the Metadata level.
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
  # Default level for known APIs
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
  # Default level for all other requests.
  - level: Metadata
    omitStages:
      - "RequestReceived"
``` 

## 권장 사항

### 감사 로그 활성화
감사 로그는 EKS에서 관리하는 EKS 관리형 쿠버네티스 컨트롤 플레인 로그의 일부입니다. 쿠버네티스 API 서버, 컨트롤러 관리자 및 스케줄러에 대한 로그와 감사 로그를 포함하는 컨트롤 플레인 로그의 활성화/비활성화 지침은 [AWS 문서](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html#enabling-control-plane-log-export)에서 확인할 수 있습니다. 

!!! info
    컨트롤 플레인 로깅을 활성화하면 로그를 CloudWatch에 저장하는 데 [비용](https://aws.amazon.com/cloudwatch/pricing/)이 발생합니다. 이로 인해 지속적인 보안 비용에 대한 광범위한 문제가 제기됩니다. 궁극적으로 이런 비용을 보안 침해 비용 (예: 재정적 손실, 평판 훼손 등)과 비교해야 합니다. 이 가이드의 권장 사항 중 일부만 구현하면 환경을 적절하게 보호할 수 있을 것입니다. 

!!! warning
    클라우드워치 로그 항목의 최대 크기는 [256KB](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html)인 반면 쿠버네티스 API 요청 최대 크기는 1.5MiB입니다. 256KB를 초과하는 로그 항목은 잘리거나 요청 메타데이터만 포함됩니다. 

### 감사 메타데이터 활용
쿠버네티스 감사 로그에는 요청이 승인되었는지 여부를 나타내는 `authorization.k8s.io/decision`와 결정의 이유를 나타내는 `authorization.k8s.io/reason`, 두 개의 어노테이션이 포함되어 있습니다. 이런 속성을 사용하여 특정 API 호출이 허용된 이유를 확인할 수 있습니다. 
   
### 의심스러운 이벤트에 대한 알람 생성
403 Forbidden 및 401 Unauthorized 응답이 증가하는 위치를 자동으로 알리는 경보를 생성한 다음 `host` , `sourceIPs` 및 `k8s_user.username` 과 같은 속성을 사용 하여 이런 요청의 출처를 찾아냅니다.
  
### Log Insights로 로그 분석
CloudWatch Log Insights를 사용하여 RBAC 객체 (예: 롤, 롤바인딩, 클러스터롤, 클러스터 롤바인딩) 에 대한 변경 사항을 모니터링할 수 있습니다. 몇 가지 샘플 쿼리는 다음과 같습니다. 

`aws-auth` 컨피그맵 에 대한 업데이트를 나열합니다:
```
fields @timestamp, @message
| filter @logStream like "kube-apiserver-audit"
| filter verb in ["update", "patch"]
| filter objectRef.resource = "configmaps" and objectRef.name = "aws-auth" and objectRef.namespace = "kube-system"
| sort @timestamp desc
```
Validation 웹훅에 대한 생성 또는 변경 사항을 나열합니다:
```
fields @timestamp, @message
| filter @logStream like "kube-apiserver-audit"
| filter verb in ["create", "update", "patch"] and responseStatus.code = 201
| filter objectRef.resource = "validatingwebhookconfigurations"
| sort @timestamp desc
```
롤에 대한 생성, 업데이트, 삭제 작업을 나열합니다:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="roles" and verb in ["create", "update", "patch", "delete"]
```
롤바인딩에 대한 생성, 업데이트, 삭제 작업을 나열합니다:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="rolebindings" and verb in ["create", "update", "patch", "delete"]
```
클러스터롤에 대한 생성, 업데이트, 삭제 작업을 나열합니다:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="clusterroles" and verb in ["create", "update", "patch", "delete"]
```
클러스터롤바인딩에 대한 생성, 업데이트, 삭제 작업을 나열합니다:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="clusterrolebindings" and verb in ["create", "update", "patch", "delete"]
```
시크릿에 대한 무단 읽기 작업을 표시합니다:
```
fields @timestamp, @message
| sort @timestamp desc
| limit 100
| filter objectRef.resource="secrets" and verb in ["get", "watch", "list"] and responseStatus.code="401"
| stats count() by bin(1m)
```
실패한 익명 요청 목록:
```
fields @timestamp, @message, sourceIPs.0
| sort @timestamp desc
| limit 100
| filter user.username="system:anonymous" and responseStatus.code in ["401", "403"]
```

### CloudTrail 로그 감사
IAM Roles for Service Account(IRSA)을 활용하는 파드에서 호출한 AWS API는 서비스 어카운트 이름과 함께 CloudTrail에 자동으로 로깅됩니다. API 호출 권한이 명시적으로 부여되지 않은 서비스 어카운트의 이름이 로그에 표시되면 IAM 역할의 신뢰 정책이 잘못 구성되었다는 표시일 수 있습니다. 일반적으로 Cloudtrail은 AWS API 호출을 특정 IAM 보안 주체에 할당할 수 있는 좋은 방법입니다. 

### CloudTrail Insights를 사용하여 의심스러운 활동 발견
CloudTrail Insights는 CloudTrail 트레일에서 쓰기 관리 이벤트를 자동으로 분석하고 비정상적인 활동이 발생하면 알려줍니다. 이를 통해 IRSA 기능을 사용하여 IAM 역할을 맡는 파드 등 AWS 계정의 쓰기 API에 대한 호출량이 증가하는 시기를 파악할 수 있습니다. 자세한 내용은 [CloudTrail Insights 발표: 비정상적인 API 활동 식별 및 대응](https://aws.amazon.com/blogs/aws/announcing-cloudtrail-insights-identify-and-respond-to-unusual-api-activity/)을 참조하십시오.

### 추가 리소스
로그의 양이 증가하면 Log Insights 또는 다른 로그 분석 도구를 사용하여 로그를 파싱하고 필터링하는 것이 비효율적일 수 있습니다. 대안으로 [Sysdig Falco](https://github.com/falcosecurity/falco)와 [ekscloudwatch](https://github.com/sysdiglabs/ekscloudwatch)를 실행하는 것도 고려해 볼 수 있습니다. Falco는 감사 로그를 분석하고 오랜 기간 동안 이상 징후나 악용에 대해 플래그를 지정합니다. ekscloudwatch 프로젝트는 분석을 위해 CloudWatch의 감사 로그 이벤트를 팔코로 전달합니다. 팔코는 일련의 [기본 감사 규칙](https://github.com/falcosecurity/plugins/blob/master/plugins/k8saudit/rules/k8s_audit_rules.yaml)과 함께 자체 감사 규칙을 추가할 수 있는 기능을 제공합니다. 

또 다른 옵션은 감사 로그를 S3에 저장하고 SageMaker [Random Cut Forest](https://docs.aws.amazon.com/sagemaker/latest/dg/randomcutforest.html) 알고리즘을 사용하여 추가 조사가 필요한 이상 동작에 사용하는 것일 수 있습니다.

## 도구
다음 상용 및 오픈 소스 프로젝트를 사용하여 클러스터가 확립된 모범 사례와 일치하는지 평가할 수 있습니다.

+ [kubeaudit](https://github.com/Shopify/kubeaudit)
+ [kube-scan](https://github.com/octarinesec/kube-scan) 쿠버네티스 공통 구성 점수 산정 시스템 프레임워크에 따라 클러스터에서 실행 중인 워크로드에 위험 점수를 할당합니다.
+ [kubesec.io](https://kubesec.io/)
+ [polaris](https://github.com/FairwindsOps/polaris)
+ [Starboard](https://github.com/aquasecurity/starboard)
+ [Snyk](https://support.snyk.io/hc/en-us/articles/360003916138-Kubernetes-integration-overview)
+ [Kubescape](https://github.com/kubescape/kubescape) Kubescape는 클러스터, YAML 파일 및 헬름 차트를 스캔하는 오픈 소스 쿠버네티스 보안 도구입니다. 여러 프레임워크 ([NSA-CISA](https://www.armosec.io/blog/kubernetes-hardening-guidance-summary-by-armo/?utm_source=github&utm_medium=repository) 및 [MITRE ATT&CK®](https://www.microsoft.com/security/blog/2021/03/23/secure-containerized-environments-with-updated-threat-matrix-for-kubernetes/))에 따라 설정 오류를 탐지합니다.