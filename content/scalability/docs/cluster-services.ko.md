---
search:
  exclude: true
---


# 클러스터 서비스

클러스터 서비스는 EKS 클러스터 내에서 실행되지만 사용자 워크로드는 아닙니다. 리눅스 서버를 사용하는 경우 워크로드를 지원하기 위해 NTP, syslog 및 컨테이너 런타임과 같은 서비스를 실행해야 하는 경우가 많습니다. 클러스터 서비스도 비슷하며 클러스터를 자동화하고 운영하는 데 도움이 되는 서비스를 지원합니다. 쿠버네티스에서 이들은 일반적으로 kube-system 네임스페이스에서 실행되고 일부는 [데몬셋](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)로 실행됩니다.

클러스터 서비스는 가동 시간이 길어질 것으로 예상되며 정전 및 문제 해결에 중요한 역할을 하는 경우가 많습니다. 코어 클러스터 서비스를 사용할 수 없는 경우 장애 복구 또는 예방에 도움이 되는 데이터 (예: 높은 디스크 사용률)에 액세스할 수 없게 될 수 있습니다. 별도의 노드 그룹 또는 AWS Fargate와 같은 전용 컴퓨팅 인스턴스에서 실행해야 합니다. 이렇게 하면 규모가 커지거나 리소스를 더 많이 사용하는 워크로드가 공유 인스턴스에 미치는 영향을 클러스터 서비스가 받지 않도록 할 수 있습니다.

## CoreDNS 스케일링

CoreDNS 스케일링에는 두 가지 기본 메커니즘이 있습니다. CoreDNS 서비스에 대한 호출 수를 줄이고 복제본 수를 늘립니다.

### ndot을 줄여 외부 쿼리를 줄입니다.

ndots 설정은 DNS 쿼리를 피하기에 충분하다고 간주되는 도메인 이름의 마침표 (일명 "점") 수를 지정합니다. 애플리케이션의 ndots 설정이 5 (기본값) 이고 api.example.com (점 2개) 과 같은 외부 도메인에서 리소스를 요청하는 경우 /etc/resolv.conf에 정의된 각 검색 도메인에 대해 CoreDNS가 쿼리되어 더 구체적인 도메인이 검색됩니다. 기본적으로 외부 요청을 하기 전에 다음 도메인이 검색됩니다.

```
api.example.<namespace>.svc.cluster.local
api.example.svc.cluster.local
api.example.cluster.local
api.example.<region>.compute.internal
```

`namespace` 및 `region` 값은 워크로드 네임스페이스 및 컴퓨팅 지역으로 대체됩니다. 클러스터 설정에 따라 추가 검색 도메인이 있을 수 있습니다.

워크로드의 [ndots 옵션 낮추기](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-dns-config) 또는 후행 항목을 포함하여 도메인 요청을 완전히 검증하여 CoreDNS에 대한 요청 수를 줄일 수 있습니다.(예: `api.example.com.`). 워크로드가 DNS를 통해 외부 서비스에 연결하는 경우 워크로드가 불필요하게 클러스터 내에서 DNS 쿼리를 클러스터링하지 않도록 ndots를 2로 설정하는 것이 좋습니다. 워크로드에 클러스터 내부 서비스에 대한 액세스가 필요하지 않은 경우 다른 DNS 서버 및 검색 도메인을 설정할 수 있습니다.

```
spec:
  dnsPolicy: "None"
  dnsConfig:
    options:
      - name: ndots
        value: "2"
      - name: edns0
```

ndots를 너무 낮은 값으로 낮추거나 연결하려는 도메인의 구체성이 충분하지 않은 경우 (후행 포함) DNS 조회가 실패할 수 있습니다.이 설정이 워크로드에 어떤 영향을 미칠지 테스트해야 합니다.

### CoreDNS 수평 스케일링

CoreDNS 인스턴스는 배포에 복제본을 추가하여 확장할 수 있습니다. CoreDNS를 확장하려면 [NodeLocal DNS](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) 또는 [cluster proportional autoscaler](https://github.com/kubernetes-sigs/cluster-proportional-autoscaler)를 사용하는 것이 좋습니다.

NodeLocal DNS는 노드당 하나의 인스턴스를 데몬셋으로 실행해야 하며, 이를 위해서는 클러스터에 더 많은 컴퓨팅 리소스가 필요하지만 DNS 요청 실패를 방지하고 클러스터의 DNS 쿼리에 대한 응답 시간을 줄입니다. Cluster propertional autoscaler는 클러스터의 노드 또는 코어 수에 따라 CoreDNS의 크기를 조정합니다. 이는 쿼리 요청과 직접적인 상관 관계는 아니지만 워크로드 및 클러스터 크기에 따라 유용할 수 있습니다. 기본 비례 척도는 클러스터의 256개 코어 또는 16개 노드마다 추가 복제본을 추가하는 것입니다(둘 중 먼저 발생하는 기준).

## 쿠버네티스 Metric Server 수직 확장

쿠버네티스 Metric Server는 수평 및 수직 확장을 지원합니다. Metric Server를 수평적으로 확장하면 가용성은 높아지지만 더 많은 클러스터 메트릭을 처리할 수 있을 만큼 수평적으로 확장되지는 않습니다. 노드와 수집된 지표가 클러스터에 추가됨에 따라 [권장 사항](https://kubernetes-sigs.github.io/metrics-server/#scaling)에 따라 메트릭 서버를 수직으로 확장해야 합니다.

Metric Server는 수집, 집계 및 제공하는 데이터를 메모리에 보관합니다. 클러스터가 커지면 Metric Server가 저장하는 데이터 양도 늘어납니다. 대규모 클러스터에서 Metric Server는 기본 설치에 지정된 메모리 및 CPU 예약량보다 더 많은 컴퓨팅 리소스를 필요로 합니다.[Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)(VPA) 또는 [Addon Resizer](https://github.com/kubernetes/autoscaler/tree/master/addon-resizer)를 사용하여 Metric Server를 확장할 수 있습니다. Addon Resizer는 Worker 노드에 비례하여 수직으로 확장되고 VPA는 CPU 및 메모리 사용량에 따라 조정됩니다.

## CoreDNS lameduck 지속 시간

파드는 이름 확인을 위해 `kube-dns` 서비스를 사용합니다. 쿠버네티스는 Destination NAT (DNAT) 를 사용하여 노드에서 CoreDNS 백엔드 파드로 `kube-dns` 트래픽을 리디렉션합니다. CoreDNS Deployment를 확장하면, `kube-proxy`는 노드의 iptables 규칙 및 체인을 업데이트하여 DNS 트래픽을 CoreDNS 파드로 리디렉션합니다. 확장 시 새 엔드포인트를 전파하고 축소할 때 규칙을 삭제하는데 클러스터 크기에 따라 CoreDNS를 삭제하는 데 1~10초 정도 걸릴 수 있습니다. 

이러한 전파 지연으로 인해 CoreDNS 파드가 종료되었지만 노드의 iptables 규칙이 업데이트되지 않은 경우 DNS 조회 오류가 발생할 수 있습니다. 이 시나리오에서 노드는 종료된 CoreDNS 파드에 DNS 쿼리를 계속 전송할 수 있다.

CoreDNS 파드에 [lameduck](https://coredns.io/plugins/health/) 기간을 설정하여 DNS 조회 실패를 줄일 수 있습니다. Lameduck 모드에 있는 동안 CoreDNS는 계속해서 진행 중인 요청에 응답합니다.Lameduck 기간을 설정하면 CoreDNS 종료 프로세스가 지연되어 노드가 iptables 규칙 및 체인을 업데이트하는 데 필요한 시간을 확보할 수 있습니다. 

CoreDNS lameduck 지속 시간을 30초로 설정하는 것이 좋습니다. 

## CoreDNS readiness 프로브

CoreDNS의 Readiness 프로브에는 `/health` 대신 `/ready`를 사용하는 것을 추천합니다.

Lameduck 지속 시간을 30초로 설정하라는 이전 권장 사항에 따라, 파드 종료 전에 노드의 iptables 규칙을 업데이트할 수 있는 충분한 시간을 제공합니다. CoreDNS 준비 상태 프로브에 `/health` 대신 `/ready'를 사용하면 시작 시 CoreDNS 파드가 DNS 요청에 즉시 응답할 수 있도록 완벽하게 준비됩니다.

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8181
    scheme: HTTP
```

CoreDNS Ready 플러그인에 대한 자세한 내용은 [https://coredns.io/plugins/ready/](https://coredns.io/plugins/ready/) 을 참조하십시오.

## 로깅 및 모니터링 에이전트

로깅 및 모니터링 에이전트는 API 서버를 쿼리하여 워크로드 메타데이터로 로그와 메트릭을 보강하므로 클러스터 컨트롤 플레인에 상당한 로드를 추가할 수 있습니다. 노드의 에이전트는 컨테이너 및 프로세스 이름과 같은 항목을 보기 위해 로컬 노드 리소스에만 액세스할 수 있습니다. API 서버를 쿼리하면 Kubernetes Deployment 이름 및 레이블과 같은 세부 정보를 추가할 수 있습니다. 이는 문제 해결에는 매우 유용하지만 확장에는 해로울 수 있습니다.

로깅 및 모니터링에 대한 옵션이 너무 다양하기 때문에 모든 공급자에 대한 예를 표시할 수는 없습니다. [fluentbit](https://docs.fluentbit.io/manual/pipeline/filters/kubernetes)를 사용하면 Use_Kubelet을 활성화하여 Kubernetes API 서버 대신 로컬 kubelet에서 메타데이터를 가져오고 `Kube_Meta_Cache_TTL`을 줄이는 숫자로 설정하는 것이 좋습니다. 데이터를 캐시할 수 있을 때 호출을 반복합니다(예: 60).

조정 모니터링 및 로깅에는 두 가지 일반 옵션이 있습니다.

* 통합 비활성화
* 샘플링 및 필터링

로그 메타데이터가 손실되므로 통합을 비활성화하는 것이 옵션이 아닌 경우가 많습니다. 이렇게 하면 API 확장 문제가 제거되지만 필요할 때 필요한 메타데이터가 없어 다른 문제가 발생합니다.

샘플링 및 필터링을 수행하면 수집되는 지표 및 로그 수가 줄어듭니다. 이렇게 하면 Kubernetes API에 대한 요청 양이 줄어들고 수집되는 지표 및 로그에 필요한 스토리지 양이 줄어듭니다. 스토리지 비용을 줄이면 전체 시스템 비용도 낮아집니다.

샘플링을 구성하는 기능은 에이전트 소프트웨어에 따라 다르며 다양한 수집 지점에서 구현될 수 있습니다. API 서버 호출이 발생할 가능성이 높기 때문에 에이전트에 최대한 가깝게 샘플링을 추가하는 것이 중요합니다. 샘플링 지원에 대해 자세히 알아보려면 공급자에게 문의하세요.

CloudWatch 및 CloudWatch Logs를 사용하는 경우 [문서에 설명된](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html) 패턴을 사용하여 에이전트 필터링을 추가할 수 있습니다.

로그 및 지표 손실을 방지하려면 수신 받는 엔드포인트에서 중단이 발생할 경우 데이터를 버퍼링할 수 있는 시스템으로 데이터를 보내야 합니다. Fluentbit를 사용하면 [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/pipeline/outputs/firehose)를 사용하여 데이터를 임시로 보관할 수 있으므로 최종 데이터 저장 위치에 과부하가 걸릴 가능성이 줄어듭니다.
