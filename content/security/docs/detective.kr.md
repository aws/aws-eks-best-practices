# 감사 및 로깅
\[ 감사 \] 로그를 수집하고 분석 하는 것은 여러 가지 이유로 유용합니다. 로그는 근본 원인 분석 및 속성, 즉 특정 사용자에 대한 변경을 설명하는 데 도움이 될 수 있습니다. 충분한 로그가 수집되면 비정상적인 동작을 감지하는 데에도 사용할 수 있습니다. EKS에서 감사 로그는 Amazon Cloudwatch Logs로 전송됩니다. EKS에 대한 감사 정책은 다음과 같습니다.

```yaml
apiVersion : audit.k8s.io/v1beta1
종류 : 정책
규칙 :
  # aws-auth configmap 변경 사항 기록
- 수준 : 요청 응답
    네임스페이스 : [ "kube-system" ]
    동사 : [ "업데이트" , "패치" , "삭제" ]
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "configmaps" ]
        리소스 이름 : [ "aws-auth" ]
    생략단계 :
- "요청 접수됨"
- 레벨 : 없음
    사용자 : [ "시스템:kube-proxy" ]
    동사 : [ "시계" ]
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "엔드포인트" , "서비스" , "서비스/상태" ]
- 레벨 : 없음
    users : [ "kubelet" ] # 레거시 kubelet ID
    동사 : [ "얻다" ]
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "노드" , "노드/상태" ]
- 레벨 : 없음
    사용자 그룹 : [ "시스템:노드" ]
    동사 : [ "얻다" ]
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "노드" , "노드/상태" ]
- 레벨 : 없음
    사용자 :
- 시스템:kube-controller-manager
- 시스템: kube-scheduler
- 시스템:서비스 계정:kube-시스템:엔드포인트 컨트롤러
    동사 : [ "얻다" , "업데이트하다" ]
    네임스페이스 : [ "kube-system" ]
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "엔드포인트" ]
- 레벨 : 없음
    사용자 : [ "시스템:apiserver" ]
    동사 : [ "얻다" ]
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "네임스페이스" , "네임스페이스/상태" , "네임스페이스/종료" ]
- 레벨 : 없음
    사용자 :
- 시스템:kube-controller-manager
    동사 : [ "얻다" , "목록" ]
    리소스 :
- 그룹 : "metrics.k8s.io"
- 레벨 : 없음
    nonResourceURLs :
- /healthz*
- /버전
- /swagger*
- 레벨 : 없음
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "이벤트" ]
- 레벨 : 의뢰
    사용자 : [ "kubelet" , "system:node-problem-detector" , "system:serviceaccount:kube-system:node-problem-detector" ]
    동사 : [ "업데이트" , "패치" ]
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "노드/상태" , "포드/상태" ]
    생략단계 :
- "요청 접수됨"
- 레벨 : 의뢰
    사용자 그룹 : [ "시스템:노드" ]
    동사 : [ "업데이트" , "패치" ]
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "노드/상태" , "포드/상태" ]
    생략단계 :
- "요청 접수됨"
- 레벨 : 의뢰
    사용자 : [ "system:serviceaccount:kube-system:namespace-controller" ]
    동사 : [ "deletecollection" ]
    생략단계 :
- "요청 접수됨"
  # Secrets, ConfigMaps 및 TokenReviews는 민감한 바이너리 데이터를 포함할 수 있습니다.
  # 따라서 메타데이터 수준에서만 기록합니다.
- 레벨 : 메타데이터
    리소스 :
- 그룹 : "" # 핵심
        리소스 : [ "비밀" , "configmaps" ]
- 그룹 : authentication.k8s.io
        자원 : [ "tokenreviews" ]
    생략단계 :
- "요청 접수됨"
- 레벨 : 의뢰
    리소스 :
- 그룹 : ""
        리소스 : [ "서비스 계정/토큰" ]
- 레벨 : 의뢰
    동사 : [ "get" , "list" , "watch" ]
    리소스 :
- 그룹 : "" # 핵심
- 그룹 : "admissionregistration.k8s.io"
- 그룹 : "apiextensions.k8s.io"
- 그룹 : "apiregistration.k8s.io"
- 그룹 : "앱"
- 그룹 : "authentication.k8s.io"
- 그룹 : "authorization.k8s.io"
- 그룹 : "자동 확장"
- 그룹 : "배치"
- 그룹 : "certificates.k8s.io"
- 그룹 : "확장 프로그램"
- 그룹 : "metrics.k8s.io"
- 그룹 : "networking.k8s.io"
- 그룹 : "정책"
- 그룹 : "rbac.authorization.k8s.io"
- 그룹 : "scheduling.k8s.io"
- 그룹 : "settings.k8s.io"
- 그룹 : "storage.k8s.io"
    생략단계 :
- "요청 접수됨"
  # 알려진 API의 기본 수준
- 수준 : 요청 응답
    리소스 :
- 그룹 : "" # 핵심
- 그룹 : "admissionregistration.k8s.io"
- 그룹 : "apiextensions.k8s.io"
- 그룹 : "apiregistration.k8s.io"
- 그룹 : "앱"
- 그룹 : "authentication.k8s.io"
- 그룹 : "authorization.k8s.io"
- 그룹 : "자동 확장"
- 그룹 : "배치"
- 그룹 : "certificates.k8s.io"
- 그룹 : "확장 프로그램"
- 그룹 : "metrics.k8s.io"
- 그룹 : "networking.k8s.io"
- 그룹 : "정책"
- 그룹 : "rbac.authorization.k8s.io"
- 그룹 : "scheduling.k8s.io"
- 그룹 : "settings.k8s.io"
- 그룹 : "storage.k8s.io"
    생략단계 :
- "요청 접수됨"
  # 다른 모든 요청에 대한 기본 수준.
- 레벨 : 메타데이터
    생략단계 :
- "요청 접수됨"
```

## 추천

### 감사 로그 활성화
감사 로그는 EKS에서 관리하는 EKS 관리형 Kubernetes 제어 플레인 로그의 일부입니다. 감사 로그와 함께 Kubernetes API 서버, 컨트롤러 관리자 및 스케줄러에 대한 로그를 포함하는 컨트롤 플레인 로그 활성화/비활성화에 대한 지침은 [ https://docs.aws.amazon. com/eks/latest/userguide/control-plane-logs.html#enabling-control-plane-log-export ]( https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs .html#enabling-control-plane-log-export ).

!!! 정보
제어 플레인 로깅을 활성화하면 CloudWatch에 로그를 저장하는 데 [ 비용 ]( https://aws.amazon.com/cloudwatch/pricing/ )이 발생합니다. 이것은 지속적인 보안 비용에 대한 더 광범위한 문제를 제기합니다. 궁극적으로 이러한 비용을 보안 위반 비용(예: 금전적 손실, 평판 손상 등)과 비교하여 평가해야 합니다. 이 가이드의 권장 사항 중 일부만 구현하여 환경을 적절하게 보호할 수 있음을 알 수 있습니다.

!!! 경고
CloudWatch Logs 항목의 최대 크기는 [ 256KB ]( https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html )인 반면 최대 Kubernetes API 요청 크기는 1.5MiB입니다. 256KB보다 큰 로그 항목은 잘리거나 요청 메타데이터만 포함합니다.

### 감사 메타데이터 활용
' 승인 되었는지 여부와 'authorization.k8s.io/reason' 결정 이유를 나타내는 두 개의 주석이 포함 됩니다 . 이러한 속성을 사용하여 특정 API 호출이 허용된 이유를 확인하십시오.
   
### 의심스러운 이벤트에 대한 알람 생성
403 Forbidden 및 401 Unauthorized 응답이 증가하는 위치를 자동으로 알리는 경보를 생성한 다음 `host` , `sourceIPs` 및 `k8s_user.username` 과 같은 속성을 사용 하여 이러한 요청이 어디에서 오는지 알아냅니다.
  
### Log Insights로 로그 분석
CloudWatch Log Insights를 사용하여 RBAC 개체(예: Roles, RoleBindings, ClusterRoles 및 ClusterRoleBindings)에 대한 변경 사항을 모니터링합니다. 몇 가지 샘플 쿼리가 아래에 나와 있습니다.

`aws-auth` ConfigMap 에 대한 업데이트를 나열합니다 .
```
필드 @timestamp, @message
| "kube-apiserver-audit"와 같은 @logStream 필터
| ["업데이트", "패치"]의 필터 동사
| 필터 objectRef.resource = "configmaps" 및 objectRef.name = "aws-auth" 및 objectRef.namespace = "kube-system"
| 정렬 @timestamp 설명
```
유효성 검사 Webhook에 대한 새로운 생성 또는 변경 사항을 나열합니다.
```
필드 @timestamp, @message
| "kube-apiserver-audit"와 같은 @logStream 필터
| ["만들기", "업데이트", "패치"] 및 responseStatus.code = 201의 필터 동사
| 필터 objectRef.resource = "webhook 구성 유효성 검사"
| 정렬 @timestamp 설명
```
역할에 대한 생성, 업데이트, 삭제 작업을 나열합니다.
```
필드 @timestamp, @message
| 정렬 @timestamp 설명
| 제한 100
| 필터 objectRef.resource="roles" 및 ["create", "update", "patch", "delete"]의 동사
```
RoleBindings에 대한 생성, 업데이트, 삭제 작업을 나열합니다.
```
필드 @timestamp, @message
| 정렬 @timestamp 설명
| 제한 100
| 필터 objectRef.resource="rolebindings" 및 ["create", "update", "patch", "delete"]의 동사
```
ClusterRole에 대한 생성, 업데이트, 삭제 작업을 나열합니다.
```
필드 @timestamp, @message
| 정렬 @timestamp 설명
| 제한 100
| 필터 objectRef.resource="clusterroles" 및 ["create", "update", "patch", "delete"]의 동사
```
ClusterRoleBindings에 대한 생성, 업데이트, 삭제 작업을 나열합니다.
```
필드 @timestamp, @message
| 정렬 @timestamp 설명
| 제한 100
| 필터 objectRef.resource="clusterrolebindings" 및 ["create", "update", "patch", "delete"]의 동사
```
보안 비밀에 대한 무단 읽기 작업을 플로팅합니다.
```
필드 @timestamp, @message
| 정렬 @timestamp 설명
| 제한 100
| 필터 objectRef.resource="secrets" 및 ["get", "watch", "list"] 및 responseStatus.code="401"의 동사
| 통계 count() by bin(1m)
```
실패한 익명 요청 목록:
```
필드 @timestamp, @message, sourceIPs.0
| 정렬 @timestamp 설명
| 제한 100
| 필터 user.username="system:anonymous" 및 ["401", "403"]의 responseStatus.code
```

### CloudTrail 로그 감사
서비스 계정에 대한 IAM 역할(IRSA)을 활용하는 포드에서 호출한 AWS API는 서비스 계정의 이름과 함께 CloudTrail에 자동으로 기록됩니다. API를 호출하도록 명시적으로 승인되지 않은 서비스 계정의 이름이 로그에 나타나면 IAM 역할의 신뢰 정책이 잘못 구성되었음을 나타낼 수 있습니다. 일반적으로 Cloudtrail은 AWS API 호출을 특정 IAM 주체에 할당하는 좋은 방법입니다.

### CloudTrail Insights를 사용하여 의심스러운 활동 발견
CloudTrail 통찰력은 CloudTrail 추적에서 쓰기 관리 이벤트를 자동으로 분석하고 비정상적인 활동을 알려줍니다. 이렇게 하면 IRSA를 사용하여 IAM 역할을 수임하는 포드를 포함하여 AWS 계정의 쓰기 API에 대한 호출 볼륨이 증가하는 시기를 식별하는 데 도움이 될 수 있습니다. [ CloudTrail Insights 발표: 비정상적인 API 활동 식별 및 대응 ]( https://aws.amazon.com/blogs/aws/announcing-cloudtrail-insights-identify-and-respond-to-unusual-api-activity/ ) 을 참조하십시오. 자세한 내용은.

### 추가 리소스
로그 볼륨이 증가함에 따라 Log Insights 또는 다른 로그 분석 도구를 사용하여 로그를 구문 분석하고 필터링하는 것이 효과가 없을 수 있습니다. 대안으로 [ Sysdig Falco ]( https://github.com/falcosecurity/falco ) 및 [ ekscloudwatch ]( https://github.com/sysdiglabs/ekscloudwatch ) 실행을 고려할 수 있습니다. Falco는 감사 로그를 분석하고 장기간에 걸쳐 이상 또는 악용을 표시합니다. ekscloudwatch 프로젝트는 분석을 위해 CloudWatch에서 Falco로 감사 로그 이벤트를 전달합니다. Falco는 고유한 추가 기능과 함께 [ 기본 감사 규칙 ]( https://github.com/falcosecurity/plugins/blob/master/plugins/k8saudit/rules/k8s_audit_rules.yaml ) 세트를 제공합니다.

또 다른 옵션은 감사 로그를 S3에 저장하고 SageMaker [ Random Cut Forest ]( https://docs.aws.amazon.com/sagemaker/latest/dg/randomcutforest.html ) 알고리즘을 사용하여 비정상적인 동작을 보장하는 것입니다. 추가 조사.

## 툴링
다음 상용 및 오픈 소스 프로젝트를 사용하여 클러스터가 확립된 모범 사례와 일치하는지 평가할 수 있습니다.

+ [ kubeaudit ]( https://github.com/Shopify/kubeaudit )
+ [ 메킷 ]( https://github.com/darkbitio/mkit )
+ [ kube-scan ]( https://github.com/octarinesec/kube-scan ) Kubernetes Common Configuration Scoring System 프레임워크에 따라 클러스터에서 실행 중인 워크로드에 위험 점수를 할당합니다.
+ [ amicontained ]( https://github.com/genuinetools/amicontained ) 어떤 기능이 허용되고 컨테이너 런타임에 의해 차단되는 시스템 호출이 표시됩니다.
+ [ kubesec.io ]( https://kubesec.io/ )
+ [ 폴라리스 ]( https://github.com/FairwindsOps/polaris )
+ [ 스타보드 ]( https://github.com/aquasecurity/starboard )
+ [ kAudit ]( https://github.com/alcideio/kaudit )
+ [ Snyk ]( https://support.snyk.io/hc/en-us/articles/360003916138-Kubernetes-integration-overview )


