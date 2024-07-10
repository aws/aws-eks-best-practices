---
search:
  exclude: true
---


# 네트워크를 위한 Amazon EKS 모범 사례 가이드

클러스터와 애플리케이션을 효율적으로 운영하려면 쿠버네티스 네트워킹를 이해하는 것이 중요합니다. 클러스터 네트워킹이라고도 하는 파드 네트워킹은 쿠버네티스 네트워킹의 중심입니다. 쿠버네티스는 클러스터 네트워킹을 위한 [컨테이너 네트워크 인터페이스](https://github.com/containernetworking/cni)(CNI) 플러그인을 지원합니다. 

Amazon EKS는 쿠버네티스 파드 네트워킹을 구현하는 [Amazon Virtual Private Cloud(VPC)](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) CNI 플러그인을 공식적으로 지원합니다. VPC CNI는 AWS VPC와의 네이티브 통합을 제공하며 언더레이(underlay) 모드에서 작동합니다. 언더레이 모드에서는 파드와 호스트가 동일한 네트워크 계층에 위치하며 네트워크 네임스페이스를 공유합니다. 파드의 IP 주소는 클러스터 및 VPC 관점에서 일관되게 구성됩니다. 

이 가이드에서는 쿠버네티스 클러스터 네트워킹의 맥락에서 [Amazon VPC 컨테이너 네트워크 인터페이스](https://github.com/aws/amazon-vpc-cni-k8s)[(VPC CNI)](https://github.com/aws/amazon-vpc-cni-k8s)를 소개합니다. VPC CNI는 EKS에서 지원하는 기본 네트워킹 플러그인이므로 이 가이드에서 중점적으로 다루도록 하겠습니다. VPC CNI는 다양한 사용 사례를 지원하도록 구성할 수 있습니다. 또한 이 가이드에는 다양한 VPC CNI 사용 사례, 운영 모드, 하위 구성 요소에 대한 섹션과 권장 사항을 포함하고 있습니다.

Amazon EKS는 업스트림 쿠버네티스를 실행하며 쿠버네티스 적합성 인증을 받았습니다. 대체 CNI 플러그인을 사용할 수 있지만, 이 가이드에서는 대체 CNI 관리에 대한 권장 사항을 제공하지 않습니다. 대체 CNI를 효과적으로 관리하기 위한 파트너 및 리소스 목록은 [EKS Alternate CNI](https://docs.aws.amazon.com/eks/latest/userguide/alternate-cni-plugins.html) 설명서를 참조합니다.

## 쿠버네티스 네트워킹 모델

쿠버네티스는 클러스터 네트워킹에 대해 다음과 같은 요구 사항을 정의했습니다.

* 동일한 노드에 스케줄링된 파드는 NAT(Network Address Translation)를 사용하지 않고 다른 파드와 통신할 수 있어야 합니다.
* 특정 노드에서 실행되는 모든 시스템 데몬(백그라운드 프로세스, 예: [kubelet](https://kubernetes.io/docs/concepts/overview/components/))은 동일한 노드에서 실행되는 파드와 통신할 수 있어야 합니다.
* [호스트 네트워크](https://docs.docker.com/network/host/)를 사용하는 파드는 NAT를 사용하지 않고 다른 모든 노드의 다른 모든 파드에 접근할 수 있어야 합니다.

쿠버네티스에서 요구하는 호환 가능한 네트워킹 구현에 대한 자세한 내용은 [쿠버네티스 네트워크 모델](https://kubernetes.io/docs/concepts/services-networking/#the-kubernetes-network-model)을 참조합니다. 다음 그림은 파드 네트워크 네임스페이스와 호스트 네트워크 네임스페이스 간의 관계를 보여줍니다.


![illustration of host network and 2 pod network namespaces](image.png)
## 컨테이너 네트워킹 인터페이스 (CNI)

쿠버네티스는 쿠버네티스 네트워크 모델을 구현하기 위한 CNI 사양 및 플러그인을 지원합니다. CNI는 컨테이너에서 네트워크 인터페이스를 구성하기 위한 플러그인을 작성하기 위한 [사양](https://github.com/containernetworking/cni/blob/main/SPEC.md)(현재 버전 1.0.0)과 라이브러리, 지원 가능한 여러 플러그인으로 구성됩니다. CNI는 컨테이너의 네트워크 연결과 컨테이너 삭제 시 할당된 리소스 제거에만 관여합니다.

CNI 플러그인은 kubelet에 `--network-plugin=cni` 명령줄 옵션을 전달함으로써 활성화됩니다. kubelet은 `--cni-conf-dir` (기본적으로 /etc/cni/net.d)에서 파일을 읽고 해당 파일의 CNI 구성을 활용하여 각 파드의 네트워크를 설정합니다. CNI 구성 파일은 CNI 사양 (최소 v0.4.0) 과 일치해야 하며 구성에서 참조하는 모든 필수 CNI 플러그인은 `--cni-bin-dir` 디렉터리(기본적으로 /opt/cni/bin)에 있어야 합니다. 디렉터리에 CNI 구성 파일이 여러 개 있는 경우, *kubelet은 구성 파일을 오름차순 기준으로 앞에 오는 이름을 가진 파일을 사용합니다*.


## Amazon Virtual Private Cloud (VPC) CNI

AWS에서 제공하는 VPC CNI는 EKS 클러스터의 기본 네트워킹 애드온입니다. VPC CNI 애드온은 EKS 클러스터를 프로비저닝할 때 기본적으로 설치됩니다. VPC CNI는 쿠버네티스 워커 노드에서 실행됩니다. VPC CNI 애드온은 CNI 바이너리와 IP 주소 관리(ipamd) 플러그인으로 구성되어 있습니다. CNI는 VPC 네트워크의 IP 주소를 파드에 할당합니다. ipamd는 각 쿠버네티스 노드에 대한 AWS Elastic Networking Interface(ENI) 를 관리하고 IP 웜 풀을 유지합니다. VPC CNI는 빠른 파드 기동 시간을 위해 ENI와 IP 주소를 사전 할당하기 위한 구성 옵션을 제공합니다. [Amazon VPC CNI](../vpc-cni/index.md)에서 권장 플러그인 관리 모범 사례를 참조합니다.

Amazon EKS는 클러스터를 생성할 때 최소 두 개의 가용 영역에 서브넷을 지정할 것을 권장합니다. Amazon VPC CNI는 노드의 서브넷에서 파드 IP 주소를 할당합니다. 해당 서브넷에서 사용 가능한 IP 주소를 확인할 것을 강력하게 권장합니다. EKS 클러스터를 배포하기 전에 [VPC 및 서브넷](../subnets/index.md) 권장사항을 고려합니다.

Amazon VPC CNI는 노드의 기본 ENI에 연결된 서브넷의 ENI와 보조 IP 주소로 구성된 웜 풀을 할당합니다. 이 VPC CNI 모드를 “[보조 IP 모드(secondary IP mode)](../vpc-cni/index.md)”라고 합니다. IP 주소 수와 이에 따른 파드 수(파드의 밀도)는 인스턴스 유형별로 정의된 ENI 및 ENI 당 IP 주소 수(제한)에 따라 정의됩니다. 보조 모드는 기본값이며 인스턴스 유형이 작은 소규모 클러스터에 적합합니다. 파드 밀도 문제가 발생하는 경우, [Prefix 모드](../prefix-mode/index_linux.md)사용을 고려합니다. ENI에 Prefix를 할당하여 파드용 노드에서 사용 가능한 IP 주소를 늘릴 수 있습니다.

Amazon VPC CNI는 기본적으로 AWS VPC와 통합되며, 이를 통해 사용자는 기존 AWS VPC 네트워킹 및 보안 모범 사례를 적용하여 쿠버네티스 클러스터를 구축할 수 있습니다. 여기에는 VPC flow logs, VPC 라우팅 정책 및 네트워크 트래픽 격리를 위한 보안 그룹을 사용할 수 있는 기능이 포함됩니다. 기본적으로 Amazon VPC CNI는 노드의 기본 ENI와 연결된 보안 그룹을 파드에 적용합니다. 파드에 별도의 네트워크 규칙을 할당하고 싶은 경우 [파드용 보안 그룹](../sgpp/index.md) 활성화를 고려합니다.

기본적으로 VPC CNI는 노드의 기본 ENI에 할당된 서브넷의 IP 주소를 Pod에 할당합니다. 수천 개의 워크로드가 있는 대규모 클러스터를 실행할 경우에는 IPv4 주소 부족이 발생하는 것이 일반적입니다. AWS VPC를 사용하면 [보조 CIDR 할당](https://docs.aws.amazon.com/vpc/latest/userguide/configure-your-vpc.html#add-cidr-block-restrictions)을 통해 사용 가능한 IP를 확장하여 IPv4 CIDR 블록 고갈을 해결할 수 있습니다. AWS VPC CNI를 사용하여 파드에 대해 다른 서브넷 CIDR 범위를 사용할 수 있습니다. VPC CNI의 이러한 기능을 [사용자 지정 네트워킹](../custom-networking/index.md)이라고 합니다. EKS에서 100.64.0.0/10 및 198.19.0.0/16 CIDR(CG-NAT)을 함께 사용하려면 사용자 지정 네트워킹을 사용하는 것을 고려해 볼 수 있습니다. 이를 통해 파드가 VPC의 RFC1918 IP 주소를 사용하지 않을 경우의 환경을 효과적으로 구성할 수 있습니다.

사용자 지정 네트워킹은 IPv4 주소 고갈 문제를 해결하는 한 가지 방법이지만 운영 오버헤드가 발생합니다. 이러한 문제를 해결하려면 사용자 지정 네트워킹보다 IPv6 클러스터를 사용하는 것이 좋습니다. 특히, VPC에서 사용 가능한 IPv4 주소를 모두 소진한 경우 [IPv6 클러스터](../ipv6/index.md)로 마이그레이션할 것을 권장합니다. IPv6의 지원을 위한 조직에서의 계획을 확인하고, IPv6에 투자하는 것이 장기적 가치가 더 높을지 고려합니다.

EKS의 IPv6 지원은 제한된 IPv4 주소 공간으로 인해 발생하는 IP 고갈 문제를 해결하는 데 중점을 두고 있습니다. IPv4 고갈로 인한 고객들의 문제에 대응하여 EKS는 듀얼 스택 파드보다 IPv6 전용 파드의 우선순위를 높입니다. 즉, 파드는 IPv4 리소스에 액세스할 수 있지만 VPC CIDR 범위의 IPv4 주소는 할당되지 않습니다. VPC CNI는 AWS 관리형 VPC IPv6 CIDR 블록에서 파드에 IPv6 주소를 할당합니다. 

## 서브넷 계산기

이 프로젝트에는 [서브넷 계산기 Excel 문서](../subnet-calc/subnet-calc.xlsx)가 포함되어 있습니다. 이 계산기 문서는 `WARM_IP_TARGET` 및 `WARM_ENI_TARGET`과 같은 다양한 ENI 구성 옵션에 따라 지정된 워크로드의 IP 주소 사용을 시뮬레이션합니다. 이 문서에는 두 개의 시트가 포함되어 있습니다. 첫 번째 시트는 웜 ENI 모드용이고 다른 하나는 웜 IP 모드용입니다. 이러한 모드에 대한 자세한 내용은 [VPC CNI guidance](../vpc-cni/index.md)를 참조합니다. 

입력 값:
- 서브넷 CIDR 크기
- 웜 ENI 타겟 *또는* 웜 IP 타겟
- 인스턴스 목록
    - 유형, 개수 및 인스턴스당 스케줄링된 워크로드 파드의 수

출력 값:
- 호스팅된 총 파드 수
- 사용된 서브넷 IP 수
- 남아 있는 서브넷 IP 수
- 인스턴스 수준 세부 정보
    - 인스턴스당 웜 IP/ENI 수
    - 인스턴스당 활성 IP/ENI 수

