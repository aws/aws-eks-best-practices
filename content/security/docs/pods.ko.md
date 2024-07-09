---
search:
  exclude: true
---


# 파드 보안

파드 사양에는 전반적인 보안 태세를 강화하거나 약화시킬 수 있는 다양한 속성이 포함되어 있습니다. 쿠버네티스 실무자로서 주요 관심사는 컨테이너에서 실행 중인 프로세스가 컨테이너 런타임의 격리 경계를 벗어나 기본 호스트에 대한 액세스 권한을 얻지 못하도록 하는 것입니다.

### 리눅스 기능

컨테이너 내에서 실행되는 프로세스는 기본적으로 \[Linux\] 루트 사용자의 컨텍스트에서 실행됩니다. 컨테이너 내의 루트 작업은 컨테이너 런타임이 컨테이너에 할당하는 리눅스 기능 세트에 의해 부분적으로 제한되지만 이런 기본 권한을 통해 공격자는 권한을 에스컬레이션하거나 호스트에 바인딩된 민감한 정보에 액세스할 수 있습니다. 비밀 및 컨피그맵을 포함합니다. 다음은 컨테이너에 할당된 기본 기능 목록입니다. 각 기능에 대한 추가 정보는 [해당 문서](http://man7.org/linux/man-pages/man7/capabilities.7.html)를 참조하십시오.

`CAP_AUDIT_WRITE, CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FOWNER, CAP_FSETID, CAP_KILL, CAP_MKNOD, CAP_NET_BIND_SERVICE, CAP_NET_RAW, CAP_SETGID, CAP_SETUID, CAP_SETFCAP, CAP_SETPCAP, CAP_SYS_CHROOT`

!!! info
    
    EC2 및 Fargate 파드에는 기본적으로 앞서 언급한 기능이 할당됩니다. 또한 Linux 기능은 Fargate 파드에서만 삭제할 수 있습니다.

Privileged 권한으로 실행되는 파드는 호스트의 루트와 연결된 Linux 기능의 _모든 권한_ 을 상속합니다. 가능한 해당 권한으로 실행은 지양하여야 합니다.

### 노드 승인

모든 쿠버네티스 워커 노드는 [노드 인증](https://kubernetes.io/docs/reference/access-authn-authz/node/)이라는 권한 부여 모드를 사용합니다.노드 인증은 kubelet에서 시작되는 모든 API 요청을 승인하고 노드가 다음 작업을 수행할 수 있도록 합니다. 

읽기 작업:

+ 서비스
+ 엔드포인트
+ 노드
+ 파드
+ kubelet의 노드에 바인딩된 파드와 관련된 시크릿, 컨피그맵, 퍼시스턴트 볼륨 클레임 및 퍼시스턴트 볼륨

쓰기 작업:

+ 노드 및 노드 상태( `NodeRestriction` 어드미션 플러그인을 활성화하여 kubelet이 자신의 노드를 수정하도록 제한)
+ 파드 및 파드 상태( `NodeRestriction` 어드미션 플러그인을 활성화하여 kubelet이 자신에게 바인딩된 pod를 수정하도록 제한)
+ 이벤트

인증 관련 작업:

+ TLS 부트스트래핑을 위한 인증서 서명 요청(CSR) API에 대한 읽기/쓰기 권한
+ 위임 인증/권한 확인을 위한 TokenReview 및 SubjectAccessReview 생성 권한

EKS는 [노드 제한 어드미션 컨트롤러](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction)를 사용하여 노드가 제한된 노드 속성 및 파드 세트만 수정하도록 허용합니다. 노드에 바인딩된 개체입니다. 그럼에도 불구하고 호스트에 대한 액세스를 관리하는 공격자는 클러스터 내에서 측면 이동을 허용할 수 있는 쿠버네티스 API에서 환경에 대한 민감한 정보를 수집할 수 있습니다.

## 파드 보안 솔루션

### 파드 시큐리티 폴리시(PSP)

과거에는 [파드 시큐리티 폴리시(PSP)](https://kubernetes.io/docs/concepts/policy/pod-security-policy/) 리소스를 사용하여 파드가 충족해야 하는 일련의 요구 사항을 지정했습니다. Kubernetes 버전 1.21부터 PSP는 더 이상 사용되지 않습니다. Kubernetes 버전 1.25에서 제거될 예정입니다.

!!! attention
    
    Kubernetes 버전 1.21부터 [PSP는 더 이상 사용되지 않습니다](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/). P2P가 더이상 지원되지 않을 버전 1.25까지 대안 솔루션으로 전환하는데 대략 2년의 시간이 남았습니다. 이 [문서](https://github.com/kubernetes/enhancements/blob/master/keps/sig-auth/2579-psp-replacement/README.md#motivation)는 이런 지원 중단의 동기에 대하여 설명합니다.

### 새로운 파드 보안 솔루션으로 마이그레이션

PSP는 제거될 예정이며 더 이상 활성 개발 중이 아니므로 클러스터 관리자와 운영자는 이런 보안 제어를 교체해야 합니다. 두 가지 솔루션으로 이런 요구를 충족할 수 있습니다.

+ 쿠버네티스 에코시스템 내 PAC(Policy-as-code) 솔루션
+ 쿠버네티스 [파드 시큐리티 스탠다드(PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

PAC 및 PSS 솔루션은 모두 PSP와 공존할 수 있습니다. PSP가 제거되기 전에 클러스터에서 사용할 수 있습니다. 따라서 PSP에서 마이그레이션할 때 쉽게 채택할 수 있습니다. PSP에서 PSS로 마이그레이션을 고려하는 경우 이 [문서](https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/)를 참조하세요.

아래에 설명된 PAC 솔루션 중 하나인 Kyverno는 PSP에서 해당 솔루션으로 마이그레이션할 때 유사한 정책, 기능 비교 및 마이그레이션 절차를 포함하여 [해당 블로그](https://kyverno.io/blog/2023/05/24/podsecuritypolicy-migration-with-kyverno/)에 구체적인 지침을 제공합니다. 파드 시큐리티 어드미션 (PSA)과 관련된 Kyverno로의 마이그레이션에 대한 추가 정보 및 지침은 [AWS 블로그](https://aws.amazon.com/blogs/containers/managing-pod-security-on-amazon-eks-with-kyverno/)에 게시되었습니다.

### 코드로서의 정책(PAC)

PAC(Policy-as-code) 솔루션은 규정된 자동 제어를 통해 클러스터 사용자를 안내하고 원치 않는 동작을 방지하는 가드레일을 제공합니다. PAC는 [쿠버네티스 동적 어드미션 컨트롤러](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)를 사용하여 웹훅 호출을 통해 쿠버네티스 API 서버 요청 흐름을 가로채고 변형 및 검증합니다. 코드로 작성되고 저장된 정책을 기반으로 페이로드를 요청합니다. 변형 및 유효성 검사는 API 서버 요청으로 인해 클러스터가 변경되기 전에 발생합니다. PAC 솔루션은 정책을 사용하여 분류 및 값을 기반으로 API 서버 요청 페이로드를 일치시키고 작동합니다.

Kubernetes에 사용할 수 있는 몇 가지 오픈 소스 PAC 솔루션이 있습니다. 이런 솔루션은 Kubernetes 프로젝트의 일부가 아닙니다. Kubernetes 생태계에서 제공됩니다. 일부 PAC 솔루션은 다음과 같습니다.

+ [OPA/게이트키퍼](https://open-policy-agent.github.io/gatekeeper/website/docs/)
+ [오픈 정책 에이전트(OPA)](https://www.openpolicyagent.org/)
+ [카이베르노](https://kyverno.io/)
+ [Kubewarden](https://www.kubewarden.io/)
+ [jsPolicy](https://www.jspolicy.com/)

PAC 솔루션에 대한 자세한 내용과 필요에 맞는 적절한 솔루션을 선택하는 데 도움이 되는 방법은 아래 링크를 참조하십시오.

+ [쿠버네티스에 대한 정책 기반 대책 - 1부](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-1/)
+ [쿠버네티스를 위한 정책 기반 대책 – 2부](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-2/)

### 파드 시큐리티 스탠다드(PSS) 및 파드 시큐리티 어드미션(PSA)

PSP 지원 중단 및 즉시 사용 가능한 파드 보안을 제어해야 하는 지속적인 필요성에 대응하여 빌트인 쿠버네티스 솔루션으로 쿠버네티스 [Auth Special Interest Group](https://github.com/kubernetes/community /tree/master/sig-auth )는 [파드 시큐리티 스탠다드(PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) 및 [파드 시큐리티 어드미션(PSA)](https://kubernetes.io/docs/concepts/security/pod-security-admission/)을 만들었습니다. PSA 에는 PSS에 정의된 제어를 구현하는 [어드미션 컨트롤러 웹훅 프로젝트](https://github.com/kubernetes/pod-security-admission#pod-security-admission)가 포함됩니다. 이 허용 컨트롤러 접근 방식은 PAC 솔루션에서 사용되는 방식과 유사합니다.

쿠버네티스 문서에 따르면 PSS는 _"보안 스펙트럼을 광범위하게 포괄하는 세 가지 다른 정책을 정의합니다. 이런 정책은 누적되며 매우 허용적인 것부터 매우 제한적인 것까지 다양합니다."_ 

이런 정책은 다음과 같이 정의됩니다:

+ **Privileged:** 제한되지 않은(안전하지 않은) 정책으로 가능한 가장 광범위한 수준의 권한을 제공합니다. 이 정책은 알려진 권한 에스컬레이션을 허용합니다. 정책이 없다는 것입니다. 이는 로깅 에이전트, CNI, 스토리지 드라이버 및 권한 액세스가 필요한 기타 시스템 전체 애플리케이션과 같은 애플리케이션에 적합합니다.

+ **Baseline:** 알려진 권한 에스컬레이션을 방지하는 최소 제한 정책입니다. 기본(최소 지정) 파드 구성을 허용합니다. 베이스라인 정책은 hostNetwork, hostPID, hostIPC, hostPath, hostPort의 사용, Linux 기능을 추가 제한 등과 같은 기타 몇 가지 제한 사항을 포함합니다.

+ **Restricted:** 현재 파드 강화 모범 사례에 따라 엄격하게 제한된 정책입니다. 이 정책은 기준선에서 상속되며 루트 또는 루트 그룹으로 실행할 수 없는 것과 같은 추가 제한 사항을 추가합니다. 제한된 정책은 애플리케이션의 기능에 영향을 미칠 수 있습니다. 이들은 주로 보안에 중요한 응용 프로그램을 실행하는 것을 목표로 합니다.

이런 정책은 [ 파드 실행을 위한 프로파일 ]( https://kubernetes.io/docs/concepts/security/pod-security-standards/#profile-details )을 정의하며, 세 가지 수준의 특권(Priviledged) 액세스에서부터 제한된(Restricted) 액세스로 정렬됩니다.

PSS에서 정의한 컨트롤을 구현하기 위해 PSA는 세 가지 모드로 작동합니다.

+ **enforce:** 정책을 위반하면 파드가 거부됩니다.

+ **audit:** 정책 위반은 감사 로그에 기록된 이벤트에 대한 감사 어노테이션 추가를 트리거하지만 그렇지 않으면 허용됩니다.

+ **warn:** 정책을 위반하면 사용자에게 경고가 표시되지만 그렇지 않으면 허용됩니다.

이런 모드와 프로파일 (제한) 수준은 아래 예와 같이 레이블을 사용하여 쿠버네티스 네임스페이스 수준에서 구성됩니다.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/enforce: restricted
```

독립적으로 사용하는 경우 이런 작동 모드는 다른 사용자 경험을 제공하는 다른 응답을 갖습니다. _enforce_ 모드는 각 podSpec이 구성된 제한 수준을 위반하는 경우 파드가 생성되지 않도록 합니다. 그러나 이 모드에서는 PodSpec이 적용된 PSS를 위반하더라도 배포와 같이 파드를 생성하는 파드가 아닌 쿠버네티스 개체가 클러스터에 적용되는 것을 방지하지 않습니다. 이 경우 배포가 적용되지만 파드는 적용되지 않습니다.

성공적으로 적용된 디플로이머트 객체는 객체 내 파드 생성 실패에 속한다는 즉각적인 표시가 없기 때문에 이를 인지하지 쉽지 않습니다. 위반 podSpec은 파드를 생성하지 않습니다. `kubectl get deploy <DEPLOYMENT_NAME>-oyaml`로 디플로이먼트 리소스를 검사하면 아래와 같이 실패한 파드 `.status.conditions` 엘리먼트의 메시지가 표시된다.

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

_audit_ 및 _warn_ 모드에서 파드 제한은 위반 파드가 생성되고 시작되는 것을 막지 않습니다 . 그러나 이런 모드에서는 API 서버 감사 로그 이벤트에 대한 감사 주석 및 API 서버 클라이언트에 대한 경고(예: _kubectl_ )는 파드와 파드를 생성하는 개체에 위반이 있는 podSpec이 포함되어 있을 때 각각 트리거됩니다. ` kubectl` _경고_ 메시지는 아래와 같습니다.

```bash
Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "test" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "test" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "test" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "test" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
deployment.apps/test created
```

PSA _audit_ 및 _warn_ 모드는 클러스터 작업에 부정적인 영향을 주지 않고 PSS를 도입할 때 유용합니다.

PSA 작동 모드는 상호 배타적이지 않으며 누적 방식으로 사용할 수 있습니다. 아래에서 볼 수 있듯이 단일 네임스페이스에서 여러 모드를 구성할 수 있습니다.

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

위의 예에서 배포를 적용할 때 사용자에게 친숙한 경고 및 감사 주석이 제공되는 반면 위반 적용도 파드 수준에서 제공됩니다. 실제로 여러 PSA 레이블은 아래와 같이 서로 다른 프로파일 수준을 사용할 수 있습니다.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: policy-test
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/warn: restricted
```

위의 예에서 PSA는 _baseline_ 프로파일 수준을 충족하는 모든 파드의 생성을 허용한 다음 _restricted_ 프로파일 수준 을 위반하는 파드(및 파드를 생성하는 개체)는 _경고_ 하도록 구성됩니다. 이는 _baseline_ 에서 _restricted_ 프로파일로 변경할 때 가능한 영향을 확인하는 데 유용한 접근 방식입니다.

#### 기존 파드

기존 파드가 있는 네임스페이스가 더 제한적인 PSS 프로파일을 사용하도록 수정되면 _audit_ 및 _warn_ 모드가 적절한 메시지를 생성합니다. 그러나 _enforce_ 모드는 파드를 삭제하지 않습니다. 경고 메시지는 아래와 같습니다.

```bash
Warning: existing pods in namespace "policy-test" violate the new PodSecurity enforce level "restricted:latest"
Warning: test-688f68dc87-htm8x: allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile
namespace/policy-test configured
```

#### 예외 처리 (Exemptions)

PSA는 _Exemptions_ 를 사용하여 달리 적용되었을 파드에 대한 위반 집행을 제외합니다. 이런 면제는 아래에 나열되어 있습니다.

+ **Usernames:** 예외 처리된 인증(또는 사칭) 사용자 이름을 가진 사용자의 요청은 무시됩니다.

+ **RuntimeClassNames:** 예외 처리된 런타임 클래스 이름을 지정하는 파드 및 워크로드 리소스는 무시됩니다.

+ **네임스페이스:** 예외 처리된 네임스페이스의 파드 및 워크로드 리소스는 무시됩니다.

이런 예외 처리는 [PSA 어드미션 컨트롤러 구성](https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-admission-controller/#configure-the-admission-controller)에서 다음과 같이 API 서버 구성의 일부로 정적으로 적용됩니다. 

_Validating Webhook_ 구현에서 예외는 [pod-security-webhook]( https://github.com/kubernetes/pod-security-admission/blob/master/webhook/manifests/50-deployment.yaml ) 컨테이너 내 볼륨으로 마운트되는 쿠버네티스 [컨피그맵](https://github.com/kubernetes/pod-security-admission/blob/master/webhook/manifests/20-configmap.yaml) 리소스 내에서 구성할 수 있습니다.

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

위의 컨피그맵 YAML에서 볼 수 있듯이 _audit_ , _enforce_ 및 _warn_ 와 같은 모든 PSA 모드에 대한 클러스터 전체의 기본 PSS 수준은  _restricted_ 로 설정되었습니다. 이는 예외인 `namespaces: ["kube-system","policy-test1"]` 을 제외한 모든 네임스페이스에 영향을 미칩니다 . 또한 아래에 표시된 _ValidatingWebhookConfiguration_ 리소스에서 _pod-security-webhook_ 네임스페이스도 구성된 PSS에서 제외됩니다.

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

!!! attention
    
    파드 시큐리티 어드미션은 쿠버네티스 v1.25에서 안정 버전으로 전환되었습니다. 파드 시큐리티 어드미션 기능이 기본적으로 활성화되기 전에 사용하려면 동적 어드미션 컨트롤러 (뮤테이팅 웹훅) 를 설치해야 했습니다. 웹훅 설치 및 구성 지침은 [본 문서](https://github.com/kubernetes/pod-security-admission/tree/master/webhook)에서 확인할 수 있습니다.

### PAC(Policy-as-Code)과 파드 시큐리티 스탠다드 중에서(PSS) 선택

파드 시큐리티 스탠다드(PSS)는 쿠버네티스에 내장되어 있고 쿠버네티스 에코시스템의 솔루션이 필요하지 않은 솔루션을 제공함으로써 파드 시큐리티 폴리시(PSP)을 대체하기 위해 개발되었습니다. PAC(Policy-as-Code) 솔루션은 훨씬 더 유연합니다.

다음 장단점 목록은 파드 보안 솔루션에 대해 정보에 입각한 결정을 내리는 데 도움이 되도록 설계되었습니다.

**PAC (파드 시큐리티 스탠다드과 비교)**

장점:

  + 보다 유연하고 세분화됨(필요한 경우 리소스 속성까지)
  + 파드에만 집중하는 것이 아니라 다양한 리소스 및 액션에 사용할 수 있음
  + 네임스페이스 수준에서만 적용되지 않음
  + 파드 시큐리티 스탠다드보다 더 성숙함
  + 의사결정은 기존 클러스터 리소스 및 외부 데이터(솔루션에 따라 다름)뿐만 아니라 API 서버 요청 페이로드의 모든 항목을 기반으로 할 수 있습니다.
  + 유효성 검사 전에 API 서버 요청 변경 지원(솔루션에 따라 다름)
  + 보완 정책 및 쿠버네티스 리소스 생성 가능 (솔루션에 따라 다름 - Kyverno는 파드 정책에서 디플로이먼트와 같은 상위 레벨 컨트롤러에 대한 정책을 [자동 생성](https://kyverno.io/docs/writing-policies/autogen/)할 수 있다. 또한 Kyverno는 [Generate Rules](https://kyverno.io/docs/writing-policies/generate/) 를 사용하여 _"새 리소스가 생성되거나 소스가 업데이트될 때"_ 쿠버네티스 리소스를 추가로 생성할 수 있습니다.)
  + 쿠버네티스 API 서버를 호출하기 전에 CICD 파이프라인상에서 보다 빠르게 보안을 도입할 수 있습니다(솔루션에 따라 다름).
  + 모범 사례, 조직 표준 등과 같이 반드시 보안과 관련되지 않은 동작을 구현하는 데 사용할 수 있습니다.
  + 쿠버네티스 이외의 사용 사례에서 사용 가능(솔루션에 따라 다름)
  + 유연성으로 인해 사용자 경험을 사용자의 요구에 맞게 조정할 수 있습니다.

단점:

  + Kubernetes에 빌트인으로 제공되지 않음
  + 학습, 구성 및 지원이 더 복잡함
  + 정책 작성에는 새로운 기술/언어/기능이 필요할 수 있습니다.

**파드 시큐리티 어드미션(PAC과 비교)**

장점:

  + 쿠버네티스에서 빌트인 제공
  + 더 간단한 구성
  + 사용할 새로운 언어나 작성할 정책이 없습니다.
  + 클러스터 기본 승인 수준이 _privileged_ 로 구성된 경우 네임스페이스 레이블을 사용하여 파드 보안 프로파일에 네임스페이스를 옵트인할 수 있습니다.

단점:

  + Policy-as-Code만큼 유연하거나 세분화되지 않음
  + 3개 단계의 제한 방식 제공
  + 주로 파드에 집중

#### 요약

현재 PSP 이외의 파드 보안 솔루션이 없고 필요한 파드 보안 태세가 파드 시큐리티 스탠다드(PSS) 에 정의된 모델에 맞는다면 PAC 솔루션 대신 PSS를 채택하는 것이 더 쉬울 수 있습니다. 그러나 파드 보안 태세가 PSS 모델에 맞지 않거나 PSS에서 정의한 것 외에 추가 제어를 추가할 계획이라면 PAC 솔루션이 더 적합해 보입니다.

## 권장 사항

### 더 나은 사용자 경험을 위해 여러 파드 시큐리티 어드미션(PSA) 모드 사용

앞서 언급했듯이 PSA _enforce_ 모드는 PSS 위반이 있는 파드가 적용되는 것을 방지하지만 디플로이먼트와 같은 상위 수준 컨트롤러를 중지하지는 않습니다. 실제로 파드 적용에 실패했다는 표시 없이 디플로이먼트가 성공적으로 적용됩니다. _kubectl_ 을 사용 하여 디플로이먼트 객체를 검사하고 PSA에서 실패한 파드 메시지를 검색할 수 있지만 사용자 경험이 더 좋을 수 있습니다. 사용자 경험을 개선하려면 여러 PSA 모드(audit, enforce, warn)를 사용해야 합니다.

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

위의 예에서 _enforce_ 모드가 정의된 경우 각 podSpec에서 PSS 위반이 있는 배포 매니페스트를 쿠버네티스 API 서버에 적용하려고 하면 배포가 성공적으로 적용되지만 파드는 적용되지 않습니다. 그리고 _audit_ 및 _warn_ 모드도 활성화되어 있으므로 API 서버 클라이언트는 경고 메시지를 수신하고 API 서버 감사 로그 이벤트에도 메시지가 표시됩니다.


### Previleged 권한으로 실행할 수 있는 컨테이너 제한

언급한 바와 같이 Previleged 권한으로 실행되는 컨테이너는 호스트의 루트에 할당된 모든 Linux 기능을 상속합니다. 컨테이너가 제대로 작동하기 위해 이런 유형의 권한이 필요한 경우는 거의 없습니다. 컨테이너의 권한과 기능을 제한하는 데 사용할 수 있는 여러 가지 방법이 있습니다.

!!! attention
    
    Fargate는 파드의 컨테이너가 AWS가 관리하는 인프라에서 실행되는 "서버리스"형태로 컨테이너를 실행할 수 있는 기능을 제공합니다. Fargate를 사용하면 Previleged 컨테이너를 실행하거나 hostNetwork 또는 hostPort를 사용하도록 파드를 구성할 수 없습니다.

### 컨테이너에서 루트로 프로세스를 실행하지 마십시오.

모든 컨테이너는 기본적으로 루트로 실행됩니다. 이는 공격자가 애플리케이션의 취약성을 악용하고 실행 중인 컨테이너에 대한 셸 액세스 권한을 얻을 수 있는 경우 문제가 될 수 있습니다. 다양한 방법으로 이 위험을 완화할 수 있습니다. 먼저 컨테이너 이미지에서 셸(Shell)을 제거합니다. 둘째, Dockerfile에 USER 지시문을 추가하거나 루트가 아닌 사용자로 파드의 컨테이너를 실행합니다. Kubernetes podSpec에는 `spec.securityContext` 아래에 애플리케이션을 실행할 사용자 및/또는 그룹을 지정할 수 있는 일련의 필드가 포함되어 있습니다. 이런 필드는 각각 `runAsUser` 및 `runAsGroup` 입니다.

`spec.securityContext` 및 관련 요소 의 사용을 강제하기 위해 PAC 정책 또는 파드 시큐리티 스탠다드(PSS)를 클러스터에 추가할 수 있습니다. 이런 솔루션을 사용하면 etcd에 유지되기 전에 인바운드 Kubernetes API 서버 요청 페이로드를 검증할 수 있는 정책 또는 프로파일을 작성 및/또는 사용할 수 있습니다. 또한 PAC 솔루션은 인바운드 요청을 변경하고 경우에 따라 새 요청을 생성할 수 있습니다.

### Docker에서 Docker를 실행하거나 컨테이너에 소켓을 마운트하지 마십시오.

이렇게 하면 편리하게 Docker 컨테이너에서 이미지를 빌드/실행할 수 있지만 기본적으로 컨테이너에서 실행 중인 프로세스에 대한 노드의 완전한 제어를 양도하는 것입니다. 쿠버네티스에서 컨테이너 이미지를 빌드해야 하는 경우 [Kaniko](https://github.com/GoogleContainerTools/kaniko), [buildah](https://github.com/containers/buildah), [img](https://github.com/genuinetools/img) 또는 [CodeBuild](https://docs.aws.amazon.com/codebuild/latest/userguide/welcome.html) 같은 빌드 서비스 를 대신 사용할 수 있습니다.

!!! tip
    
    컨테이너 이미지 빌드와 같은 CICD 처리에 사용되는 쿠버네티스 클러스터는 보다 일반화된 워크로드를 실행하는 클러스터와 격리되어야 합니다.

### hostPath 사용을 제한하거나 hostPath가 필요한 경우 사용할 수 있는 접두사를 제한하고 볼륨을 읽기 전용으로 구성합니다.

`hostPath` 는 호스트에서 컨테이너로 직접 디렉토리를 마운트하는 볼륨입니다. 파드에 이런 유형의 액세스가 필요한 경우는 거의 없지만 필요한 경우 위험을 인식해야 합니다. 기본적으로 루트로 실행되는 파드는 hostPath에 의해 노출된 파일 시스템에 대한 쓰기 액세스 권한을 갖습니다. 이를 통해 공격자는 kubelet 설정을 수정하고, /etc/shadow와 같이 hostPath에 의해 직접 노출되지 않는 디렉토리 또는 파일에 대한 심볼릭 링크를 생성하고, ssh 키를 설치하고, 호스트에 마운트된 비밀을 읽고, 기타 악의적인 것들을 할 수 있습니다. hostPath의 위험을 완화하려면 `spec.containers.volumeMounts` 를 `readOnly` 로 구성하십시오. 예를 들면 다음과 같습니다.

```yaml
volumeMounts:
- name: hostPath-volume
    readOnly: true
    mountPath: /host-path
```

또한 PAC 솔루션을 사용하여 `hostPath` 볼륨에서 사용할 수 있는 디렉토리를 제한하거나 `hostPath` 사용을 모두 방지해야 합니다. 파드 시큐리티 스탠다드 _Baseline_ 또는 _Restricted_ 정책을 사용하여 `hostPath` 사용을 방지할 수 있습니다.

권한 상승의 위험성에 대한 자세한 내용은 Seth Art의 블로그 [Bad Pods: Kubernetes Pod Privilege Escalation](https://labs.bishopfox.com/tech-blog/bad-pods-kubernetes-pod-privilege-escalation)를 참조하십시오.

### 리소스 경합 및 DoS 공격을 피하기 위해 각 컨테이너에 대한 요청 및 제한 설정

요청이나 제한이 없는 파드는 이론적으로 호스트에서 사용 가능한 모든 리소스를 소비할 수 있습니다. 추가 파드가 노드에 예약되면 노드에서 CPU 또는 메모리 압력이 발생하여 Kubelet이 종료되거나 노드에서 파드가 제거될 수 있습니다. 이런 일이 함께 발생하는 것을 방지할 수는 없지만 요청 및 제한을 설정하면 리소스 경합을 최소화하고 리소스를 과도하게 소비하는 잘못 작성된 애플리케이션으로 인한 위험을 완화하는 데 도움이 됩니다.

`podSpec` 을 사용하면 CPU 및 메모리에 대한 요청 및 제한을 지정할 수 있습니다. CPU는 초과 신청될 수 있기 때문에 압축 가능한 리소스로 간주됩니다. 메모리는 압축할 수 없습니다. 즉, 여러 컨테이너 간에 공유할 수 없습니다.

CPU 또는 메모리에 대해 _requests_ 를 지정할 때 본질적으로 컨테이너가 확보할 수 있는 _memory_ 의 양을 지정하는 것입니다. Kubernetes는 파드에 있는 모든 컨테이너의 요청을 집계하여 파드를 예약할 노드를 결정합니다. 컨테이너가 요청된 메모리 양을 초과하면 노드에 메모리 압력이 있으면 종료될 수 있습니다.

_Limits_ 는 컨테이너가 사용할 수 있는 CPU 및 메모리 리소스의 최대량이며 컨테이너에 대해 생성된 cgroup 의 `memory.limit_in_bytes` 값에 직접 해당합니다. 메모리 제한을 초과하는 컨테이너는 OOM 종료됩니다. 컨테이너가 CPU 제한을 초과하면 제한됩니다.

!!! tip

컨테이너 `resources.limits`를 사용하는 경우 컨테이너 리소스 사용량(리소스 풋프린트라고도 함)은 부하 테스트를 기반으로 데이터 기반이고 정확해야 합니다. 정확하고 신뢰할 수 있는 리소스 공간이 없으면 컨테이너 'resources.limits'를 채울 수 있습니다. 예를 들어 'resources.limits.memory'는 잠재적인 메모리 리소스 제한 부정확성을 설명하기 위해 관찰 가능한 최대값보다 20-30% 높게 패딩될 수 있습니다.

Kubernetes는 세 가지 서비스 품질(QoS) 클래스를 사용하여 노드에서 실행되는 워크로드의 우선 순위를 지정합니다. 여기에는 다음이 포함됩니다.

+ guaranteed
+ burstable
+ best-effort

제한 및 요청이 설정되지 않은 경우 파드는 _best-effort_ (가장 낮은 우선 순위)로 구성됩니다. Best-effort 파드는 메모리가 부족할 때 가장 먼저 종료됩니다. 파드 내의 _all_ 컨테이너 에 제한이 설정 되거나 요청 및 제한이 동일한 값으로 설정되고 0이 아닌 경우 파드는 _guaranteed_ (가장 높은 우선 순위)로 구성됩니다. 보장된 파드는 구성된 메모리 제한을 초과하지 않는 한 종료되지 않습니다. 제한 및 요청이 0이 아닌 다른 값으로 구성되거나 파드 내의 한 컨테이너가 제한을 설정하고 다른 컨테이너는 다른 리소스에 대해 제한이 설정되지 않거나 설정된 경우 파드는 _burstable_ (중간 우선 순위)로 구성됩니다. 이런 파드에는 일부 리소스 보장이 있지만 요청된 메모리를 초과하면 종료될 수 있습니다.

!!! attention
    
요청은 컨테이너 cgroup의 `memory_limit_in_bytes` 값에 영향을 미치지 않습니다. cgroup 제한은 호스트에서 사용 가능한 메모리 양으로 설정됩니다. 그럼에도 불구하고 요청 값을 너무 낮게 설정하면 노드가 메모리 압력을 받는 경우 파드가 kubelet에 의해 종료 대상이 될 수 있습니다.

| 클래스 | 우선순위 | 조건 | 죽이기 조건 |
| :-- | :-- | :-- | :-- |
| Guaranteed | 최고 | 제한 = 요청 != 0 | 메모리 제한만 초과 |
| Burstable | 중간 | 제한 != 요청 != 0 | 요청 메모리를 초과하면 종료됨 |
| Best-Effort| 최저 | 한도 및 요청이 설정되지 않음 | 메모리가 부족할 때 가장 먼저 강제 종료됨 |

리소스 QoS에 대한 추가 정보는 [쿠버네티스 문서](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/node/resource-qos.md)를 참조하십시오.

네임스페이스에 [리소스 할당량](https://kubernetes.io/docs/concepts/policy/resource-quotas/)을 설정하거나 [제한 범위](https://kubernetes.io/docs/concepts/policy/limit-range/)를 생성하여 리소스 요청(request) 및 리소스 제한(limit)을 강제로 사용할 수 있습니다. 리소스 할당량을 사용하면 네임스페이스에 할당된 총 리소스 양 (예: CPU 및 RAM)을 지정할 수 있습니다. 네임스페이스에 적용하면 해당 네임스페이스에 배포된 모든 컨테이너에 대한 리소스 요청 및 리소스 제한을 지정해야 합니다. 반대로 제한 범위를 사용하면 리소스 할당을 더 세밀하게 제어할 수 있습니다. 제한 범위를 사용하면 네임스페이스 내 파드 또는 컨테이너당 CPU 및 메모리 리소스를 최소/최대로 설정할 수 있습니다. 기본 리소스 요청(request)/리소스 제한(limit) 값이 제공되지 않은 경우 이를 사용하여 기본 요청/제한 값을 설정할 수도 있습니다.

코드형 정책(PAC) 솔루션을 사용하여 요청 및 제한을 적용하거나 네임스페이스를 생성할 때 리소스 할당량 및 제한 범위를 만들 수도 있습니다.

### 특권 에스컬레이션을 허용하지 않음

특권 에스컬레이션을 통해 프로세스는 실행 중인 보안 컨텍스트를 변경할 수 있습니다. Sudo는 SUID 또는 SGID 비트가 있는 바이너리와 마찬가지로 이에 대한 좋은 예입니다. 특권 에스컬레이션은 기본적으로 사용자가 다른 사용자 또는 그룹의 권한으로 파일을 실행하는 방법입니다. `allowPrivilegeEscalation` 을 ` false`로 설정하는 정책 코드 변경 정책을 구현하거나 `podSpec`에서 `securityContext.allowPrivilegeEscalation`을 설정하여 컨테이너가 권한 있는 에스컬레이션을 사용하지 못하도록 방지 할 수 있습니다 . Policy-as-code 정책을 사용하여 잘못된 설정이 감지된 경우 API 서버 요청이 성공하지 못하도록 할 수도 있습니다. 파드 시큐리티 스탠다드을 사용하여 파드가 권한 에스컬레이션을 사용하지 못하도록 할 수도 있습니다.

### ServiceAccount 토큰 탑재 비활성화

쿠버네티스 API에 액세스할 필요가 없는 파드의 경우, 파드 스펙 또는 특정 서비스어카운트를 사용하는 모든 파드에 대해 서비스어카운트 토큰의 자동 마운트를 비활성화할 수 있다.



!!! attention
    
    서비스어카운트 마운트를 비활성화해도 파드가 쿠버네티스 API에 네트워크로 액세스하는 것을 막을 수는 없습니다. 파드가 쿠버네티스 API에 네트워크로 액세스하는 것을 방지하려면 [EKS 클러스터 엔드포인트 액세스][eks-ep-access]를 수정하고 [네트워크정책](../network/ #network -policy)를 사용하여 파드 액세스를 차단합니다.





[eks-ep-access]: https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html

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

### 서비스 검색 비활성화

클러스터 내 서비스를 조회하거나 호출할 필요가 없는 파드의 경우 파드에 제공되는 정보의 양을 줄일 수 있다. CoreDNS를 사용하지 않도록 Pod의 DNS 정책을 설정하고 파드 네임스페이스의 서비스를 환경 변수로 노출하지 않도록 설정할 수 있습니다. 서비스 링크에 대한 자세한 내용은 [환경 변수에 관한 쿠버네티스 문서][k8s-env-var-docs]를 참조하십시오. 파드 DNS 정책의 기본값은 클러스터 내 DNS를 사용하는 "ClusterFirst"이고, 기본값이 아닌 "Default"는 기본 노드의 DNS 확인을 사용합니다. 자세한 내용은 [파드 DNS 정책에 관한 쿠버네티스 문서][dns-policy] 를 참조하십시오.








[k8s-env-var-docs]: https://kubernetes.io/docs/concepts/services-networking/service/#environment-variables
[dns-policy]: https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-s-dns-policy

!!! attention
    
    서비스 링크를 비활성화하고 파드의 DNS 정책을 변경해도 파드가 클러스터 내 DNS 서비스에 네트워크로 액세스하는 것을 막을 수는 없습니다.
    공격자는 여전히 클러스터 내 DNS 서비스에 접속하여 클러스터의 서비스를 열거할 수 있습니다.(예: `dig SRV *.*.svc.cluster.local @$CLUSTER_DNS_IP`) 클러스터 내 서비스 검색을 방지하려면 [NetworkPolicy](../network/ #network -policy) 를 사용하여 파드 액세스를 차단합니다.





```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-service-info
spec:
    dnsPolicy: Default # "Default" is not the true default value
    enableServiceLinks: false
```

### 읽기 전용 루트 파일 시스템으로 이미지 구성

읽기 전용 루트 파일 시스템으로 이미지를 구성하면 공격자가 애플리케이션에서 사용하는 파일 시스템의 바이너리를 덮어쓰는 것을 방지할 수 있습니다. 애플리케이션이 파일 시스템에 기록해야 하는 경우 임시 디렉터리에 쓰거나 볼륨을 연결하고 마운트하는 것을 고려해 보세요.다음과 같이 파드의 SecurityContext를 설정하여 이를 적용할 수 있다.

```yaml
...
securityContext:
  readOnlyRootFilesystem: true
...
``` 

코드형 정책(PaC) 및 파드 시큐리티 스탠다드를 사용하여 이 동작을 시행할 수 있습니다.


!!! info
    
    [쿠버네티스의 Windows 컨테이너](https://kubernetes.io/docs/concepts/windows/intro/) 에 따르면 Windows에서 실행되는 컨테이너의 경우 `SecurityContext.readOnlyRootFileSystem`은 `true`로 설정할 수 없습니다. 
    레지스트리 및 시스템 프로세스를 컨테이너 내에서 실행하려면 쓰기 권한이 필요하기 때문입니다.

## 도구 및 리소스

+ [open-policy-agent/gatekeeper-library: OPA Gatekeeper 정책 라이브러리](https://github.com/open-policy-agent/gatekeeper-library) PSP 대신 사용할 수 있는 OPA/게이트키퍼 정책 라이브러리입니다.
+ [Kyverno 정책 라이브러리](https://kyverno.io/policies/)
+ EKS를 위한 공통 OPA 및 Kyverno [정책](https://github.com/aws/aws-eks-best-practices/tree/master/policies) 모음입니다.
+ [정책 기반 대책: 파트 1](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-1/)
+ [정책 기반 대책: 파트 2](https://aws.amazon.com/blogs/containers/policy-based-countermeasures-for-kubernetes-part-2/)
+ [Pod Security Policy Migrator](https://appvia.github.io/psp-migration/) PSP를 OPA/Gatekeeper, KubeWarden 또는 Kyverno 정책으로 변환하는 도구입니다.
+ [NeuVector by SUSE](https://www.suse.com/neuvector/) 오픈 소스 제로 트러스트 컨테이너 보안 플랫폼은 프로세스 및 파일 시스템 정책과 승인 제어 규칙을 제공합니다.