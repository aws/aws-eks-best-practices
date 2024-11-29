---
search:
  exclude: true
---


# OOM(Out of Memory) 에러 방지

윈도우에는 Linux처럼 OOM 프로세스 킬러가 없습니다. 윈도우는 항상 모든 사용자 모드(user-mode) 메모리 할당을 가상으로 취급하며 pagefiles 가 필수입니다. 결과적으로 윈도우는 Linux와 같은 방식으로 OOM 상태에 도달하지 않습니다. 프로세스는 OOM로 종료되는 대신 디스크로 페이징됩니다. 메모리가 과도하게 프로비저닝되고 물리적 메모리가 모두 소진되면 페이징으로 인해 성능이 저하될 수 있습니다.

## 시스템 및 kubelet 메모리 예약
`--kubelet-reserve` 는 kubelet, 컨테이너 런타임 등과 같은 쿠버네티스 시스템 데몬에 대한 리소스 예약을 **캡처**하고 `--system-reserve` 는 sshd, udev 등과 같은 OS 시스템 데몬에 대한 리소스 예약을 **캡처**하고 설정하는 리눅스와는 다릅니다. **윈도우**에서 이런 플래그는 **kubelet** 또는 노드에서 실행되는 **프로세스**에 대한 메모리 제한을 **캡처**하거나 **설정**하지 않습니다.

하지만 이런 플래그를 조합하여 **NodeAllocatable**을 관리하여 파드 매니페스트에 **메모리 리소스 한도(memory resource limit)**가 있는 노드의 용량을 줄여 파드별로 메모리 할당을 제어할 수 있습니다. 이 전략을 사용하면 메모리 할당을 더 잘 제어할 수 있을 뿐만 아니라 윈도우 노드의 OOM을 최소화하는 메커니즘도 확보할 수 있습니다.

윈도우 노드에서는 OS 및 프로세스에 사용할 최소 2GB의 메모리를 예약하는 것이 가장 좋습니다. `--kubelet-reserve` 또는 `--system-reserve`  파라미터를 활용하여 NodeAllocatable을 줄일 수 있습니다.

[Amazon EKS 자체 관리형 윈도우 노드](https://docs.aws.amazon.com/eks/latest/userguide/launch-windows-workers.html) 설명에 따라 CloudFormation 템플릿을 사용하여 kubelet 구성을 커스터마이제이션 하여 새 윈도우 노드 그룹으로 시작할 수 있습니다. CloudFormation에는 `BootstraArguments`라는 요소가 있는데, 이는 `KubeletExtraArgs`와 동일합니다. 다음 플래그 및 값과 함께 사용할 수 있습니다.

```bash 
--kube-reserved memory=0.5Gi,ephemeral-storage=1Gi --system-reserved memory=1.5Gi,ephemeral-storage=1Gi --eviction-hard memory.available<200Mi,nodefs.available<10%"
```

eksctl을 배포 도구로 사용하는 경우, 다음 https://eksctl.io/usage/customizing-the-kubelet/ 문서를 참조하여 kubelet을 커스터마이즈 할 수 있습니다.

## 윈도우 컨테이너 메모리 요구 사항
[Microsoft 문서](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/system-requirements)에 따르면 NANO용 Windows Server 베이스 이미지에는 최소 30MB가 필요한 반면 윈도우 Server Core 이미지에는 45MB가 필요합니다. 이 수치는 .NET 프레임워크, IIS 웹 서비스 및 응용 프로그램과 같은 윈도우 구성 요소를 추가함에 따라 증가합니다.

윈도우 컨테이너 이미지(예: 기본 이미지와 해당 응용 프로그램 계층)에 필요한 최소 메모리 양을 알고 파드 스펙에 컨테이너의 리소스 requests를 설정하는 것이 중요합니다. 또한 애플리케이션 문제 발생 시 파드가 가용 노드 메모리를 모두 사용하지 않도록 limit을 설정해야 합니다.

아래 예제에서, 쿠버네티스 스케줄러가 노드에 파드를 배치하려고 할 때, 파드의 requests을 통해 충분한 리소스가 있는 노드를 결정하는데 사용합니다.

```yaml 
 spec:
  - name: iis
    image: mcr.microsoft.com/windows/servercore/iis:windowsservercore-ltsc2019
    resources:
      limits:
        cpu: 1
        memory: 800Mi
      requests:
        cpu: .1
        memory: 128Mi
```
## 결론

위와 같은 접근 방식을 사용해도 메모리 고갈 위험이 최소화되지만 발생 자체를 방지할 수는 없습니다. Amazon CloudWatch 메트릭 지표를 사용하면 메모리 소진이 발생할 경우 알림 및 해결 방법을 설정할 수 있습니다.

