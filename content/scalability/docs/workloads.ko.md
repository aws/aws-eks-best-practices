# 워크로드

워크로드는 클러스터를 확장할 수 있는 규모에 영향을 미칩니다. 쿠버네티스 API를 많이 사용하는 워크로드는 단일 클러스터에서 보유할 수 있는 워크로드의 총량을 제한하지만, 부하를 줄이기 위해 변경할 수 있는 몇 가지 기본값이 있습니다.

쿠버네티스 클러스터의 워크로드는 쿠버네티스 API와 통합되는 기능(예: Secrets 및 ServiceAccount)에 액세스할 수 있지만, 이런 기능이 항상 필요한 것은 아니므로 사용하지 않는 경우 비활성화해야 합니다.워크로드 액세스와 쿠버네티스 컨트롤 플레인에 대한 종속성을 제한하면 클러스터에서 실행할 수 있는 워크로드 수가 증가하고 워크로드에 대한 불필요한 액세스를 제거하고 최소 권한 관행을 구현하여 클러스터의 보안을 개선할 수 있습니다. 자세한 내용은 [보안 모범 사례](https://aws.github.io/aws-eks-best-practices/security/docs/)를 참고하세요.

## 파드 네트워킹에 IPv6 사용하기

VPC를 IPv4에서 IPv6으로 전환할 수 없으므로 클러스터를 프로비저닝하기 전에 IPv6를 활성화하는 것이 중요합니다. 다만 VPC에서 IPv6를 활성화한다고 해서 반드시 사용해야 하는 것은 아니며, 파드 및 서비스가 IPv6를 사용하는 경우에도 IPv4 주소를 오가는 트래픽을 라우팅할 수 있습니다. 자세한 내용은 [EKS 네트워킹 모범 사례](https://aws.github.io/aws-eks-best-practices/networking/index/)를 참고하세요.

[클러스터에서 IPv6 사용하기 튜토리얼](https://docs.aws.amazon.com/eks/latest/userguide/cni-ipv6.html)를 사용하면 가장 일반적인 클러스터 및 워크로드 확장 제한을 피할 수 있습니다. IPv6는 사용 가능한 IP 주소가 없어 파드와 노드를 생성할 수 없는 IP 주소 고갈을 방지합니다. 또한 노드당 ENI 어태치먼트 수를 줄여 파드가 IP 주소를 더 빠르게 수신하므로 노드당 성능도 개선되었습니다. [VPC CNI의 IPv4 Prefix 모드](https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/)를 사용하여 유사한 노드 성능을 얻을 수 있지만, 여전히 VPC에서 사용할 수 있는 IP 주소가 충분한지 확인해야 합니다.

## 네임스페이스당 서비스 수 제한

[네임스페이스의 최대 서비스 수는 5,000개이고 클러스터의 최대 서비스 수는 10,000개](https://github.com/kubernetes/community/blob/master/sig-scalability/configs-and-limits/thresholds.md) 입니다. 워크로드와 서비스를 구성하고, 성능을 높이고, 네임스페이스 범위 리소스가 연쇄적으로 영향을 받지 않도록 하려면 네임스페이스당 서비스 수를 500개로 제한하는 것이 좋습니다.

kube-proxy를 사용하여 노드당 생성되는 IP 테이블 규칙의 수는 클러스터의 총 서비스 수에 따라 증가합니다.수천 개의 IP 테이블 규칙을 생성하고 이런 규칙을 통해 패킷을 라우팅하면 노드의 성능이 저하되고 네트워크 지연 시간이 늘어납니다.

네임스페이스당 서비스 수가 500개 미만인 경우 단일 애플리케이션 환경을 포함하는 쿠버네티스 네임스페이스를 생성하십시오. 이렇게 하면 서비스 검색 제한을 피할 수 있을 만큼 서비스 검색 크기가 작아지고 서비스 이름 충돌을 방지하는 데도 도움이 됩니다. 애플리케이션 환경(예: dev, test, prod) 은 네임스페이스 대신 별도의 EKS 클러스터를 사용해야 합니다.

## Elastic Load Balancer 할당량 이해

서비스를 생성할 때 사용할 로드 밸런싱 유형(예: 네트워크 로드밸런서 (NLB) 또는 애플리케이션 로드밸런서 (ALB)) 를 고려하세요. 각 로드밸런서 유형은 서로 다른 기능을 제공하며 [할당량](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html)이 다릅니다. 기본 할당량 중 일부는 조정할 수 있지만 일부 할당량 최대값은 변경할 수 없습니다. 계정 할당량 및 사용량을 보려면 AWS 콘솔의 [서비스 할당량 대시보드](http://console.aws.amazon.com/servicequotas)를 참조하십시오.

예를 들어, 기본 ALB 목표는 1000입니다. 엔드포인트가 1,000개가 넘는 서비스가 있는 경우 할당량을 늘리거나 서비스를 여러 ALB로 분할하거나 쿠버네티스 인그레스(Ingress)를 사용해야 합니다. 기본 NLB 대상은 3000이지만 AZ당 500개 대상으로 제한됩니다. 클러스터에서 NLB 서비스에 대해 500개 이상의 파드를 실행하는 경우 여러 AZ를 사용하거나 할당량 한도 증가를 요청해야 합니다.

서비스에 연결된 로드밸런서를 사용하는 대신 [인그레스 컨트롤러](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/) 를 사용할 수 있습니다. AWS Load Balancer Controller는 수신 리소스용 ALB를 생성할 수 있지만, 클러스터에서 전용 컨트롤러를 실행하는 것도 고려해 볼 수 있습니다.클러스터 내 수신 컨트롤러를 사용하면 클러스터 내에서 역방향 프록시를 실행하여 단일 로드밸런서에서 여러 쿠버네티스 서비스를 노출할 수 있습니다. 컨트롤러는 [Gateway API](https://gateway-api.sigs.k8s.io/) 지원과 같은 다양한 기능을 제공하므로 워크로드의 수와 규모에 따라 이점이 있을 수 있습니다.

## Route 53, Global Accelerator, 또는 CloudFront 사용하기

여러 로드밸런서를 사용하는 서비스를 단일 엔드포인트로 사용하려면 [Amazon CloudFront](https://aws.amazon.com/cloudfront/), [AWS Global Accelerator](https://aws.amazon.com/global-accelerator/) 또는 [Amazon Route 53](https://aws.amazon.com/route53/)를 사용하여 모든 로드밸런서를 단일 고객 대상 엔드포인트로 노출해야 합니다. 각 옵션에는 서로 다른 이점이 있으며 필요에 따라 개별적으로 또는 함께 사용할 수 있습니다.

Route 53은 공통 이름으로 여러 로드밸런서를 노출할 수 있으며 할당된 가중치에 따라 각 로드밸런서에 트래픽을 전송할 수 있습니다. [DNS 가중치](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-values-weighted.html#rrsets-values-weighted-weight)설명서에 자세한 내용을 확인할 수 있으며 [쿠버네티스 외부 DNS 컨트롤러](https://github.com/kubernetes-sigs/external-dns)를 사용하여 이를 구현하는 방법은 [AWS Load Balancer Controller 설명서](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/guide/integrations/external_dns/#usage)에서 확인할 수 있습니다.

Global Accelerator터는 요청 IP 주소를 기반으로 가장 가까운 지역으로 워크로드를 라우팅할 수 있습니다. 이는 여러 지역에 배포되는 워크로드에 유용할 수 있지만 단일 지역의 단일 클러스터로의 라우팅을 개선하지는 않습니다. Route 53을 Global Accelerator터와 함께 사용하면 가용영역을 사용할 수 없는 경우 상태 점검 및 자동 장애 조치와 같은 추가적인 이점이 있습니다. Route 53과 함께 Global Accelerator터를 사용하는 예는 [이 블로그 게시물](https://aws.amazon.com/blogs/containers/operating-a-multi-regional-stateless-application-using-amazon-eks/)에서 확인할 수 있습니다.

CloudFront는 Route 53 및 Global Accelerator와 함께 사용하거나 단독으로 트래픽을 여러 목적지로 라우팅하는 데 사용할 수 있습니다. CloudFront는 오리진 소스에서 제공되는 자산을 캐시하므로 제공하는 대상에 따라 대역폭 요구 사항을 줄일 수 있습니다.

## 엔드포인트(Endpoints) 대신에 엔드포인트 슬라이스(EndpointSlices) 사용하기

서비스 레이블과 일치하는 파드를 발견할 때는 엔드포인트 대신 [엔드포인트 슬라이스](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)를 사용해야 합니다. 엔드포인트는 서비스를 소규모로 노출할 수 있는 간단한 방법이었지만, 대규모 서비스가 자동으로 확장되거나 업데이트되면 쿠버네티스 컨트롤 플레인에서 많은 트래픽이 발생합니다. 엔드포인트슬라이스에는 토폴로지 인식 힌트와 같은 기능을 사용할 수 있는 자동 그룹화 기능이 있습니다.

모든 컨트롤러가 기본적으로 엔드포인트슬라이스를 사용하는 것은 아닙니다. 컨트롤러 설정을 확인하고 필요한 경우 활성화해야 합니다. [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/configurations/#controller-command-line-flags)의 경우 엔드포인트슬라이스를 사용하려면 `--enable-endpoint-slices` 선택적 플래그를 활성화해야 합니다.

## 가능하다면 변경 불가(immutable)하고 외부(external) 시크릿 사용하기

kubelet은 해당 노드의 파드에 대한 볼륨에서 사용되는 시크릿의 현재 키와 값을 캐시에 보관한다. kubelet은 시크릿을 감시하여 변경 사항을 탐지합니다. 클러스터가 확장됨에 따라 시계의 수가 증가하면 API 서버 성능에 부정적인 영향을 미칠 수 있습니다.

시크릿의 감시 수를 줄이는 두 가지 전략이 있습니다.

* 쿠버네티스 리소스에 액세스할 필요가 없는 애플리케이션의 경우 AutoMountServiceAccountToken: false를 설정하여 서비스 어카운트 시크릿 자동 탑재를 비활성화할 수 있습니다.
* 애플리케이션 암호가 정적이어서 향후 수정되지 않을 경우 [암호를 변경 불가능](https://kubernetes.io/docs/concepts/configuration/secret/#secret-immutable)으로 표시하십시오. kubelet은 변경 불가능한 비밀에 대한 API 감시 기능을 유지하지 않습니다.

서비스 어카운트을 파드에 자동으로 마운트하는 것을 비활성화하려면 워크로드에서 다음 설정을 사용할 수 있습니다. 특정 워크로드에 서비스 어카운트이 필요한 경우 이런 설정을 재정의할 수 있습니다.

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app
automountServiceAccountToken: true
```

클러스터의 암호 수가 제한인 10,000개를 초과하기 전에 모니터링하세요. 다음 명령을 사용하여 클러스터의 총 암호 수를 확인할 수 있습니다. 클러스터 모니터링 도구를 통해 이 한도를 모니터링해야 합니다.

```
kubectl get secrets -A | wc -l
```

이 한도에 도달하기 전에 클러스터 관리자에게 알리도록 모니터링을 설정해야 합니다.[Secrets Store CSI 드라이버](https://secrets-store-csi-driver.sigs.k8s.io/)와 함께 [AWS Key Management Service (AWS KMS)](https://aws.amazon.com/kms/) 또는 [Hashicorp Vault](https://www.vaultproject.io/)와 같은 외부 비밀 관리 옵션을 사용하는 것을 고려해 보십시오.

## 배포 이력 제한

클러스터에서 이전 객체가 계속 추적되므로 파드를 생성, 업데이트 또는 삭제할 때 속도가 느려질 수 있습니다. [디플로이먼트](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#clean-up-policy)의 `therevisionHistoryLimit`을 줄이면 구형 레플리카셋을 정리하여 쿠버네티스 컨트롤러 매니저가 추적하는 오브젝트의 총량을 줄일 수 있습니다. 디플로이먼트의 기본 기록 한도는 10개입니다.

클러스터가 CronJobs나 다른 메커니즘을 통해 많은 수의 작업 개체를 생성하는 경우, [`TTLSecondsFinished` 설정](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/)을 사용하여 클러스터의 오래된 파드를 자동으로 정리해야 합니다. 이렇게 하면 지정된 시간이 지나면 성공적으로 실행된 작업이 작업 기록에서 제거됩니다.

## enableServiceLinks를 기본으로 비활성화하기

파드가 노드에서 실행될 때, kubelet은 각 활성 서비스에 대한 환경 변수 세트를 추가합니다. 리눅스 프로세스에는 환경에 맞는 최대 크기가 있으며 네임스페이스에 서비스가 너무 많으면 이 크기에 도달할 수 있습니다. 네임스페이스당 서비스 수는 5,000개를 초과할 수 없습니다. 그 이후에는 서비스 환경 변수 수가 셸 한도를 초과하여 시작 시 파드가 크래시를 일으키게 됩니다. 

파드가 서비스 검색에 서비스 환경 변수를 사용하지 않아야 하는 다른 이유도 있습니다. 환경 변수 이름 충돌, 서비스 이름 유출, 전체 환경 크기 등이 있습니다. 서비스 엔드포인트를 검색하려면 CoreDNS를 사용해야 합니다.

## 리소스당 동적 어드미션 웹훅(Webhook) 제한하기

[Dynamic Admission Webhooks](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)에는 어드미션 웹훅과 뮤테이팅(Mutating) 웹훅이 포함됩니다. 쿠버네티스 컨트롤 플레인에 속하지 않는 API 엔드포인트로, 리소스가 쿠버네티스 API로 전송될 때 순서대로 호출됩니다. 각 웹훅의 기본 제한 시간은 10초이며, 웹훅이 여러 개 있거나 제한 시간이 초과된 경우 API 요청에 걸리는 시간이 늘어날 수 있습니다.

특히 가용영역 장애 발생 시 웹훅의 가용성이 높은지 확인하고 [FailurePolicy](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#failure-policy)가 리소스를 거부하거나 실패를 무시하도록 적절하게 설정되어 있는지 확인하세요. --dry-run kubectl 명령이 웹훅을 우회하도록 허용하여 필요하지 않을 때는 웹훅을 호출하지 마십시오.

```
apiVersion: admission.k8s.io/v1
kind: AdmissionReview
request:
  dryRun: False
```

웹훅를 변경하면 리소스를 자주 연속적으로 수정할 수 있습니다. 뮤테이팅 웹훅이 5개 있고 리소스 50개를 배포하면 수정된 리소스의 이전 버전을 제거하기 위해 5분마다 컴팩션이 실행될 때까지 etcd는 각 리소스의 모든 버전을 저장합니다. 이 시나리오에서 etcd가 대체된 리소스를 제거하면 etcd에서 200개의 리소스 버전이 제거되며 리소스 크기에 따라 15분마다 조각 모음이 실행될 때까지 etcd 호스트에서 상당한 공간을 사용할 수 있습니다.

이런 조각 모음(defragmentation)으로 인해 etcd가 일시 중지되어 쿠버네티스 API 및 컨트롤러에 다른 영향을 미칠 수 있습니다. 대규모 리소스를 자주 수정하거나 수백 개의 리소스를 순식간에 연속해서 수정하는 것은 피해야 합니다.
