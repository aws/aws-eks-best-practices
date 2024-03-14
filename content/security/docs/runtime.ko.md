# 런타임 보안

런타임 보안은 컨테이너가 실행되는 동안 컨테이너를 능동적으로 보호합니다. 컨테이너 내부에서 발생하는 악의적인 활동을 탐지 및 방지하는 것이 관건입니다. 이는 리눅스 기능, 보안 컴퓨팅 (seccomp), AppArmor 또는 SELinux와 같이 쿠버네티스와 통합된 리눅스 커널 또는 커널 익스텐션의 여러 메커니즘을 통해 달성할 수 있습니다. Amazon GuardDuty 및 타사 도구와 같은 옵션도 있습니다. 이러한 도구를 사용하면 Linux 커널 메커니즘을 수동으로 구성하지 않고도 기준을 설정하고 이상 활동을 탐지하는 데 도움을 줄 수 있습니다.

!!! Attention

  쿠버네티스는 현재 seccomp, AppArmor 또는 SELinux 프로파일을 노드에 로드하기 위한 네이티브 메커니즘을 제공하지 않는다. 수동으로 로드하거나 부트스트랩할 때 노드에 설치해야 합니다. 스케줄러가 어떤 노드에 프로파일이 있는지 인식하지 못하기 때문에 파드에서 참조하기 전에 이 작업을 수행해야 한다.Security Profiles Operator와 같은 도구를 사용하여 프로파일을 노드에 자동으로 프로비저닝하는 방법을 아래에서 확인하세요.

## 보안 컨텍스트 및 빌트인 쿠버네티스 컨트롤

많은 리눅스 런타임 보안 메커니즘은 쿠버네티스와 긴밀하게 통합되어 있으며 쿠버네티스 [보안 컨텍스트](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)를 통해 구성할 수 있습니다. 이러한 옵션 중 하나는 `privileged` 플래그인데, 이 플래그는 기본적으로 `false`이며 활성화되면 기본적으로 호스트의 루트와 동일합니다. 프로덕션 워크로드에서 권한 모드를 활성화하는 것은 거의 항상 부적절하지만, 컨테이너에 적절한 권한을 더 세부적으로 제공할 수 있는 컨트롤은 훨씬 더 많습니다.

### 리눅스 기능

Linux 기능을 사용하면 루트 사용자의 모든 기능을 제공하지 않고도 파드 또는 컨테이너에 특정 기능을 부여할 수 있습니다. 네트워크 인터페이스 또는 방화벽을 구성할 수 있는 `CAP_NET_ADMIN`이나 시스템 클럭을 조작할 수 있는 `CAP_SYS_TIME`이 그런 예입니다.

### Seccomp

Seccomp를 사용하면 컨테이너식 애플리케이션이 기본 호스트 운영 체제의 커널에 특정 시스템 호출을 수행하는 것을 방지할 수 있습니다. Linux 운영 체제에는 수백 개의 시스템 호출이 있지만 그 중 대부분은 컨테이너를 실행하는 데 필요하지 않습니다. 컨테이너에서 생성할 수 있는 시스템 호출을 제한하면 애플리케이션의 공격 범위를 효과적으로 줄일 수 있습니다.

Seccomp는 시스템 호출을 가로채고 허용 목록에 있는 시스템만 통과하도록 하는 방식으로 작동합니다.Docker에는 대부분의 범용 워크로드에 적합한 [디폴트](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json) seccomp 프로파일이 있으며, containerd와 같은 다른 컨테이너 런타임도 비슷한 디폴트값을 제공합니다. 파드 사양의 `SecurityContext` 섹션에 다음을 추가하여 컨테이너 또는 파드가 컨테이너 런타임의 디폴트 seccomp 프로파일을 사용하도록 구성할 수 있다.

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

1.22 (Alpha, 1.27부터 Stable)부터, 위의 '런타임디폴트'는 [단일 kubelet 플래그](https://kubernetes.io/docs/tutorials/security/seccomp/#enable-the-use-of-runtimedefault-as-the-default-seccomp-profile-for-all-workloads), `--seccomp-default'를 사용하여 노드의 모든 파드에 사용할 수 있다. 그러면 'SecurityContext'에 지정된 프로파일은 다른 프로파일에만 필요합니다.

또한 추가 권한이 필요한 항목에 대해 프로파일을 직접 만들 수도 있습니다. 수동으로 작업하기에는 매우 지루할 수 있지만 eBPF 또는 logs와 같은 도구를 사용하여 기본 권한 요구 사항을 seccomp 프로파일로 기록하는 것을 지원하는 [Inspektor Gadget](https://github.com/inspektor-gadget/inspektor-gadget)(네트워크 정책을 생성을 위해 [네트워크 보안 섹션](../network/) 문서에서도 권장) 및 [Security Profiles Operator](https://github.com/inspektor-gadget/inspektor-gadget)와 같은 도구가 있습니다. 또한 Security Profiles Operator를 사용하면 기록된 프로파일을 파드와 컨테이너에서 사용할 수 있도록 노드에 배포하는 작업을 자동화할 수 있다.

### AppArmor와 SELinux

AppMor와 SELinux는 [필수 액세스 제어(MAC 시스템)](https://en.wikipedia.org/wiki/Mandatory_access_control)로 알려져 있습니다. 이들은 seccomp와 개념적으로는 비슷하지만 API와 기능이 다르기 때문에 특정 파일 시스템 경로 또는 네트워크 포트 등에 대한 액세스 제어가 가능합니다. 이러한 도구에 대한 지원은 리눅스 배포판에 따라 달라지는데, 데비안/우분투는 AppArmor를 지원하고 RHEL/Centos/BottleRocket/Amazon Linux 2023은 SELinux를 지원합니다. SELinux에 대한 자세한 내용은 [인프라 보안 섹션](../hosts/#run-selinux)를 참조하십시오.

AppArmor와 SELinux는 모두 쿠버네티스와 통합되어 있지만, 쿠버네티스 1.28부터 AppArmor 프로파일은 [어노테이션](https://kubernetes.io/docs/tutorials/security/apparmor/#securing-a-pod) 을 통해 지정해야 하며, SELinux 레이블은 보안 컨텍스트의 [SELinuxOptions](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/#selinuxoptions-v1-core) 필드를 통해 직접 설정할 수 있습니다.

seccomp 프로파일과 마찬가지로 위에서 언급한 보안 프로파일 운영자는 클러스터의 노드에 프로파일을 배포하는 데 도움을 줄 수 있습니다. (향후 이 프로젝트는 seccomp와 마찬가지로 AppMor 및 SELinux용 프로파일도 생성하는 것을 목표로 하고 있습니다.)

## 권장 사항

### Amazon GuardDuty를 사용하여 런타임 모니터링 및 EKS 환경에 대한 위협을 탐지하십시오

현재 EKS 런타임을 지속적으로 모니터링하고, EKS 감사 로그를 분석하고, 멀웨어 및 기타 의심스러운 활동을 검사할 수 있는 솔루션이 없는 경우, Amazon은 AWS 환경을 보호하는 간단하고, 빠르고, 안전하고, 확장 가능하고, 비용 효율적인 원클릭 방법을 원하는 고객에게 [Amazon GuardDuty](https://aws.amazon.com/guardduty/)를 사용할 것을 강력히 권장합니다. Amazon GuardDuty는 AWS CloudTrail 관리 이벤트, AWS CloudTrail 이벤트 로그, VPC 플로우 로그(Amazon EC2 인스턴스 트래픽), 쿠버네티스 감사 로그 및 DNS 로그와 같은 기본 데이터 소스를 분석하고 처리하는 보안 모니터링 서비스입니다. 또한 EKS 런타임 모니터링도 포함됩니다. 지속적으로 업데이트되는 위협 인텔리전스 피드(예: 악성 IP 주소 및 도메인 목록), 기계 학습을 사용하여 AWS 환경 내에서 예상치 못한, 잠재적으로 승인되지 않은 악의적인 활동을 식별합니다. 여기에는 권한 상승, 노출된 자격 증명 사용, 악성 IP 주소, 도메인과의 통신, Amazon EC2 인스턴스 및 EKS 컨테이너 워크로드에 악성코드가 존재하거나 의심스러운 API 활동 발견과 같은 문제가 포함될 수 있습니다. GuardDuty는 GuardDuty 콘솔이나 Amazon EventBridge를 통해 확인할 수 있는 보안 조사 결과를 생성하여 AWS 환경의 상태를 알려줍니다. 또한 GuardDuty는 조사 결과를 Amazon 심플 스토리지 서비스 (S3) 버킷으로 내보내고 AWS Security Hub 및 Detective과 같은 다른 서비스와 통합할 수 있도록 지원합니다.

위와 관련된 AWS 온라인 테크 토크인 ["Amazon GuardDuty를 통한 Amazon EKS의 향상된 위협 탐지 — AWS 온라인 테크 토크"](https://www.youtube.com/watch?v=oNHGRRroJuE)를 시청하여 이러한 추가 EKS 보안 기능을 몇 분 만에 단계별로 활성화하는 방법을 알아보십시오.

### 런타임 방어를 위해 타사 솔루션 사용

Linux 보안에 익숙하지 않은 경우 seccomp 및 Apparmor 프로파일을 만들고 관리하기 어려울 수 있습니다. 능숙해질 시간이 없다면 상용 솔루션 사용을 고려하십시오. 그들 중 다수는 Apparmor 및 seccomp와 같은 정적 프로파일을 넘어 기계 학습을 사용하여 의심스러운 활동을 차단하거나 경고하기 시작했습니다. 이런 솔루션 중 일부는 아래의 [도구](#도구-및-리소스) 섹션에서 찾을 수 있습니다. 추가 옵션은 [AWS Marketplace for Containers](https://aws.amazon.com/marketplace/features/containers)에서 찾을 수 있습니다.

### seccomp 정책을 작성하기 전에 Linux 기능 추가/삭제 고려

기능에는 시스템 콜이 도달할 수 있는 커널 기능의 다양한 검사가 포함됩니다. 확인에 실패하면 시스템 콜은 일반적으로 오류를 반환합니다. 확인은 특정 syscall의 시작 부분에서 바로 수행하거나 여러 다른 syscall을 통해 도달할 수 있는 커널의 더 깊은 영역(예: 특정 특권 파일에 쓰기)에서 수행할 수 있습니다. 반면에 Seccomp는 실행되기 전에 모든 시스템 콜에 적용되는 시스템 콜 필터입니다. 프로세스는 특정 시스템 콜 또는 특정 시스템 콜에 대한 특정 인수를 실행할 권한을 취소할 수 있는 필터를 설정할 수 있습니다.

seccomp를 사용하기 전에 Linux 기능 추가/제거가 필요한 제어 기능을 제공하는지 고려하십시오. 자세한 내용은 [를 참조하십시오.](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container)

### 파드 시큐리티 폴리시(PSP)을 사용하여 목표를 달성할 수 있는지 확인하십시오

PSP는 과도한 복잡성을 유발하지 않으면서 보안 태세를 개선할 수 있는 다양한 방법을 제공합니다. seccomp 및 Apparmor 프로파일을 구축하기 전에 PSP에서 사용할 수 있는 옵션을 살펴보세요.

!!! Warning
    쿠버네티스 1.25부터 PSP가 제거되고 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) 컨트롤러로 대체되었습니다. 현재 존재하는 타사 대안으로는 OPA/게이트키퍼 및 Kyverno가 있습니다. PSP에서 흔히 볼 수 있는 정책을 구현하기 위한 게이트키퍼 제약 조건 및 제약 조건 템플릿 모음은 GitHub의 [Gatekeeper 라이브러리](https://github.com/open-policy-agent/gatekeeper-library/tree/master/library/pod-security-policy) 저장소에서 가져올 수 있습니다. 또한 [Kyverno 정책 라이브러리](https://main.kyverno.io/policies/)에서 [파드 시큐리티 스탠다드(PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/)의  전체 컬렉션을 포함하여 PSP를 대체할 수 있는 다양한 제품을 찾을 수 있습니다.

## 도구 및 리소스

+ [시작하기 전에 알아야 할 7가지](https://itnext.io/seccomp-in-kubernetes-part-i-7-things-you-should-know-before-you-even-start-97502ad6b6d6)
+ [AppArmor Loader](https://github.com/kubernetes/kubernetes/tree/master/test/images/apparmor-loader)
+ [프로파일을 사용하여 노드 설정](https://kubernetes.io/docs/tutorials/clusters/apparmor/#setting-up-nodes-with-profiles)
+ [Security Profiles Operator](https://github.com/kubernetes-sigs/security-profiles-operator)는 사용자가 쿠버네티스 클러스터에서 SELinux, seccomp 및 AppArmor를 더 쉽게 사용할 수 있도록 하는 것을 목표로 하는 쿠버네티스 개선 사항입니다. 워크로드를 실행하여 프로파일을 생성하고, 프로파일을 쿠버네티스 노드에 로드하여 파드에서 사용할 수 있는 기능을 모두 제공한다.
+ [Inspektor Gadget](https://github.com/inspektor-gadget/inspektor-gadget)를 사용하면 seccomp 프로파일 생성 지원을 포함하여 쿠버네티스에서 런타임 동작의 여러 측면을 검사, 추적 및 프로파일링할 수 있습니다.
+ [Aqua](https://www.aquasec.com/products/aqua-cloud-native-security-platform/)
+ [Qualys](https://www.qualys.com/apps/container-security/)
+ [Stackrox](https://www.stackrox.com/use-cases/threat-detection/)
+ [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
+ [Prisma](https://docs.paloaltonetworks.com/cn-series)
