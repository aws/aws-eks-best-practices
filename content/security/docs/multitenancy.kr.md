# 임차인 격리
다중 테넌시를 생각할 때 공유 인프라에서 실행되는 다른 사용자 또는 애플리케이션으로부터 사용자 또는 애플리케이션을 격리하려는 경우가 많습니다.

Kubernetes는 _단일 테넌트 오케스트레이터_ 입니다 . 즉, 컨트롤 플레인의 단일 인스턴스가 클러스터 내의 모든 테넌트 간에 공유됩니다. 그러나 다중 테넌시의 유사성을 생성하는 데 사용할 수 있는 다양한 Kubernetes 개체가 있습니다. 예를 들어 네임스페이스 및 RBAC(역할 기반 액세스 제어)를 구현하여 테넌트를 서로 논리적으로 격리할 수 있습니다. 마찬가지로 할당량 및 제한 범위를 사용하여 각 테넌트가 사용할 수 있는 클러스터 리소스의 양을 제어할 수 있습니다. 그럼에도 불구하고 클러스터는 강력한 보안 경계를 제공하는 유일한 구조입니다. 이는 클러스터 내의 호스트에 대한 액세스를 관리하는 공격자가 해당 호스트에 마운트된 _all_ 비밀, ConfigMap 및 볼륨을 검색할 수 있기 때문입니다. 그들은 또한 Kubelet을 사칭하여 노드의 속성을 조작하거나 클러스터 내에서 측면으로 이동할 수 있습니다.

다음 섹션에서는 Kubernetes와 같은 단일 테넌트 오케스트레이터를 사용하는 위험을 완화하면서 테넌트 격리를 구현하는 방법을 설명합니다.

## 소프트 멀티테넌시

소프트 멀티 테넌시에서는 네임스페이스, 역할 및 역할 바인딩, 네트워크 정책과 같은 기본 Kubernetes 구조를 사용하여 테넌트 간에 논리적 분리를 생성합니다. 예를 들어 RBAC는 테넌트가 서로의 리소스에 액세스하거나 조작하는 것을 방지할 수 있습니다. 할당량 및 제한 범위는 각 테넌트가 사용할 수 있는 클러스터 리소스의 양을 제어하는 반면 네트워크 정책은 서로 다른 네임스페이스에 배포된 애플리케이션이 서로 통신하지 못하도록 방지할 수 있습니다.

그러나 이러한 제어 중 어느 것도 다른 테넌트의 포드가 노드를 공유하는 것을 방지하지 않습니다. 더 강력한 격리가 필요한 경우 노드 선택기, 반선호도 규칙 및/또는 taint 및 toleration을 사용하여 다른 테넌트의 포드를 별도의 노드에 예약하도록 강제할 수 있습니다. 종종 _단독 테넌트 노드_ 라고 합니다 . 테넌트가 많은 환경에서는 다소 복잡하고 비용이 많이 들 수 있습니다.

!!! 주목
Namespaces로 구현된 Soft multi-tenancy는 Namespaces가 전역 범위 유형이기 때문에 필터링된 Namespaces 목록을 테넌트에게 제공할 수 없습니다. 테넌트가 특정 네임스페이스를 볼 수 있는 경우 클러스터 내의 모든 네임스페이스를 볼 수 있습니다.

!!! 경고
소프트 멀티테넌시를 통해 테넌트는 기본적으로 클러스터 내에서 실행되는 모든 서비스에 대해 CoreDNS를 쿼리할 수 있는 기능을 유지합니다. 공격자 는 클러스터의 모든 포드에서 dig SRV *.* .svc.cluster.local을 실행하여 이를 악용할 수 있습니다. 클러스터 내에서 실행되는 서비스의 DNS 레코드에 대한 액세스를 제한해야 하는 경우 CoreDNS용 방화벽 또는 정책 플러그인을 사용하는 것이 좋습니다. 추가 정보는 [ https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy ]( https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy )를 참조하십시오. ).

[ 키오스크 ]( https://github.com/kiosk-sh/kiosk )는 소프트 멀티 테넌시의 구현을 지원할 수 있는 오픈 소스 프로젝트입니다. 다음 기능을 제공하는 일련의 CRD 및 컨트롤러로 구현됩니다.

  + 공유 Kubernetes 클러스터에서 테넌트를 분리하기 위한 **계정 및 계정 사용자**
  + 계정 사용자를 위한 **셀프 서비스 네임스페이스 프로비저닝**
  + 클러스터 공유 시 서비스 품질 및 공정성을 보장하기 위한 **계정 제한**
  + 안전한 테넌트 격리 및 셀프 서비스 네임스페이스 초기화를 위한 **네임스페이스 템플릿**
  
[ Loft ]( https://loft.sh )는 다음 기능을 추가하는 Kiosk 및 [ DevSpace ]( https://github.com/devspace-cloud/devspace )의 관리자가 제공하는 상용 제품입니다.

  + 다른 클러스터의 공간에 대한 액세스 권한을 부여하기 위한 **멀티 클러스터 액세스**
  + **절전 모드** 는 비활성 기간 동안 공간에서 배포를 축소합니다.
  + ** GitHub와 같은 OIDC 인증 공급자를 사용한 싱글 사인온**

소프트 멀티 테넌시로 해결할 수 있는 세 가지 기본 사용 사례가 있습니다.

### 엔터프라이즈 설정

첫 번째는 "임차인"이 직원, 계약자이거나 조직에서 다른 방식으로 권한을 부여한다는 점에서 반신뢰되는 엔터프라이즈 환경에 있습니다. 각 테넌트는 일반적으로 부서 또는 팀과 같은 관리 부서에 맞춰집니다.

이러한 유형의 설정에서 클러스터 관리자는 일반적으로 네임스페이스 생성 및 정책 관리를 담당합니다. 또한 특정 개인에게 네임스페이스를 감독하는 위임된 관리 모델을 구현하여 배포, 서비스, 포드, 작업 등과 같은 정책과 관련되지 않은 개체에 대한 CRUD 작업을 수행할 수 있습니다.

컨테이너 런타임에서 제공하는 격리는 이 설정 내에서 허용되거나 포드 보안을 위한 추가 제어로 강화되어야 할 수 있습니다. 더 엄격한 격리가 필요한 경우 다른 네임스페이스의 서비스 간 통신을 제한해야 할 수도 있습니다.

### 서비스형 쿠버네티스

반대로 소프트 멀티테넌시는 Kubernetes를 KaaS(Kubernetes as a Service)로 제공하려는 설정에서 사용할 수 있습니다. KaaS를 사용하면 애플리케이션이 일련의 PaaS 서비스를 제공하는 컨트롤러 및 CRD 모음과 함께 공유 클러스터에서 호스팅됩니다. 테넌트는 Kubernetes API 서버와 직접 상호 작용하며 비정책 개체에서 CRUD 작업을 수행할 수 있습니다. 테넌트가 자신의 네임스페이스를 만들고 관리할 수 있다는 점에서 셀프 서비스 요소도 있습니다 . 이러한 유형의 환경에서 테넌트는 신뢰할 수 없는 코드를 실행하는 것으로 간주됩니다.

_pod sandboxing_ 을 구현해야 할 가능성이 높습니다 . 샌드박싱은 Firecracker와 같은 마이크로 VM 또는 사용자 공간 커널에서 포드의 컨테이너를 실행하는 곳입니다. 현재 EKS Fargate를 사용하여 샌드박스 포드를 생성할 수 있습니다.

### 서비스형 소프트웨어(SaaS)

소프트 멀티테넌시의 최종 사용 사례는 SaaS(Software-as-a-Service) 설정입니다. 이 환경에서 각 테넌트는 클러스터 내에서 실행 중인 애플리케이션의 특정 _instance_ 와 연결됩니다. 각 인스턴스에는 종종 자체 데이터가 있으며 일반적으로 Kubernetes RBAC와 독립적인 별도의 액세스 제어를 사용합니다.

다른 사용 사례와 달리 SaaS 설정의 테넌트는 Kubernetes API와 직접 인터페이스하지 않습니다. 대신 SaaS 애플리케이션은 각 테넌트를 지원하는 데 필요한 객체를 생성하기 위해 Kubernetes API와의 인터페이스를 담당합니다.

## Kubernetes 구성

이러한 각 인스턴스에서 테넌트를 서로 격리하는 데 다음 구성이 사용됩니다.

### 네임스페이스

네임스페이스는 소프트 멀티테넌시 구현의 기본입니다. 이를 통해 클러스터를 논리적 파티션으로 나눌 수 있습니다. 다중 테넌시를 구현하는 데 필요한 할당량, 네트워크 정책, 서비스 계정 및 기타 개체의 범위는 네임스페이스로 지정됩니다.

### 네트워크 정책

기본적으로 Kubernetes 클러스터의 모든 포드는 서로 통신할 수 있습니다. 이 동작은 네트워크 정책을 사용하여 변경할 수 있습니다.

네트워크 정책은 레이블 또는 IP 주소 범위를 사용하여 포드 간의 통신을 제한합니다. 테넌트 간에 엄격한 네트워크 격리가 필요한 다중 테넌트 환경에서는 포드 간의 통신을 거부하는 기본 규칙과 모든 포드가 이름 확인을 위해 DNS 서버를 쿼리하도록 허용하는 다른 규칙으로 시작하는 것이 좋습니다. 이를 통해 네임스페이스 내에서 통신을 허용하는 더 많은 허용 규칙을 추가할 수 있습니다. 이는 필요에 따라 더 세분화할 수 있습니다.

!!! 주목
네트워크 정책은 필요하지만 충분하지 않습니다. 네트워크 정책을 시행하려면 Calico 또는 Cilium과 같은 정책 엔진이 필요합니다.

### 역할 기반 액세스 제어(RBAC)

역할 및 역할 바인딩은 Kubernetes에서 역할 기반 액세스 제어(RBAC)를 적용하는 데 사용되는 Kubernetes 개체입니다. **역할** 에는 클러스터의 개체에 대해 수행할 수 있는 작업 목록이 포함되어 있습니다. **역할 결합** 은 역할이 적용되는 개인 또는 그룹을 지정합니다. 엔터프라이즈 및 KaaS 설정에서 RBAC를 사용하여 선택한 그룹 또는 개인이 개체를 관리할 수 있습니다.

### 할당량

할당량은 클러스터에서 호스팅되는 워크로드에 대한 제한을 정의하는 데 사용됩니다. 할당량을 사용하면 포드가 사용할 수 있는 최대 CPU 및 메모리 양을 지정하거나 클러스터 또는 네임스페이스에 할당할 수 있는 리소스 수를 제한할 수 있습니다. **제한 범위** 를 사용하면 각 제한에 대한 최소값, 최대값 및 기본값을 선언할 수 있습니다.

공유 클러스터에서 리소스를 오버 커밋하면 리소스를 최대화할 수 있기 때문에 종종 유익합니다. 그러나 클러스터에 대한 제한 없는 액세스는 리소스 고갈을 유발할 수 있으며, 이는 성능 저하 및 애플리케이션 가용성 손실로 이어질 수 있습니다. Pod의 요청이 너무 낮게 설정되고 실제 리소스 사용률이 노드의 용량을 초과하면 노드에서 CPU 또는 메모리 압력이 발생하기 시작합니다. 이 경우 Pod가 다시 시작되거나 노드에서 제거될 수 있습니다.

이를 방지하려면 다중 테넌트 환경에서 네임스페이스에 할당량을 부과하여 테넌트가 클러스터에서 포드를 예약할 때 요청 및 제한을 지정하도록 해야 합니다. 또한 포드가 소비할 수 있는 리소스 양을 제한하여 잠재적인 서비스 거부를 완화합니다.

또한 할당량을 사용하여 테넌트의 지출에 맞게 클러스터의 리소스를 할당할 수 있습니다. 이는 KaaS 시나리오에서 특히 유용합니다.

### 포드 우선순위 및 선점

포드 우선 순위 및 선점은 다양한 고객에게 다양한 서비스 품질(QoS)을 제공하려는 경우에 유용할 수 있습니다. 예를 들어 포드 우선 순위를 사용하면 고객 A의 포드가 고객 B보다 높은 우선 순위로 실행되도록 구성할 수 있습니다. 사용 가능한 용량이 충분하지 않으면 Kubelet은 고객 B의 우선 순위가 낮은 포드를 제거하여 고객의 우선 순위가 높은 포드를 수용합니다. A. 프리미엄을 기꺼이 지불하려는 고객이 더 높은 품질의 서비스를 받는 SaaS 환경에서 특히 유용할 수 있습니다.

## 완화 제어

다중 테넌트 환경의 관리자로서 귀하의 주요 관심사는 공격자가 기본 호스트에 대한 액세스 권한을 얻지 못하도록 방지하는 것입니다. 이 위험을 완화하려면 다음 제어를 고려해야 합니다.

### 컨테이너용 샌드박스 실행 환경

샌드박싱은 각 컨테이너가 자체 격리된 가상 머신에서 실행되는 기술입니다. 포드 샌드박싱을 수행하는 기술에는 [ Firecracker ]( https://firecracker-microvm.github.io/ ) 및 Weave의 [ Firekube ]( https://www.weave.works/blog/firekube-fast-and-secure-kubernetes 가 포함됩니다. -clusters-using-weave-ignite ).

AWS에서 자체 관리형 Kubernetes 클러스터를 구축하는 경우 [ Kata 컨테이너 ]( https://github.com/kata-containers/documentation/wiki/Initial-release- 와 같은 대체 컨테이너 런타임을 구성할 수 있습니다. of-Kata-Containers-with-Firecracker-support ).

Firecracker를 EKS에 대해 지원되는 런타임으로 만들기 위한 노력에 대한 추가 정보는 다음을 참조하십시오.
[ https://threadreaderapp.com/thread/1238496944684597248.html ]( https://threadreaderapp.com/thread/1238496944684597248.html ).

### 개방형 정책 에이전트(OPA) 및 게이트키퍼

[ Gatekeeper ]( https://github.com/open-policy-agent/gatekeeper )는 [ OPA ]( https://www.openpolicyagent.org/ ) 로 생성된 정책을 시행하는 Kubernetes 승인 컨트롤러입니다 . OPA를 사용하면 별도의 인스턴스 또는 다른 테넌트보다 더 높은 우선순위에서 테넌트의 포드를 실행하는 정책을 생성할 수 있습니다. 이 프로젝트에 대한 일반적인 OPA 정책 모음은 GitHub [ 리포지토리 ]( https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa )에서 찾을 수 있습니다.

를 사용하여 CoreDNS에서 반환된 레코드를 필터링/제어할 수 있는 실험적인 [ CoreDNS용 OPA 플러그인 ]( https://github.com/coredns/coredns-opa )도 있습니다.

### 카이베르노

[ Kyverno ]( https://kyverno.io )는 정책을 Kubernetes 리소스로 사용하여 구성을 검증, 변경 및 생성할 수 있는 Kubernetes 기본 정책 엔진입니다. Kyverno는 유효성 검사를 위해 Kustomize 스타일 오버레이를 사용하고 변형을 위한 JSON 패치 및 전략적 병합 패치를 지원하며 유연한 트리거를 기반으로 네임스페이스 간에 리소스를 복제할 수 있습니다.

Kyverno를 사용하여 네임스페이스를 격리하고, 포드 보안 및 기타 모범 사례를 적용하고, 네트워크 정책과 같은 기본 구성을 생성할 수 있습니다. 이 프로젝트 의 GitHub [ 리포지토리 ]( https://github.com/aws/aws-eks-best-practices/tree/master/policies/kyverno )에 몇 가지 예제가 포함되어 있습니다. 다른 많은 것들이 Kyverno 웹사이트 의 [ 정책 라이브러리 ]( https://kyverno.io/policies/ )에 포함되어 있습니다.

### 테넌트 워크로드를 특정 노드로 격리

특정 노드에서 실행되도록 테넌트 워크로드를 제한하면 소프트 다중 테넌시 모델에서 격리를 강화하는 데 사용할 수 있습니다. 이 접근 방식을 사용하면 테넌트별 워크로드는 각 테넌트에 대해 프로비저닝된 노드에서만 실행됩니다. 이러한 격리를 달성하기 위해 기본 Kubernetes 속성(노드 선호도, 오염 및 허용 오차)을 사용하여 Pod 예약을 위해 특정 노드를 대상으로 지정하고 다른 테넌트의 Pod가 테넌트별 노드에서 예약되지 않도록 합니다.

#### 1부 - 노드 선호도

Kubernetes [ 노드 선호도 ]( https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity )는 노드 [ 레이블 을 기반으로 예약 대상 노드에 사용됩니다. ]( https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/ ). 노드 친화성 규칙을 사용하면 포드는 선택기 용어와 일치하는 특정 노드에 끌립니다. 아래 포드 사양에서 'requiredDuringSchedulingIgnoredDuringExecution' 노드 어피니티가 각 포드에 적용됩니다. 그 결과 포드는 `tenant: tenants-x` 키/값으로 레이블이 지정된 노드를 대상으로 합니다 .

``` 얌
...
사양 :
  선호도 :
    노드친화도 :
      requiredDuringSchedulingIgnoredDuringExecution :
        nodeSelector조건 :
- matchExpressions :
- 키 : 테넌트
            연산자 : 안으로
            값 :
- 테넌트-x
...
```

이 노드 선호도를 사용하면 예약 중에는 레이블이 필요하지만 실행 중에는 필요하지 않습니다. 기본 노드의 레이블이 변경되면 해당 레이블 변경만으로 포드가 제거되지 않습니다. 그러나 향후 일정에 영향을 미칠 수 있습니다.

!!! 정보
노드 선호도 대신 [ 노드 선택기 ]( https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector )를 사용할 수 있습니다. 그러나 노드 어피니티는 표현력이 더 풍부하며 포드 스케줄링 중에 더 많은 조건을 고려할 수 있습니다. 차이점 및 고급 스케줄링 선택에 대한 추가 정보는 [ Advanced Kubernetes pod to node scheduling ]( https://www.cncf.io/blog/2021/07/27/advanced-kubernetes- 에 대한 CNCF 블로그 게시물을 참조하십시오. Pod-to-node-scheduling/ ).

#### 파트 2 - 오염 및 허용

Pod를 노드로 끌어들이는 것은 이 세 부분으로 구성된 접근 방식의 첫 번째 부분에 불과합니다. 이 접근 방식이 작동하려면 포드가 권한이 부여되지 않은 노드로 예약되지 않도록 포드를 밀어내야 합니다. 원치 않거나 승인되지 않은 포드를 방지하기 위해 Kubernetes는 노드 [ taints ]( https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/ )를 사용합니다. taint는 Pod가 예약되지 않도록 노드에 조건을 지정하는 데 사용됩니다. 아래 taint는 `tenant: tenants-x` 의 키-값 쌍을 사용합니다 .

``` 얌
...
    오염 :
- 키 : 테넌트
        값 : 테넌트-x
        효과 : 스케줄 없음
...
```

위의 노드 `taint` 가 주어지면 오염을 _용인하는_ 포드만 노드에서 예약할 수 있습니다. 승인된 포드가 노드에 예약되도록 하려면 각 포드 사양에 아래와 같이 taint에 대한 'toleration' 이 포함되어야 합니다.

``` 얌
...
  관용 :
- 효과 : NoSchedule
    키 : 임차인
    연산자 : 같음
    값 : 테넌트-x
...
```

'toleration' 이 있는 포드 는 적어도 해당 특정 오염으로 인해 노드에서 스케줄링이 중지되지 않습니다. 테인트는 Kubernetes에서 노드 리소스 압력과 같은 특정 조건에서 Pod 예약을 일시적으로 중지하는 데에도 사용됩니다. 노드 선호도, taint 및 toleration을 통해 원하는 pod를 특정 노드로 효과적으로 유인하고 원치 않는 pod를 격퇴할 수 있습니다.

!!! 주목
모든 노드에서 실행하려면 특정 Kubernetes 포드가 필요합니다. 이러한 포드의 예는 [ 컨테이너 네트워크 인터페이스(CNI) ]( https://github.com/containernetworking/cni ) 및 [ kube-proxy ]( https://kubernetes.io/docs/reference/command 에 의해 시작된 포드입니다. -line-tools-reference/kube-proxy/ ) [ daemonsets ]( https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/ ). 이를 위해 이러한 팟(Pod)의 사양에는 다양한 오염을 허용하기 위해 매우 허용적인 허용 오차가 포함되어 있습니다. 이러한 허용 오차를 변경하지 않도록 주의해야 합니다. 이러한 내결함성을 변경하면 잘못된 클러스터 작업이 발생할 수 있습니다. 또한 [ OPA/Gatekeeper ]( https://github.com/open-policy-agent/gatekeeper ) 및 [ Kyverno ]( https://kyverno.io/ )와 같은 정책 관리 도구를 사용하여 작성할 수 있습니다. 승인되지 않은 팟(Pod)이 이러한 관대한 내결함성을 사용하지 못하도록 방지하는 정책을 검증합니다.

#### 3부 - 노드 선택을 위한 정책 기반 관리

CICD 파이프라인의 규칙 적용을 포함하여 포드 사양의 노드 선호도 및 내결함성을 관리하는 데 사용할 수 있는 몇 가지 도구가 있습니다. 그러나 격리 적용은 Kubernetes 클러스터 수준에서도 수행되어야 합니다. 이를 위해 정책 관리 도구를 사용하여 요청 페이로드를 기반으로 인바운드 Kubernetes API 서버 요청을 _변형_ 하여 위에서 언급한 각 노드 선호도 규칙 및 허용을 적용할 수 있습니다.

예를 들어 _tenants-x_ 네임스페이스 로 향하는 포드는 _tenants-x_ 노드 에서 예약을 허용하기 위해 올바른 노드 선호도 및 내결함성 을 사용하여 _스탬프_될 수 있습니다 . Kubernetes [ Mutating Admission Webhook ]( https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#mutatingadmissionwebhook )를 사용하여 구성된 정책 관리 도구를 활용하여 정책을 사용하여 인바운드 포드를 변형할 수 있습니다. 명세서. 돌연변이는 원하는 일정을 허용하는 데 필요한 요소를 추가합니다. 노드 선호도를 추가하는 OPA/게이트키퍼 정책의 예는 아래에 나와 있습니다.

``` 얌
apiVersion : mutations.gatekeeper.sh/v1alpha1
종류 : 할당
메타데이터 :
  이름 : mutator-add-nodeaffinity-pod
  주석 :
    aws-eks-best-practices/description : > -
노드 선호도 추가 - https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#node-affinity
사양 :
  적용 대상 :
- 그룹 : [ "" ]
    종류 : [ "포드" ]
    버전 : [ "v1" ]
  일치 :
    네임스페이스 : [ "tenants-x" ]
  위치 : "spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms"
  매개변수 :
    할당 :
      값 :
- matchExpressions :
- 키 : "임차인"
            연산자 : 안으로
            값 :
- "세입자-x"
```

_tenants-x_ 네임스페이스 에 포드를 적용하기 위해 Kubernetes API 서버 요청에 적용됩니다 . 이 정책은 `requiredDuringSchedulingIgnoredDuringExecution` 노드 친화성 규칙을 추가하여 포드가 `tenant: tenants-x` 레이블이 있는 노드에 유인됩니다.

아래에 표시된 두 번째 정책은 대상 네임스페이스와 그룹, 종류 및 버전의 동일한 일치 기준을 사용하여 동일한 포드 사양에 내결함성을 추가합니다.

``` 얌
apiVersion : mutations.gatekeeper.sh/v1alpha1
종류 : 할당
메타데이터 :
  이름 : mutator-add-toleration-pod
  주석 :
    aws-eks-best-practices/description : > -
관용 추가 - https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
사양 :
  적용 대상 :
- 그룹 : [ "" ]
    종류 : [ "포드" ]
    버전 : [ "v1" ]
  일치 :
    네임스페이스 : [ "tenants-x" ]
  위치 : "사양 허용"
  매개변수 :
    할당 :
      값 :
- 키 : "임차인"
        연산자 : "같음"
        값 : "테넌트-x"
        효과 : "NoSchedule"
```

위의 정책은 포드에만 적용됩니다. 이는 정책의 `location` 요소에서 변경된 요소에 대한 경로 때문입니다. 배포 및 작업 리소스와 같이 포드를 생성하는 리소스를 처리하기 위해 추가 정책을 작성할 수 있습니다. 나열된 정책 및 기타 예제는 다음을 위한 동반자 [ GitHub 프로젝트 ]( https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa/gatekeeper/node-selector ) 에서 볼 수 있습니다. 이 가이드.

이 두 변이의 결과는 포드가 원하는 노드에 끌리는 동시에 특정 노드 오염에 의해 반발되지 않는다는 것입니다. 이를 확인하기 위해 `tenant=tenants-x` 로 레이블이 지정된 노드를 가져 오고 `tenants-x` 네임스페이스 에서 포드를 가져 오기 위해 두 개의 `kubectl` 호출에서 출력 스니펫을 볼 수 있습니다.

``` 강타
kubectl 노드 가져오기 -l 테넌트=테넌트-x
이름
IP-10-0-11-255...
IP-10-0-28-81...
IP-10-0-43-107...

kubectl -n tenants-x 팟(Pod) 가져오기 -owide
이름 준비 상태 다시 시작 연령 IP 노드
테넌트-테스트-배포-58b895ff87-2q7xw 1/1 실행 0 13s 10.0.42.143 ip-10-0-43-107...
테넌트-테스트-배포-58b895ff87-9b6hg 1/1 실행 0 13s 10.0.18.145 ip-10-0-28-81...
테넌트-테스트-배포-58b895ff87-nxvw5 1/1 실행 0 13s 10.0.30.117 ip-10-0-28-81...
테넌트-테스트-배포-58b895ff87-vw796 1/1 실행 중 0 13s 10.0.3.113 ip-10-0-11-255...
테넌트 테스트 포드 1/1 실행 0 13s 10.0.35.83 ip-10-0-43-107...
```

위 출력에서 볼 수 있듯이 모든 포드는 `tenant=tenants-x` 레이블이 지정된 노드에서 예약됩니다 . 간단히 말해서 포드는 원하는 노드에서만 실행되고 다른 포드(필수 친화성 및 내약성 없음)는 실행되지 않습니다. 테넌트 워크로드는 효과적으로 격리됩니다.

변형된 포드 사양의 예는 아래에 나와 있습니다.

``` 얌
api버전 : v1
종류 : 포드
메타데이터 :
  이름 : 테넌트 테스트 포드
  네임스페이스 : 테넌트-x
사양 :
  선호도 :
    노드친화도 :
      requiredDuringSchedulingIgnoredDuringExecution :
        nodeSelector조건 :
- matchExpressions :
- 키 : 테넌트
            연산자 : 안으로
            값 :
- 테넌트-x
...
  관용 :
- 효과 : NoSchedule
    키 : 임차인
    연산자 : 같음
    값 : 테넌트-x
...
```

!!! 주목
변경 및 검증 승인 웹후크를 사용하여 Kubernetes API 서버 요청 흐름에 통합된 정책 관리 도구는 지정된 시간 내에 API 서버의 요청에 응답하도록 설계되었습니다. 일반적으로 3초 이하입니다. Webhook 호출이 구성된 시간 내에 응답을 반환하지 못하면 인바운드 API 서버 요청의 변형 및/또는 유효성 검사가 발생할 수도 있고 발생하지 않을 수도 있습니다. 이 동작은 허용 웹후크 구성이 [ Fail Open 또는 Fail Close ]( https://open-policy-agent.github.io/gatekeeper/website/docs/#admission-webhook-fail-open- 기본적으로 ).

위의 예에서는 OPA/Gatekeeper용으로 작성된 정책을 사용했습니다. 그러나 노드 선택 사용 사례도 처리하는 다른 정책 관리 도구가 있습니다. 예를 들어 이 [ Kyverno 정책 ]( https://kyverno.io/policies/other/add_node_affinity/add_node_affinity/ )을 사용하여 노드 선호도 변경을 처리할 수 있습니다.

!!! 팁
올바르게 작동하는 경우 변경 정책은 인바운드 API 서버 요청 페이로드에 원하는 변경 사항을 적용합니다. 그러나 변경 사항이 지속되도록 허용되기 전에 원하는 변경 사항이 발생하는지 확인하기 위한 검증 정책도 포함되어야 합니다. 이는 테넌트-노드 격리를 위해 이러한 정책을 사용할 때 특히 중요합니다. 클러스터에서 원하지 않는 구성이 있는지 정기적으로 확인하기 위해 _Audit_ 정책을 포함하는 것도 좋은 생각 입니다.

### 참조

+ [ k-rail ]( https://github.com/cruise-automation/k-rail ) 특정 정책 시행을 통해 다중 테넌트 환경을 보호할 수 있도록 설계되었습니다.

+ [ Amazon EKS를 사용하는 다중 테넌트 SaaS 애플리케이션에 대한 보안 사례 ]( https://d1.awsstatic.com/whitepapers/security-practices-for-multi-tenant-saas-apps-using-eks.pdf )

## 하드 멀티테넌시
각 테넌트에 대해 별도의 클러스터를 프로비저닝하여 하드 멀티테넌시를 구현할 수 있습니다. 이렇게 하면 테넌트 간에 매우 강력한 격리가 제공되지만 몇 가지 단점이 있습니다.

첫째, 테넌트가 많은 경우 이 접근 방식은 금세 비용이 많이 들 수 있습니다. 각 클러스터에 대한 컨트롤 플레인 비용을 지불해야 할 뿐만 아니라 클러스터 간에 컴퓨팅 리소스를 공유할 수 없습니다. 이로 인해 결국 클러스터의 하위 집합이 충분히 활용되지 않고 나머지는 과도하게 활용되는 조각화가 발생합니다.

둘째, 이러한 모든 클러스터를 관리하려면 특수 도구를 구입하거나 구축해야 할 수 있습니다. 시간이 지나면 수백 또는 수천 개의 클러스터를 관리하는 것이 너무 어려워질 수 있습니다.

마지막으로, 테넌트당 클러스터를 생성하는 것은 네임스페이스 생성에 비해 느립니다. 그럼에도 불구하고 규제가 엄격한 산업이나 강력한 격리가 필요한 SaaS 환경에서는 하드 테넌시 접근 방식이 필요할 수 있습니다.

## 향후 방향

쿠버네티스 커뮤니티는 소프트 멀티테넌시의 현재 단점과 하드 멀티테넌시의 문제점을 인식했습니다. [ Multi-Tenancy SIG(Special Interest Group) ]( https://github.com/kubernetes-sigs/multi-tenancy )는 HNC(Hierarchical Namespace Controller) 및 가상 클러스터를 비롯한 여러 인큐베이션 프로젝트를 통해 이러한 단점을 해결하려고 시도하고 있습니다. .

은 테넌트 관리자가 하위 네임스페이스를 생성할 수 있는 기능과 함께 \[ 정책 \] 개체 상속을 사용하여 네임스페이스 간에 부모-자식 관계를 생성하는 방법을 설명합니다 .

가상 클러스터 제안은 클러스터 내의 각 테넌트에 대해 API 서버, 컨트롤러 관리자 및 스케줄러를 포함하여 컨트롤 플레인 서비스의 별도 인스턴스를 생성하기 위한 메커니즘을 설명합니다("Kubernetes on Kubernetes"라고도 함).

[ Multi-Tenancy Benchmarks ]( https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/README.md ) 제안은 격리 및 세분화를 위한 네임스페이스와 명령을 사용하여 클러스터를 공유하기 위한 지침을 제공합니다. 라인 도구 [ kubectl-mtb ]( https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/kubectl-mtb/README.md )를 사용하여 가이드라인 준수 여부를 확인합니다.

## 다중 클러스터 관리 리소스

+ [ 반자이 클라우드 ]( https://banzaicloud.com/ )
+ [ 코맨더 ]( https://d2iq.com/solutions/ksphere/kommander )
+ [ 렌즈 ]( https://github.com/lensapp/lens )
+ [ 니르마타 ]( https://nirmata.com )
+ [ 라페이 ]( https://rafay.co/ )
+ [ 목장주 ]( https://rancher.com/products/rancher/ )
+ [ 위브 플럭스 ]( https://www.weave.works/oss/flux/ )


