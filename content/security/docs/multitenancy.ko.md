---
search:
  exclude: true
---


# 테넌트 격리
멀티테넌시를 생각할 때 공유 인프라에서 실행되는 다른 사용자나 애플리케이션으로부터 사용자나 애플리케이션을 분리하려는 경우가 많습니다. 

쿠버네티스는 _단일 테넌트 오케스트레이터_ 입니다. 즉, 컨트롤 플레인의 단일 인스턴스가 클러스터 내 모든 테넌트 간에 공유됩니다. 하지만 멀티테넌시와 유사한 형태를 만드는 데 사용할 수 있는 다양한 쿠버네티스 객체가 있습니다. 예를 들어 네임스페이스와 역할 기반 접근 제어(RBAC) 를 구현하여 테넌트를 논리적으로 서로 격리할 수 있습니다. 마찬가지로 할당량 및 제한 범위를 사용하여 각 테넌트가 사용할 수 있는 클러스터 리소스의 양을 제어할 수 있습니다. 하지만 클러스터는 강력한 보안 경계를 제공하는 유일한 구조입니다. 클러스터 내 호스트에 대한 액세스 권한을 획득한 공격자는 해당 호스트에 마운트된 _모든_ 시크릿, 컨피그맵, 볼륨을 가져올 수 있기 때문입니다. 또한 Kubelet을 가장하여 노드의 속성을 조작하거나 클러스터 내에서 옆으로 이동할 수도 있습니다.

다음 섹션에서는 쿠버네티스와 같은 단일 테넌트 오케스트레이터를 사용할 때 발생하는 위험을 줄이면서 테넌트 격리를 구현하는 방법을 설명합니다.

## 소프트 멀티테넌시

소프트 멀티테넌시를 사용하면 네임스페이스, 역할 및 롤바인딩, 네트워크 정책과 같은 네이티브 쿠버네티스 구조를 사용하여 테넌트를 논리적으로 분리할 수 있습니다.예를 들어 RBAC는 테넌트가 서로의 리소스에 액세스하거나 조작하는 것을 방지할 수 있습니다. 쿼터 및 리밋 범위는 각 테넌트가 소비할 수 있는 클러스터 리소스의 양을 제어하는 반면, 네트워크 정책은 서로 다른 네임스페이스에 배포된 애플리케이션이 서로 통신하지 못하도록 하는 데 도움이 될 수 있습니다.

그러나 이런 컨트롤 중 어느 것도 다른 테넌트의 파드가 노드를 공유하는 것을 막지는 못합니다. 더 강력한 격리가 필요한 경우 노드 셀렉터, 안티-어피니티 규칙 및/또는 테인트 및 톨러레이션을 사용하여 서로 다른 테넌트의 파드를 별도의 노드로 강제로 스케줄링할 수 있습니다. 이를 종종 _단독 테넌트 노드_ 라고 합니다. 테넌트가 많은 환경에서는 이 작업이 다소 복잡하고 비용이 많이 들 수 있습니다. 

!!! attention
    네임스페이스는 전역적으로 범위가 지정된 유형이므로 네임스페이스로 구현된 소프트 멀티테넌시는 필터링된 네임스페이스 목록을 테넌트에 제공할 수 없습니다. 테넌트가 특정 네임스페이스를 볼 수 있는 경우 클러스터 내의 모든 네임스페이스를 볼 수 있습니다. 

!!! warning
    소프트 멀티테넌시를 사용하면 테넌트는 기본적으로 클러스터 내에서 실행되는 모든 서비스에 대해 CoreDNS를 쿼리할 수 있습니다.공격자는 클러스터의 모든 파드에서 `dig SRV *.*.svc.cluster.local`을 실행하여 이를 악용할 수 있습니다.클러스터 내에서 실행되는 서비스의 DNS 레코드에 대한 액세스를 제한해야 하는 경우 CoreDNS용 방화벽 또는 정책 플러그인을 사용하는 것이 좋습니다. 자세한 내용은 [https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy](https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy)을 참조하십시오.

[Kiosk](https://github.com/kiosk-sh/kiosk)는 소프트 멀티 테넌시의 구현을 지원하는 오픈 소스 프로젝트입니다. 다음 기능을 제공하는 일련의 CRD 및 컨트롤러로 구현됩니다.

  + 공유 쿠버네티스 클러스터에서 테넌트를 분리하기 위한 **계정 및 계정 사용자**
  + 계정 사용자를 위한 **셀프 서비스 네임스페이스 프로비저닝**
  + 클러스터 공유 시 서비스 품질 및 공정성을 보장하기 위한 **계정 제한**
  + 안전한 테넌트 격리 및 셀프 서비스 네임스페이스 초기화를 위한 **네임스페이스 템플릿**
  
[Loft](https://loft.sh)는 다음 기능을 추가하는 Kiosk 및 [DevSpace](https://github.com/devspace-cloud/devspace)의 관리자가 제공하는 상용 제품입니다.

  + 다른 클러스터의 공간에 대한 액세스 권한을 부여하기 위한 **멀티 클러스터 액세스**
  + **절전 모드** 는 비활성 기간 동안 공간에서 배포를 축소합니다.
  + ** GitHub와 같은 OIDC 인증 공급자를 사용한 싱글 사인온**

소프트 멀티 테넌시로 해결할 수 있는 세 가지 주요 사용 사례가 있습니다.

### 엔터프라이즈 설정

첫 번째는 "테넌트"가 직원, 계약자 또는 조직의 승인을 받았다는 점에서 어느정도 신뢰을 받는 기업 환경입니다. 각 테넌트는 일반적으로 부서 또는 팀과 같은 행정 부서에 소속됩니다. 

이런 유형의 설정에서는 일반적으로 클러스터 관리자가 네임스페이스 생성 및 정책 관리를 담당합니다. 또한 특정 개인에게 네임스페이스를 감독하는 위임 관리 모델을 구현하여 배포, 서비스, 파드, 작업 등과 같이 정책과 관련이 없는 개체에 대해 CRUD 작업을 수행할 수 있도록 할 수도 있습니다.

컨테이너 런타임에서 제공하는 격리는 이 설정 내에서 허용될 수도 있고 파드 보안을 위한 추가 제어 기능으로 보강해야 할 수도 있습니다.더 엄격한 격리가 필요한 경우 서로 다른 네임스페이스에 있는 서비스 간의 통신을 제한해야 할 수도 있습니다.

### 서비스로서 쿠버네티스

대조적으로 소프트 멀티테넌시는 Kuberenetes as a Service(KaaS) 상황에서 사용할 수 있는 설정입니다. KaaS를 사용하면 애플리케이션이 일련의 PaaS 서비스를 제공하는 컨트롤러 및 CRD 컬렉션과 함께 공유 클러스터에서 호스팅됩니다. 테넌트는 쿠버네티스 API 서버와 직접 상호 작용하며 비정책 객체에 대해 CRUD 작업을 수행할 수 있습니다. 테넌트가 자체 네임스페이스를 생성하고 관리할 수 있다는 점에서 셀프 서비스의 요소도 있습니다. 이런 유형의 환경에서는 테넌트는 신뢰할 수 없는 코드도 실행할 수 있는 것으로 간주됩니다.

이런 유형의 환경에서 테넌트를 격리하려면 엄격한 네트워크 정책과 _파드 샌드박싱_ 을 구현해야 할 수 있습니다. 샌드박싱은 Firecracker와 같은 마이크로 VM 내에서 또는 사용자 공간 커널에서 파드 컨테이너를 실행하는 것입니다. 이제 EKS Fargate를 사용하여 샌드박스가 적용된 파드를 만들 수 있습니다.

### 서비스형 소프트웨어(SaaS)

소프트 멀티테넌시의 최종 사용 사례는 서비스형 소프트웨어 (SaaS) 설정입니다.이 환경에서 각 테넌트는 클러스터 내에서 실행되는 애플리케이션의 특정 _인스턴스_ 와 연결됩니다.각 인스턴스는 종종 자체 데이터를 갖고 있으며 일반적으로 쿠버네티스 RBAC와 독립적인 별도의 액세스 제어를 사용합니다.

다른 사용 사례와 달리 SaaS 설정의 테넌트는 쿠버네티스 API와 직접 인터페이스하지 않습니다. 대신 SaaS 애플리케이션은 쿠버네티스 API와 인터페이스하여 각 테넌트를 지원하는 데 필요한 객체를 생성합니다.

## 쿠버네티스 구성

각 인스턴스에서 다음 구조를 사용하여 테넌트를 서로 격리합니다:

### 네임스페이스

네임스페이스는 소프트 멀티테넌시를 구현하는 데 필수적입니다.클러스터를 논리적 파티션으로 나눌 수 있습니다.멀티테넌시를 구현하는 데 필요한 할당량, 네트워크 정책, 서비스 어카운트 및 기타 개체의 범위는 네임스페이스로 지정됩니다.

### 네트워크 정책

기본적으로 쿠버네티스 클러스터의 모든 파드는 서로 통신할 수 있습니다. 이 동작은 네트워크 정책을 사용하여 변경할 수 있습니다.

네트워크 정책은 레이블 또는 IP 주소 범위를 사용하여 파드 간 통신을 제한합니다. 테넌트 간 엄격한 네트워크 격리가 필요한 멀티 테넌트 환경에서는 파드 간 통신을 거부하는 기본 규칙과 모든 파드가 DNS 서버에 이름 확인을 쿼리할 수 있도록 허용하는 다른 규칙으로 시작하는 것이 좋습니다. 이를 통해 네임스페이스 내에서 통신을 허용하는 더 많은 허용 규칙을 추가할 수 있습니다. 필요에 따라 이를 더 세분화할 수 있습니다. 

!!! attention
    네트워크 정책은 필요하지만 충분하지는 않습니다. 네트워크 정책을 적용하려면 Calico 또는 Cilium과 같은 정책 엔진이 필요합니다.

### 역할 기반 접근 제어(RBAC)

역할 및 롤바인딩은 쿠버네티스에서 역할 기반 접근 제어 (RBAC) 를 적용하는 데 사용되는 쿠버네티스 오브젝트입니다. **역할**에는 클러스터의 오브젝트에 대해 수행할 수 있는 작업 목록이 포함되어 있습니다. **롤바인딩**은 역할이 적용되는 개인 또는 그룹을 지정합니다. 엔터프라이즈 및 KaaS 설정에서 RBAC를 사용하여 선택한 그룹 또는 개인이 개체를 관리할 수 있도록 허용할 수 있습니다.

### 쿼터

쿼터은 클러스터에서 호스팅되는 워크로드에 대한 제한을 정의하는 데 사용됩니다. 쿼터을 사용하면 파드가 소비할 수 있는 최대 CPU 및 메모리 양을 지정하거나 클러스터 또는 네임스페이스에 할당할 수 있는 리소스 수를 제한할 수 있습니다. **Limit Range**를 사용하면 각 제한의 최소값, 최대값 및 기본값을 선언할 수 있습니다.

공유 클러스터에서 리소스를 오버커밋하면 리소스를 최대화할 수 있으므로 종종 유용합니다. 그러나 클러스터에 대한 무제한 액세스는 리소스 부족을 초래하여 성능 저하 및 애플리케이션 가용성 손실로 이어질 수 있습니다. 파드의 요청이 너무 낮게 설정되고 실제 리소스 사용량이 노드의 용량을 초과하면 노드에 CPU 또는 메모리 압력이 발생하기 시작합니다. 이 경우 파드가 재시작되거나 노드에서 제거될 수 있습니다.

이를 방지하려면 멀티 테넌트 환경에서 네임스페이스에 할당량을 부과하여 테넌트가 클러스터에서 파드를 예약할 때 요청 및 제한을 지정하도록 계획해야 합니다. 또한 파드가 소비할 수 있는 리소스의 양을 제한하여 잠재적인 서비스 거부를 완화할 수 있습니다.

또는 쿼터를 사용하여 테넌트의 지출에 맞게 클러스터의 리소스를 할당할 수 있습니다.이는 KaaS 시나리오에서 특히 유용합니다.

### 파드 우선순위 및 선점

파드 우선순위 및 선점은 다른 파드에 비해 파드에 더 많은 중요성을 부여하고자 할 때 유용할 수 있다.예를 들어 파드 우선 순위를 사용하면 고객 A의 파드가 고객 B보다 높은 우선 순위로 실행되도록 구성할 수 있습니다. 사용 가능한 용량이 충분하지 않은 경우 스케줄러는 고객 B의 우선 순위가 낮은 파드를 제외하고 고객 A의 우선 순위가 높은 파드를 수용합니다. 이는 프리미엄을 지불하려는 고객이 더 높은 우선 순위를 받는 SaaS 환경에서 특히 유용할 수 있습니다.

!!! attention 
    파드의 우선순위는 우선순위가 낮은 다른 파드에 원치 않는 영향을 미칠 수 있다. 예를 들어, 대상 파드는 정상적으로 종료되지만 PodDisruptionBudget은 보장되지 않아 파드 쿼럼에 의존하는 우선순위가 낮은 애플리케이션이 중단될 수 있습니다. [선점 제한](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/#limitations-of-preemption)을 참조하십시오.

## 완화 제어

멀티 테넌트 환경 관리자의 주된 관심사는 공격자가 기본 호스트에 대한 접근 권한을 얻지 못하도록 하는 것입니다. 이런 위험을 완화하려면 다음 제어 방법을 고려해야 합니다. 

### 컨테이너를 위한 샌드박스 실행 환경

샌드박싱은 각 컨테이너를 격리된 자체 가상 시스템에서 실행하는 기술입니다. 파드 샌드박싱을 수행하는 기술로는 [Firecracker](https://firecracker-microvm.github.io/), Weave의 [Firekube](https://www.weave.works/blog/firekube-fast-and-secure-kubernetes-clusters-using-weave-ignite)등이 있습니다.

Firecracker를 EKS 지원 런타임으로 만들기 위한 노력에 대한 추가 정보는 [이 글](https://threadreaderapp.com/thread/1238496944684597248.html)을 참조하십시오. 


### 개방형 정책 에이전트(OPA) 및 게이트키퍼

[Gatekeeper](https://github.com/open-policy-agent/gatekeeper)는 [OPA](https://www.openpolicyagent.org/)로 생성된 정책을 시행하는 Kubernetes 어드미션 컨트롤러입니다. OPA를 사용하면 별도의 인스턴스 또는 다른 테넌트보다 더 높은 우선순위에서 테넌트의 파드를 실행하는 정책을 생성할 수 있습니다. 이 프로젝트에 대한 일반적인 OPA 정책 모음은 GitHub [리포지토리](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa)에서 찾을 수 있습니다.

OPA를 사용하여 CoreDNS에서 반환되는 레코드를 필터링/제어할 수 있는 실험적인 [CoreDNS를 위한 OPA 플러그인](https://github.com/coredns/coredns-opa)도 있습니다. 

### Kyverno

[Kyverno](https://kyverno.io)는 정책을 쿠버네티스 리소스로 사용하여 구성을 검증, 변경 및 생성할 수 있는 쿠버네티스 기본 정책 엔진입니다. Kyverno는 유효성 검사를 위해 Kustomize 스타일 오버레이를 사용하고 변형을 위한 JSON 패치 및 전략적 병합 패치를 지원하며 유연한 트리거를 기반으로 네임스페이스 간에 리소스를 복제할 수 있습니다.

Kyverno를 사용하여 네임스페이스를 격리하고, 파드 보안 및 기타 모범 사례를 적용하고, 네트워크 정책과 같은 기본 구성을 생성할 수 있습니다. 이 프로젝트의 GitHub [리포지토리](https://github.com/aws/aws-eks-best-practices/tree/master/policies/kyverno)에 몇 가지 예제가 포함되어 있습니다. 다른 많은 것들이 Kyverno 웹사이트 내 [정책 라이브러리](https://kyverno.io/policies/)에 포함되어 있습니다.

### 테넌트 워크로드를 특정 노드로 격리

테넌트 워크로드가 특정 노드에서 실행되도록 제한하면 소프트 멀티 테넌시 모델의 격리를 높이는 데 사용할 수 있습니다. 이 접근 방식을 사용하면 테넌트별 워크로드가 각 테넌트용으로 프로비저닝된 노드에서만 실행됩니다. 이런 격리를 달성하기 위해 네이티브 쿠버네티스 속성(노드 어피니티, 테인트 및 톨러레이션)을 사용하여 특정 노드를 파드 스케줄링 대상으로 지정하고 다른 테넌트의 파드가 테넌트별 노드에 스케줄링되지 않도록 합니다.

#### 파트 1 - 노드 어피니티

쿠버네티스 [노드 어피니티](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)는 노드 [레이블](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)을 기반으로 노드를 스케줄링할 대상으로 지정하는 데 사용됩니다. 노드 어피니티 규칙을 사용하면 셀렉터 용어와 일치하는 특정 노드에 파드가 몰리도록 구성할 수 있습니다. 아래 파드 사양에서는 `requiredDuringSchedulingIgnoredDuringExecution` 노드 어피니티가 각 파드에 적용된다. 결과적으로 파드는 `node-restriction.kubernetes.io/tenant: tenants-x`와 같은 키/값으로 레이블이 지정된 노드에 배포됩니다. 

``` yaml
...
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node-restriction.kubernetes.io/tenant
            operator: In
            values:
            - tenants-x
...
```

이 노드 어피니티를 사용하면 스케줄링 중에 레이블이 필요하지만 실행 중에는 필요하지 않습니다. 기본 노드의 레이블이 변경되더라도 해당 레이블 변경으로 인해 파드가 제거되지는 않습니다. 하지만 향후 스케줄링이 영향을 받을 수 있습니다.

!!! warning
    `node-restriction.kubernetes.io/` 레이블 접두사는 쿠버네티스에서 특별한 의미를 가집니다. EKS 클러스터에 사용할 수 있는 [NodeRestriction](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#noderestriction)은 'kubelet'이 이 접두사를 가진 레이블을 추가/제거/업데이트하는 것을 방지합니다. 공격자는 `kubelet`의 레이블을 수정할 수 없으므로, `kubelet`의 자격 증명을 사용하여 노드 개체를 업데이트하거나 이런 레이블을 `kubelet`으로 전달하도록 시스템 설정을 수정할 수 없습니다. 이 접두사를 모든 파드의 노드 스케줄링에 사용하면 공격자가 노드 레이블을 수정하여 다른 워크로드 세트를 노드로 끌어들이려는 시나리오를 방지할 수 있습니다.

!!! info
    노드 어피니티 대신 [노드 셀렉터](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector)를 사용할 수도 있습니다. 하지만 노드 어피니티는 표현방식이 더 다양하고 파드 스케줄링 중에 더 복잡한 조건을 정의할 수 있습니다. 차이점과 고급 스케줄링 선택에 대한 추가 정보는 CNCF 블로그 게시물인 [고급 쿠버네티스 파드의 노드 스케줄링](https://www.cncf.io/blog/2021/07/27/advanced-kubernetes-pod-to-node-scheduling/)을 참조하십시오.

#### 파트 2 - 테인트(Taint) 및 톨러레이션(Toleration)

파드를 노드로 끌어들이는 것은 이 세 부분으로 구성된 접근 방식의 첫 번째 부분에 불과합니다. 이 접근 방식이 제대로 작동하려면 권한이 부여되지 않은 노드에 파드를 스케줄링하지 않도록 해야 합니다. 쿠버네티스는 원치 않거나 승인되지 않은 파드를 차단하기 위해 노트 [테인트](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)를 사용합니다. 테인트는 파드가 스케줄링되지 않도록 노드에 조건을 설정하는 데 사용됩니다. 아래 테인트는 `tenant: tenants-x`의 키-값 쌍을 사용합니다.

``` yaml
...
    taints:
      - key: tenant
        value: tenants-x
        effect: NoSchedule
...
```

위와 같이 노드 `테인트`가 주어지면, 테인트를 _허용하는_ 파드만 노드에 스케줄링할 수 있다. 승인된 파드를 노드에 스케줄링할 수 있으려면 아래와 같이 각 파드 사양에 테인트에 대한 `톨러레이션`이 포함되어야 합니다.

``` yaml
...
  tolerations:
  - effect: NoSchedule
    key: tenant
    operator: Equal
    value: tenants-x
...
```

위의 `톨러레이션`을 가진 파드는 적어도 그 특정 테인트로 인하여 해당 노드로 스케줄링이 중단되지는 않을 것이다. 쿠버네티스는 노드 리소스 압박과 같은 특정 상황에서 파드 스케줄링을 일시적으로 중단하기 위해 테인트를 사용하기도 합니다. 노드 어피니티, 테인트 및 톨러레이션을 사용하면 원하는 파드를 특정 노드로 효과적으로 배포하고 원치 않는 파드를 제거할 수 있습니다.

!!! attention
특정 쿠버네티스 파드는 모든 노드에서 실행되어야 합니다. 이런 파드는 예로 [컨테이너 네트워크 인터페이스 (CNI)](https://github.com/containernetworking/cni) 및 [kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) [데몬셋](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)등이 있습니다. 이를 위해 이런 파드의 사양에는 다양한 테인트을 견딜 수 있는 매우 관대한 톨러레이션이 포함되어야 합니다. 이런 톨러레이션을 변경하지 않도록 주의해야 합니다. 이런 허용치를 변경하면 클러스터 작동이 잘못될 수 있습니다. 또한 [OPA/Gatekeeper](https://github.com/open-policy-agent/gatekeeper) 및 [Kyverno](https://kyverno.io/)와 같은 정책 관리 도구를 사용하여 승인되지 않은 파드가 이런 관대한 톨러레이션을 사용하지 못하도록 하는 검증 정책도 작성할 수 있습니다.

#### 파트 3 - 노드 선택을 위한 정책 기반 관리

CICD 파이프라인의 규칙 적용을 포함하여 파드 사양의 노드 어피니티 및 톨러레이션을  관리하는 데 사용할 수 있는 여러 도구가 있습니다. 하지만 쿠버네티스 클러스터 수준에서도 격리를 적용해야 합니다. 이를 위해 정책 관리 도구를 사용하여 요청 페이로드를 기반으로 인바운드 쿠버네티스 API 서버 요청을 _변경_ 하여 위에서 언급한 각 노드 어피니티 규칙 및 톨러레이션을 적용할 수 있습니다.

예를 들어, _tenants-x_ 네임스페이스로 향하는 파드에 올바른 노드 어피니티 및 톨러레이션을 _스탬핑_하여 _tenants-x_ 노드에 대한 스케줄링을 허용할 수 있다. 쿠버네티스 [뮤테이팅(Mutating) 어드미션 웹훅](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#mutatingadmissionwebhook)을 사용하여 구성된 정책 관리 도구를 활용하면 정책을 사용하여 인바운드 파드 사양을 변경할 수 있습니다. 뮤테이션은 원하는 스케줄링이 가능하도록 필요한 요소를 추가합니다. 노드 어피니티를 추가하는 OPA/게이트키퍼 정책의 예는 다음과 같습니다.

``` yaml
apiVersion: mutations.gatekeeper.sh/v1alpha1
kind: Assign
metadata:
  name: mutator-add-nodeaffinity-pod
  annotations:
    aws-eks-best-practices/description: >-
      Adds Node affinity - https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#node-affinity
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    namespaces: ["tenants-x"]
  location: "spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms"
  parameters:
    assign:
      value: 
        - matchExpressions:
          - key: "tenant"
            operator: In
            values:
            - "tenants-x"
```

위의 정책은 _tenants-x_ 네임스페이스에 파드를 적용하기 위한 쿠버네티스 API 서버 요청에 적용됩니다. 이 정책은 `requiredDuringSchedulingIgnoredDuringExecution` 노드 어피니티 규칙을 추가하여, 파드가 `tenant: tenants-x` 레이블이 붙은 노드에 집중되도록 합니다.

아래에 나와 있는 두 번째 정책은 대상 네임스페이스와 그룹, 종류, 버전의 동일한 일치 기준을 사용하여 동일한 파드 사양에 톨러레이션을 추가합니다.

``` yaml
apiVersion: mutations.gatekeeper.sh/v1alpha1
kind: Assign
metadata:
  name: mutator-add-toleration-pod
  annotations:
    aws-eks-best-practices/description: >-
      Adds toleration - https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    namespaces: ["tenants-x"]
  location: "spec.tolerations"
  parameters:
    assign:
      value: 
      - key: "tenant"
        operator: "Equal"
        value: "tenants-x"
        effect: "NoSchedule"
```

위의 정책은 파드에만 해당된다. 이는 정책의 `location` 요소에 있는 변경되는 요소에 대한 경로 때문입니다. 디플로이먼트 및 잡 리소스와 같이 파드를 생성하는 리소스를 처리하기 위한 추가 정책을 작성할 수 있다. 나열된 정책 및 기타 예는 이 가이드의 동반 [GitHub 프로젝트](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa/gatekeeper/node-selector)에서 확인할 수 있습니다.

이 두 뮤테이션의 결과는 파드가 원하는 노드에 끌리는 동시에 특정 노드 테인트에 의해 반발되지 않는다는 것입니다. 이를 확인하기 위해 `tenant=tenants-x` 로 레이블이 지정된 노드를 가져 오고 `tenants-x` 네임스페이스 에서 파드를 가져 오기 위해 두 개의 `kubectl` 호출에서 출력 스니펫을 볼 수 있습니다.

``` bash
kubectl get nodes -l tenant=tenants-x
NAME                                        
ip-10-0-11-255...
ip-10-0-28-81...
ip-10-0-43-107...

kubectl -n tenants-x get pods -owide
NAME                                  READY   STATUS    RESTARTS   AGE   IP            NODE
tenant-test-deploy-58b895ff87-2q7xw   1/1     Running   0          13s   10.0.42.143   ip-10-0-43-107...
tenant-test-deploy-58b895ff87-9b6hg   1/1     Running   0          13s   10.0.18.145   ip-10-0-28-81...
tenant-test-deploy-58b895ff87-nxvw5   1/1     Running   0          13s   10.0.30.117   ip-10-0-28-81...
tenant-test-deploy-58b895ff87-vw796   1/1     Running   0          13s   10.0.3.113    ip-10-0-11-255...
tenant-test-pod                       1/1     Running   0          13s   10.0.35.83    ip-10-0-43-107...
```

위의 출력에서 볼 수 있듯이 모든 파드는 `tenant=tenants-x`로 표시된 노드에 스케줄링됩니다. 간단히 말해, 파드는 원하는 노드에서만 실행되고 다른 파드(필수 어피니티 및 톨러레이션 제외)는 실행되지 않습니다. 테넌트 워크로드는 효과적으로 격리됩니다.

뮤테이션된 파드 스펙의 예는 아래에 나와 있습니다.

``` yaml
apiVersion: v1
kind: Pod
metadata:
  name: tenant-test-pod
  namespace: tenants-x
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: tenant
            operator: In
            values:
            - tenants-x
...
  tolerations:
  - effect: NoSchedule
    key: tenant
    operator: Equal
    value: tenants-x
...
```

!!! attention
    뮤테이팅(mutating) 및 검증(validating) 어드미션 웹훅을 사용하여 쿠버네티스 API 서버 요청 흐름에 통합된 정책 관리 도구는 지정된 기간 내에 API 서버의 요청에 응답하도록 설계되었습니다. 이 시간은 보통 3초 이내입니다. 웹훅 호출이 구성된 시간 내에 응답을 반환하지 못하면 인바운드 API 서버 요청의 변경 및/또는 검증이 발생할 수도 있고 그렇지 않을 수도 있습니다. 이 동작은 승인 웹훅 구성이 [Fail-Open 또는 Fail-Closed](https://open-policy-agent.github.io/gatekeeper/website/docs/#admission-webhook-fail-open-by-default)로 설정되어 있는지 여부에 따라 달라집니다.

위 예시에서는 OPA/게이트키퍼용으로 작성된 정책을 사용했습니다. 하지만 노드 선택 사용 사례를 처리하는 다른 정책 관리 도구도 있습니다. 예를 들어, 이 [Kyverno 정책](https://kyverno.io/policies/other/add_node_affinity/add_node_affinity/)을 사용하여 노드 어피니티 뮤테이션을 처리할 수 있습니다.

!!! tip
    제대로 작동하는 경우 정책을 변경하면 인바운드 API 서버 요청 페이로드에 대한 원하는 변경 사항이 적용됩니다. 하지만 변경 사항이 계속 적용되기 전에 원하는 변경 사항이 적용되는지 확인하는 검증 정책도 포함해야 합니다. 이는 테넌트-노드 격리에 이런 정책을 사용할 때 특히 중요합니다. 또한 클러스터에 원치 않는 구성이 있는지 정기적으로 점검할 수 있도록 _감사_ 정책을 포함하는 것도 좋습니다.

### 참조

+ [k-rail](https://github.com/cruise-automation/k-rail)는 특정 정책의 적용을 통해 멀티테넌트 환경을 보호할 수 있도록 설계되었습니다. 

+ [Amazon EKS를 사용하는 멀티 테넌트 SaaS 애플리케이션에 대한 보안 사례](https://d1.awsstatic.com/whitepapers/security-practices-for-multi-tenant-saas-apps-using-eks.pdf)

## 하드 멀티테넌시
각 테넌트에 대해 별도의 클러스터를 프로비저닝하여 하드 멀티테넌시를 구현할 수 있습니다. 이렇게 하면 테넌트 간에 매우 강력한 격리가 가능하지만 몇 가지 단점이 있습니다.

첫째, 테넌트가 많은 경우 이 접근 방식은 비용이 많이 들 수 있습니다. 각 클러스터의 컨트롤 플레인 비용을 지불해야 할 뿐만 아니라 클러스터 간에 컴퓨팅 리소스를 공유할 수 없게 됩니다. 이로 인해 결국 클러스터의 일부는 활용도가 낮고 다른 클러스터는 과도하게 사용되는 단편화가 발생합니다.

둘째, 이런 클러스터를 모두 관리하려면 특수 도구를 구입하거나 구축해야 할 수 있습니다.시간이 지나면 수백 또는 수천 개의 클러스터를 관리하는 것이 너무 복잡해질 수 있습니다.

마지막으로 테넌트별로 클러스터를 생성하는 것은 네임스페이스를 생성하는 것보다 느립니다. 하지만 규제가 엄격한 산업이나 강력한 격리가 필요한 SaaS 환경에서는 하드 테넌시 접근 방식이 필요할 수 있습니다.

## 향후 방향

Kubernetes 커뮤니티는 소프트 멀티테넌시의 현재 단점과 하드 멀티테넌시의 문제점을 인식하고 있습니다.[멀티테넌시 SIG 그룹](https://github.com/kubernetes-sigs/multi-tenancy)은 계층적 네임스페이스 컨트롤러(HNC) 및 가상 클러스터를 비롯한 여러 인큐베이션 프로젝트를 통해 이런 단점을 해결하려고 노력하고 있습니다.

HNC 제안(KEP)은 테넌트 관리자가 하위 네임스페이스를 생성할 수 있는 기능과 함께 \[policy\] 개체 상속을 통해 네임스페이스 간의 상위-하위 관계를 생성하는 방법을 설명합니다.

가상 클러스터 제안서는 클러스터 내의 각 테넌트("Kubernetes on Kubernetes"라고도 표현)에 대해 API 서버, 컨트롤러 관리자 및 스케줄러를 포함한 컨트롤 플레인 서비스의 개별 인스턴스를 생성하는 메커니즘을 설명합니다.

[멀티테넌시 벤치마크](https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/README.md) 제안서는 격리 및 분할을 위한 네임스페이스를 사용하여 클러스터를 공유하는 지침과 지침 준수 여부를 검증하기 위한 명령줄 도구 [kubectl-mtb](https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/kubectl-mtb/README.md)를 제공합니다.

## 멀티 클러스터 관리 리소스

+ [Banzai Cloud](https://banzaicloud.com/)
+ [Kommander](https://d2iq.com/solutions/ksphere/kommander)
+ [Lens](https://github.com/lensapp/lens)
+ [Nirmata](https://nirmata.com)
+ [Rafay](https://rafay.co/)
+ [Rancher](https://rancher.com/products/rancher/)
+ [Weave Flux](https://www.weave.works/oss/flux/)
