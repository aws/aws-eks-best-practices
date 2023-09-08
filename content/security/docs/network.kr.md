# 네트워크 보안
네트워크 보안에는 여러 측면이 있습니다. 첫 번째는 서비스 간의 네트워크 트래픽 흐름을 제한하는 규칙 적용과 관련됩니다. 두 번째는 전송 중인 트래픽의 암호화와 관련이 있습니다. EKS에서 이러한 보안 조치를 구현하는 메커니즘은 다양하지만 종종 다음 항목을 포함합니다.

#### 교통 통제
+ 네트워크 정책
+ 보안 그룹
#### 전송 중 암호화
+ 서비스 메시
+ 컨테이너 네트워크 인터페이스(CNI)
+ 니트로 인스턴스
+ cert-manager가 있는 ACM 사설 CA

## 네트워크 정책
Kubernetes 클러스터 내에서 모든 포드 간 통신은 기본적으로 허용됩니다. 이러한 유연성은 실험을 촉진하는 데 도움이 될 수 있지만 안전한 것으로 간주되지는 않습니다. Kubernetes 네트워크 정책은 Pod 간(종종 East/West 트래픽이라고 함) 및 Pod와 외부 서비스 간의 네트워크 트래픽을 제한하는 메커니즘을 제공합니다. Kubernetes 네트워크 정책은 OSI 모델의 계층 3과 4에서 작동합니다. 네트워크 정책은 팟 선택기 및 레이블을 사용하여 소스 및 대상 팟을 식별하지만 IP 주소, 포트 번호, 프로토콜 번호 또는 이들의 조합을 포함할 수도 있습니다. [ Calico ]( https://docs.projectcalico.org/introduction/ ) 는 EKS와 잘 작동하는 [ Tigera ]( https://tigera.io ) 의 오픈 소스 정책 엔진입니다 . 전체 Kubernetes 네트워크 정책 기능 세트를 구현하는 것 외에도 Calico는 Istio와 통합될 때 HTTP와 같은 계층 7 규칙 지원을 포함하여 더 풍부한 기능 세트로 확장된 네트워크 정책을 지원합니다. Isovalent, [ Cilium ]( https://cilium.readthedocs.io/en/stable/intro/ )의 관리자는 HTTP와 같은 계층 7 규칙에 대한 부분 지원을 포함하도록 네트워크 정책을 확장했습니다. Cilium은 또한 Kubernetes Services/Pod와 VPC 내부 또는 외부에서 실행되는 리소스 간의 트래픽을 제한하는 데 유용할 수 있는 DNS 호스트 이름을 지원합니다. 반대로 Calico Enterprise에는 Kubernetes 네트워크 정책을 AWS 보안 그룹과 DNS 호스트 이름에 매핑할 수 있는 기능이 포함되어 있습니다.

!!! 주목
EKS 클러스터를 처음 프로비저닝할 때 Calico 정책 엔진은 기본적으로 설치되지 않습니다. Calico 설치를 위한 매니페스트는 VPC CNI 리포지토리([ https://github.com/aws/amazon-vpc-cni-k8s/tree/master/config ]( https://github.com/aws/ )에서 찾을 수 있습니다. amazon-vpc-cni-k8s/tree/master/config ).

Calico 정책은 네임스페이스, 포드, 서비스 계정 또는 전역으로 범위가 지정될 수 있습니다. 정책 범위가 서비스 계정으로 지정되면 수신/발신 규칙 집합을 해당 서비스 계정과 연결합니다. 적절한 RBAC 규칙을 사용하면 팀이 이러한 규칙을 재정의하지 못하도록 방지하여 IT 보안 전문가가 네임스페이스 관리를 안전하게 위임할 수 있습니다.

일반적인 Kubernetes 네트워크 정책 목록은 [ https://github.com/ahmetb/kubernetes-network-policy-recipes ]( https://github.com/ahmetb/kubernetes-network-policy-recipes )에서 찾을 수 있습니다. Calico에 대한 유사한 규칙 세트는 [ https://docs.projectcalico.org/security/calico-network-policy ]( https://docs.projectcalico.org/security/calico-network-policy )에서 사용할 수 있습니다.

## 추천

### 기본 거부 정책 만들기
RBAC 정책과 마찬가지로 네트워크 정책은 최소 권한 액세스 정책을 준수해야 합니다. 네임스페이스로부터의 모든 인바운드 및 아웃바운드 트래픽을 제한하는 모두 거부 정책을 생성하여 시작하거나 Calico를 사용하여 글로벌 정책을 생성하십시오.

_쿠버네티스 네트워크 정책_
```yaml
apiVersion : networking.k8s.io/v1
종류 : NetworkPolicy
메타데이터 :
  이름 : 기본 거부
  네임스페이스 : 기본값
사양 :
  포드 선택기 : {}
  정책 유형 :
- 인 그레스
- 이그레스
```

![]( ./images/default-deny.jpg )

!!! 팁
위 이미지는 [ Tufin ]( https://orca.tufin.io/netpol/ )의 네트워크 정책 뷰어로 생성되었습니다.

_Calico 글로벌 네트워크 정책_
```yaml
apiVersion : crd.projectcalico.org/v1
종류 : GlobalNetworkPolicy
메타데이터 :
  이름 : 기본 거부
사양 :
  선택자 : 모두()
  유형 :
- 인 그레스
- 이그레스
```

### DNS 쿼리를 허용하는 규칙 만들기
기본 거부 모든 규칙을 적용한 후에는 포드가 이름 확인을 위해 CoreDNS를 쿼리하도록 허용하는 전역 규칙과 같은 추가 규칙에 계층화를 시작할 수 있습니다. 네임스페이스에 레이블을 지정하여 시작합니다.

```
kubectl 레이블 네임스페이스 kube-system 이름=kube-system
```

그런 다음 네트워크 정책을 추가합니다.

```yaml
apiVersion : networking.k8s.io/v1
종류 : NetworkPolicy
메타데이터 :
  이름 : 허용-dns-액세스
  네임스페이스 : 기본값
사양 :
  포드 선택기 :
    일치 라벨 : {}
  정책 유형 :
- 이그레스
  출구 :
- 에 :
- 네임스페이스 선택기 :
        일치 라벨 :
          이름 : kube-system
    포트 :
- 프로토콜 : UDP
      포트 : 53
```

![]( ./images/allow-dns-access.jpg )

_Calico 글로벌 정책 등가물_

```yaml
apiVersion : crd.projectcalico.org/v1
종류 : GlobalNetworkPolicy
메타데이터 :
  이름 : allow-dns-egress
사양 :
  선택자 : 모두()
  유형 :
- 이그레스
  출구 :
- 조치 : 허용
    프로토콜 : UDP  
    목적지 :
      namespaceSelector : 이름 == "kube-시스템"
      포트 :
- 53
```

다음은 readonly-sa-group과 연결된 사용자가 기본 네임스페이스에서 my-sa 서비스 계정을 편집하지 못하도록 하면서 네트워크 정책을 서비스 계정과 연결하는 방법의 예입니다.

```yaml
api버전 : v1
종류 : ServiceAccount
메타데이터 :
  이름 : 마이사
  네임스페이스 : 기본값
  라벨 :
    이름 : 마이사
---
apiVersion : rbac.authorization.k8s.io/v1
종류 : 역할
메타데이터 :
  네임스페이스 : 기본값
  이름 : readonly-sa-role
규칙 :
# 주체가 my-sa라는 서비스 계정을 읽을 수 있도록 허용합니다.
- api그룹 : [ "" ]
  리소스 : [ "서비스 계정" ]
  리소스 이름 : [ "my-sa" ]
  동사 : [ "get" , "watch" , "list" ]
---
apiVersion : rbac.authorization.k8s.io/v1
종류 : 롤바인딩
메타데이터 :
  네임스페이스 : 기본값
  이름 : readonly-sa-rolebinding
# readonly-sa-role을 readonly-sa-group이라는 RBAC 그룹에 바인드합니다.
과목 :
- 종류 : 그룹
  이름 : 읽기 전용-sa-그룹
  api 그룹 : rbac.authorization.k8s.io
역할 참조 :
  종류 : 역할
  이름 : readonly-sa-role
  api 그룹 : rbac.authorization.k8s.io
---
apiVersion : crd.projectcalico.org/v1
종류 : NetworkPolicy
메타데이터 :
  이름 : netpol-sa-demo
  네임스페이스 : 기본값
# 참조하는 기본 네임스페이스의 서비스에 대한 모든 인그레스 트래픽을 허용합니다.
# my-sa라는 서비스 계정
사양 :
  진입 :
- 조치 : 허용
      출처 :
        서비스 계정 :
          선택기 : '이름 == "my-sa"'
  선택자 : 모두()
```

### 네임스페이스/팟 간의 트래픽 흐름을 선택적으로 허용하는 규칙을 점진적으로 추가
네임스페이스 내의 포드가 서로 통신하도록 허용하는 것으로 시작한 다음 해당 네임스페이스 내의 포드 간 통신을 추가로 제한하는 사용자 지정 규칙을 추가합니다.

### 네트워크 트래픽 메타데이터 기록
[ AWS VPC 흐름 로그 ]( https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html )는 원본 및 대상 IP 주소와 포트와 같은 VPC를 통해 흐르는 트래픽에 대한 메타데이터를 캡처합니다. 수락/삭제된 패킷과 함께. 이 정보를 분석하여 Pod를 포함하여 VPC 내의 리소스 간에 의심스럽거나 비정상적인 활동을 찾을 수 있습니다. 그러나 Pod의 IP 주소는 교체되는 경우가 많기 때문에 Flow Log만으로는 충분하지 않을 수 있습니다. Calico Enterprise는 팟(Pod) 레이블 및 기타 메타데이터로 플로우 로그를 확장하여 팟(Pod) 간의 트래픽 플로우를 더 쉽게 해독합니다.

### AWS 로드 밸런서로 암호화 사용
[ AWS Application Load Balancer ]( https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html ) (ALB) 및 [ Network Load Balancer ]( https://docs.aws.amazon. com/elasticloadbalancing/latest/network/introduction.html )(NLB) 둘 다 전송 암호화(SSL 및 TLS)를 지원합니다. ALB에 대한 'alb.ingress.kubernetes.io/certificate-arn' 주석을 사용하면 ALB에 추가할 인증서를 지정할 수 있습니다. 주석을 생략하면 컨트롤러는 사용 가능한 [ AWS Certificate Manager(ACM) ]( https://docs.aws.amazon.com/acm/latest/userguide/acm- overview.html ) 호스트 필드를 사용하는 인증서. EKS v1.15부터는 아래 예와 같이 NLB와 함께 service.beta.kubernetes.io/aws-load-balancer-ssl-cert 주석을 사용할 수 있습니다.

```yaml
api버전 : v1
종류 : 서비스
메타데이터 :
  이름 : 데모 앱
  네임스페이스 : 기본값
  라벨 :
    앱 : 데모 앱
  주석 :
     service.beta.kubernetes.io/aws-load-balancer-type : "nlb"
     service.beta.kubernetes.io/aws-load-balancer-ssl-cert : "<인증서 ARN>"
     service.beta.kubernetes.io/aws-load-balancer-ssl-ports : "443"
     service.beta.kubernetes.io/aws-load-balancer-backend-protocol : "http"
사양 :
  유형 : 로드밸런서
  포트 :
- 포트 : 443
    대상포트 : 80
    프로토콜 : TCP
  선택기 :
    앱 : 데모 앱
---
종류 : 배포
apiVersion : 앱/v1
메타데이터 :
  이름 : nginx
  네임스페이스 : 기본값
  라벨 :
    앱 : 데모 앱
사양 :
  복제본 : 1
  선택기 :
    일치 라벨 :
      앱 : 데모 앱
  템플릿 :
    메타데이터 :
      라벨 :
        앱 : 데모 앱
    사양 :
      용기 :
- 이름 : nginx
          이미지 : nginx
          포트 :
- 컨테이너 포트 : 443
              프로토콜 : TCP
- 컨테이너포트 : 80
              프로토콜 : TCP
```

### 추가 리소스
+ [ Kubernetes & Tigera: 네트워크 정책, 보안 및 감사 ]( https://youtu.be/lEY2WnRHYpg )
+ [ Calico Enterprise ]( https://www.tigera.io/tigera-products/calico-enterprise/ )
+ [ 섬모 ]( https://cilium.readthedocs.io/en/stable/intro/ )
+ [ NetworkPolicy Editor ]( https://cilium.io/blog/2021/02/10/network-policy-editor ) Cilium의 대화형 정책 편집기
+ [ Kinvolk의 네트워크 정책 어드바이저 ]( https://kinvolk.io/blog/2020/03/writing-kubernetes-network-policies-with-inspektor-gadgets-network-policy-advisor/ ) 분석을 기반으로 네트워크 정책 제안 네트워크 트래픽

## 보안 그룹
EKS는 [ AWS VPC 보안 그룹 ]( https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html )(SG)을 사용하여 Kubernetes 제어 플레인과 클러스터의 작업자 노드 간의 트래픽을 제어합니다. 보안 그룹은 작업자 노드와 다른 VPC 리소스 및 외부 IP 주소 간의 트래픽을 제어하는 데에도 사용됩니다. EKS 클러스터(Kubernetes 버전 1.14-eks.3 이상 포함)를 프로비저닝하면 클러스터 보안 그룹이 자동으로 생성됩니다. 이 보안 그룹은 EKS 컨트롤 플레인과 관리형 노드 그룹의 노드 간에 자유로운 통신을 허용합니다. 단순화를 위해 비관리 노드 그룹을 포함하여 모든 노드 그룹에 클러스터 SG를 추가하는 것이 좋습니다.

Kubernetes 버전 1.14 및 EKS 버전 eks.3 이전에는 EKS 컨트롤 플레인 및 노드 그룹에 대해 별도의 보안 그룹이 구성되었습니다. 컨트롤 플레인 및 노드 그룹 보안 그룹에 대한 최소 및 제안 규칙은 [ https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html ]( https:// docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html ). _ 컨트롤 플레인 보안 그룹_ 에 대한 최소 규칙 은 작업자 노드 SG에서 포트 443 인바운드를 허용합니다. 이 규칙은 kubelet이 Kubernetes API 서버와 통신할 수 있도록 허용합니다. 또한 작업자 노드 SG에 대한 아웃바운드 트래픽용 포트 10250도 포함합니다. 10250은 kubelet이 수신 대기하는 포트입니다. 마찬가지로 최소 _node group_ 규칙은 컨트롤 플레인 SG에서 포트 10250 인바운드 및 컨트롤 플레인 SG로 아웃바운드 443을 허용합니다. 마지막으로 노드 그룹 내의 노드 간에 자유로운 통신을 허용하는 규칙이 있습니다.

클러스터 내에서 실행되는 서비스와 RDS 데이터베이스와 같은 클러스터 외부에서 실행되는 서비스 간의 통신을 제어해야 하는 경우 [ 포드용 보안 그룹 ]( https://docs.aws.amazon.com/eks/latest/ userguide/security-groups-for-pods.html ). Pod용 보안 그룹을 사용하면 **기존** 보안 그룹을 Pod 모음에 할당할 수 있습니다 .

!!! 경고
포드 생성 전에 존재하지 않는 보안 그룹을 참조하는 경우 포드가 예약되지 않습니다.

`SecurityGroupPolicy` 객체 를 생성하고 `PodSelector` 또는 `ServiceAccountSelector` 를 지정 하여 보안 그룹에 할당되는 포드를 제어할 수 있습니다 . 선택기를 `{}` 로 설정하면 `SecurityGroupPolicy` 에서 참조되는 SG 를 네임스페이스의 모든 포드 또는 네임스페이스의 모든 서비스 계정에 할당합니다. 모든 [ 고려 사항 ]( https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html#security-groups-pods-considerations ) 을 숙지 했는지 확인하십시오 . 포드에 대한 보안 그룹을 구현하기 전에.

!!! 중요한
포드에 SG를 사용하는 경우 **반드시** 클러스터 보안 그룹에 대한 포트 53 아웃바운드를 허용하는 SG를 생성해야 합니다. 마찬가지로 포드 보안 그룹에서 포트 53 인바운드 트래픽을 수락하도록 클러스터 보안 그룹을 **반드시** 업데이트해야 합니다.

!!! 중요한
[ 보안 그룹에 대한 제한 ]( https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html#vpc-limits-security-groups )은 포드에 보안 그룹을 사용할 때 계속 적용됩니다. 따라서 신중하게 사용하십시오.

!!! 중요한
포드에 구성된 모든 프로브에 대해 클러스터 보안 그룹(kubelet)의 인바운드 트래픽에 대한 규칙을 **반드시** 생성 해야 합니다 .

!!! 경고
현재 kubelet이 SG에 할당된 포드와 통신하지 못하게 하는 [ 버그 ]( https://github.com/aws/amazon-vpc-cni-k8s/pull/1212 )가 있습니다. 현재 해결 방법은 영향을 받는 작업자 노드에서 `sudo sysctl net.ipv4.tcp_early_demux=0` 을 실행하는 것입니다. 이것은 CNI v1.7.3에서 수정되었습니다. [ https://github.com/aws/amazon-vpc-cni-k8s/releases/tag/v1.7.3 ]( https://github.com/aws/amazon-vpc -cni-k8s/releases/tag/v1.7.3 ).

!!! 중요한
포드의 보안 그룹은 [ ENI 트렁킹 ]( https://docs.aws.amazon.com/AmazonECS/latest/developerguide/container-instance-eni.html )이라는 기능을 사용합니다. 이 기능은 포드의 ENI 밀도를 높이기 위해 생성되었습니다. EC2 인스턴스. 포드가 SG에 할당되면 VPC 컨트롤러는 노드 그룹의 분기 ENI를 포드와 연결합니다. 포드가 예약된 시점에 노드 그룹에서 사용할 수 있는 분기 ENI가 충분하지 않으면 포드는 보류 상태로 유지됩니다. 인스턴스가 지원할 수 있는 분기 ENI 수는 인스턴스 유형/패밀리에 따라 다릅니다. [ https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html#supported-instance-types ]( https://docs.aws.amazon.com/eks 참조 /latest/userguide/security-groups-for-pods.html#supported-instance-types )에서 자세한 내용을 확인하세요.

포드의 보안 그룹은 정책 데몬의 오버헤드 없이 클러스터 내부 및 외부의 네트워크 트래픽을 제어하는 AWS 고유의 방법을 제공하지만 다른 옵션도 사용할 수 있습니다. 예를 들어 Cilium 정책 엔진을 사용하면 네트워크 정책에서 DNS 이름을 참조할 수 있습니다. Calico Enterprise에는 네트워크 정책을 AWS 보안 그룹에 매핑하는 옵션이 포함되어 있습니다. Istio와 같은 서비스 메시를 구현한 경우 송신 게이트웨이를 사용하여 네트워크 송신을 특정 정규화된 도메인 또는 IP 주소로 제한할 수 있습니다. 이 옵션에 대한 자세한 내용은 [ Istio의 송신 트래픽 제어 ]( https://istio.io/blog/2019/egress-traffic-control-in-istio-part-1/ )에 대한 3 부작 시리즈를 읽어보십시오 .

## 전송 중 암호화
PCI, HIPAA 또는 기타 규정을 준수해야 하는 애플리케이션은 전송 중인 데이터를 암호화해야 할 수 있습니다. 오늘날 TLS는 유선 트래픽을 암호화하기 위한 사실상의 선택입니다. 이전 SSL과 마찬가지로 TLS는 암호화 프로토콜을 사용하여 네트워크를 통해 보안 통신을 제공합니다. TLS는 세션 시작 시 협상되는 공유 암호를 기반으로 데이터를 암호화하는 키가 생성되는 대칭 암호화를 사용합니다. 다음은 Kubernetes 환경에서 데이터를 암호화할 수 있는 몇 가지 방법입니다.

### Nitro 인스턴스
다음 Nitro 인스턴스 유형 C5n, G4, I3en, M5dn, M5n, P3dn, R5dn 및 R5n 간에 교환되는 트래픽은 기본적으로 자동으로 암호화됩니다. 전송 게이트웨이 또는 로드 밸런서와 같은 중간 홉이 있는 경우 트래픽이 암호화되지 않습니다. [ 전송 중 암호화 ]( https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/data-protection.html#encryption-transit ) 및 다음 [ 새로운 기능 ]( https://aws.amazon )을 참조하십시오. 자세한 내용은 .com/about-aws/whats-new/2019/10/introducing-amazon-ec2-m5n-m5dn-r5n-and-r5dn-instances-featuring-100-gbps-of-network-bandwidth/ ) 발표를 참조하십시오. .

### 컨테이너 네트워크 인터페이스(CNI)
[ WeaveNet ]( https://www.weave.works/oss/net/ )은 슬리브 트래픽에 NaCl 암호화를 사용하고 빠른 데이터 경로 트래픽에 IPsec ESP를 사용하여 모든 트래픽을 자동으로 암호화하도록 구성할 수 있습니다.

### 서비스 메시
App Mesh, Linkerd v2 및 Istio와 같은 서비스 메시를 사용하여 전송 중 암호화를 구현할 수도 있습니다. AppMesh는 X.509 인증서 또는 Envoy의 SDS(Secret Discovery Service)로 [ mTLS ]( https://docs.aws.amazon.com/app-mesh/latest/userguide/mutual-tls.html )를 지원합니다. Linkerd와 Istio는 모두 mTLS를 지원합니다.

[ aws-app-mesh-examples ]( https://github.com/aws/aws-app-mesh-examples ) GitHub 리포지토리는 X.509 인증서 및 SPIRE를 Envoy 컨테이너와 함께 SDS 공급자로 사용하여 mTLS를 구성하는 연습을 제공합니다. :

+ [ X.509 인증서를 사용하여 mTLS 구성 ]( https://github.com/aws/aws-app-mesh-examples/tree/main/walkthroughs/howto-k8s-mtls-file-based )
+ [ SPIRE(SDS)를 사용하여 TLS 구성 ]( https://github.com/aws/aws-app-mesh-examples/tree/main/walkthroughs/howto-k8s-mtls-sds-based )

또한 App Mesh는 [ AWS Certificate Manager ] ( https ://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html ) (ACM) 또는 가상 노드의 로컬 파일 시스템에 저장된 인증서.

[ aws-app-mesh-examples ]( https://github.com/aws/aws-app-mesh-examples ) GitHub 리포지토리는 ACM에서 발급한 인증서 및 Envoy 컨테이너와 함께 패키징된 인증서를 사용하여 TLS를 구성하는 연습을 제공합니다. :
+ [ 파일 제공 TLS 인증서로 TLS 구성 ]( https://github.com/aws/aws-app-mesh-examples/tree/master/walkthroughs/howto-tls-file-provided )
+ [ AWS Certificate Manager로 TLS 구성 ]( https://github.com/aws/aws-app-mesh-examples/tree/master/walkthroughs/tls-with-acm )

### 인그레스 컨트롤러 및 로드 밸런서
수신 컨트롤러는 클러스터 외부에서 발생하는 HTTP/S 트래픽을 클러스터 내부에서 실행되는 서비스로 지능적으로 라우팅하는 방법입니다. 종종 이러한 Ingress는 Classic Load Balancer 또는 NLB(Network Load Balancer)와 같은 계층 4 로드 밸런서에 의해 전면에 배치됩니다. 암호화된 트래픽은 로드 밸런서, 인그레스 리소스 또는 포드와 같이 네트워크 내의 다른 위치에서 종료될 수 있습니다. SSL 연결을 종료하는 방법과 위치는 궁극적으로 조직의 네트워크 보안 정책에 따라 결정됩니다. 예를 들어 종단 간 암호화를 요구하는 정책이 있는 경우 Pod에서 트래픽을 해독해야 합니다. 이렇게 하면 초기 핸드셰이크를 설정하는 주기를 소비해야 하므로 Pod에 추가 부담이 가해집니다. 전반적인 SSL/TLS 처리는 CPU를 많이 사용합니다. 따라서 유연성이 있는 경우 인그레스 또는 로드 밸런서에서 SSL 오프로드를 수행해 보십시오.

수신 컨트롤러는 SSL/TLS 연결을 종료하도록 구성할 수 있습니다. NLB에서 SSL/TLS 연결을 종료하는 방법에 대한 예는 [ 위 ]( #use-encryption-with-aws-load-balancers )에 나와 있습니다. SSL/TLS 종료에 대한 추가 예는 아래에 나와 있습니다.

+ [ Contour로 EKS 인그레스 보호 및 GitOps 방식 암호화 ]( https://aws.amazon.com/blogs/containers/securing-eks-ingress-contour-lets-encrypt-gitops/ )
+ [ ACM을 사용하여 Amazon EKS 워크로드에서 HTTPS 트래픽을 종료하려면 어떻게 해야 합니까? ]( https://aws.amazon.com/premiumsupport/knowledge-center/terminate-https-traffic-eks-acm/ )

!!! 주목
ALB 수신 컨트롤러와 같은 일부 수신은 수신 사양의 일부가 아닌 주석을 사용하여 SSL/TLS를 구현합니다.

### cert-manager가 있는 ACM 사설 CA
cert-manager ]( https://cert-manager.io/ ) 를 사용하여 수신, 포드 및 포드 간에 EKS 애플리케이션 워크로드를 보호할 수 있습니다 . 인증서를 배포, 갱신 및 취소하는 인기 있는 Kubernetes 추가 기능입니다. ACM 사설 CA는 자체 CA를 관리하는 선행 비용 및 유지 관리 비용이 없는 가용성이 높고 안전한 관리형 CA입니다. 기본 Kubernetes 인증 기관을 사용하는 경우 ACM Private CA를 통해 보안을 개선하고 규정 준수 요구 사항을 충족할 수 있습니다. ACM 사설 CA는 FIPS 140-2 레벨 3 하드웨어 보안 모듈(매우 안전함)의 개인 키를 보호하며, 이는 메모리에 인코딩된 키를 저장하는 기본 CA(덜 안전함)와 비교됩니다. 또한 중앙 집중식 CA 는 Kubernetes 환경 내부와 외부 모두에서 사설 인증서에 대해 더 많은 제어 기능과 향상된 감사 기능을 제공합니다. [ 여기에서 ACM 사설 CA 및 그 이점에 대해 자세히 알아보십시오 ]( https://aws.amazon.com/certificate-manager/private-certificate-authority/ ).

#### 설정 지침
ACM 사설 CA 기술 문서 ]( https://docs.aws.amazon.com/acm-pca/latest/userguide/create-CA.html ) 에 제공된 절차에 따라 사설 CA 생성부터 시작하십시오 . 사설 CA가 있으면 [ 일반 설치 지침 ]( https://cert-manager.io/docs/installation/ )을 사용하여 cert-manager를 설치합니다. cert-manager를 설치한 후 [ GitHub의 설정 지침 ]( https://github.com/cert-manager/aws-privateca-issuer#setup )에 따라 Private CA Kubernetes cert-manager 플러그인을 설치합니다. 플러그인을 사용하면 cert-manager가 ACM Private CA에서 사설 인증서를 요청할 수 있습니다.

이제 cert-manager 및 플러그인이 설치된 사설 CA 및 EKS 클러스터가 있으므로 권한을 설정하고 발급자를 생성할 차례입니다. ACM Private CA에 대한 액세스를 허용하도록 EKS 노드 역할의 IAM 권한을 업데이트합니다. `<CA_ARN>` 을 사설 CA의 값으로 바꿉니다 .

```
{
"버전": "2012-10-17",
"성명": [
{
"시드": "awspcaissuer",
"동작": [
"acm-pca:DescribeCertificateAuthority",
"acm-pca:GetCertificate",
"acm-pca:IssueCertificate"
],
"효과": "허용",
"리소스": "<CA_ARN>"
}
]
}
```
[ IAM 계정의 서비스 역할 또는 IRSA ]( https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html )도 사용할 수 있습니다. 전체 예제는 아래의 추가 리소스 섹션을 참조하십시오.

다음 텍스트가 포함된 cluster-issuer.yaml이라는 사용자 지정 리소스 정의 파일을 생성하고 `<CA_ARN>` 및 `<Region>` 정보를 사설 CA 로 대체하여 Amazon EKS에서 발급자를 생성합니다.

```
apiVersion: awspca.cert-manager.io/v1beta1
종류: AWSPCAClusterIssuer
메타데이터:
이름: 데모-테스트-루트-ca
투기:
안: <CA_ARN>
지역: <지역>
```

생성한 발급자를 배포합니다.

```
kubectl 적용 -f 클러스터-issuer.yaml
```

EKS 클러스터는 사설 CA에서 인증서를 요청하도록 구성되어 있습니다. 이제 위에서 생성한 사설 CA 발급자로 'issuerRef' 필드의 값을 변경하여 cert-manager의 'Certificate' 리소스를 사용하여 인증서를 발급할 수 있습니다. 인증서 리소스 지정 및 요청 방법에 대한 자세한 내용은 cert-manager의 [ 인증서 리소스 가이드 ]( https://cert-manager.io/docs/usage/certificate/ )를 확인하세요. [ 여기에서 예시 보기 ]( https://github.com/cert-manager/aws-privateca-issuer/tree/main/config/samples/ ).

#### 추가 리소스
+ [ EKS에서 TLS를 활성화하기 위해 cert-manager 및 ACM Private CA 플러그인을 구현하는 방법 ]( https://aws.amazon.com/blogs/security/tls-enabled-kubernetes-clusters-with-acm-private-ca -and-amazon-eks-2/ ).
+ [ 새로운 AWS 로드 밸런서 컨트롤러 및 ACM 사설 CA를 사용하여 Amazon EKS에서 종단 간 TLS 암호화 설정 ]( https://aws.amazon.com/blogs/containers/setting-up-end-to-end -tls-encryption-on-amazon-eks-with-the-new-aws-load-balancer-controller/ ).
+ [ Github의 Private CA Kubernetes cert-manager 플러그인 ]( https://github.com/cert-manager/aws-privateca-issuer ).
+ [ 사설 CA Kubernetes cert-manager 플러그인 사용자 가이드 ]( https://docs.aws.amazon.com/acm-pca/latest/userguide/PcaKubernetes.html ).

## 툴링
+ [ ksniff 및 Wireshark를 사용하여 Kubernetes에서 Service Mesh TLS 확인 ]( https://itnext.io/verifying-service-mesh-tls-in-kubernetes-using-ksniff-and-wireshark-2e993b26bf95 )
+ [ ksniff ]( https://github.com/eldadru/ksniff )
+ [ egress-operator ]( https://github.com/monzo/egress-operator ) 프로토콜 검사 없이 클러스터에서 나가는 트래픽을 제어하는 운영자 및 DNS 플러그인


