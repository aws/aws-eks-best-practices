---
search:
  exclude: true
---


# 쿠버네티스 업스트림 SLO

Amazon EKS는 업스트림 쿠버네티스 릴리스와 동일한 코드를 실행하고 EKS 클러스터가 쿠버네티스 커뮤니티에서 정의한 SLO 내에서 작동하도록 합니다. 쿠버네티스 [확장성 SIG](https://github.com/kubernetes/community/tree/master/sig-scalability)는 확장성 목표를 정의하고, 정의된 SLI(Service Level Indicator)와 SLO(Service Level Objective)를 통해 성능 병목 현상을 조사합니다. 

SLI는 시스템이 얼마나 “잘” 실행되고 있는지 판단하는 데 사용할 수 있는 메트릭이나 측정값과 같이 시스템을 측정하는 방법(예: 요청 지연 시간 또는 개수)입니다. SLO는 시스템이 '정상' 실행될 때 예상되는 값을 정의합니다. 예를 들어 요청 지연 시간이 3초 미만으로 유지됩니다. 쿠버네티스 SLO와 SLI는 쿠버네티스 구성 요소의 성능에 초점을 맞추고 EKS 클러스터 엔드포인트의 가용성에 초점을 맞춘 Amazon EKS 서비스 SLA와는 완전히 독립적입니다.

쿠버네티스는 사용자가 CSI 드라이버, 어드미션 웹훅, 자동 스케일러와 같은 커스텀 애드온 또는 드라이버로 시스템을 확장할 수 있는 많은 기능을 제공합니다. 이러한 확장은 다양한 방식으로 쿠버네티스 클러스터의 성능에 큰 영향을 미칠 수 있다. 예를 들어 `FailurePolicy=Ignore`가 포함된 어드미션 웹훅은 웹훅 타겟을 사용할 수 없는 경우 K8s API 요청에 지연 시간을 추가할 수 있다. 쿠버네티스 확장성 SIG는 ["you promise, we promise" 프레임워크](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md#how-we-define-scalability)를 사용하여 확장성을 정의합니다.


> 사용자가 다음과 같이 약속하는 경우 (`You promise`):  
>     - 클러스터를 올바르게 구성하세요  
>     - 확장성 기능을 “합리적으로” 사용  
>     - 클러스터의 부하를 [권장 리밋](https://github.com/kubernetes/community/blob/master/sig-scalability/configs-and-limits/thresholds.md) 이내로 유지  
> 
> 그러면 클러스터가 확장될 것을 약속합니다. (`We promise`):  
>     - 모든 SLO가 만족합니다.    

# 쿠버네티스 SLO
쿠버네티스 SLO는 워커 노드 스케일링이나 어드미션 웹훅과 같이 클러스터에 영향을 미칠 수 있는 모든 플러그인과 외부 제한을 고려하지 않습니다. 이러한 SLO는 [쿠버네티스 컴포넌트](https://kubernetes.io/docs/concepts/overview/components/)에 초점을 맞추고 쿠버네티스 액션과 리소스가 기대 범위 내에서 작동하도록 합니다. SLO는 쿠버네티스 개발자가 쿠버네티스 코드를 변경해도 전체 시스템의 성능이 저하되지 않도록 하는 데 도움이 됩니다.

[쿠버네티스 확장성 SIG는 다음과 같은 공식 SLO/SLI를 정의합니다](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md). Amazon EKS 팀은 이러한 SLO/SLI에 대해 EKS 클러스터에서 정기적으로 확장성 테스트를 실행하여 변경 및 새 버전 출시에 따른 성능 저하를 모니터링합니다.


|Objective	|Definition	|SLO	|
|---	|---	|---	|
|API request latency (mutating)	|모든 (리소스, 동사) 쌍의 단일 객체에 대한 변경 API 호출 처리 지연 (지난 5분 동안 백분위 99로 측정) |기본 Kubernetes 설치에서 모든 (리소스, 동사) 쌍에 대해 (가상 및 집계 리소스 정의 제외), 클러스터당 백분위 99 <= 1초 |
|API request latency (read-only)	|모든 (리소스, 범위) 쌍에 대한 비스트리밍 읽기 전용 API 호출 처리 대기 시간 (지난 5분 동안 백분위 99로 측정) |기본 Kubernetes 설치에서 모든 (리소스, 범위) 쌍에 대해 (가상 및 집계 리소스 및 사용자 지정 리소스 정의 제외), 클러스터당 백분위 99: (a) <= `scope=resource`인 경우 1초 (b) << = 30초 (`scope=namespace` 또는 `scope=cluster`인 경우) |
|Pod startup latency	| 예약 가능한 상태 비저장 파드의 시작 지연 시간 (이미지를 가져오고 초기화 컨테이너를 실행하는 데 걸리는 시간 제외), 파드 생성 타임스탬프부터 모든 컨테이너가 시작 및 시계를 통해 관찰된 것으로 보고되는 시점까지 측정 (지난 5분 동안 백분위 99로 측정) |기본 쿠버네티스 설치에서 클러스터당 백분위 99 <= 5초 |

<!-- |Objective	|Definition	|SLO	|
|---	|---	|---	|
|API request latency (mutating)	|Latency of processing mutating  API calls for single objects for every (resource, verb) pair, measured as 99th percentile over last 5 minutes	|In default Kubernetes installation, for every (resource, verb) pair, excluding virtual and aggregated resources and Custom Resource Definitions, 99th percentile per cluster-day <= 1s	|
|API request latency (read-only)	|Latency of processing non-streaming read-only API calls for every (resource, scope) pair, measured as 99th percentile over last 5 minutes	|In default Kubernetes installation, for every (resource, scope) pair, excluding virtual and aggregated resources and Custom Resource Definitions, 99th percentile per cluster-day: (a) <= 1s if `scope=resource` (b) <= 30s otherwise (if `scope=namespace` or `scope=cluster`)	|
|Pod startup latency	|Startup latency of schedulable stateless pods, excluding time to pull images and run init containers, measured from pod creation timestamp to when all its containers are reported as started and observed via watch, measured as 99th percentile over last 5 minutes	|In default Kubernetes installation, 99th percentile per cluster-day <= 5s	| -->

### API 요청 지연 시간 

`kube-apiserver`에는 기본적으로 `--request-timeout`이 `1m0s`로 정의되어 있습니다. 즉, 요청을 최대 1분 (60초) 동안 실행한 후 제한 시간을 초과하여 취소할 수 있습니다. 지연 시간에 대해 정의된 SLO는 실행 중인 요청 유형별로 구분되며, 변경되거나 읽기 전용일 수 있습니다.

#### 뮤테이팅 (Mutating)

쿠버네티스에서 요청을 변경하면 생성, 삭제 또는 업데이트와 같은 리소스가 변경됩니다. 이러한 요청은 업데이트된 오브젝트가 반환되기 전에 변경 사항을 [etcd 백엔드](https://kubernetes.io/docs/concepts/overview/components/#etcd)에 기록해야 하기 때문에 비용이 많이 든다. [Etcd](https://etcd.io/)는 모든 쿠버네티스 클러스터 데이터에 사용되는 분산 키-밸류 저장소입니다.

이 지연 시간은 쿠버네티스 리소스의 (resource, verb) 쌍에 대한 5분 이상의 99번째 백분위수로 측정됩니다. 예를 들어 이 지연 시간은 파드 생성 요청과 업데이트 노드 요청의 지연 시간을 측정합니다. SLO를 충족하려면 요청 지연 시간이 1초 미만이어야 합니다.

#### 읽기 전용 (read-only)

읽기 전용 요청은 단일 리소스 (예: Pod X 정보 가져오기) 또는 컬렉션 (예: “네임스페이스 X에서 모든 파드 정보 가져오기”) 을 검색한다. `kube-apiserver`는 오브젝트 캐시를 유지하므로 요청된 리소스가 캐시에서 반환될 수도 있고, 먼저 etcd에서 검색해야 할 수도 있다. 
이러한 지연 시간은 5분 동안의 99번째 백분위수로도 측정되지만, 읽기 전용 요청은 별도의 범위를 가질 수 있습니다.SLO는 두 가지 다른 목표를 정의합니다.

* *단일* 리소스(예: `kubectl get pod -n mynamespace my-controller-xxx`)에 대한 요청의 경우 요청 지연 시간은 1초 미만으로 유지되어야 합니다.
* 네임스페이스 또는 클러스터의 여러 리소스에 대해 요청한 경우 (예: `kubectl get pods -A`) 지연 시간은 30초 미만으로 유지되어야 합니다.

Kubernetes 리소스 목록에 대한 요청은 요청에 포함된 모든 오브젝트의 세부 정보가 SLO 내에 반환될 것으로 예상하기 때문에 SLO는 요청 범위에 따라 다른 목표 값을 가집니다. 대규모 클러스터 또는 대규모 리소스 컬렉션에서는 응답 크기가 커져 반환하는 데 다소 시간이 걸릴 수 있습니다. 예를 들어 수만 개의 파드를 실행하는 클러스터에서 JSON으로 인코딩할 때 각 파드가 대략 1KiB인 경우 클러스터의 모든 파드를 반환하는 데 10MB 이상이 된다. 쿠버네티스 클라이언트는 이러한 응답 크기를 줄이는 데 도움이 될 수 있다 [APIListChunking을 사용하여 대규모 리소스 컬렉션을 검색](https://kubernetes.io/docs/reference/using-api/api-concepts/#retrieving-large-results-sets-in-chunks). 

### 파드 시작 지연

이 SLO는 주로 파드 생성부터 해당 파드의 컨테이너가 실제로 실행을 시작할 때까지 걸리는 시간과 관련이 있다. 이를 측정하기 위해 파드에 기록된 생성 타임스탬프와 [파드 WATCH요청](https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes)에서 보고된 컨테이너가 시작된 시점 (컨테이너 이미지 풀링 및 초기화 컨테이너 실행 시간 제외)과의 차이를 계산합니다. SLO를 충족하려면 이 파드 시작 지연 시간의 클러스터 일당 99번째 백분위수를 5초 미만으로 유지해야 한다. 

참고로, 이 SLO에서는 워커 노드가 이 클러스터에 이미 존재하며 파드를 스케줄링할 준비가 된 상태인 것으로 가정한다. 이 SLO는 이미지 풀이나 초기화 컨테이너 실행을 고려하지 않으며, 영구 스토리지 플러그인을 활용하지 않는 “스테이트리스(stateless) 파드"로만 테스트를 제한한다. 

## 쿠버네티스 SLI 메트릭스 

또한 쿠버네티스는 시간이 지남에 따라 이러한 SLI를 추적하는 쿠버네티스 컴포넌트에 [프로메테우스 메트릭](https://prometheus.io/docs/concepts/data_model/)을 추가하여 SLI에 대한 옵저버빌리티를 개선하고 있습니다. [프로메테우스 쿼리 언어 (PromQL)](https://prometheus.io/docs/prometheus/latest/querying/basics/)를 사용하여 Prometheus 또는 Grafana 대시보드와 같은 도구에서 시간 경과에 따른 SLI 성능을 표시하는 쿼리를 작성할 수 있습니다. 아래는 위의 SLO에 대한 몇 가지 예입니다.

### API 서버 요청 레이턴시

|Metric	|Definition	|
|---	|---	|
|apiserver_request_sli_duration_seconds	| 각 verb, 그룹, 버전, 리소스, 하위 리소스, 범위 및 구성 요소에 대한 응답 지연 시간 분포 (웹훅 지속 시간, 우선 순위 및 공정성 대기열 대기 시간 제외)	|
|apiserver_request_duration_seconds	| 각 verb, 테스트 실행 값, 그룹, 버전, 리소스, 하위 리소스, 범위 및 구성 요소에 대한 응답 지연 시간 분포 (초)	|  

*참고: `apiserver_request_sli_duration_seconds` 메트릭은 쿠버네티스 1.27 버전부터 사용할 수 있다.*

이러한 메트릭을 사용하여 API 서버 응답 시간과 Kubernetes 구성 요소 또는 기타 플러그인/구성 요소에 병목 현상이 있는지 조사할 수 있습니다. 아래 쿼리는 [커뮤니티 SLO 대시보드](https://github.com/kubernetes/perf-tests/tree/master/clusterloader2/pkg/prometheus/manifests/dashboards)를 기반으로 합니다. 

**API 요청 레이턴시 SLI (mutating)** - 해당 시간은 웹훅 실행 또는 대기열 대기 시간을 포함*하지 않습니다*.   
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"CREATE|DELETE|PATCH|POST|PUT", subresource!~"proxy|attach|log|exec|portforward"}[5m])) by (resource, subresource, verb, scope, le)) > 0`

**API 요청 레이턴시 시간 합계 (mutating)** - API 서버에서 요청이 소요된 총 시간입니다. 이 시간은 웹훅 실행, API 우선 순위 및 공정성 대기 시간을 포함하므로 SLI 시간보다 길 수 있습니다.  
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"CREATE|DELETE|PATCH|POST|PUT", subresource!~"proxy|attach|log|exec|portforward"}[5m])) by (resource, subresource, verb, scope, le)) > 0`

이 쿼리에서는 `kubectl port-forward` 또는 `kubectl exec` 요청과 같이 즉시 반환되지 않는 스트리밍 API 요청을 제외합니다. (`subresource!~"proxy|attach|log|exec|portforward"`). 그리고 객체를 수정하는 쿠버네티스 verb에 대해서만 필터링하고 있습니다 (`verb=~"Create|Delete|Patch|Post|put"`).그런 다음 지난 5분 동안의 해당 지연 시간의 99번째 백분위수를 계산합니다.

읽기 전용 API 요청에도 비슷한 쿼리를 사용할 수 있습니다. 필터링 대상 verb에 읽기 전용 작업 `LIST`와 `GET`이 포함되도록 수정하기만 하면 됩니다. 또한 요청 범위(예: 단일 리소스를 가져오거나 여러 리소스를 나열하는 경우)에 따라 SLO 임계값도 다릅니다.

**API 요청 레이턴시 시간 SLI (읽기 전용)** - 이번에는 웹훅 실행 또는 대기열 대기 시간을 포함*하지 않습니다*.
단일 리소스의 경우 (범위=리소스, 임계값=1s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"GET", scope=~"resource"}[5m])) by (resource, subresource, verb, scope, le))`

동일한 네임스페이스에 있는 리소스 컬렉션의 경우 (범위=네임스페이스, 임계값=5s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"LIST", scope=~"namespace"}[5m])) by (resource, subresource, verb, scope, le))`

전체 클러스터의 리소스 컬렉션의 경우 (범위=클러스터, 임계값=30초)  
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"LIST", scope=~"cluster"}[5m])) by (resource, subresource, verb, scope, le))`

**API 요청 레이턴시 시간 합계 (읽기 전용) ** - API 서버에서 요청이 소요된 총 시간입니다. 이 시간은 웹훅 실행 및 대기 시간을 포함하므로 SLI 시간보다 길 수 있습니다.
단일 리소스의 경우 (범위=리소스, 임계값=1초)  
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"GET", scope=~"resource"}[5m])) by (resource, subresource, verb, scope, le))`

동일한 네임스페이스에 있는 리소스 컬렉션의 경우 (범위=네임스페이스, 임계값=5s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"LIST", scope=~"namespace"}[5m])) by (resource, subresource, verb, scope, le))`

전체 클러스터의 리소스 모음의 경우 (범위=클러스터, 임계값=30초)  
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"LIST", scope=~"cluster"}[5m])) by (resource, subresource, verb, scope, le))`

SLI 메트릭은 요청이 API Priority 및 Fairness 대기열에서 대기하거나, 승인 웹훅 또는 기타 쿠버네티스 확장을 통해 작업하는 데 걸리는 시간을 제외함으로써 쿠버네티스 구성 요소의 성능에 대한 통찰력을 제공합니다. 전체 지표는 애플리케이션이 API 서버의 응답을 기다리는 시간을 반영하므로 보다 총체적인 시각을 제공합니다. 이러한 지표를 비교하면 요청 처리 지연이 발생하는 위치를 파악할 수 있습니다. 

### 파드 시작 레이턴시

|Metric	| Definition	|
|---	|---	|
|kubelet_pod_start_sli_duration_seconds	|파드를 시작하는 데 걸리는 시간 (초) (이미지를 가져오고 초기화 컨테이너를 실행하는 데 걸리는 시간 제외), 파드 생성 타임스탬프부터 모든 컨테이너가 시계를 통해 시작 및 관찰된 것으로 보고될 때까지의 시간 	|
|kubelet_pod_start_duration_seconds	|kubelet이 파드를 처음 본 시점부터 파드가 실행되기 시작할 때까지의 시간(초). 여기에는 파드를 스케줄링하거나 워커 노드 용량을 확장하는 시간은 포함되지 않는다.	|

*참고: `kubelet_pod_start_sli_duration_seconds`는 쿠버네티스 1.27부터 사용할 수 있다.*

위의 쿼리와 마찬가지로 이러한 메트릭을 사용하여 노드 스케일링, 이미지 풀 및 초기화 컨테이너가 Kubelet 작업과 비교하여 파드 출시를 얼마나 지연시키는지 파악할 수 있습니다. 

**파드 시작 레이턴시 시간 SLI -** 이것은 파드 생성부터 애플리케이션 컨테이너가 실행 중인 것으로 보고된 시점까지의 시간입니다. 여기에는 워커 노드 용량을 사용할 수 있고 파드를 스케줄링하는 데 걸리는 시간이 포함되지만, 이미지를 가져오거나 초기화 컨테이너를 실행하는 데 걸리는 시간은 포함되지 않습니다.  
`histogram_quantile(0.99, sum(rate(kubelet_pod_start_sli_duration_seconds_bucket[5m])) by (le))`

**파드 시작 레이턴시 시간 합계 -** kubelet이 처음으로 파드를 시작하는 데 걸리는 시간입니다. 이는 kubelet이 WATCH를 통해 파드를 수신한 시점부터 측정되며, 워커 노드 스케일링 또는 스케줄링에 걸리는 시간은 포함되지 않는다. 여기에는 이미지를 가져오고 실행할 컨테이너를 초기화하는 데 걸리는 시간이 포함됩니다.  
`histogram_quantile(0.99, sum(rate(kubelet_pod_start_duration_seconds_bucket[5m])) by (le))`



## 클러스터의 SLO

EKS 클러스터의 쿠버네티스 리소스에서 Prometheus 메트릭을 수집하면 쿠버네티스 컨트롤 플레인 구성 요소의 성능에 대한 심층적인 통찰력을 얻을 수 있습니다. 

[perf-test repo](https://github.com/kubernetes/perf-tests/)에는 테스트 중 클러스터의 지연 시간 및 중요 성능 메트릭을 표시하는 Grafana 대시보드가 포함되어 있습니다. perf 테스트 구성은 쿠버네티스 메트릭을 수집하도록 구성된 오픈 소스 프로젝트인 [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)을 활용하지만 [Amazon Managed Prometheus 및 Amazon Managed Grafana 사용](https://aws-observability.github.io/terraform-aws-observability-accelerator/eks/)도 가능합니다.

`kube-prometheus-stack` 또는 유사한 프로메테우스 솔루션을 사용하는 경우 동일한 대시보드를 설치하여 클러스터의 SLO를 실시간으로 관찰할 수 있습니다. 

1. 먼저 `kubectl apply -f prometheus-rules.yaml`로 대시보드에서 사용되는 프로메테우스 규칙을 설치해야 한다. 여기에서 규칙 사본을 다운로드할 수 있습니다: https://github.com/kubernetes/perf-tests/blob/master/clusterloader2/pkg/prometheus/manifests/prometheus-rules.yaml
    1. 파일의 네임스페이스가 사용자 환경과 일치하는지 확인하세요.
    2. `kube-prometheus-stack`을 사용하는 경우 레이블이 `Prometheus.PrometheusSpec.RuleSelector` 헬름 값과 일치하는지 확인하세요.
2. 그런 다음 Grafana에 대시보드를 설치할 수 있습니다. 이를 생성하는 json 대시보드와 파이썬 스크립트는 다음에서 확인할 수 있습니다: https://github.com/kubernetes/perf-tests/tree/master/clusterloader2/pkg/prometheus/manifests/dashboards
    1. [`slo.json` 대시보드](https://github.com/kubernetes/perf-tests/blob/master/clusterloader2/pkg/prometheus/manifests/dashboards/slo.json)는 쿠버네티스 SLO와 관련된 클러스터의 성능을 보여줍니다.

SLO는 클러스터의 Kubernetes 구성 요소 성능에 초점을 맞추고 있지만 클러스터에 대한 다양한 관점이나 통찰력을 제공하는 추가 메트릭을 검토할 수 있습니다. [Kube-State-Metrics](https://github.com/kubernetes/kube-state-metrics/tree/main)와 같은 쿠버네티스 커뮤니티 프로젝트는 클러스터의 추세를 빠르게 분석하는 데 도움이 될 수 있습니다. 쿠버네티스 커뮤니티에서 가장 많이 사용되는 플러그인과 드라이버도 Prometheus 메트릭을 내보내므로 오토스케일러 또는 사용자 지정 스케줄러와 같은 사항을 조사할 수 있습니다. 

[옵저버빌리티 모범 사례 가이드](https://aws-observability.github.io/observability-best-practices/guides/containers/oss/eks/best-practices-metrics-collection/#control-plane-metrics)에는 추가 통찰력을 얻는 데 사용할 수 있는 다른 쿠버네티스 메트릭의 예가 나와 있습니다. 






