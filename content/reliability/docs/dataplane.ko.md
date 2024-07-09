---
search:
  exclude: true
---


# EKS 데이터 플레인

가용성과 복원력이 뛰어난 애플리케이션을 운영하려면 가용성과 복원력이 뛰어난 데이터 플레인이 필요합니다. 탄력적인 데이터 플레인을 사용하면 쿠버네티스가 애플리케이션을 자동으로 확장하고 복구할 수 있습니다. 복원력이 뛰어난 데이터 플레인은 2개 이상의 워커 노드로 구성되며, 워크로드에 따라 확장 및 축소될 수 있으며 장애 발생 시 자동으로 복구할 수 있습니다.

EKS를 사용하는 워커 노드에는 [EC2 인스턴스](https://docs.aws.amazon.com/eks/latest/userguide/worker.html)와 [Fargate] (https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)라는 두 가지 옵션이 있습니다. EC2 인스턴스를 선택하면 워커 노드를 직접 관리하거나 [EKS 관리 노드 그룹](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)을 사용할 수 있습니다. 관리형 워커 노드와 자체 관리형 워커 노드와 Fargate가 혼합된 클러스터를 구성할 수 있습니다. 

Fargate의 EKS는 복원력이 뛰어난 데이터 플레인을 위한 가장 쉬운 방법을 제공합니다. Fargate는 격리된 컴퓨팅 환경에서 각 파드를 실행합니다. Fargate에서 실행되는 각 파드에는 자체 워커 노드가 있습니다. 쿠버네티스가 파드를 확장함에 따라 Fargate는 데이터 플레인을 자동으로 확장합니다. [horizontal pod autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html)를 사용하여 데이터 플레인과 워크로드를 모두 확장할 수 있습니다.

EC2 워커 노드를 확장하는 데 선호되는 방법은 [쿠버네티스 Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md), [EC2 Auto Scaling 그룹](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) 또는 [Atlassian's Esclator](https://github.com/atlassian/escalator)와 같은 커뮤니티 프로젝트를 사용하는 것입니다.

## 권장 사항 

### EC2 오토 스케일링 그룹을 사용하여 워커 노드 생성

개별 EC2 인스턴스를 생성하여 클러스터에 조인하는 대신 EC2 오토 스케일링 그룹을 사용하여 워커 노드를 생성하는 것이 가장 좋습니다. 오토 스케일링 그룹은 종료되거나 장애가 발생한 노드를 자동으로 교체하므로 클러스터가 항상 워크로드를 실행할 수 있는 용량을 확보할 수 있습니다. 

### 쿠버네티스 Cluster Autoscaler를 사용하여 노드를 확장하세요

Cluster Autoscaler는 클러스터의 리소스가 충분하지 않아 실행할 수 없는 파드가 있을 때 데이터 플레인 크기를 조정하며, 다른 워커 노드를 추가하여 도움을 줍니다. Cluster Autoscaler는 반응형 프로세스이긴 하지만 클러스터의 용량이 충분하지 않아 파드가 *pending* 상태가 될 때까지 기다립니다. 이러한 이벤트가 발생하면 클러스터에 EC2 인스턴스가 추가됩니다. 클러스터의 용량이 부족해지면 워커 노드가 추가될 때까지 새 복제본 또는 새 파드를 사용할 수 없게 됩니다(*Pending 상태*). 데이터 플레인이 워크로드 수요를 충족할 만큼 충분히 빠르게 확장되지 않는 경우 이러한 지연은 애플리케이션의 신뢰성에 영향을 미칠 수 있습니다. 워커 노드의 사용률이 지속적으로 낮고 해당 노드의 모든 파드를 다른 워커 노드에 스케줄링할 수 있는 경우 Cluster Autoscaler는 해당 워커 노드를 종료합니다.

### Cluster Autoscaler를 사용하여 오버 프로비저닝을 구성합니다.

Cluster Autoscaler는 클러스터의 파드가 이미 *pending* 상태일 때 데이터 플레인 스케일링을 트리거합니다. 따라서 애플리케이션에 더 많은 복제본이 필요한 시점과 실제로 더 많은 복제본을 가져오는 시점 사이에 지연이 있을 수 있습니다. 이러한 지연을 방지할 수 있는 방법은 필요한 것보다 많은 복제본을 추가하여 애플리케이션의 복제본 수를 늘리는 것입니다. 

Cluster Autoscaler에서 권장하는 또 다른 패턴은 [*pause* 파드와 우선순위 선점 기능](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-can-i-configure-overprovisioning-with-cluster-autoscaler)입니다. *pause 파드*는 [pause 컨테이너](https://github.com/kubernetes/kubernetes/tree/master/build/pause)를 실행하는데, 이름에서 알 수 있듯이 클러스터의 다른 파드에서 사용할 수 있는 컴퓨팅 용량의 placeholder 역할을 하는 것 외에는 아무것도 하지 않습니다. *매우 낮은 할당 우선 순위*로 실행되기 때문에, 다른 파드를 생성해야 하고 클러스터에 가용 용량이 없을 때 일시 중지 파드가 노드에서 제거됩니다. 쿠버네티스 스케줄러는 pause 파드의 축출을 감지하고 스케줄을 다시 잡으려고 합니다. 하지만 클러스터가 최대 용량으로 실행되고 있기 때문에 일시 중지 파드는 *pending* 상태로 유지되며, Cluster Autoscaler는 이에 대응하여 노드를 추가합니다. 

Helm 차트를 통해 [클러스터 오버프로비저너](https://github.com/helm/charts/tree/master/stable/cluster-overprovisioner)를 설치할 수 있다.

### 여러 오토 스케일링 그룹과 함께 Cluster Autoscaler 사용

`--node-group-auto-discovery` 플래그를 활성화한 상태로 Cluster Autoscaler를 실행합니다.이렇게 하면 Cluster Autoscaler가 정의된 특정 태그가 포함된 모든 오토스케일링 그룹을 찾을 수 있으므로 매니페스트에서 각 오토스케일링 그룹을 정의하고 유지할 필요가 없습니다.

### 로컬 스토리지와 함께 Cluster Autoscaler 사용

기본적으로 Cluster Autoscaler는 로컬 스토리지가 연결된 상태로 배포된 파드가 있는 노드를 축소하지 않습니다. `--skip-nodes-with-local-storage` 플래그를 false로 설정하면 Cluster Autoscaler가 이러한 노드를 축소할 수 있습니다.

### 워커 노드와 워크로드를 여러 AZ에 분산합니다.

여러 AZ에서 워커 노드와 파드를 실행하여 개별 AZ에서 장애가 발생하지 않도록 워크로드를 보호할 수 있습니다. 노드를 생성하는 서브넷을 사용하여 워커 노드가 생성되는 AZ를 제어할 수 있습니다.

쿠버네티스 1.18+를 사용하는 경우 AZ에 파드를 분산하는 데 권장되는 방법은 [파드에 대한 토폴로지 분산 제약](https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/#spread-constraints-for-pods)을 사용하는 것입니다.

아래 디플로이먼트는 가능한 경우 AZ에 파드를 분산시키고, 그렇지 않을 경우 해당 파드는 그냥 실행되도록 합니다.

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          whenUnsatisfiable: ScheduleAnyway
          topologyKey: topology.kubernetes.io/zone
          labelSelector:
            matchLabels:
              app: web-server
      containers:
      - name: web-app
        image: nginx
        resources:
          requests:
            cpu: 1
```

!!! note
    `kube-scheduler`는 해당 레이블이 있는 노드를 통한 토폴로지 도메인만 인식합니다. 위의 디플로이먼트를 단일 존에만 노드가 있는 클러스터에 배포하면, `kube-scheduler`가 다른 존을 인식하지 못하므로 모든 파드가 해당 노드에서 스케줄링됩니다. 이 Topology Spread가 스케줄러와 함께 예상대로 작동하려면 모든 존에 노드가 이미 있어야 합니다. 이 문제는 쿠버네티스 1.24에서 `MinDomainsInPodToplogySpread` [기능 게이트](https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/#api)가 추가되면서 해결될 것입니다. 이 기능을 사용하면 스케줄러에 적격 도메인 수를 알리기 위해 `MinDomains` 속성을 지정할 수 있습니다.

!!! warning
    `whenUnsatisfiable`를 `Donot Schedule`로 설정하면 Topology Spread Constraints을 충족할 수 없는 경우 파드를 스케줄링할 수 없게 됩니다. Topology Spread Constraints을 위반하는 대신 파드를 실행하지 않는 것이 더 좋은 경우에만 설정해야 합니다.

이전 버전의 쿠버네티스에서는 파드 anti-affinity 규칙을 사용하여 여러 AZ에 걸쳐 파드를 스케줄링할 수 있습니다. 아래 매니페스트는 쿠버네티스 스케줄러에게 별개의 AZ에서 파드를 스케줄링하는 것을 *선호*한다고 알려줍니다. 

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
  labels:
    app: web-server
spec:
  replicas: 4
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-server
              topologyKey: failure-domain.beta.kubernetes.io/zone
            weight: 100
      containers:
      - name: web-app
        image: nginx
```

!!! warning 
    파드를 서로 다른 AZ에 스케줄할 필요는 없습니다. 그렇지 않으면 디플로이먼트의 파드 수가 AZ 수를 절대 초과하지 않습니다. 

### EBS 볼륨을 사용할 때 각 AZ의 용량을 확보하십시오.

[Amazon EBS를 사용하여 영구 볼륨 제공](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)을 사용하는 경우 파드 및 관련 EBS 볼륨이 동일한 AZ에 있는지 확인해야 합니다. 이 글을 쓰는 시점에서 EBS 볼륨은 단일 AZ 내에서만 사용할 수 있습니다. 파드는 다른 AZ에 위치한 EBS 지원 영구 볼륨에 액세스할 수 없습니다. 쿠버네티스 [스케줄러는 워커 노드가 어느 AZ에 위치하는지 알고 있습니다](https://kubernetes.io/docs/reference/kubernetes-api/labels-annotations-taints/#topologykubernetesiozone). 쿠버네티스는 해당 볼륨과 동일한 AZ에 EBS 볼륨이 필요한 파드를 항상 스케줄링합니다. 하지만 볼륨이 위치한 AZ에 사용 가능한 워커 노드가 없는 경우 파드를 스케줄링할 수 없습니다. 

클러스터가 항상 필요한 EBS 볼륨과 동일한 AZ에 파드를 스케줄링할 수 있는 용량을 확보할 수 있도록 충분한 용량을 갖춘 각 AZ에 오토 스케일링 그룹을 생성하십시오. 또한 클러스터 오토스케일러에서 `--balance-similar-similar-node groups` 기능을 활성화해야 합니다.

EBS 볼륨을 사용하지만 가용성을 높이기 위한 요구 사항이 없는 애플리케이션을 실행 중인 경우 애플리케이션 배포를 단일 AZ로 제한할 수 있습니다. EKS에서는 워커 노드에 AZ 이름이 포함된 `failure-domain.beta.kubernetes.io/zone` 레이블이 자동으로 추가됩니다. `kubectl get nodes --show-labels`를 실행하여 노드에 첨부된 레이블을 확인할 수 있습니다. 빌트인 노드 레이블에 대한 자세한 내용은 [여기] (https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#built-in-node-labels)에서 확인할 수 있습니다. 노드 셀렉터를 사용하여 특정 AZ에서 파드를 스케줄링할 수 있습니다. 

아래 예시에서는 파드가 `us-west-2c` AZ에서만 스케줄링됩니다.

```
apiVersion: v1
kind: Pod
metadata:
  name: single-az-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: failure-domain.beta.kubernetes.io/zone
            operator: In
            values:
            - us-west-2c
  containers:
  - name: single-az-container
    image: kubernetes/pause
```

퍼시스턴트 볼륨(EBS 지원) 역시 AZ 이름으로 자동 레이블이 지정됩니다. `kubectl get pv -L topology.ebs.csi.aws.com/zone` 명령을 실행해 퍼시스턴트 볼륨이 어느 AZ에 속하는지 확인할 수 있습니다. 파드가 생성되고 볼륨을 요청하면, 쿠버네티스는 해당 볼륨과 동일한 AZ에 있는 노드에 파드를 스케줄링합니다. 

노드 그룹이 하나인 EKS 클러스터가 있는 시나리오를 생각해 보십시오. 이 노드 그룹에는 3개의 AZ에 분산된 세 개의 워커 노드가 있습니다. EBS 지원 퍼시스턴트 볼륨을 사용하는 애플리케이션이 있습니다. 이 애플리케이션과 해당 볼륨을 생성하면 해당 파드가 세 개의 AZ 중 첫 번째 AZ에 생성됩니다. 그러면 이 파드를 실행하는 워커 노드가 비정상 상태가 되고 이후에는 사용할 수 없게 된다. Cluster Autoscaler는 비정상 노드를 새 워커 노드로 교체합니다. 그러나 자동 확장 그룹이 세 개의 AZ에 걸쳐 있기 때문에 상황에 따라 새 워커 노드가 두 번째 또는 세 번째 AZ에서 시작될 수 있지만 첫 번째 AZ에서는 실행되지 않을 수 있습니다. AZ 제약이 있는 EBS 볼륨은 첫 번째 AZ에만 존재하고 해당 AZ에는 사용 가능한 워커 노드가 없으므로 파드를 스케줄링할 수 없습니다. 따라서 각 AZ에 노드 그룹을 하나씩 생성해야 합니다. 그래야 다른 AZ에서 스케줄링할 수 없는 파드를 실행할 수 있는 충분한 용량이 항상 확보됩니다. 


또는 영구 스토리지가 필요한 애플리케이션을 실행할 때 [EFS] (https://github.com/kubernetes-sigs/aws-efs-csi-driver)를 사용하여 클러스터 자동 크기 조정을 단순화할 수 있습니다. 클라이언트는 리전 내 모든 AZ에서 동시에 EFS 파일 시스템에 액세스할 수 있습니다. EFS 기반 퍼시스턴트 볼륨을 사용하는 파드가 종료되어 다른 AZ에 스케줄되더라도 볼륨을 마운트할 수 있습니다.

### 노드 문제 감지기 실행

워커 노드의 장애는 애플리케이션의 가용성에 영향을 미칠 수 있습니다. [node-problem-detector](https://github.com/kubernetes/node-problem-detector)는 클러스터에 설치하여 워커 노드 문제를 탐지할 수 있는 쿠버네티스 애드온입니다. [npd의 치료 시스템](https://github.com/kubernetes/node-problem-detector#remedy-systems)을 사용하여 노드를 자동으로 비우고 종료할 수 있습니다.

### 시스템 및 쿠버네티스 데몬을 위한 리소스 예약

[운영 체제 및 쿠버네티스 데몬을 위한 컴퓨팅 용량를 예약](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/)하여 워커 노드의 안정성을 개선할 수 있습니다. 파드, 특히 `limits`이 선언되지 않은 파드는 시스템 리소스를 포화시켜 운영체제 프로세스와 쿠버네티스 데몬 (`kubelet`, 컨테이너 런타임 등)이 시스템 리소스를 놓고 파드와 경쟁하는 상황에 놓이게 됩니다.`kubelet` 플래그 `--system-reserved`와 `--kube-reserved`를 사용하여 시스템 프로세스 (`udev`, `sshd` 등)와 쿠버네티스 데몬을 위한 리소스를 각각 예약할 수 있습니다. 

[EKS에 최적화된 Linux AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html)를 사용하는 경우 CPU, 메모리 및 스토리지는 기본적으로 시스템 및 쿠버네티스 데몬용으로 예약됩니다. 이 AMI를 기반으로 하는 워커 노드가 시작되면 [`bootstrap.sh` 스크립트](https://github.com/awslabs/amazon-eks-ami/blob/master/files/bootstrap.sh) 를 트리거하도록 EC2 사용자 데이터가 구성됩니다. 이 스크립트는 EC2 인스턴스에서 사용할 수 있는 CPU 코어 수와 총 메모리를 기반으로 CPU 및 메모리 예약을 계산합니다. 계산된 값은 `/etc/kubernetes/kubelet/kubelet-config.json`에 있는 `KubeletConfiguration` 파일에 기록됩니다. 

노드에서 사용자 지정 데몬을 실행하고 기본적으로 예약된 CPU 및 메모리 양이 충분하지 않은 경우 시스템 리소스 예약을 늘려야 할 수 있습니다. 

`eksctl`은 [시스템 및 쿠버네티스 데몬의 리소스 예약](https://eksctl.io/usage/customizing-the-kubelet/)을 사용자 지정하는 가장 쉬운 방법을 제공합니다. 

### QoS 구현

중요한 애플리케이션의 경우, 파드의 컨테이너에 대해 `requests`=`limits` 정의를 고려해보십시오. 이렇게 하면 다른 파드가 리소스를 요청하더라도 컨테이너가 종료되지 않습니다.

모든 컨테이너에 CPU 및 메모리 제한을 적용하는 것이 가장 좋습니다. 이렇게 하면 컨테이너가 실수로 시스템 리소스를 소비하여 같은 위치에 배치된 다른 프로세스의 가용성에 영향을 미치는 것을 방지할 수 있기 때문입니다.

### 모든 워크로드에 대한 리소스 요청/제한 구성 및 크기 조정

리소스 요청의 크기 조정 및 워크로드 한도에 대한 몇 가지 일반적인 지침을 적용할 수 있습니다.

- CPU에 리소스 제한을 지정하지 마십시오. 제한이 없는 경우 요청은 [컨테이너의 상대적 CPU 사용 시간](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#how-pods-with-resource-limits-are-run)에 가중치 역할을 합니다. 이렇게 하면 인위적인 제한이나 과다 현상 없이 워크로드에서 CPU 전체를 사용할 수 있습니다.

- CPU가 아닌 리소스의 경우, `requests`=`limits`를 구성하면 가장 예측 가능한 동작이 제공됩니다. 만약 `requests`!=`limits`이면, 컨테이너의 [QOS](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/#qos-classes)도 Guaranteed에서 Burstable로 감소하여 [node pressure](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/) 이벤트에 축출될 가능성이 높아졌습니다.

- CPU가 아닌 리소스의 경우 요청보다 훨씬 큰 제한을 지정하지 마십시오. `limits`이 `requests`에 비해 크게 구성될수록 노드가 오버 커밋되어 워크로드가 중단될 가능성이 높아집니다.

- [Karpenter](https://aws.github.io/aws-eks-best-practices/karpenter/) 또는 [Cluster AutoScaler](https://aws.github.io/aws-eks-best-practices/cluster-autoscaling/)와 같은 노드 자동 크기 조정 솔루션을 사용할 때는 요청 크기를 올바르게 지정하는 것이 특히 중요합니다. 이러한 도구는 워크로드 요청을 검토하여 프로비저닝할 노드의 수와 크기를 결정합니다. 요청이 너무 작아 제한이 더 큰 경우, 워크로드가 노드에 꽉 차 있으면 워크로드가 제거되거나 OOM으로 종료될 수 있습니다.

리소스 요청을 결정하는 것은 어려울 수 있지만 [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)와 같은 도구를 사용하면 런타임 시 컨테이너 리소스 사용량을 관찰하여 요청 규모를 '적정'하게 조정할 수 있습니다. 요청 크기를 결정하는 데 유용할 수 있는 다른 도구는 다음과 같습니다.

- [Goldilocks](https://github.com/FairwindsOps/goldilocks)
- [Parca](https://www.parca.dev/)
- [Prodfiler](https://prodfiler.com/)
- [rsg](https://mhausenblas.info/right-size-guide/)


### 네임스페이스의 리소스 할당량 구성

네임스페이스는 사용자가 여러 팀 또는 프로젝트에 분산되어 있는 환경에서 사용하기 위한 것입니다. 이름 범위를 제공하고 클러스터 리소스를 여러 팀, 프로젝트, 워크로드 간에 나누는 방법입니다. 네임스페이스의 총 리소스 사용량을 제한할 수 있습니다. [`ResourceQuota`](https://kubernetes.io/docs/concepts/policy/resource-quotas/) 객체는 유형별로 네임스페이스에 만들 수 있는 개체 수와 해당 프로젝트의 리소스가 소비할 수 있는 총 컴퓨팅 리소스 양을 제한할 수 있습니다. 지정된 네임스페이스에서 요청할 수 있는 스토리지 및/또는 컴퓨팅(CPU 및 메모리) 리소스의 총합을 제한할 수 있습니다.

> CPU 및 메모리와 같은 컴퓨팅 리소스의 네임스페이스에 리소스 쿼터가 활성화된 경우 사용자는 해당 네임스페이스의 각 컨테이너에 대한 요청 또는 제한을 지정해야 합니다.

각 네임스페이스에 할당량을 구성하는 것을 고려해 보십시오. 네임스페이스 내의 컨테이너에 사전 구성된 제한을 자동으로 적용하려면 `LimitRanges`를 사용해 보십시오. 

### 네임스페이스 내에서 컨테이너 리소스 사용을 제한합니다.

리소스 쿼터는 네임스페이스가 사용할 수 있는 리소스의 양을 제한하는 데 도움이 됩니다. [`LimitRange` 개체](https://kubernetes.io/docs/concepts/policy/limit-range/)는 컨테이너가 요청할 수 있는 최소 및 최대 리소스를 구현하는 데 도움이 될 수 있습니다. `LimitRange`를 사용하면 컨테이너에 대한 기본 요청 및 제한을 설정할 수 있는데, 이는 컴퓨팅 리소스 제한을 설정하는 것이 조직의 표준 관행이 아닌 경우에 유용합니다. 이름에서 알 수 있듯이, `LimitRange`는 네임스페이스의 파드 또는 컨테이너당 최소 및 최대 컴퓨팅 리소스 사용량을 적용할 수 있습니다. 또한 네임스페이스에서 퍼시스턴트볼륨클레임당 최소 및 최대 스토리지 요청을 적용할 수 있습니다.

컨테이너와 네임스페이스 수준에서 제한을 적용하려면 `LimitRange`와 `ResourceQuota`를 함께 사용하는 것이 좋습니다. 이러한 제한을 설정하면 컨테이너 또는 네임스페이스가 클러스터의 다른 테넌트가 사용하는 리소스에 영향을 주지 않도록 할 수 있습니다. 

## CoreDNS

CoreDNS는 쿠버네티스에서 이름 확인 및 서비스 검색 기능을 수행합니다. EKS 클러스터에 기본적으로 설치됩니다. 상호 운용성을 위해 CoreDNS용 쿠버네티스 서비스의 이름은 여전히 [kube-dns](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/)로 지정됩니다. CoreDNS 파드는 디플로이먼트의 일부로 `kube-system` 네임스페이스에서 실행되며, EKS에서는 기본적으로 요청과 제한이 선언된 두 개의 복제본을 실행합니다. DNS 쿼리는 `kube-system` 네임스페이스에서 실행되는 `kube-dns` 서비스로 전송됩니다.

## 권장 사항
### 핵심 DNS 지표 모니터링
CoreDNS는 [프로메테우스](https://github.com/coredns/coredns/tree/master/plugin/metrics)에 대한 지원을 내장하고 있습니다. 특히 CoreDNS 지연 시간(`coredns_dns_request_duration_seconds_sum`, [1.7.0](https://github.com/coredns/coredns/blob/master/notes/coredns-1.7.0.md) 버전 이전에는 메트릭이 `core_dns_response_rcode_count_total`이라고 불렸음), 오류 (`coredns_dns_responses_total`, NXDOMAIN, SERVFAIL, FormErr) 및 CoreDNS 파드의 메모리 사용량에 대한 모니터링을 고려해야 합니다.

문제 해결을 위해 kubectl을 사용하여 CoreDNS 로그를 볼 수 있습니다.

```shell
for p in $(kubectl get pods —namespace=kube-system -l k8s-app=kube-dns -o name); do kubectl logs —namespace=kube-system $p; done
```

### 노드 로컬 DNS 캐시 사용
[노드 로컬 DNS 캐시](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/)를 실행하여 클러스터 DNS 성능을 개선할 수 있습니다. 이 기능은 클러스터 노드에서 DNS 캐싱 에이전트를 데몬셋으로 실행합니다. 모든 파드는 이름 확인을 위해 `kube-dns` 서비스를 사용하는 대신 노드에서 실행되는 DNS 캐싱 에이전트를 사용합니다.

### CoreDNS의 cluster-proportional-scaler를 구성합니다.

클러스터 DNS 성능을 개선하는 또 다른 방법은 클러스터의 노드 및 CPU 코어 수에 따라 [CoreDNS 배포를 자동으로 수평으로 확장](https://kubernetes.io/docs/tasks/administer-cluster/dns-horizontal-autoscaling/#enablng-dns-horizontal-autoscaling)하는 것입니다. [수평 클러스터 비례 자동 확장](https://github.com/kubernetes-sigs/cluster-proportional-autoscaler/blob/master/README.md)은 스케줄 가능한 데이터 플레인의 크기에 따라 디플로이먼트의 복제본 수를 조정하는 컨테이너입니다.

노드와 노드의 CPU 코어 집계는 CoreDNS를 확장할 수 있는 두 가지 지표입니다. 두 지표를 동시에 사용할 수 있습니다. 더 큰 노드를 사용하는 경우 CoreDNS 스케일링은 CPU 코어 수를 기반으로 합니다. 반면 더 작은 노드를 사용하는 경우 CoreDNS 복제본의 수는 데이터 플레인의 CPU 코어에 따라 달라집니다. 비례 오토스케일러 구성은 다음과 같습니다.

```
linear: '{"coresPerReplica":256,"min":1,"nodesPerReplica":16}'
```

### 노드 그룹이 있는 AMI 선택
EKS는 고객이 자체 관리형 노드 그룹과 관리형 노드 그룹을 모두 생성하는 데 사용하는 최적화된 EC2 AMI를 제공합니다. 이러한 AMI는 지원되는 모든 쿠버네티스 버전에 대해 모든 리전에 게시됩니다. EKS는 CVE 또는 버그가 발견되면 이러한 AMI를 더 이상 사용되지 않는 것으로 표시합니다. 따라서 노드 그룹에 사용할 AMI를 선택할 때는 더 이상 사용되지 않는 AMI를 사용하지 않는 것이 좋습니다.

Ec2 describe-images api를 사용하여 아래 명령을 사용하여 더 이상 사용되지 않는 AMI를 필터링할 수 있습니다.

```
aws ec2 describe-images --image-id ami-0d551c4f633e7679c --no-include-deprecated
```

이미지 설명 출력에 DeprecationTime이 필드로 포함되어 있는지 확인하여 지원 중단된 AMI를 식별할 수도 있습니다. 예를 들면:

```
aws ec2 describe-images --image-id ami-xxx --no-include-deprecated
{
    "Images": [
        {
            "Architecture": "x86_64",
            "CreationDate": "2022-07-13T15:54:06.000Z",
            "ImageId": "ami-xxx",
            "ImageLocation": "123456789012/eks_xxx",
            "ImageType": "machine",
            "Public": false,
            "OwnerId": "123456789012",
            "PlatformDetails": "Linux/UNIX",
            "UsageOperation": "RunInstances",
            "State": "available",
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "DeleteOnTermination": true,
                        "SnapshotId": "snap-0993a2fc4bbf4f7f4",
                        "VolumeSize": 20,
                        "VolumeType": "gp2",
                        "Encrypted": false
                    }
                }
            ],
            "Description": "EKS Kubernetes Worker AMI with AmazonLinux2 image, (k8s: 1.19.15, docker: 20.10.13-2.amzn2, containerd: 1.4.13-3.amzn2)",
            "EnaSupport": true,
            "Hypervisor": "xen",
            "Name": "aws_eks_optimized_xxx",
            "RootDeviceName": "/dev/xvda",
            "RootDeviceType": "ebs",
            "SriovNetSupport": "simple",
            "VirtualizationType": "hvm",
            "DeprecationTime": "2023-02-09T19:41:00.000Z"
        }
    ]
}
```

