# 런타임 보안
런타임 보안은 실행 중인 컨테이너에 대한 활성 보호를 제공합니다. 아이디어는 컨테이너 내부에서 악의적인 활동이 발생하는 것을 감지 및/또는 방지하는 것입니다. 보안 컴퓨팅(seccomp)을 사용하면 컨테이너화된 애플리케이션이 기본 호스트 운영 체제의 커널에 대한 특정 시스템 호출을 수행하지 못하도록 방지할 수 있습니다. Linux 운영 체제에는 수백 개의 시스템 호출이 있지만 대부분의 시스템 호출은 컨테이너를 실행하는 데 필요하지 않습니다. 컨테이너에서 수행할 수 있는 syscall을 제한하여 애플리케이션의 공격 표면을 효과적으로 줄일 수 있습니다. seccomp를 시작하려면 [`strace`](https://man7.org/linux/man-pages/man1/strace.1.html)를 사용하여 스택 추적을 생성하여 애플리케이션이 어떤 시스템 호출을 수행하는지 확인하세요. 그런 다음 [syscall2seccomp](https://github.com/antitree/syscall2seccomp)와 같은 도구를 사용하여 추적에서 수집된 데이터에서 seccomp 프로필을 만듭니다.

SELinux와 달리 seccomp는 컨테이너를 서로 격리하도록 설계되지 않았지만 승인되지 않은 시스템 호출로부터 호스트 커널을 보호합니다. 시스템 호출을 가로채고 허용된 항목만 통과하도록 허용하는 방식으로 작동합니다. Docker에는 대부분의 범용 워크로드에 적합한 [기본](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json) seccomp 프로필이 있습니다. 컨테이너 또는 포드의 사양(1.19 이전)에 다음 주석을 추가하여 이 프로필을 사용하도록 컨테이너 또는 포드를 구성할 수 있습니다.

```
주석:
   seccomp.security.alpha.kubernetes.io/pod: "런타임/기본값"
```

1.19 이상:

```
보안 컨텍스트:
   seccomp 프로필:
     유형: RuntimeDefault
```

추가 권한이 필요한 항목에 대한 고유한 프로필을 만들 수도 있습니다.

!!! 주의
     seccomp 프로필은 Kubelet 알파 기능입니다. 이 기능을 사용하려면 Kubelet 인수에 `--seccomp-profile-root` 플래그를 추가해야 합니다.

AppArmor는 seccomp와 유사하지만 파일 시스템의 일부에 액세스하는 것을 포함하여 컨테이너의 기능을 제한합니다. 시행 또는 불평 모드에서 실행할 수 있습니다. Apparmor 프로필을 구축하는 것은 어려울 수 있으므로 대신 [bane](https://github.com/genuinetools/bane)과 같은 도구를 사용하는 것이 좋습니다.

!!! 주목
     Apparmor는 Linux의 Ubuntu/Debian 배포판에서만 사용할 수 있습니다.

!!! 주목
     Kubernetes는 현재 AppArmor 또는 seccomp 프로필을 노드에 로드하기 위한 기본 메커니즘을 제공하지 않습니다. 수동으로 로드하거나 부트스트랩될 때 노드에 설치해야 합니다. 스케줄러는 프로필이 있는 노드를 알지 못하기 때문에 Pod에서 참조하기 전에 수행해야 합니다.

## 추천
### 런타임 방어를 위해 타사 솔루션 사용
Linux 보안에 익숙하지 않은 경우 seccomp 및 Apparmor 프로필을 만들고 관리하기 어려울 수 있습니다. 능숙해질 시간이 없다면 상용 솔루션 사용을 고려하십시오. 그들 중 다수는 Apparmor 및 seccomp와 같은 정적 프로필을 넘어 기계 학습을 사용하여 의심스러운 활동을 차단하거나 경고하기 시작했습니다. 이러한 솔루션 중 일부는 아래의 [도구](##도구) 섹션에서 찾을 수 있습니다. 추가 옵션은 [AWS Marketplace for Containers](https://aws.amazon.com/marketplace/features/containers)에서 찾을 수 있습니다.

### seccomp 정책을 작성하기 전에 Linux 기능 추가/삭제 고려
기능에는 시스템 호출이 도달할 수 있는 커널 기능의 다양한 검사가 포함됩니다. 확인에 실패하면 시스템 호출은 일반적으로 오류를 반환합니다. 확인은 특정 syscall의 시작 부분에서 바로 수행하거나 여러 다른 syscall을 통해 도달할 수 있는 커널의 더 깊은 영역(예: 특정 특권 파일에 쓰기)에서 수행할 수 있습니다. 반면에 Seccomp는 실행되기 전에 모든 시스템 호출에 적용되는 시스템 호출 필터입니다. 프로세스는 특정 시스템 호출 또는 특정 시스템 호출에 대한 특정 인수를 실행할 권한을 취소할 수 있는 필터를 설정할 수 있습니다.

seccomp를 사용하기 전에 Linux 기능 추가/제거가 필요한 제어 기능을 제공하는지 고려하십시오. [https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container](https://kubernetes.io/docs/tasks/configure- 자세한 내용은 pod-container/security-context/#set-capabilities-for-a-container)를 참조하십시오.

### 포드 보안 정책(PSP)을 사용하여 목표를 달성할 수 있는지 확인하십시오.
포드 보안 정책은 과도한 복잡성을 도입하지 않고 보안 태세를 개선할 수 있는 다양한 방법을 제공합니다. seccomp 및 Apparmor 프로파일을 구축하기 전에 PSP에서 사용 가능한 옵션을 살펴보십시오.

!!! 경고
     Kubernetes 1.25부터 PSP가 제거되고 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) 컨트롤러로 대체되었습니다. 존재하는 타사 대안에는 OPA/Gatekeeper 및 Kyverno가 포함됩니다. Gatekeeper 제약 조건 및 제약 조건 모음