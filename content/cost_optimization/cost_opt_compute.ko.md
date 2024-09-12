---
search:
  exclude: true
---


# 비용 최적화 - 컴퓨팅 및 오토스케일링

개발자는 애플리케이션의 리소스 요구 사항(예: CPU 및 메모리)을 초기 예상하지만 이런 리소스 스펙을 지속적으로 조정하지 않으면 비용이 증가하고 성능 및 안정성이 저하될 수 있습니다. 초기에 정확한 예측값을 얻는 것보다 애플리케이션의 리소스 요구 사항을 지속적으로 조정하는 것이 더 중요합니다.

아래에 언급된 모범 사례는 비용을 최소화하고 조직이 투자 수익을 극대화할 수 있도록 하는 동시에 비즈니스 성과를 달성하는 비용 인지형 워크로드를 구축하고 운영하는 데 도움이 됩니다. 클러스터 컴퓨팅 비용을 최적화하는 데 있어 가장 중요한 순서는 다음과 같습니다:

1. 워크로드 규모 조정(Right-sizing)
2. 사용되지 않는 용량 줄이기
3. 컴퓨팅 유형(예: 스팟) 및 가속기(예: GPU) 최적화

## 워크로드 규모 조정(Right-sizing)

대부분의 EKS 클러스터에서 대부분의 비용은 컨테이너식 워크로드를 실행하는 데 사용되는 EC2 인스턴스에서 발생합니다. 워크로드 요구 사항을 이해하지 않고는 컴퓨팅 리소스의 크기를 적절하게 조정할 수 없습니다. 따라서 적절한 요청(request) 및 제한(limit)을 사용하고 필요에 따라 해당 설정을 조정해야 합니다. 또한 인스턴스 크기 및 스토리지 선택과 같은 종속성이 워크로드 성능에 영향을 미쳐 비용과 안정성에 의도하지 않은 다양한 결과를 초래할 수 있습니다.

*request*는 실제 사용률과 일치해야 합니다. 컨테이너의 request가 너무 크면 사용되지 않은 용량이 발생하여 총 클러스터 비용의 큰 부분을 차지합니다. 파드 내 각 컨테이너 (예: 애플리케이션 및 사이드카) 에는 총 파드 한도가 최대한 정확하도록 자체 request 및 limit을 설정해야 합니다.

컨테이너에 대한 리소스 요청 및 한도를 추정하는 [Goldilocks](https://www.youtube.com/watch?v=DfmQWYiwFDk), [KRR](https://www.youtube.com/watch?v=uITOzpf82RY), [Kubecost](https://aws.amazon.com/blogs/containers/aws-and-kubecost-collaborate-to-deliver-cost-monitoring-for-eks-customers/)와 같은 도구를 활용하세요. 애플리케이션의 특성, 성능/비용 요구 사항 및 복잡성에 따라 어떤 메트릭을 확장하는 것이 가장 좋은지, 애플리케이션 성능이 저하되는 시점 (포화 시점), 그리고 그에 따라 요청 및 제한을 조정하는 방법을 평가해야 합니다. 이 주제에 대한 자세한 지침은 [애플리케이션 적정 크기 조정](https://aws.github.io/aws-eks-best-practices/scalability/docs/node_efficiency/#application-right-sizing)을 참조하십시오.

Horizontal Pod Autoscaler(HPA)를 사용하여 실행해야 하는 애플리케이션 복제본 수를 제어하고, Vertical Pod Autoscaler(VPA)를 사용하여 복제본 당 애플리케이션에 필요한 요청 수와 제한을 조정하고, [Karpenter](http://karpenter.sh/) 또는 [Cluster Autoscaler](https://github.com/kubernetes/autoscaler)와 같은 노드 오토스케일링을 사용하여 클러스터의 총 노드 수를 지속적으로 조정하는 것이 좋습니다. Karpenter 및 Cluster Autoscaler를 사용한 비용 최적화 기법은 이 문서의 뒷부분에 설명되어 있습니다.

VPA는 워크로드가 최적으로 실행되도록 컨테이너에 할당된 요청 및 제한을 조정할 수 있습니다. VPA를 감사 모드에서 실행하여 자동으로 변경한 후 파드를 다시 시작하지 않도록 해야 합니다. 관찰된 메트릭을 기반으로 변경 사항을 제안합니다. 프로덕션 워크로드에 영향을 미치는 변경 사항은 애플리케이션의 안정성과 성능에 영향을 미칠 수 있으므로 비프로덕션 환경에서 먼저 해당 변경 사항을 검토하고 테스트해야 합니다.

## 소비 감소

비용을 절감하는 가장 좋은 방법은 리소스를 적게 프로비저닝하는 것입니다.이를 위한 한 가지 방법은 현재 요구 사항에 따라 워크로드를 조정하는 것입니다. 워크로드가 요구 사항을 정의하고 동적으로 확장되도록 하는 것부터 비용 최적화 노력을 시작해야 합니다. 이를 위해서는 애플리케이션에서 메트릭을 가져오고 [`PodDisruptionBudgets`](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) 및 [Pod Readiness Gates](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.5/deploy/pod_readiness_gate/)와 같은 구성을 설정하여 애플리케이션이 안전하게 동적으로 확장 및 축소할 수 있는지 확인해야 합니다.

HPA는 애플리케이션의 성능 및 안정성 요구 사항을 충족하는 데 필요한 복제본 수를 조정할 수 있는 유연한 워크로드 오토스케일러입니다. CPU, 메모리 또는 사용자 지정 메트릭 (예: 큐 깊이, 파드에 대한 연결 수 등) 과 같은 다양한 메트릭을 기반으로 확장 및 축소 시기를 정의할 수 있는 유연한 모델을 제공합니다.

쿠버네티스 메트릭 서버는 CPU 및 메모리 사용량과 같은 내장된 지표에 따라 크기를 조정할 수 있지만 Amazon CloudWatch 또는 SQS 대기열 깊이와 같은 다른 지표를 기반으로 확장하려면 [KEDA](https://keda.sh/)와 같은 이벤트 기반 자동 크기 조정 프로젝트를 고려해야 합니다. KEDA를 CloudWatch 지표와 함께 사용하는 방법에 대해서는 [이 블로그 게시물](https://aws.amazon.com/blogs/mt/proactive-autoscaling-of-kubernetes-workloads-with-keda-using-metrics-ingested-into-amazon-cloudwatch/)을 참조하십시오. 어떤 지표를 모니터링하고 규모를 조정해야 할지 잘 모르겠다면 [중요한 지표 모니터링에 대한 모범 사례](https://aws-observability.github.io/observability-best-practices/guides/#monitor-what-matters)를 확인하십시오.

워크로드 소비를 줄이면 클러스터에 초과 용량이 생성되며 적절한 자동 크기 조정 구성을 통해 노드를 자동으로 축소하여 총 지출을 줄일 수 있습니다. 컴퓨팅 파워를 수동으로 최적화하지 않는 것이 좋습니다. 쿠버네티스 스케줄러와 노드 오토스케일러는 이 프로세스를 처리하도록 설계되었습니다.

## 미사용 용량 줄이기

애플리케이션의 크기를 올바르게 결정하고 초과 요청을 줄인 후 프로비저닝된 컴퓨팅 파워를 줄일 수 있습니다. 위 섹션에서 시간을 들여 워크로드 크기를 올바르게 조정했다면 이 작업을 동적으로 수행할 수 있을 것입니다.AWS의 쿠버네티스와 함께 사용되는 기본 노드 자동 확장 프로그램은 두 가지입니다.

### Karpenter와 Cluster Autoscaler

Karpenter와 쿠버네티스 Cluster Autoscaler는 모두 파드가 생성되거나 제거되고 컴퓨팅 요구 사항이 변경됨에 따라 클러스터의 노드 수를 확장합니다. 둘 다 기본 목표는 같지만 Karpenter는 비용을 줄이고 클러스터 전체 사용을 최적화하는 데 도움이 되는 노드 관리 프로비저닝과 디프로비저닝에 대해 다른 접근 방식을 취합니다.

클러스터의 규모가 커지고 워크로드의 다양성이 증가함에 따라 노드 그룹과 인스턴스를 미리 구성하기가 더욱 어려워지고 있습니다.워크로드 요청과 마찬가지로 초기 기준을 설정하고 필요에 따라 지속적으로 조정하는 것이 중요합니다.

### Cluster Autoscaler Priority Expander

쿠버네티스 Cluster Autoscaler는 노드 그룹을 확장하거나 축소하는 방식으로 작동합니다. 워크로드를 동적으로 확장하지 않는 경우 클러스터 오토스케일러는 비용 절감에 도움이 되지 않습니다. Cluster Autoscaler를 사용하려면 클러스터 관리자가 워크로드 사용에 대비하여 노드 그룹을 미리 생성해야 합니다. 노드 그룹은 "프로파일"이 동일한 인스턴스, 즉 CPU와 메모리 양이 거의 같은 인스턴스를 사용하도록 구성해야 합니다.

노드 그룹을 여러 개 가질 수 있으며 우선 순위 조정 수준을 설정하도록 클러스터 오토스케일러를 구성할 수 있으며 각 노드 그룹은 서로 다른 크기의 노드를 포함할 수 있습니다.노드 그룹은 다양한 용량 유형을 가질 수 있으며 우선 순위 확장기를 사용하여 비용이 저렴한 그룹을 먼저 확장할 수 있습니다.

다음은 온디맨드 인스턴스를 사용하기 전에 '컨피그맵'을 사용하여 예약 용량의 우선 순위를 지정하는 클러스터 구성 스니펫의 예입니다. 동일한 기법을 사용하여 다른 유형보다 Graviton 또는 스팟 인스턴스의 우선 순위를 지정할 수 있습니다.  

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: my-cluster
managedNodeGroups:
  - name: managed-ondemand
    minSize: 1
    maxSize: 7
    instanceType: m5.xlarge
  - name: managed-reserved
    minSize: 2
    maxSize: 10
    instanceType: c5.2xlarge
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    10:
      - .*ondemand.*
    50:
      - .*reserved.*
```

노드 그룹을 사용하면 기본 컴퓨팅 리소스가 기본적으로 예상한 작업을 수행하는 데 도움이 될 수 있습니다(예: AZ 전체에 노드를 분산시키는 경우). 그러나 모든 워크로드의 요구 사항이나 기대치가 동일하지는 않으므로 애플리케이션이 요구 사항을 명시적으로 선언하도록 하는 것이 좋습니다. Cluster Autoscaler에 대한 자세한 내용은 [모범 사례 섹션](https://aws.github.io/aws-eks-best-practices/cluster-autoscaling/)을 참조하십시오.

### 스케줄 조정자

Cluster Autoscaler는 스케줄이 필요한 새 파드 또는 사용률이 낮은 노드를 기반으로 클러스터에서 노드 용량을 추가하고 제거할 수 있습니다. 노드에 스케줄링된 후에는 파드 배치를 전체적으로 살펴볼 수 없습니다. 클러스터 오토스케일러를 사용하는 경우 클러스터의 용량 낭비를 방지하기 위해 [Kubernetes descheduler](https://github.com/kubernetes-sigs/descheduler)도 살펴봐야 합니다.

클러스터에 10개의 노드가 있고 각 노드의 사용률이 60%라면 클러스터에서 프로비저닝된 용량의 40% 를 사용하지 않는 것입니다. 클러스터 오토스케일러를 사용하면 노드당 사용률 임계값을 60% 로 설정할 수 있지만, 이렇게 하면 사용률이 60% 미만으로 떨어진 후 단일 노드만 축소하려고 합니다.

Descheduler를 사용하면 파드가 스케줄링되거나 클러스터에 노드가 추가된 후 클러스터 용량 및 사용률을 확인할 수 있습니다. 클러스터의 총 용량을 지정된 임계값 이상으로 유지하려고 시도합니다. 또한 노드 테인트나 클러스터에 합류하는 새 노드를 기반으로 파드를 제거하여 파드가 최적의 컴퓨팅 환경에서 실행되도록 할 수 있습니다. 참고로 Descheduler는 제거된 파드의 교체를 스케줄링하지 않고 기본 스케줄러를 사용한다.

### Karpenter 통합 기능

Karpenter는 노드 관리에 대해 "그룹과 무관한(groupless)" 접근 방식을 취합니다. 이 접근 방식은 다양한 워크로드 유형에 더 유연하며 클러스터 관리자의 사전 구성이 덜 필요합니다. 그룹을 미리 정의하고 워크로드 필요에 따라 각 그룹을 조정하는 대신 Karpenter는 프로비저너와 노드 템플릿을 사용하여 생성할 수 있는 EC2 인스턴스 유형과 생성 시 인스턴스에 대한 설정을 광범위하게 정의합니다.

빈패킹(Bin Packing)은 더 적은 수의 최적 크기의 인스턴스에 더 많은 워크로드를 패킹하여 인스턴스의 리소스를 더 많이 활용하는 방법입니다. 이렇게 하면 워크로드에서 사용하는 리소스만 프로비저닝하여 컴퓨팅 비용을 줄이는 데 도움이 되지만 절충점이 있습니다. 특히 대규모 확장 이벤트의 경우 클러스터에 용량을 추가해야 하므로 새 워크로드를 시작하는 데 시간이 더 오래 걸릴 수 있습니다. 빈패킹을 설정할 때는 비용 최적화, 성능 및 가용성 간의 균형을 고려하십시오. 

Karpenter는 지속적으로 모니터링하고 빈패킹하여 인스턴스 리소스 사용률을 높이고 컴퓨팅 비용을 낮출 수 있습니다. 또한 Karpenter는 워크로드에 대해 더 비용 효율적인 워커 노드를 선택할 수 있습니다. 프로비저닝 도구에서 "consolidation" 플래그를 true로 설정하면 이를 달성할 수 있습니다 (아래 샘플 코드 스니펫 참조). 아래 예제는 통합을 지원하는 프로비저닝 도구의 예를 보여줍니다. 이 안내서를 작성하는 시점에서 Karpenter는 실행 중인 스팟 인스턴스를 더 저렴한 스팟 인스턴스로 대체하지 않을 것입니다. Karpenter 통합에 대한 자세한 내용은 [이 블로그](https://aws.amazon.com/blogs/containers/optimizing-your-kubernetes-compute-costs-with-karpenter-consolidation/)를 참조하십시오.  

```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: enable-binpacking
spec:
  consolidation:
    enabled: true
```

중단이 불가능할 수 있는 워크로드(예: 체크포인트 없이 장기간 실행되는 일괄 작업)의 경우, 파드에 `do-not-evict` 어노테이션을 달아 보세요. 파드를 제거에서 제외시키는 것은 Karpenter가 이 파드를 포함하는 노드를 자발적으로 제거해서는 안 된다고 말하는 것입니다. 하지만 노드가 드레이닝되는 동안 노드에 `do-not-evict` 파드가 추가되면 나머지 파드는 여전히 제거되지만 해당 파드는 제거될 때까지 종료를 차단합니다. 어느 경우든 노드에 추가 작업이 스케줄링되는 것을 방지하기 위해 노드는 cordon됩니다. 다음은 어노테이션을 설정하는 방법을 보여주는 예시입니다.

```yaml hl_lines="8"
apiVersion: v1
kind: Pod
metadata:
  name: label-demo
  labels:
    environment: production
  annotations:  
    "karpenter.sh/do-not-evict": "true"
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```

### Cluster Autoscaler 파라미터를 조정하여 사용률이 낮은 노드를 제거합니다.

노드 사용률은 요청된 리소스의 합계를 용량으로 나눈 값으로 정의됩니다. 기본적으로 'scale-down-utilization-threshold'은 50% 로 설정됩니다. 이 파라미터는 'scale-down-unneeded-time'과 함께 사용할 수 있습니다. 이 시간은 노드를 축소할 수 있을 때까지 필요하지 않게 되는 기간을 결정합니다. 기본값은 10분입니다.축소된 노드에서 여전히 실행 중인 파드는 kube-scheduler에 의해 다른 노드에 스케줄링됩니다. 이러한 설정을 조정하면 활용도가 낮은 노드를 제거하는 데 도움이 될 수 있지만, 클러스터를 조기에 강제로 축소하지 않도록 먼저 이 값을 테스트하는 것이 중요합니다.

제거하는 데 비용이 많이 드는 파드를 클러스터 오토스케일러에서 인식하는 레이블로 보호함으로써 스케일 다운이 발생하지 않도록 할 수 있습니다. 이렇게 하려면 제거 비용이 많이 드는 파드에 `cluster-autoscaler.kubernetes.io/safe-to-evict=false`라는 주석을 달아야 한다. 다음은 어노테이션을 설정하는 yaml의 예시입니다.

```yaml hl_lines="8"
apiVersion: v1
kind: Pod
metadata:
  name: label-demo
  labels:
    environment: production
  annotations:  
    "cluster-autoscaler.kubernetes.io/safe-to-evict": "false"
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```

### 노드에 Cluster Autoscaler 및 Karpenter 태그 지정

AWS  [태그](https://docs.aws.amazon.com/tag-editor/latest/userguide/tagging.html)는 리소스를 구성하고 세부 수준에서 AWS 비용을 추적하는 데 사용됩니다. 비용 추적을 위한 Kubernetes 레이블과 직접적인 상관 관계를 맺지는 않습니다. 먼저 쿠버네티스 리소스 레이블링으로 시작하고 [Kubecost](https://aws.amazon.com/blogs/containers/aws-and-kubecost-collaborate-to-deliver-cost-monitoring-for-eks-customers/)와 같은 도구를 활용하여 파드, 네임스페이스 등의 쿠버네티스 레이블을 기반으로 인프라 비용을 보고하는 것이 좋습니다.

AWS Cost Explorer에서 결제 정보를 표시하려면 워커 노드에 태그가 있어야 합니다. Cluster Autoscaler를 사용하면 [시작 템플릿](https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html)을 사용하여 관리형 노드 그룹 내의 워커 노드에 태그를 지정합니다. 자체 관리형 노드 그룹의 경우 [EC2 Auto Scaling 그룹](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-tagging.html) 을 사용하여 인스턴스에 태그를 지정합니다. Karpenter에서 프로비저닝한 인스턴스의 경우 [노드 템플릿의 spec.tags](https://karpenter.sh/v0.29/concepts/node-templates/#spectags)를 사용하여 태그를 지정하십시오.

### 멀티 테넌트 클러스터

다른 팀이 공유하는 클러스터에서 작업하는 경우 동일한 노드에서 실행되는 다른 워크로드를 파악하지 못할 수 있습니다. 리소스 요청은 CPU 공유와 같은 일부 "시끄러운 이웃(noisy neighbor)" 문제를 격리하는 데 도움이 될 수 있지만 디스크 I/O 병목과 같은 모든 리소스 경계를 분리하지는 못할 수도 있습니다. 워크로드에 의해 사용 가능한 모든 리소스를 분리하거나 제한할 수는 없습니다. 다른 워크로드보다 높은 비율로 공유 리소스를 사용하는 워크로드는 노드 [taint와 toleration](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)을 통해 격리해야 합니다. 이러한 워크로드를 위한 또 다른 고급 기법은 컨테이너의 공유 CPU 대신 전용 CPU를 보장하는 [CPU pinning](https://kubernetes.io/docs/tasks/administer-cluster/cpu-management-policies/#static-policy)을 적용할 수 있습니다.

워크로드를 노드 수준에서 분리하는 것은 비용이 더 많이 들 수 있지만 [예약 인스턴스](https://aws.amazon.com/ec2/pricing/reserved-instances/), [Graviton 프로세서](https://aws.amazon.com/ec2/graviton/) 또는 [스팟 인스턴스](https://aws.amazon.com/ec2/spot/)을 사용하여 [BestEffort](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/#besteffort) 작업을 예약하거나 추가 비용 절감을 활용할 수 있습니다. 

공유 클러스터에는 IP 고갈, 쿠버네티스 서비스 제한 또는 API 확장 요청과 같은 클러스터 수준 리소스 제약이 있을 수도 있습니다. [확장성 모범 사례 가이드](https://aws.github.io/aws-eks-best-practices/scalability/docs/control-plane/)를 검토하여 클러스터가 이러한 제한이 없는지 확인해야 합니다.

네임스페이스 또는 Karpenter 프로비저너 수준에서 리소스를 격리할 수 있습니다. [리소스 할당량(Quota)](https://kubernetes.io/docs/concepts/policy/resource-quotas/)은 네임스페이스의 워크로드가 소비할 수 있는 리소스 수를 제한하는 방법을 제공합니다. 이는 초기 보호 수단으로 유용할 수 있지만, 워크로드 확장을 인위적으로 제한하지 않도록 지속적으로 평가해야 합니다.

Karpenter 프로비저너는 클러스터에서 [일부 사용 가능한 리소스(예: CPU, GPU)에 제한을 설정](https://karpenter.sh/docs/concepts/provisioners/#speclimitsresources)할 수 있지만 적절한 프로비저너를 사용하도록 테넌트 애플리케이션을 구성해야 합니다. 이렇게 하면 단일 제공자가 클러스터에 너무 많은 노드를 생성하는 것을 방지할 수 있지만, 제한을 너무 낮게 설정하지 않도록 지속적으로 평가하여 워크로드가 확장되지 않도록 해야 합니다.

### 오토스케일링 스케줄링

주말 또는 휴일에는 클러스터를 축소해야 할 수도 있습니다. 이는 사용하지 않을 때 0으로 축소하려는 테스트 및 비프로덕션 클러스터에 특히 적합합니다. [cluster-turndown](https://github.com/kubecost/cluster-turndown) 와 같은 솔루션은 크론 스케줄에 따라 복제본을 0으로 축소할 수 있습니다. 다음 [AWS 블로그](https://aws.amazon.com/blogs/containers/manage-scale-to-zero-scenarios-with-karpenter-and-serverless/)에 설명된 대로 Karpenter를 사용하여 동일한 작업을 수행할 수도 있습니다.

## 컴퓨팅 용량 유형 최적화

클러스터의 총 컴퓨팅 용량을 최적화하고 빈 패킹을 사용한 후에는 클러스터에 프로비저닝한 컴퓨팅 유형과 해당 리소스에 대한 비용을 확인해야 합니다. AWS는 컴퓨팅 비용을 절감할 수 있는 [컴퓨팅 절감형 플랜(Savings Plan)](https://aws.amazon.com/savingsplans/compute-pricing/)을 운영하고 있으며, 이를 다음과 같은 용량 유형으로 분류해 보겠습니다.

* 스팟
* 절감형 플랜(Savings Plan)
* 온디맨드
* Fargate

각 용량 유형에는 관리 오버헤드, 가용성 및 장기 약정 측면에서 서로 다른 절충점이 있으므로 환경에 적합한 것을 결정해야 합니다. 어떤 환경도 단일 용량 유형에 의존해서는 안 되며 단일 클러스터에 여러 실행 유형을 혼합하여 특정 워크로드 요구 사항 및 비용을 최적화할 수 있습니다.

### 스팟 인스턴스

[스팟](https://aws.amazon.com/ec2/spot/) 용량 유형은 가용영역의 예비 용량에서 EC2 인스턴스를 프로비저닝합니다. 스팟은 최대 90% 까지 할인을 제공하지만, 다른 곳에서 필요할 경우 해당 인스턴스가 중단될 수 있습니다. 또한 새 스팟 인스턴스를 프로비저닝할 용량이 항상 있는 것은 아니며 [2분 중단 알림](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html)을 통해 기존 스팟 인스턴스를 회수할 수 있습니다. 애플리케이션의 시작 또는 종료 프로세스가 오래 걸리는 경우 스팟 인스턴스가 최선의 옵션이 아닐 수 있습니다.

스팟 컴퓨팅은 다양한 인스턴스 유형을 사용하여 사용 가능한 스팟 용량이 없을 가능성을 줄여야 합니다. 노드를 안전하게 종료하려면 인스턴스 중단을 처리해야 합니다. Karpenter 또는 관리형 노드 그룹의 일부로 프로비저닝된 노드는 [인스턴스 중단 알림](https://aws.github.io/aws-eks-best-practices/karpenter/#enable-interruption-handling-when-using-spot)을 자동으로 지원합니다. 자체 관리형 노드를 사용하는 경우 [노드 종료 핸들러](https://github.com/aws/aws-node-termination-handler)를 별도로 실행하여 스팟 인스턴스를 정상적으로 종료해야 합니다.

단일 클러스터에서 스팟 인스턴스와 온디맨드 인스턴스의 균형을 맞출 수 있습니다. Karpenter를 사용하면 [가중치 프로비저너](https://karpenter.sh/docs/concepts/scheduling/#on-demandspot-ratio-split)를 생성하여 다양한 용량 유형의 균형을 맞출 수 있습니다. Cluster Autoscaler를 사용하면 [스팟 및 온디맨드 또는 예약 인스턴스가 포함된 혼합 노드 그룹](https://aws.amazon.com/blogs/containers/amazon-eks-now-supports-provisioning-and-managing-ec2-spot-instances-in-managed-node-groups/)을 생성할 수 있습니다.

다음은 Karpenter를 사용하여 온디맨드 인스턴스보다 스팟 **** 인스턴스 우선 순위를 높게 정하는 예입니다. 프로비저너를 생성할 때 스팟, 온디맨드 또는 둘 다 지정할 수 있습니다(아래 그림 참조). 둘 다 지정하고 파드가 스팟 또는 온디맨드를 사용해야 하는지 명시적으로 지정하지 않는 경우 Karpenter는 [price-capacity-optimization 할당 전략](https://aws.amazon.com/blogs/compute/introducing-price-capacity-optimized-allocation-strategy-for-ec2-spot-instances/)으로 노드를 프로비저닝할 때 스팟의 우선 순위를 지정합니다.

```yaml hl_lines="9"
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: spot-prioritized
spec:
  requirements:
    - key: "karpenter.sh/capacity-type" 
      operator: In
        values: ["spot", "on-demand"]
```

### Savings Plans, 예약 인스턴스 및 AWS 엔터프라이즈 할인 프로그램(EDP)

[Compute Savings Plan](https://aws.amazon.com/savingsplans/compute-pricing/)을 사용하면 컴퓨팅 비용을 줄일 수 있습니다. Savings Plan은 1년 또는 3년 컴퓨팅 사용 약정 시 할인된 가격을 제공합니다. 사용량은 EKS 클러스터의 EC2 인스턴스에 적용할 수 있지만 Lambda 및 Fargate와 같은 모든 컴퓨팅 사용에도 적용됩니다. Savings Plan을 사용하면 비용을 절감하면서도 약정 기간 동안 모든 EC2 인스턴스 유형을 선택할 수 있습니다.

Compute Savings Plan을 사용하면 사용하려는 인스턴스 유형, 제품군 또는 리전에 대한 약정 없이 EC2 비용을 최대 66% 절감할 수 있습니다. 절감액은 인스턴스를 사용할 때 인스턴스에 자동으로 적용됩니다.

EC2 인스턴스 Savings Plan은 특정 리전 및 EC2 제품군(예: C 제품군 인스턴스)의 사용량을 약정하여 컴퓨팅 비용을 최대 72% 절감합니다. 리전 내 모든 AZ로 사용량을 전환하고, c5 또는 c6와 같은 모든 세대의 인스턴스 패밀리를 사용하고, 패밀리 내에서 원하는 크기의 인스턴스를 사용할 수 있습니다. 할인은 Savings Plan 기준과 일치하는 계정 내 모든 인스턴스에 자동으로 적용됩니다.

[예약 인스턴스](https://aws.amazon.com/ec2/pricing/reserved-instances/)는 EC2 인스턴스 Savings Plan과 비슷하지만 가용영역 또는 지역의 용량을 보장하고 온디맨드 인스턴스에 비해 비용을 최대 72% 절감합니다 .필요한 예약 용량을 계산한 후 예약 기간(1년 또는 3년)을 선택할 수 있습니다. 어카운트에서 해당 EC2 인스턴스를 실행하면 할인이 자동으로 적용됩니다.

또한 고객은 AWS와 기업 계약을 체결할 수 있습니다.기업 계약은 고객에게 요구 사항에 가장 적합한 계약을 조정할 수 있는 옵션을 제공합니다.고객은 AWS 엔터프라이즈 할인 프로그램(EDP, Enterprise Discount Program)를 기반으로 가격 할인을 받을 수 있습니다. 기업 계약에 대한 추가 정보는 AWS 영업 담당자에게 문의하세요.

### 온디맨드

온디맨드 EC2 인스턴스는 (스팟에 비해) 중단 없이 사용할 수 있고 (Savings Plan에 비해) 장기 약정이 없다는 이점이 있습니다. 클러스터에서 비용을 절감하려면 온디맨드 EC2 인스턴스의 사용량을 줄여야 합니다.

워크로드 요구 사항을 최적화한 후에는 클러스터의 최소 및 최대 용량을 계산하여야 합니다. 이 수치는 시간이 지남에 따라 변경될 수 있지만 감소하는 경우는 거의 없습니다. 최소 금액 미만의 모든 항목에는 Savings Plan을 사용하고 애플리케이션 가용성에 영향을 미치지 않는 용량은 확보해 두는 것이 좋습니다. 지속적으로 사용되지 않거나 가용성이 필요한 다른 모든 항목은 온디맨드로 사용할 수 있습니다.

이 섹션에서 언급한 것처럼 사용량을 줄이는 가장 좋은 방법은 리소스를 적게 사용하고 프로비저닝한 리소스를 최대한 활용하는 것입니다. Cluster Autoscaler를 사용하면 `scale-down-utilization-threshold` 설정으로 사용률이 낮은 노드를 제거할 수 있습니다.Karpenter의 경우 통합을 활성화하는 것이 좋습니다.

워크로드에 사용할 수 있는 EC2 인스턴스 유형을 수동으로 식별하려면 [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector)를 사용할 수 있습니다. 그러면 각 러전에서 사용 가능한 인스턴스는 물론 EKS와 호환되는 인스턴스도 표시할 수 있습니다. 다음 예는 x86 프로세스 아키텍처, 4Gb 메모리, vCPU 2개를 갖추고 us-east-1 지역에서 사용 가능한 인스턴스를 보여줍니다.

```bash
ec2-instance-selector --memory 4 --vcpus 2 --cpu-architecture x86_64 \
  -r us-east-1 --service eks
c5.large
c5a.large
c5ad.large
c5d.large
c6a.large
c6i.large
t2.medium
t3.medium
t3a.medium
```

운영 환경이 아닌 경우 야간 및 주말과 같이 사용하지 않는 시간에는 클러스터를 자동으로 축소할 수 있습니다. kubecost 프로젝트 [cluster-turndown](https://github.com/kubecost/cluster-turndown)은 설정된 일정에 따라 클러스터를 자동으로 축소할 수 있는 컨트롤러의 예입니다.

### Fargate 컴퓨팅

Fargate 컴퓨팅은 EKS 클러스터를 위한 완전 관리형 컴퓨팅 옵션입니다. 쿠버네티스 클러스터의 노드당 파드 하나를 스케줄링하여 파드 격리를 제공합니다. 이를 통해 워크로드의 CPU 및 RAM 메모리 요구 사항에 맞게 컴퓨팅 노드의 크기를 조정하여 클러스터의 워크로드 사용을 엄격하게 제어할 수 있습니다.

Fargate는 최소 0.25vCPU, 0.5GB 메모리에서부터 최대 16vCPU, 120GB 메모리까지 워크로드를 확장할 수 있습니다. 사용할 수 있는 [파드 크기 변형](https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html)에 제한이 있으므로 Fargate 설정이 워크로드에 적합한지 확인해야 합니다. 예를 들어 워크로드가 vCPU 1개, 0.5GB 메모리가 필요한 경우 이를 위한 가장 작은 Fargate 파드는 vCPU 1개, 2GB 메모리입니다.

Fargate는 EC2 인스턴스 또는 운영 체제 관리가 필요 없는 등 많은 이점을 제공하지만 배포된 모든 파드가 클러스터의 개별 노드로 격리되어 있기 때문에 기존 EC2 인스턴스보다 더 많은 컴퓨팅 파워가 필요할 수 있습니다. 이를 위해서는 Kubelet, 로깅 에이전트, 일반적으로 노드에 배포하는 데몬셋 등의 항목을 더 많이 복제해야 합니다. 데몬셋은 Fargate에서 지원되지 않으므로 파드 "사이드카"로 변환하여 애플리케이션과 함께 실행해야 합니다.

Fargate는 노드별로 각 워크로드간 분리되기 때문에 버스팅이 불가능하고 공유될 수 없기 때문에 빈패킹이나 CPU 오버프로비저닝의 이점을 누릴 수 없습니다. Fargate를 사용하면 비용이 드는 EC2 인스턴스 관리 시간을 절약할 수 있지만 CPU 및 메모리 비용은 다른 EC2 용량 유형보다 비쌀 수 있습니다. Fargate 파드는 컴퓨팅 Savings Plan을 활용하여 온디맨드 비용을 절감할 수 있습니다.

## 컴퓨팅 사용 최적화

컴퓨팅 인프라 비용을 절감하는 또 다른 방법은 워크로드에 더 효율적인 컴퓨팅을 사용하는 것입니다. 이는 x86보다 최대 20% 저렴하고 에너지 효율이 60% 더 높은 [Graviton 프로세서](https://aws.amazon.com/ec2/graviton/)와 같이 성능이 더 뛰어난 범용 컴퓨팅이나 GPU 및 [FPGA](https://aws.amazon.com/ec2/instance-types/f1/) 와 같은 워크로드별 가속기를 통해 얻을 수 있습니다. 워크로드에 맞게 [ARM 아키텍처에서 실행](https://aws.amazon.com/blogs/containers/how-to-build-your-containers-for-arm-and-save-with-graviton-and-spot-instances-on-amazon-ecs/)하고 [적절한 가속기로 노드를 설정](https://aws.amazon.com/blogs/compute/running-gpu-accelerated-kubernetes-workloads-on-p3-and-p2-ec2-instances-with-amazon-eks/)할 수 있는 컨테이너를 구축해야 합니다.

EKS는 혼합 아키텍처(예: amd64 및 arm64)로 클러스터를 실행할 수 있으며 컨테이너가 멀티 아키텍처용으로 컴파일된 경우 프로비저너에서 두 아키텍처를 모두 허용하여 Karpenter와 함께 Graviton 프로세서를 활용할 수 있습니다. 하지만 성능을 일관되게 유지하려면 각 워크로드를 단일 컴퓨팅 아키텍처에 두고 추가 용량이 없는 경우에만 다른 아키텍처를 사용하는 것이 좋습니다.

프로비저너는 여러 아키텍처로 구성할 수 있으며 워크로드는 워크로드 사양에서 특정 아키텍처를 요청할 수도 있습니다.

```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: default
spec:
  requirements:
  - key: "kubernetes.io/arch"
    operator: In
    values: ["arm64", "amd64"]
```

Cluster Autoscaler를 사용하면 Graviton 인스턴스용 노드 그룹을 생성하고 새 용량을 활용하려면 [워크로드에 대한 노드 허용 범위](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)를 설정해야 합니다.

GPU와 FPGA는 워크로드의 성능을 크게 향상시킬 수 있지만 가속기를 사용하려면 워크로드를 최적화해야 합니다. 머신러닝 및 인공지능을 위한 다양한 워크로드 유형은 컴퓨팅에 GPU를 사용할 수 있으며, 리소스 요청을 사용하여 클러스터에 인스턴스를 추가하고 워크로드에 마운트할 수 있습니다.

```yaml
spec:
  template:
    spec:
    - containers:
      ...
      resources:
          limits:
            nvidia.com/gpu: "1"
```

일부 GPU 하드웨어는 여러 워크로드에서 공유할 수 있으므로 단일 GPU를 프로비저닝하고 사용할 수 있습니다. 워크로드 GPU 공유를 구성하는 방법을 보려면 자세한 내용은 [가상 GPU 장치 플러그인](https://aws.amazon.com/blogs/opensource/virtual-gpu-device-plugin-for-inference-workload-in-kubernetes/)을 참조하십시오. 다음 블로그를 참조할 수도 있습니다. 

* [NVIDIA 타임슬라이싱 및 가속화 EC2 인스턴스를 사용하는 Amazon EKS에서의 GPU 공유](https://aws.amazon.com/blogs/containers/gpu-sharing-on-amazon-eks-with-nvidia-time-slicing-and-accelerated-ec2-instances/)
* [Amazon EKS에서 NVIDIA의 멀티 인스턴스 GPU(MIG)를 사용하여 GPU 사용률 극대화: GPU 당 더 많은 파드를 실행하여 성능 향상](https://aws.amazon.com/blogs/containers/maximizing-gpu-utilization-with-nvidias-multi-instance-gpu-mig-on-amazon-eks-running-more-pods-per-gpu-for-enhanced-performance/)