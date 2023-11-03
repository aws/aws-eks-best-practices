# Kubernetes 애플리케이션 및 AWS 로드 밸런서를 통한 오류 및 타임아웃 방지

필요한 쿠버네티스 리소스 (서비스, 디플로이먼트, 인그레스 등) 를 생성한 후, 파드는 Elastic Load Balancer를 통해 클라이언트로부터 트래픽을 수신할 수 있어야 합니다. 하지만 애플리케이션 또는 Kubernetes 환경을 변경할 때 오류, 시간 초과 또는 연결 재설정이 생성될 수 있습니다. 이런 변경으로 인해 애플리케이션 배포 또는 조정 작업 (수동 또는 자동) 이 트리거될 수 있습니다.

안타깝게도 이런 오류는 애플리케이션이 문제를 기록하지 않는 경우에도 생성될 수 있습니다. 클러스터의 리소스를 제어하는 Kubernetes 시스템이 로드 밸런서의 대상 등록 및 상태를 제어하는 AWS 시스템보다 빠르게 실행될 수 있기 때문입니다. 애플리케이션이 요청을 수신할 준비가 되기 전에 파드가 트래픽을 수신하기 시작할 수도 있습니다.

파드가 Ready 상태가 되는 프로세스와 트래픽을 파드로 라우팅하는 방법을 살펴보겠습니다.


## 파드 Readiness

[2019 Kubecon talk](https://www.youtube.com/watch?v=Vw9GmSeomFg)에서 발췌한 이 다이어그램은 파드가 레디 상태가 되고 '로드밸런서' 서비스에 대한 트래픽을 수신하기 위해 거쳐진 단계를 보여준다.
![readiness.png](readiness.png)
*[Ready? A Deep Dive into Pod Readiness Gates for Service Health... - Minhan Xia & Ping Zou](https://www.youtube.com/watch?v=Vw9GmSeomFg)*  
NodePort 서비스의 멤버인 파드가 생성되면 쿠버네티스는 다음 단계를 거칩니다.

1. 파드는 쿠버네티스 컨트롤 플레인 (즉, `kubectl` 명령 또는 스케일링 액션으로부터) 에서 생성됩니다.
2. 파드는 `kube-scheduler`에 의해 스케줄링되며 클러스터의 노드에 할당됩니다.
3. 할당된 노드에서 실행 중인 kubelet은 업데이트를 수신하고 ('watch'를 통해) 로컬 컨테이너 런타임과 통신하여 파드에 지정된 컨테이너를 시작한다.
    1. 컨테이너가 실행을 시작하면 (그리고 선택적으로 `ReadinessProbes`만 전달하면), kubelet은 `kube-apiserver`로 업데이트를 전송하여 파드 상태를 `Ready`로 업데이트합니다.
4.  엔드포인트 컨트롤러는 ('watch'를 통해) 서비스의 엔드포인트 목록에 추가할 새 파드가 `Ready`라는 업데이트를 수신하고 적절한 엔드포인트 배열에 파드 IP/포트 튜플을 추가합니다.
5. `kube-proxy`는 서비스에 대한 iptables 규칙에 추가할 새 IP/포트가 있다는 업데이트 (`watch`를 통해) 를 수신한다.
    1. 워커 노드의 로컬 iptables 규칙이 NodePort 서비스의 추가 대상 파드로 업데이트됩니다.

!!! 참조
    인그레스 리소스와 인그레스 컨트롤러 (예: AWS 로드 밸런서 컨트롤러) 를 사용하는 경우 5단계는 `kube-proxy` 대신 관련 컨트롤러에서 처리됩니다.그러면 컨트롤러는 필요한 구성 단계 (예: 로드 밸런서에 대상 등록/등록 취소) 를 수행하여 트래픽이 예상대로 흐르도록 합니다.

[파드가 종료되거나](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) 준비되지 않은 상태로 변경되는 경우에도 유사한 프로세스가 발생합니다. API 서버는 컨트롤러, kubelet 또는 kubectl 클라이언트로부터 업데이트를 수신하여 파드를 종료합니다. 3~5단계는 거기서부터 계속되지만, 엔드포인트 목록과 iptables 규칙에서 파드 IP/튜플을 삽입하는 대신 제거합니다.

### 배포에 미치는 영향

다음은 애플리케이션 배포로 인해 파드 교체가 트리거될 때 취해진 단계를 보여주는 다이어그램입니다.
Below is a diagram showing the steps taken when an application deployment triggers the replacement of pods:
![deployments.png](deployments.png)
*[Ready? A Deep Dive into Pod Readiness Gates for Service Health... - Minhan Xia & Ping Zou](https://www.youtube.com/watch?v=Vw9GmSeomFg)*  
이 다이어그램에서 주목할 점은 첫 번째 파드가 "Ready" 상태에 도달할 때까지 두 번째 파드가 배포되지 않는다는 것입니다. 이전 섹션의 4단계와 5단계도 위의 배포 작업과 병행하여 수행됩니다.

즉, 디플로이먼트 컨트롤러가 다음 파드로 넘어갈 때 새 파드 상태를 전파하는 액션이 여전히 진행 중일 수 있습니다. 이 프로세스는 이전 버전의 파드도 종료하므로, 파드가 Ready 상태에 도달했지만 변경 사항이 계속 전파되고 이전 버전의 파드가 종료되는 상황이 발생할 수 있습니다.

위에서 설명한 Kubernetes 시스템은 기본적으로 로드 밸런서의 등록 시간이나 상태 확인을 고려하지 않기 때문에 AWS와 같은 클라우드 공급자의 로드 밸런서를 사용하면 이 문제가 더욱 악화됩니다. **즉 디플로이먼트 업데이트가 파드 전체에 걸쳐 완전히 순환될 수 있지만 로드 밸런서가 상태 점검 수행 또는 새 파드 등록을 완료하지 않아 운영 중단이 발생할 수 있습니다.**

파드가 종료될 때도 비슷한 문제가 발생합니다. 로드 밸런서 구성에 따라 파드의 등록을 취소하고 새 요청 수신을 중지하는 데 1~2분 정도 걸릴 수 있습니다. **쿠버네티스는 이런 등록 취소를 위해 롤링 디플로이먼트를 지연시키지 않으며, 이로 인해 로드 밸런서가 이미 종료된 대상 파드의 IP/포트로 트래픽을 계속 보내는 상태로 이어질 수 있습니다.**

이런 문제를 방지하기 위해 Kubernetes 시스템이 AWS Load Balancer 동작에 더 부합하는 조치를 취하도록 구성을 추가할 수 있습니다.

## 권장 사항

### IP 대상 유형 로드 밸런서 이용

`LoadBalancer` 유형의 서비스를 생성할 때, **인스턴스 대상 유형** 등록을 통해 로드 밸런서에서 *클러스터의 모든 노드*로 트래픽이 전송됩니다. 그러면 각 노드가 'NodePort'의 트래픽을 서비스 엔드포인트 어레이의 파드/IP 튜플로 리디렉션합니다. 이 타겟은 별도의 워커 노드에서 실행될 수 있습니다.

!!! 참조
    배열에는 "Ready" 파드만 있어야 한다는 점을 기억하세요.

![nodeport.png](nodeport.png)

이렇게 하면 요청에 홉이 추가되고 로드 밸런서 구성이 복잡해집니다.예를 들어 위의 로드 밸런서가 세션 어피니티로 구성된 경우 어피니티는 어피니티 구성에 따라 로드 밸런서와 백엔드 노드 사이에만 유지될 수 있습니다.

로드 밸런서가 백엔드 파드와 직접 통신하지 않기 때문에 쿠버네티스 시스템으로 트래픽 흐름과 타이밍을 제어하기가 더 어려워집니다.

[AWS 로드 밸런서 컨트롤러](https://github.com/kubernetes-sigs/aws-load-balancer-controller)를 사용하는 경우, **IP 대상 유형**을 사용하여 파드 IP/포트 튜플을 로드 밸런서에 직접 등록할 수 있습니다.
![ip.png](ip.png)  
이는 로드 밸런서에서 대상 파드로의 트래픽 경로를 단순화 합니다. 즉 새 대상이 등록되면 대상이 "Ready" Pod IP 및 포트인지 확인할 수 있고, 로드 밸런서의 상태 확인이 Pod에 직접 전달되며, VPC 흐름 로그를 검토하거나 유틸리티를 모니터링할 때 로드 밸런서와 파드 간의 트래픽을 쉽게 추적할 수 있습니다.

또한 IP 등록을 사용하면 `NodePort` 규칙을 통해 연결을 관리하는 대신 백엔드 파드에 대한 트래픽의 타이밍과 구성을 직접 제어할 수 있습니다.

### 파드 레디니스 게이트 활용

[파드 레디니스 게이트](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-readiness-gate) 는 파드가 "준비 완료" 상태에 도달하기 전에 충족되어야 하는 추가 요구사항이다.


>[[...] AWS Load Balancer 컨트롤러는 인그레스 또는 서비스 백엔드를 구성하는 파드에 대한 준비 조건을 설정할 수 있습니다. ALB/NLB 대상 그룹의 해당 대상의 상태가 "Healthy"로 표시되는 경우에만 파드의 조건 상태가 'True'로 설정됩니다. 이렇게 하면 새로 생성된 파드가 ALB/NLB 대상 그룹에서 "정상"으로 되어 트래픽을 받을 준비가 될 때까지 디플로이먼트의 롤링 업데이트가 기존 파드를 종료하지 않도록 한다.](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/pod_readiness_gate/)

레디니스 게이트는 배포 중에 새 복제본을 생성할 때 Kubernetes가 "너무 빨리" 움직이지 않도록 하고 Kubernetes는 배포를 완료했지만 새 Pod가 등록을 완료하지 않은 상황을 방지합니다.

이를 활성화하려면 다음을 수행해야 합니다.

1. 최신 버전의 [AWS 로드 밸런서 컨트롤](https://github.com/kubernetes-sigs/aws-load-balancer-controller)를 배포합니다. (**[*이전 버전을 업그레이드하는 경우 설명서를 참조*](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/upgrade/migrate_v1_v2/)**)
2. 파드 레디니스 게이트를 자동으로 주입하려면 `elbv2.k8s.aws/pod-readiness-gate-inject: enabled` 레이블로 [타겟 파드가 실행 중인 네임스페이스에 레이블을 붙입니다.](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/pod_readiness_gate/).
3. 네임스페이스의 모든 파드가 준비 게이트 컨피그레이션을 가져오도록 하려면 인그레스 또는 서비스를 생성하고 파드를 생성하기 ***전에*** 네임스페이스에 레이블을 지정해야 한다.


### 종료*전*에 로드 밸런서에서 파드의 등록이 취소되었는지 확인

When a pod is terminated steps 4 and 5 from the pod readiness section occur at the same time that the container processes receive the termination signals. This means that if your container is able to shut down quickly it may shut down faster than the Load Balancer is able to deregister the target. To avoid this situation adjust the Pod spec with:

1. 애플리케이션이 등록을 취소하고 연결을 정상적으로 종료할 수 있도록 'PreStop' 라이프사이클 훅을 추가합니다. 이 훅은 API 요청 또는 관리 이벤트 (예: 라이브니스/스타트업 프로브 실패, 선점, 리소스 경합 등) 로 인해 컨테이너가 종료되기 직전에 호출됩니다. 중요한 점은 [이 훅이 호출되어 종료 신호가 전송되기 **전에** 완료되도록 허용됨](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) 입니다. 단, 유예 기간이 실행을 수용할 수 있을 만큼 충분히 길어야 합니다.

```
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 180"] 
```
위와 같은 간단한 sleep 명령을 사용하면 파드가 `Terminating (종료 중)`으로 표시된 시점 (그리고 로드 밸런서 등록 취소가 시작되는 시점) 과 종료 신호가 컨테이너 프로세스로 전송되는 시점 사이에 짧은 지연을 발생시킬 수 있다.필요한 경우 이 훅를 고급 애플리케이션 종료/종료 절차에도 활용할 수 있습니다.

2. 전체 `프리스톱` 실행 시간과 애플리케이션이 종료 신호에 정상적으로 응답하는 데 걸리는 시간을 수용할 수 있도록 'TerminationGracePeriodsSeconds'를 연장하십시오.아래 예시에서는 유예 기간을 200초로 연장하여 전체 `sleep 180` 명령을 완료한 다음, 앱이 정상적으로 종료될 수 있도록 20초 더 연장했습니다.

```
    spec:
      terminationGracePeriodSeconds: 200
      containers:
      - name: webapp
        image: webapp-st:v1.3
        [...]
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 180"] 
```

### 파드에 레디니스 프로브가 있는지 확인

쿠버네티스에서 파드를 생성할 때 기본 준비 상태는 "Ready"이지만, 대부분의 애플리케이션은 인스턴스화하고 요청을 받을 준비가 되는 데 1~2분 정도 걸립니다. [파드 스펙에서 '레디니스 프로브'를 정의할 수 있습니다.](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) 실행 명령어 또는 네트워크 요청을 사용하여 애플리케이션이 시작을 완료하고 트래픽을 처리할 준비가 되었는지 확인하는 데 사용됩니다.

`레디니스 프로브`로 정의된 파드는 "NotReady" 상태에서 시작하며, `레디니스 프로브`가 성공했을 때만 "준비 완료"로 변경됩니다. 이렇게 하면 애플리케이션 시작이 완료될 때까지 애플리케이션이 "서비스 중"으로 전환되지 않습니다.

장애 상태 (예: 교착 상태) 에 들어갈 때 애플리케이션을 다시 시작할 수 있도록 라이브니스 프로브를 사용하는 것이 좋지만, 활성 장애가 발생하면 애플리케이션 재시작을 트리거하므로 Stateful 애플리케이션을 사용할 때는 주의해야 합니다. 시작 속도가 느린 애플리케이션에도 [스타트업 프로브](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#define-startup-probes)를 활용할 수 있습니다.

아래 프로브는 포트 80에 대한 HTTP 프로브를 사용하여 웹 애플리케이션이 언제 준비되는지 확인합니다 (활성 프로브에도 동일한 프로브 구성이 사용됨).

```
        [...]
        ports:
        - containerPort: 80
        livenessProbe:
          httpGet:
            path: /
            port: 80
          failureThreshold: 1
          periodSeconds: 10
          initialDelaySeconds: 5
        readinessProbe:
          httpGet:
            path: /
            port: 80
          periodSeconds: 5
        [...]
```

### 파드 중단 예산 (PDB) 설정

[파드 중단 예산 (PDB)](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/#pod-disruption-budgets)은 복제된 애플리케이션 중 [자발적 중단](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/#voluntary-and-involuntary-disruptions)으로 인해 동시에 다운되는 파드의 수를 제한합니다. 예를 들어 쿼럼 기반 응용 프로그램에서는 실행 중인 복제본 수가 쿼럼에 필요한 수 이하로 떨어지지 않도록 하려는 경우가 있습니다. 웹 프런트 엔드는 부하를 처리하는 복제본의 수가 전체 복제본의 특정 비율 이하로 떨어지지 않도록 해야 할 수 있습니다.

PDB는 노드 드레이닝 또는 애플리케이션 배포와 같은 것으로부터 애플리케이션을 보호합니다. PDB는 이런 조치를 취하는 동안 사용할 수 있는 파드의 수 또는 비율을 최소한으로 유지합니다.

!!! 주의
    PDB는 호스트 OS 장애 또는 네트워크 연결 손실과 같은 비자발적 중단으로부터 애플리케이션을 보호하지 않습니다.

아래 예시는 `app: echoserver` 레이블이 붙은 파드를 항상 1개 이상 사용할 수 있도록 만듭니다. [애플리케이션에 맞는 올바른 레플리카 수를 구성하거나 백분율을 사용할 수 있습니다.](https://kubernetes.io/docs/tasks/run-application/configure-pdb/#think-about-how-your-application-reacts-to-disruptions):

```
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: echoserver-pdb
  namespace: echoserver
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: echoserver
```

### 종료 신호를 정상적으로 처리

파드가 종료되면 컨테이너 내에서 실행되는 애플리케이션은 두 개의 [Signal](https://www.gnu.org/software/libc/manual/html_node/Standard-Signals.html)을 수신합니다. 첫 번째는 [`SIGTERM` 신호](https://www.gnu.org/software/libc/manual/html_node/Termination-Signals.html)이며, 이는 프로세스 실행을 중단하라는 "정중한" 요청입니다. 이 신호는 차단될 수도 있고 애플리케이션이 단순히 이 신호를 무시할 수도 있으므로, `terminationGracePeriodSeconds`이 경과하면 애플리케이션은 [`SIGKILL` 신호](https://www.gnu.org/software/libc/manual/html_node/Termination-Signals.html)를 받게 됩니다. `SIGKILL`은 프로세스를 강제로 중지하는 데 사용되며, [차단, 처리 또는 무시](https://man7.org/linux/man-pages/man7/signal.7.html) 될 수 없으므로 항상 치명적입니다.

이런 신호는 컨테이너 런타임에서 애플리케이션 종료를 트리거하는 데 사용됩니다.또한 `SIGTERM` 신호는 `preStop` 훅이 실행된 후에 전송됩니다. 위 구성에서 `preStop` 훅은 로드 밸런서에서 파드의 등록이 취소되었는지 확인하므로 애플리케이션은 `SIGTERM` 신호가 수신될 때 열려 있는 나머지 연결을 정상적으로 종료할 수 있습니다.

!!! 참조
    [애플리케이션의 진입점에 "래퍼 스크립트"를 사용할 경우 컨테이너 환경에서의 신호 처리는 복잡할 수 있습니다.](https://petermalmgren.com/signal-handling-docker/) 스크립트는 PID 1이므로 신호를 애플리케이션으로 전달하지 않을 수 있습니다.


### 등록 취소 지연에 주의

Elastic Load Balancing은 등록 취소 중인 대상에 대한 요청 전송을 중지합니다.기본적으로 Elastic Load Balancing은 등록 취소 프로세스를 완료하기 전에 300초 정도 대기하므로 대상에 대한 진행 중인 요청을 완료하는 데 도움이 될 수 있습니다. Elastic Load Balancing이 대기하는 시간을 변경하려면 등록 취소 지연 값을 업데이트하십시오.
등록 취소 대상의 초기 상태는 `draining`입니다. 등록 취소 지연이 경과하면 등록 취소 프로세스가 완료되고 대상의 상태는 `unused`가 됩니다. 대상이 Auto Scaling 그룹의 일부인 경우 대상을 종료하고 교체할 수 있습니다.

등록 취소 대상에 진행 중인 요청이 없고 활성 연결이 없는 경우 Elastic Load Balancing은 등록 취소 지연이 경과할 때까지 기다리지 않고 등록 취소 프로세스를 즉시 완료합니다.

!!! 주의
    대상 등록 취소가 완료되더라도 등록 취소 지연 제한 시간이 만료될 때까지 대상 상태가 '드레이닝 중'으로 표시됩니다. 제한 시간이 만료되면 대상은 '미사용' 상태로 전환됩니다.

[등록 취소 지연이 경과하기 전에 등록 취소 대상이 연결을 종료하면 클라이언트는 500레벨 오류 응답을 받습니다.](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html#deregistration-delay).

이는 [`alb.ingress.kubernetes.io/target-group-attributes` 어노테이션](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/guide/ingress/annotations/#target-group-attributes)을 사용하여 인그레스 리소스의 어노테이션을 사용하여 구성할 수 있습니다. 아래는 예제입니다.

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: echoserver-ip
  namespace: echoserver
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/load-balancer-name: echoserver-ip
    alb.ingress.kubernetes.io/target-group-attributes: deregistration_delay.timeout_seconds=30
spec:
  ingressClassName: alb
  rules:
    - host: echoserver.example.com
      http:
        paths:
          - path: /
            pathType: Exact
            backend:
              service:
                name: echoserver-service
                port:
                  number: 8080
```
