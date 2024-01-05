# 쿠버네티스 컨트롤 플레인

Kubernetes 컨트롤 플레인은 Kubernetes API Server, Kubernetes Controller Manager, Scheduler 및 Kubernetes가 작동하는 데 필요한 기타 구성 요소로 구성됩니다. 이러한 구성 요소의 확장성 제한은 클러스터에서 실행 중인 항목에 따라 다르지만 확장에 가장 큰 영향을 미치는 영역에는 Kubernetes 버전, 사용률 및 개별 노드 확장이 포함됩니다.

## EKS 1.24 이상을 사용하세요

EKS 1.24에는 여러 가지 변경 사항이 도입되었으며 컨테이너 런타임을 docker 대신 [containerd](https://containerd.io/)로 전환했습니다. Containerd는 Kubernetes의 요구 사항에 긴밀하게 맞춰 컨테이너 런타임 기능을 제한하여 개별 노드 성능을 높여 클러스터 확장을 돕습니다. Containerd는 지원되는 모든 EKS 버전에서 사용할 수 있으며, 1.24 이전 버전에서 Containerd로 전환하려면 [`--container-runtime` bootstrap flag](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html#containerd-bootstrap) 를 사용하세요.

## 워크로드 및 노드 버스팅 제한

!!! Attention
    컨트롤 플레인에서 API 한도에 도달하지 않으려면 클러스터 크기를 한 번에 두 자릿수 비율로 늘리는 급격한 확장을 제한해야 합니다(예: 한 번에 1000개 노드에서 1100개 노드로 또는 4000개에서 4500개 포드로).

EKS 컨트롤 플레인은 클러스터가 성장함에 따라 자동으로 확장되지만 확장 속도에는 제한이 있습니다. EKS 클러스터를 처음 생성할 때 컨트롤 플레인은 즉시 수백 개의 노드 또는 수천 개의 포드로 확장될 수 없습니다. EKS의 스케일링 개선 방법에 대해 자세히 알아보려면 [이 블로그 게시물](https://aws.amazon.com/blogs/containers/amazon-eks-control-plane-auto-scaling-enhancements-improve-speed-by-4x/)을 참조하세요.

대규모 애플리케이션을 확장하려면 인프라가 완벽하게 준비되도록 조정해야 합니다(예: 로드 밸런서 워밍). 확장 속도를 제어하려면 애플리케이션에 적합한 측정 지표를 기반으로 확장하고 있는지 확인합니다. CPU 및 메모리 확장은 애플리케이션 제약 조건을 정확하게 예측하지 못할 수 있으며 Kubernetes HPA(Horizontal Pod Autoscaler)에서 사용자 지정 지표(예: 초당 요청)를 사용하는 것이 더 나은 확장 옵션일 수 있습니다.

사용자 정의 지표를 사용하려면 [Kubernetes 문서](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/#autoscaling-on-multiple-metrics-and-custom-metrics)의 예를 참조하세요. 고급 확장이 필요하거나 외부 소스(예: AWS SQS 대기열)를 기반으로 확장해야 하는 경우 이벤트 기반 워크로드 확장을 위해 [KEDA](https://keda.sh)를 사용하세요.

## 노드와 포드를 안전하게 축소

### 장기 실행 인스턴스 교체

정기적으로 노드를 교체하면 구성 드리프트와 가동 시간이 연장된 후에만 발생하는 문제(예: 느린 메모리 누수)를 방지하여 클러스터를 건강한 상태로 유지할 수 있습니다. 자동 교체는 노드 업그레이드 및 보안 패치에 대한 좋은 프로세스와 사례를 제공합니다. 클러스터의 모든 노드가 정기적으로 교체되면 지속적인 유지 관리를 위해 별도의 프로세스를 유지하는 데 필요한 노력이 줄어듭니다.

Karpenter의 [Time To Live (TTL)](https://aws.github.io/aws-eks-best-practices/karpenter/#use-timers-ttl-to-automatically-delete-nodes-from-the-cluster) 설정을 통해 지정된 시간 동안 인스턴스가 실행된 후 인스턴스를 교체할 수 있습니다. 자체 관리형 노드 그룹은 `max-instance-lifetime` 설정을 사용하여 노드를 자동으로 교체할 수 있습니다. 관리형 노드 그룹에는 현재 이 기능이 없지만 [여기 GitHub에서](https://github.com/aws/containers-roadmap/issues/1190) 요청을 확인할 수 있습니다.

### 활용도가 낮은 노드 제거

[`--scale-down-utilization-threshold`](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-does-scale-down-work)를 통해 Kubernetes Cluster Autoscaler의 축소 임계값을 사용하여 실행 중인 워크로드가 없을 때 노드를 제거할 수 있습니다. 또는 Karpenter에서 `ttlSecondsAfterEmpty` 프로비저너 설정을 활용용할 수 있습니다.

### Pod Distruption Budgets 및 안전한 노드 셧다운 사용

Kubernetes 클러스터에서 파드와 노드를 제거하려면 컨트롤러가 여러 리소스(예: EndpointSlices)를 업데이트해야 합니다. 이 작업을 자주 또는 너무 빠르게 수행하면 변경 사항이 컨트롤러에 전파되면서 API Server 쓰로틀링 및 애플리케이션 중단이 발생할 수 있습니다. [Pod Distruption Budgets](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)은 클러스터에서 노드가 제거되거나 스케줄이 조정될 때 변동 속도를 늦추어 워크로드 가용성을 보호하는 모범 사례입니다.

## Kubectl 실행 시 클라이언트측 캐시 사용

kubectl 명령을 비효율적으로 사용하면 Kubernetes API Server에 추가 로드가 발생될 수 있습니다. kubectl을 반복적으로(예: for 루프에서) 사용하는 스크립트나 자동화를 실행하거나 로컬 캐시 없이 명령을 실행하는 것을 피해야 합니다.

`kubectl`에는 필요한 API 호출 양을 줄이기 위해 클러스터에서 검색 정보를 캐시하는 클라이언트 측 캐시가 있습니다. 캐시는 기본적으로 활성화되어 있으며 10분마다 새로 고쳐집니다.

컨테이너에서 또는 클라이언트 측 캐시 없이 kubectl을 실행하는 경우 API 쓰로틀링 문제가 발생할 수 있습니다. 불필요한 API 호출을 피하기 위해 `--cache-dir`을 마운트하여 클러스터 캐시를 유지하는 것이 좋습니다.

## kubectl Compression 비활성화

kubeconfig 파일에서 kubectl compression을 비활성화하면 API 및 클라이언트 CPU 사용량을 줄일 수 있습니다. 기본적으로 서버는 클라이언트로 전송된 데이터를 압축하여 네트워크 대역폭을 최적화합니다. 이렇게 하면 요청마다 클라이언트와 서버에 CPU 부하가 가중되며, 대역폭이 충분하다면 압축을 비활성화하면 오버헤드와 지연 시간을 줄일 수 있습니다. 압축을 비활성화하려면 kubeconfig 파일에서 `--disable-compression=true` 플래그를 사용하거나 `disable-compression: true`로 설정하면 됩니다.

```
apiVersion: v1
clusters:
- cluster:
    server: serverURL
    disable-compression: true
  name: cluster
```

## Cluster Autoscaler 샤딩

[Kubernetes Cluster Autoscaler는 테스트를 거쳤습니다](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/proposals/scalability_tests.md). 최대 1,000개 노드까지 확장할 수 있습니다. 1000개 이상의 노드가 있는 대규모 클러스터에서는 Cluster AutoScaler를 여러 인스턴스에 샤드 모드로 실행하는 것이 좋습니다. 각 클러스터 오토스케일러 인스턴스는 노드 그룹 세트를 확장하도록 구성되어 있습니다. 다음 예는 각 4개의 노드 그룹에 구성된 2개의 클러스터 오토 스케일링 구성을 보여줍니다.

ClusterAutoscaler-1

```
autoscalingGroups:
- name: eks-core-node-grp-20220823190924690000000011-80c1660e-030d-476d-cb0d-d04d585a8fcb
  maxSize: 50
  minSize: 2
- name: eks-data_m1-20220824130553925600000011-5ec167fa-ca93-8ca4-53a5-003e1ed8d306
  maxSize: 450
  minSize: 2
- name: eks-data_m2-20220824130733258600000015-aac167fb-8bf7-429d-d032-e195af4e25f5
  maxSize: 450
  minSize: 2
- name: eks-data_m3-20220824130553914900000003-18c167fa-ca7f-23c9-0fea-f9edefbda002
  maxSize: 450
  minSize: 2
```

ClusterAutoscaler-2

```
autoscalingGroups:
- name: eks-data_m4-2022082413055392550000000f-5ec167fa-ca86-6b83-ae9d-1e07ade3e7c4
  maxSize: 450
  minSize: 2
- name: eks-data_m5-20220824130744542100000017-02c167fb-a1f7-3d9e-a583-43b4975c050c
  maxSize: 450
  minSize: 2
- name: eks-data_m6-2022082413055392430000000d-9cc167fa-ca94-132a-04ad-e43166cef41f
  maxSize: 450
  minSize: 2
- name: eks-data_m7-20220824130553921000000009-96c167fa-ca91-d767-0427-91c879ddf5af
  maxSize: 450
  minSize: 2
```

## API Priority and Fairness

![](../images/APF.jpg)

### Overview

<iframe width="560" height="315" src="https://www.youtube.com/embed/YnPPHBawhE0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

요청이 증가하는 기간 동안 과부하가 발생하지 않도록 보호하기 위해 API 서버는 특정 시간에 처리할 수 있는 진행 중인 요청 수를 제한합니다. 이 제한을 초과하면 API 서버는 요청을 거부하기 시작하고 "Too many requests"에 대한 429 HTTP 응답 코드를 클라이언트에 반환합니다. 서버가 요청을 삭제하고 클라이언트가 나중에 다시 시도하도록 하는 것이 요청 수에 대한 서버 측 제한을 두지 않고 컨트롤 플레인에 과부하를 주어 성능이 저하되거나 가용성이 저하될 수 있는 것보다 더 좋습니다.

이러한 진행 중인 요청이 다양한 요청 유형으로 나누어지는 방식을 구성하기 위해 Kubernetes에서 사용하는 메커니즘을 [API Priority and Fairness](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/)이라고 합니다. API 서버는 `--max-requests-inflight` 및 `--max-mutating-requests-inflight` 플래그로 지정된 값을 합산하여 허용할 수 있는 총 진행 중인 요청 수를 구성합니다. EKS는 이러한 플래그에 대해 기본값인 400개 및 200개 요청을 사용하므로 주어진 시간에 총 600개의 요청을 전달할 수 있습니다. APF는 이러한 600개의 요청을 다양한 요청 유형으로 나누는 방법을 지정합니다. EKS 컨트롤 플레인은 각 클러스터에 최소 2개의 API 서버가 등록되어 있어 가용성이 높습니다. 이렇게 하면 클러스터 전체의 총 진행 중인 요청 수가 1200개로 늘어납니다.

PriorityLevelConfigurations 및 FlowSchemas라는 두 종류의 Kubernetes 객체는 총 요청 수가 다양한 요청 유형 간에 분할되는 방식을 구성합니다. 이러한 객체는 API 서버에 의해 자동으로 유지 관리되며 EKS는 지정된 Kubernetes 마이너 버전에 대해 이러한 객체의 기본 구성을 사용합니다. PriorityLevelConfigurations는 허용된 총 요청 수의 일부를 나타냅니다. 예를 들어 워크로드가 높은 PriorityLevelConfiguration에는 총 600개의 요청 중 98개가 할당됩니다. 모든 PriorityLevelConfigurations에 할당된 요청의 합계는 600입니다(또는 특정 수준이 요청의 일부만 허용된 경우 API Server가 반올림하므로 600보다 약간 높음). 클러스터의 PriorityLevelConfigurations와 각각에 할당된 요청 수를 확인하려면 다음 명령을 실행할 수 있습니다. EKS 1.24의 기본값은 다음과 같습니다.

```
$ kubectl get --raw /metrics | grep apiserver_flowcontrol_request_concurrency_limit
apiserver_flowcontrol_request_concurrency_limit{priority_level="catch-all"} 13
apiserver_flowcontrol_request_concurrency_limit{priority_level="global-default"} 49
apiserver_flowcontrol_request_concurrency_limit{priority_level="leader-election"} 25
apiserver_flowcontrol_request_concurrency_limit{priority_level="node-high"} 98
apiserver_flowcontrol_request_concurrency_limit{priority_level="system"} 74
apiserver_flowcontrol_request_concurrency_limit{priority_level="workload-high"} 98
apiserver_flowcontrol_request_concurrency_limit{priority_level="workload-low"} 245
```

두 번째 유형의 객체는 FlowSchemas입니다. 특정 속성 세트가 포함된 API 서버 요청은 동일한 FlowSchema로 분류됩니다. 이러한 속성에는 인증된 사용자나 API Group, 네임스페이스 또는 리소스와 같은 요청의 속성이 포함됩니다. FlowSchema는 또한 이 유형의 요청이 매핑되어야 하는 PriorityLevelConfiguration을 지정합니다. 두 개체는 함께 "이 유형의 요청이 이 inflight 요청 비율에 포함되기를 원합니다."라고 말합니다. 요청이 API Server에 도달하면 모든 필수 속성과 일치하는 FlowSchemas를 찾을 때까지 각 FlowSchemas를 확인합니다. 여러 FlowSchemas가 요청과 일치하는 경우 API Server는 개체의 속성으로 지정된 일치 우선 순위가 가장 작은 FlowSchema를 선택합니다.

FlowSchemas와 PriorityLevelConfigurations의 매핑은 다음 명령을 사용하여 볼 수 있습니다.

```
$ kubectl get flowschemas
NAME                           PRIORITYLEVEL     MATCHINGPRECEDENCE   DISTINGUISHERMETHOD   AGE     MISSINGPL
exempt                         exempt            1                    <none>                7h19m   False
eks-exempt                     exempt            2                    <none>                7h19m   False
probes                         exempt            2                    <none>                7h19m   False
system-leader-election         leader-election   100                  ByUser                7h19m   False
endpoint-controller            workload-high     150                  ByUser                7h19m   False
workload-leader-election       leader-election   200                  ByUser                7h19m   False
system-node-high               node-high         400                  ByUser                7h19m   False
system-nodes                   system            500                  ByUser                7h19m   False
kube-controller-manager        workload-high     800                  ByNamespace           7h19m   False
kube-scheduler                 workload-high     800                  ByNamespace           7h19m   False
kube-system-service-accounts   workload-high     900                  ByNamespace           7h19m   False
eks-workload-high              workload-high     1000                 ByUser                7h14m   False
service-accounts               workload-low      9000                 ByUser                7h19m   False
global-default                 global-default    9900                 ByUser                7h19m   False
catch-all                      catch-all         10000                ByUser                7h19m   False
```

PriorityLevelConfigurations에는 Queue, Reject 또는 Exempt 유형이 있을 수 있습니다. Queue 및 Reject 유형의 경우 해당 우선순위 수준에 대한 최대 진행 중인 요청 수에 제한이 적용되지만 해당 제한에 도달하면 동작이 달라집니다. 예를 들어 워크로드가 높은 PriorityLevelConfiguration은 Queue 유형을 사용하며 컨트롤러 매니저, 엔드포인트 컨트롤러, 스케줄러 및 kube-system 네임스페이스에서 실행되는 파드에서 사용할 수 있는 요청이 98개 있습니다. Queue 유형이 사용되므로 API Server는 요청을 메모리에 유지하려고 시도하며 이러한 요청이 시간 초과되기 전에 진행 중인 요청 수가 98개 미만으로 떨어지기를 희망합니다. 특정 요청이 대기열에서 시간 초과되거나 너무 많은 요청이 이미 대기열에 있는 경우 API Server는 요청을 삭제하고 클라이언트에 429를 반환할 수밖에 없습니다. 대기열에 있으면 요청이 429를 수신하지 못할 수 있지만 요청의 종단 간 지연 시간이 늘어나는 단점이 있습니다.

이제 Reject 유형을 사용하여 포괄적인 PriorityLevelConfiguration에 매핑되는 포괄적인 FlowSchema를 살펴보겠습니다. 클라이언트가 13개의 진행 중인 요청 제한에 도달하면 API Server는 대기열을 실행하지 않고 429 응답 코드를 사용하여 요청을 즉시 삭제합니다. 마지막으로 Exempt 유형을 사용하여 PriorityLevelConfiguration에 매핑하는 요청은 429를 수신하지 않으며 항상 즉시 전달됩니다. 이는 healthz 요청이나 system:masters 그룹에서 오는 요청과 같은 우선순위가 높은 요청에 사용됩니다. 

### APF 및 삭제된 요청 모니터링

APF로 인해 삭제된 요청이 있는지 확인하려면 `apiserver_flowcontrol_rejected_requests_total`에 대한 API Server 지표를 모니터링하여 영향을 받은 FlowSchemas 및 PriorityLevelConfigurations를 확인할 수 있습니다. 예를 들어 이 지표는 워크로드가 낮은 대기열의 요청 시간 초과로 인해 service account FlowSchema의 요청 100개가 삭제되었음을 보여줍니다.

```
% kubectl get --raw /metrics | grep apiserver_flowcontrol_rejected_requests_total
apiserver_flowcontrol_rejected_requests_total{flow_schema="service-accounts",priority_level="workload-low",reason="time-out"} 100
```

지정된 PriorityLevelConfiguration이 429를 수신하거나 큐로 인해 지연 시간이 증가하는 정도를 확인하려면 동시성 제한과 사용 중인 동시성의 차이를 비교할 수 있습니다. 이 예에는 100개의 요청 버퍼가 있습니다.

```
% kubectl get --raw /metrics | grep 'apiserver_flowcontrol_request_concurrency_limit.*workload-low'
apiserver_flowcontrol_request_concurrency_limit{priority_level="workload-low"} 245

% kubectl get --raw /metrics | grep 'apiserver_flowcontrol_request_concurrency_in_use.*workload-low'
apiserver_flowcontrol_request_concurrency_in_use{flow_schema="service-accounts",priority_level="workload-low"} 145
```

특정 PriorityLevelConfiguration에서 대기열이 발생하지만 반드시 요청이 삭제되는 것은 아닌지 확인하려면 `apiserver_flowcontrol_current_inqueue_requests`에 대한 측정 지표를 참조할 수 있습니다.

```
% kubectl get --raw /metrics | grep 'apiserver_flowcontrol_current_inqueue_requests.*workload-low'
apiserver_flowcontrol_current_inqueue_requests{flow_schema="service-accounts",priority_level="workload-low"} 10
```

기타 유용한 Prometheus 측정항목은 다음과 같습니다:

- apiserver_flowcontrol_dispatched_requests_total
- apiserver_flowcontrol_request_execution_seconds
- apiserver_flowcontrol_request_wait_duration_seconds

[APF 지표](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/#observability)의 전체 목록은 업스트림 문서를 참조하세요.

### 삭제된 요청 방지

#### 워크로드를 변경하여 429를 방지

APF가 허용된 최대 내부 요청 수를 초과하는 지정된 PriorityLevelConfiguration으로 인해 요청을 삭제하는 경우 영향을 받는 FlowSchemas의 클라이언트는 지정된 시간에 실행되는 요청 수를 줄일 수 있습니다. 이는 429가 발생하는 기간 동안 이루어진 총 요청 수를 줄임으로써 달성할 수 있습니다. 비용이 많이 드는 목록 호출과 같은 장기 실행 요청은 실행되는 전체 기간 동안 진행 중인 요청으로 계산되기 때문에 특히 문제가 됩니다. 비용이 많이 드는 요청 수를 줄이거나 목록 호출의 대기 시간을 최적화하면(예: 요청 당 가져오는 객체 수를 줄이거나 watch 요청을 사용하도록 전환) 해당 워크로드에 필요한 총 동시성을 줄이는 데 도움이 될 수 있습니다.

#### APF 설정을 변경하여 429를 방지

!!! 경고
     수행 중인 작업을 알고 있는 경우에만 기본 APF 설정을 변경하십시오. APF 설정이 잘못 구성되면 API Server 요청이 중단되고 워크로드가 크게 중단될 수 있습니다.

요청 삭제를 방지하기 위한 또 다른 접근 방식은 EKS 클러스터에 설치된 기본 FlowSchemas 또는 PriorityLevelConfigurations를 변경하는 것입니다. EKS는 지정된 Kubernetes 마이너 버전에 대한 FlowSchemas 및 PriorityLevelConfigurations의 업스트림 기본 설정을 설치합니다. API는 객체에 대한 다음 주석이 false로 설정되지 않은 한 이러한 객체를 기본값으로 자동으로 다시 조정합니다.

```
  metadata:
    annotations:
      apf.kubernetes.io/autoupdate-spec: "false"
```

높은 수준에서 APF 설정은 다음 중 하나로 수정될 수 있습니다.

- 관심 있는 요청에 더 많은 기내 수용 능력을 할당하세요.
- 다른 요청 유형에 대한 용량이 부족할 수 있는 비필수적이거나 비용이 많이 드는 요청을 격리합니다.

이는 기본 FlowSchemas 및 PriorityLevelConfigurations를 변경하거나 이러한 유형의 새 개체를 생성하여 수행할 수 있습니다. 관리자는 관련 PriorityLevelConfigurations 개체에 대한 authenticateConcurrencyShares 값을 늘려 할당되는 진행 중 요청 비율을 늘릴 수 있습니다. 또한 요청이 발송되기 전에 대기열에 추가되어 발생하는 추가 대기 시간을 애플리케이션에서 처리할 수 있는 경우 특정 시간에 대기열에 추가할 수 있는 요청 수도 늘어날 수 있습니다.

또는 고객의 워크로드에 맞는 새로운 FlowSchema 및 PriorityLevelConfigurations 개체를 생성할 수 있습니다. 기존 PriorityLevelConfigurations 또는 새로운 PriorityLevelConfigurations에 더 많은 secureConcurrencyShares를 할당하면 전체 한도가 API Server 당 600개로 유지되므로 다른 버킷에서 처리할 수 있는 요청 수가 줄어듭니다.

APF 기본값을 변경할 때 설정 변경으로 인해 의도하지 않은 429가 발생하지 않도록 비프로덕션 클러스터에서 이러한 측정항목을 모니터링해야 합니다.

1. 버킷이 요청 삭제를 시작하지 않도록 모든 FlowSchemas에 대해 `apiserver_flowcontrol_rejected_requests_total`에 대한 측정 지표를 모니터링해야 합니다.
2. `apiserver_flowcontrol_request_concurrency_limit` 및 `apiserver_flowcontrol_request_concurrency_in_use` 값을 비교하여 사용 중인 동시성이 해당 우선순위 수준의 제한을 위반할 위험이 없는지 확인해야 합니다.

새로운 FlowSchema 및 PriorityLevelConfiguration을 정의하는 일반적인 사용 사례 중 하나는 격리입니다. 파드에서 장기 실행 목록 이벤트 호출을 자체 요청 공유로 분리한다고 가정해 보겠습니다. 이렇게 하면 기존 서비스 계정 FlowSchema를 사용하는 파드의 중요한 요청이 429를 수신하여 요청 용량이 부족해지는 것을 방지할 수 있습니다. 진행 중인 요청의 총 개수는 유한하지만 이 예에서는 APF 설정을 수정하여 지정된 워크로드에 대한 요청 용량을 더 잘 나눌 수 있음을 보여줍니다.

List 이벤트 요청을 분리하기 위한 FlowSchema 객체의 예:

```
apiVersion: flowcontrol.apiserver.k8s.io/v1beta1
kind: FlowSchema
metadata:
  name: list-events-default-service-accounts
spec:
  distinguisherMethod:
    type: ByUser
  matchingPrecedence: 8000
  priorityLevelConfiguration:
    name: catch-all
  rules:
  - resourceRules:
    - apiGroups:
      - '*'
      namespaces:
      - default
      resources:
      - events
      verbs:
      - list
    subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: default
        namespace: default
```

- 이 FlowSchema는 기본 네임스페이스의 Service Account에서 수행된 모든 List 이벤트 호출을 캡처합니다.
- 일치 우선 순위 8000은 기존 Service Account FlowSchema에서 사용하는 값 9000보다 낮으므로 이러한 List 이벤트 호출은 Service Account가 아닌 list-events-default-service-account와 일치합니다.
- 이러한 요청을 격리하기 위해 포괄적인 PriorityLevelConfiguration을 사용하고 있습니다. 이 버킷은 장기 실행되는 list 이벤트 호출에서 13개의 진행 중인 요청만 사용할 수 있도록 허용합니다. 파드는 동시에 13개 이상의 요청을 발행하려고 시도하지만 즉시 429를 응답받기 시작합니다.

## API Server에서 리소스 검색

API Server에서 정보를 가져오는 것은 모든 규모의 클러스터에서 예상되는 동작입니다. 클러스터의 리소스 수를 확장하면 요청 빈도와 데이터 볼륨이 빠르게 컨트롤 플레인의 병목 현상이 되어 API 쓰로틀링 및 속도 저하로 이어질 수 있습니다. 지연 시간의 심각도에 따라 주의하지 않으면 예상치 못한 다운타임이 발생할 수 있습니다.

이러한 유형의 문제를 방지하기 위한 첫 번째 단계는 무엇을 요청하고 얼마나 자주 요청하는지 파악하는 것입니다. 다음은 규모 조정 모범 사례에 따라 쿼리 양을 제한하는 지침입니다. 이 섹션의 제안 사항은 확장성이 가장 좋은 것으로 알려진 옵션부터 순서대로 제공됩니다.

### Shared Informers 사용

Kubernetes API와 통합되는 컨트롤러 및 자동화를 구축할 때 Kubernetes 리소스에서 정보를 가져와야 하는 경우가 많습니다. 이러한 리소스를 정기적으로 폴링하면 API Server에 상당한 부하가 발생할 수 있습니다.

client-go 라이브러리의 [informer](https://pkg.go.dev/k8s.io/client-go/informers) 를 사용하면 변경 사항을 폴링하는 대신 이벤트를 기반으로 리소스의 변경 사항을 관찰할 수 있다는 이점이 있습니다. Shared Informer는 이벤트 및 변경 사항에 공유 캐시를 사용하여 부하를 더욱 줄이므로 동일한 리소스를 감시하는 여러 컨트롤러로 인해 추가 부하가 가중되지 않습니다.

컨트롤러는 특히 대규모 클러스터의 경우 label 및 field selectors 없이 클러스터 전체 리소스를 폴링하지 않아야 합니다. 필터링되지 않은 각 폴링에는 클라이언트가 필터링하기 위해 etcd에서 API Server를 통해 많은 양의 불필요한 데이터를 전송해야 합니다. 레이블과 네임스페이스를 기반으로 필터링하면 API 서버가 요청을 처리하고 클라이언트에 전송되는 데이터를 처리하기 위해 수행해야 하는 작업량을 줄일 수 있습니다.

### Kubernetes API 사용 최적화

사용자 정의 컨트롤러 또는 자동화를 사용하여 Kubernetes API를 호출할 때 필요한 리소스로만 호출을 제한하는 것이 중요합니다. 제한이 없으면 API Server 및 etcd에 불필요한 로드가 발생할 수 있습니다.

가능하면 watch 인자를 사용하는 것이 좋습니다. 인자가 없으면 기본 동작은 객체를 나열하는 것입니다. list 대신 watch를 사용하려면 API 요청 끝에 `?watch=true`를 추가하면 됩니다. 예를 들어 watch를 사용하여 기본 네임스페이스의 모든 파드를 가져오려면 다음을 사용하세요.

```
/api/v1/namespaces/default/pods?watch=true
```

객체를 나열하는 경우 나열하는 항목의 범위와 반환되는 데이터의 양을 제한해야 합니다. 요청에 `limit=500` 인수를 추가하여 반환되는 데이터를 제한할 수 있습니다. `fieldSelector` 인수와 `/namespace/` 경로는 목록의 범위를 필요에 따라 좁게 지정하는 데 유용할 수 있습니다. 예를 들어 기본 네임스페이스에서 실행 중인 파드만 나열하려면 다음 API 경로와 인수를 사용합니다.

```
/api/v1/namespaces/default/pods?fieldSelector=status.phase=Running&limit=500
```

또는 다음을 사용하여 실행 중인 모든 파드를 나열합니다.

```
/api/v1/pods?fieldSelector=status.phase=Running&limit=500
```

나열된 오브젝트를 제한하는 또 다른 옵션은 [`ResourceVersions` (쿠버네티스 설명서 참조)](https://kubernetes.io/docs/reference/using-api/api-concepts/#resource-versions)를 사용하는 것 입니다. `ResourceVersion` 인자가 없으면 사용 가능한 최신 버전을 받게 되며, 이 경우 데이터베이스에서 가장 비용이 많이 들고 가장 느린 etcd 쿼럼 읽기가 필요합니다. resourceVersion은 쿼리하려는 리소스에 따라 달라지며, `Metadata.Resourceversion` 필드에서 찾을 수 있습니다.

API Server 캐시에서 결과를 반환하는 특별한 `ResourceVersion=0`이 있습니다. 이렇게 하면 etcd 부하를 줄일 수 있지만 Pagination은 지원하지 않습니다.

```
/api/v1/namespaces/default/pods?resourceVersion=0
```

인자 없이 API를 호출하면 API Server 및 etcd에서 리소스를 가장 많이 사용하게 됩니다.이 호출을 사용하면 Pagination이나 범위 제한 없이 모든 네임스페이스의 모든 파드를 가져오고 etcd에서 쿼럼을 읽어야 합니다.

```
/api/v1/pods
```
