# 파드 보안 컨텍스트


**파드 시큐리티 폴리시(PSP)** 와 **파드 시큐리티 스탠다드(PSS)**는 쿠버네티스에서 보안을 강화하는 두 가지 주요 방법입니다. PSP는 쿠버네티스 v1.21부터 더 이상 사용되지 않으며 v1.25에서 제거될 예정입니다. 향후 보안을 강화하기 위해 쿠버네티스가 권장하는 접근 방식은 PSS입니다.

PSP는 보안 정책을 구현하기 위한 쿠버네티스의 네이티브 솔루션입니다. PSP는 파드 스펙에서 정의하고 보안에 민감한 측면을 제어하는 클러스터 레벨의 리소스 입니다. PSP를 사용하면 클러스터에서 승인 되기 위해 파드가 충족해야 하는 일련의 조건을 정의할 수 있습니다.
PSP 기능은 쿠버네티스 초기부터 사용 가능했으며 특정 클러스터에서 잘못 구성된 파드가 생성되는 것을 차단하도록 설계되었습니다.

PSP에 대한 자세한 내용은 쿠버네티스 [문서](https://kubernetes.io/docs/concepts/policy/pod-security-policy/)를 참조하십시오. [쿠버네티스 지원 중단 정책](https://kubernetes.io/docs/reference/using-api/deprecation-policy/)에 따라 이전 버전은 기능 지원 중단 후 9개월이 지나면 지원이 중단됩니다.

반면, 일반적으로 보안 컨텍스트를 사용하여 구현되는 권장 보안 접근 방식인 PSS는 파드 매니페스트에서 파드 및 컨테이너 스펙에 정의됩니다. PSS는 쿠버네티스 프로젝트 팀이 파드의 보안 관련 모범 사례를 다루기 위해 정의한 공식 표준입니다. baseline (최소 제한, 기본값), privileged (비제한) 그리고 restricted(가장 제한적) 등의 정책을 정의합니다.

baseline 프로파일부터 시작하는 것이 좋습니다. PSS baseline 프로파일은 최소한의 예외 항목을 처리하고 보안과 잠재적 요소 사이의 적절한 균형을 제공하여 워크로드 보안을 위한 좋은 출발점 역할을 합니다. 현재 PSP를 사용하고 있다면 PSS로 전환하는 것이 좋습니다. PSS 정책에 대한 자세한 내용은 쿠버네티스 [문서](https://kubernetes.io/docs/concepts/security/pod-security-standards/)에서 확인할 수 있습니다. 이런 정책은 [OPA](https://www.openpolicyagent.org/)와 [Kyverno](https://kyverno.io/) 같은 도구를 포함한 여러 도구를 사용하여 강제할 수 있습니다. 예를 들어, Kyverno는 [여기](https://kyverno.io/policies/pod-security/)에서 PSS 정책의 전체 컬렉션을 제공합니다.

보안 컨텍스트 설정을 통해 프로세스를 선택할 수 있는 권한을 부여하고, 프로그램 프로파일을 사용하여 개별 프로그램의 기능을 제한하고, 권한 상승을 허용하고, 시스템 콜을 필터링하는 등의 작업을 수행할 수 있습니다.

쿠버네티스의 윈도우 파드에는 보안 컨텍스트와 관련하여 표준 리눅스 기반 워크로드와 몇 가지 제한 사항 및 차별화 요소가 있습니다.

윈도우는 시스템 네임스페이스 필터와 함께 컨테이너당 작업 개체를 사용하여 컨테이너의 모든 프로세스를 포함하고 호스트로부터 논리적 격리를 제공합니다. 네임스페이스 필터링 없이 윈도우 컨테이너를 실행할 수 있는 방법은 없습니다. 이는 호스트의 컨텍스트에서 시스템 권한을 취득할 수 없으므로 윈도우에서는 권한이 있는 컨테이너를 사용할 수 없습니다.

다음 `windowsOptions` 은 문서화된 유일한 [Windows Security Context options](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/#windowssecuritycontextoptions-v1-core)이고, 나머지는 일반적인 [Security Context options](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.21/#securitycontext-v1-core) 입니다.

윈도우와 리눅스에서 지원되는 보안 컨텍스트 속성 목록은 [여기](https://kubernetes.io/docs/setup/production-environment/windows/_print/#v1-container)의 공식 문서를 참조하십시오.

Pod별 설정은 모든 컨테이너에 적용 됩니다. 지정하지 않으면 PodSecurityContext의 옵션이 사용됩니다. SecurityContext와 PodSecurityContext가 모두 설정된 경우 SecurityContext에 지정된 값이 우선 적용됩니다.

예를 들어, 윈도우 옵션인 파드 및 컨테이너에 대한 runAsUserName 설정은 리눅스 관련 runAsUser 설정과 거의 동일하며 다음 매니페스트에서는 파드 관련 보안 컨텍스트가 모든 컨테이너에 적용됩니다.

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

다음에서는 컨테이너 수준 보안 컨텍스트가 파드 수준 보안 컨텍스트보다 우선 적용됩니다.

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

runAsUserName 필드에 허용되는 값의 예: ContainerAdministrator, ContainerUser, NT AUTHORITY\NETWORK SERVICE, NT AUTHORITY\LOCAL SERVICE

일반적으로 윈도우 파드용 ContainerUser를 사용하여 컨테이너를 실행하는 것이 좋습니다. 사용자는 컨테이너와 호스트 간에 공유되지 않지만 ContainerAdministrator는 컨테이너 내에서 추가 권한을 갖습니다. 주의해야 할 username의 [제한 사항](https://kubernetes.io/docs/tasks/configure-pod-container/configure-runasusername/#windows-username-limitations)이 있습니다.

ContainerAdministrator를 사용하는 좋은 예는 PATH를 설정하는 것 입니다. USER 지시어를 사용한다면 다음과 같이 할 수 있습니다:

```bash
USER ContainerAdministrator
RUN setx /M PATH "%PATH%;C:/your/path"
USER ContainerUser
```

또한 secrets 는 노드 볼륨에 일반 텍스트로 기록됩니다(Linux의 tmpfs/in-memory와 비교). 이는 두 가지 작업을 수행해야 함을 의미합니다.

* file ACL을 사용하여 secrets 파일 위치를 보호
* [BitLocker](https://docs.microsoft.com/en-us/windows/security/information-protection/bitlocker/bitlocker-how-to-deploy-on-windows-server)를 사용하여 볼륨 수준 암호화 사용

