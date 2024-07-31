---
search:
  exclude: true
---


# 쿠버네티스 데이터 플레인

쿠버네티스 데이터 플레인은 쿠버네티스 컨트롤 플레인이 사용하는 EC2 인스턴스, 로드 밸런서, 스토리지 및 기타 API를 포함합니다. 조직화를 위해 [클러스터 서비스](./cluster-services.md)를 별도의 페이지로 그룹화했으며 로드 밸런서 확장은 [워크로드 섹션](./workloads.md)에서 찾을 수 있습니다. 이 섹션에서는 컴퓨팅 리소스 확장에 중점을 둡니다.

여러 워크로드가 있는 클러스터에서는 EC2 인스턴스 유형을 선택하는 것이 고객이 직면하는 가장 어려운 결정 중 하나일 수 있습니다. 모든 상황에 맞는 단일 솔루션은 없습니다. 다음은 컴퓨팅 확장과 관련된 일반적인 위험을 방지하는 데 도움이 되는 몇 가지 팁입니다.

## 자동 노드 오토 스케일링

수고를 줄이고 쿠버네티스와 긴밀하게 통합되는 노드 오토 스케일링을 사용하는 것이 좋습니다. 대규모 클러스터에는 [관리형 노드 그룹](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 및 [Karpenter](https://karpenter.sh/) 를 사용하는 것이 좋습니다.

관리형 노드 그룹은 관리형 업그레이드 및 구성에 대한 추가 이점과 함께 Amazon EC2 Auto Scaling 그룹의 유연성을 제공합니다. [쿠버네티스 Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)를 사용하여 확장할 수 있으며 다양한 컴퓨팅 요구 사항이 있는 클러스터에 대한 일반적인 옵션입니다.

Karpenter는 AWS에서 만든 오픈 소스 워크로드 네이티브 노드 오토 스케일러입니다. 노드 그룹을 관리하지 않고도 리소스 (예: GPU) 와 taint 및 tolerations (예: zone spread)에 대한 워크로드 요구 사항을 기반으로 클러스터의 노드를 확장합니다. 노드는 EC2로부터 직접 생성되므로 기본 노드 그룹 할당량 (그룹당 450개 노드)이 필요 없으며 운영 오버헤드를 줄이면서 인스턴스 선택 유연성이 향상됩니다. 고객은 가능하면 Karpenter를 사용하는 것이 좋습니다.

## 다양한 EC2 인스턴스 유형 사용

각 AWS 리전에는 인스턴스 유형별로 사용 ​​가능한 인스턴스 수가 제한되어 있습니다. 하나의 인스턴스 유형만 사용하는 클러스터를 생성하고 리전의 용량을 초과하여 노드 수를 확장하면 사용 가능한 인스턴스가 없다는 오류가 발생합니다. 이 문제를 방지하려면 클러스터에서 사용할 수 있는 인스턴스 유형을 임의로 제한해서는 안 됩니다.

Karpenter는 기본적으로 호환되는 다양한 인스턴스 유형을 사용하며 보류 중인 워크로드 요구 사항, 가용성 및 비용을 기반으로 프로비저닝 시 인스턴스를 선택합니다. [NodePools](https://karpenter.sh/docs/concepts/nodepools/#instance-types)의 `karpenter.k8s.aws/instance-category` 키에 사용되는 인스턴스 유형 목록을 정의할 수 있습니다.

쿠버네티스 Cluster Autoscaler를 사용하려면 노드 그룹이 일관되게 확장될 수 있도록 유사한 크기의 유형을 필요로 합니다. CPU 및 메모리 크기를 기준으로 여러 그룹을 생성하고 독립적으로 확장해야 합니다. [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector)를 사용하여 노드 그룹과 비슷한 크기의 인스턴스를 식별하세요.

```
ec2-instance-selector --service eks --vcpus-min 8 --memory-min 16
a1.2xlarge
a1.4xlarge
a1.metal
c4.4xlarge
c4.8xlarge
c5.12xlarge
c5.18xlarge
c5.24xlarge
c5.2xlarge
c5.4xlarge
c5.9xlarge
c5.metal
```

## API 서버 부하를 줄이기 위해 더 큰 노드를 선호

어떤 인스턴스 유형을 사용할지 결정할 때 노드 수가 적고 크면 쿠버네티스 컨트롤 플레인에 걸리는 부하가 줄어듭니다. 실행 중인 kubelet과 데몬셋의 수가 줄어들기 때문입니다. 그러나 큰 노드는 작은 노드처럼 충분히 활용되지 않을 수 있습니다. 노드 크기는 워크로드의 가용성 및 확장성을 기반으로 평가해야 합니다.

u-24tb1.metal 인스턴스 3개 (24TB Memory 및 448 cores)가 있는 클러스터에는 3개의 kubelets가 있으며 기본적으로 노드당 110개의 파드로 제한됩니다. 파드가 각각 4개의 코어를 사용하는 경우 이는 예상할 수 있습니다 (4코어 x 110 = 노드당 440코어). 클러스터에 3개의 노드를 사용하면 인스턴스 1개가 중단될 때 클러스터의 1/3에 영향을 미칠 수 있으므로 인스턴스 인시던트를 처리하는 능력이 떨어집니다. 쿠버네티스 스케줄러가 워크로드를 적절하게 배치할 수 있도록 워크로드에 노드 요구 사항과 pod spread를 지정해야 합니다.

워크로드는 taint, tolerations 및 [PodTopologySpread](https://kubernetes.io/blog/2020/05/introducing-podtopologyspread/)를 통해 필요한 리소스와 필요한 가용성을 정의해야 합니다. 이들은 컨트롤 플레인의 부하 감소, 운영 감소, 비용 절감이라는 가용성 목표를 충분히 활용할 수 있고 가용성 목표를 충족할 수 있는 가장 큰 노드를 선호해야 합니다.

쿠버네티스 Scheduler는 리소스를 사용할 수 있는 경우 가용 영역과 호스트에 워크로드를 자동으로 분산하려고 합니다. 사용 가능한 용량이 없는 경우 쿠버네티스 Cluster Autoscaler는 각 가용 영역에 노드를 균등하게 추가하려고 시도합니다. 워크로드에 다른 요구 사항이 지정되어 있지 않는 한 Karpenter는 가능한 한 빠르고 저렴하게 노드를 추가하려고 시도합니다.

스케줄러를 통해 워크로드를 분산시키고 가용 영역 전체에 새 노드를 생성하도록 하려면 TopologySpreadConstraints (topologySpreadConstraints) 를 사용해야 합니다.

```
spec:
  topologySpreadConstraints:
    - maxSkew: 3
      topologyKey: "topology.kubernetes.io/zone"
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          dev: my-deployment
    - maxSkew: 2
      topologyKey: "kubernetes.io/hostname"
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          dev: my-deployment
```

## 일관된 워크로드 성능을 위해 유사한 노드 크기 사용

워크로드는 일관된 성능과 예측 가능한 확장을 허용하기 위해 실행해야 하는 노드 크기를 정의해야 합니다. 500m CPU를 요청하는 워크로드는 4 cores 인스턴스와 16 cores 인스턴스에서 다르게 수행됩니다. T 시리즈 인스턴스와 같이 버스트 가능한 CPU를 사용하는 인스턴스 유형은 피하세요.

워크로드가 일관된 성능을 얻을 수 있도록 워크로드는 [지원되는 Karpenter 레이블](https://karpenter.sh/docs/concepts/scheduling/#labels)을 사용하여 특정 인스턴스 크기를 대상으로 할 수 있습니다.

```
kind: deployment
...
spec:
  template:
    spec:
    containers:
    nodeSelector:
      karpenter.k8s.aws/instance-size: 8xlarge
```

쿠버네티스 Cluster Autoscaler를 사용하여 클러스터에서 스케줄링되는 워크로드는 레이블 매칭을 기반으로 node selector를 노드 그룹과 일치시켜야 합니다.

```
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: eks.amazonaws.com/nodegroup
            operator: In
            values:
            - 8-core-node-group    # match your node group name
```

## 컴퓨팅 리소스를 효율적으로 사용

컴퓨팅 리소스에는 EC2 인스턴스 및 가용 영역이 포함됩니다. 컴퓨팅 리소스를 효과적으로 사용하면 확장성, 가용성, 성능이 향상되고 총 비용이 절감됩니다. 오토 스케일링 환경에서 여러 애플리케이션은 효율적인 리소스 사용량을 예측하기가 극히 어렵습니다. [Karpenter](https://karpenter.sh/)는 워크로드 요구 사항에 따라 온디맨드로 인스턴스를 프로비저닝하여 활용도와 유연성을 극대화하기 위해 만들어졌습니다.

Karpenter를 사용하면 먼저 노드 그룹을 생성하거나 특정 노드에 대한 label taint를 구성하지 않고도 워크로드에 필요한 컴퓨팅 리소스 유형을 선언할 수 있습니다. 자세한 내용은 [Karpenter best practices](https://aws.github.io/aws-eks-best-practices/karpenter/)를 참조하세요. Karpenter provisioner에서 [consolidation](https://aws.github.io/aws-eks-best-practices/karpenter/#configure-requestslimits-for-all-non-cpu-resources-when-using-consolidation)을 활성화하여 활용도가 낮은 노드를 교체해 보세요.

## Amazon Machine Image (AMI) 업데이트 자동화

Worker 노드 구성 요소를 최신 상태로 유지하면 최신 보안 패치와 쿠버네티스 API와 호환되는 기능을 사용할 수 있습니다. kublet 업데이트는 쿠버네티스 기능의 가장 중요한 구성 요소이지만 OS, 커널 및 로컬에 설치된 애플리케이션 패치를 자동화하면 확장에 따른 유지 관리 비용을 줄일 수 있습니다.

노드 이미지에는 최신 [Amazon EKS optimized Amazon Linux 2](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) 또는 [Amazon EKS optimized Bottlerocket AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami-bottlerocket.html)를 사용하는 것이 좋습니다. Karpenter는 [사용 가능한 최신 AMI](https://karpenter.sh/docs/concepts/nodepools/#instance-types) 를 자동으로 사용하여 클러스터에 새 노드를 프로비저닝합니다. 관리형 노드 그룹은 [노드 그룹 업데이트](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html) 중에 AMI를 업데이트하지만 노드 프로비저닝 시에는 AMI ID를 업데이트하지 않습니다.

관리형 노드 그룹의 경우 패치 릴리스에 사용할 수 있게 되면 Auto Scaling Group (ASG) 시작 템플릿을 새 AMI ID로 업데이트해야 합니다. AMI 마이너 버전 (예: 1.23.5~1.24.3)은 EKS 콘솔 및 API에서 [노드 그룹 업그레이드](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html)로 제공됩니다. 패치 릴리스 버전 (예: 1.23.5 ~ 1.23.6)은 노드 그룹에 대한 업그레이드로 제공되지 않습니다. AMI 패치 릴리스를 통해 노드 그룹을 최신 상태로 유지하려면 새 시작 템플릿 버전을 생성하고 노드 그룹이 인스턴스를 새 AMI 릴리스로 교체하도록 해야 합니다.

[이 페이지](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) 에서 사용 가능한 최신 AMI를 찾거나 AWS CLI를 사용할 수 있습니다.

```
aws ssm get-parameter \
  --name /aws/service/eks/optimized-ami/1.24/amazon-linux-2/recommended/image_id \
  --query "Parameter.Value" \
  --output text
```
## 컨테이너에 여러 EBS 볼륨 사용

EBS 볼륨에는 볼륨 유형 (예: gp3) 및 디스크 크기에 따른 입/출력 (I/O) 할당량이 있습니다. 애플리케이션이 호스트와 단일 EBS 루트 볼륨을 공유하는 경우 전체 호스트의 디스크 할당량이 고갈되고 다른 애플리케이션이 가용 용량을 기다리게 될 수 있습니다.응 용 프로그램은 오버레이 파티션에 파일을 쓰고, 호스트에서 로컬 볼륨을 마운트하고, 사용된 로깅 에이전트에 따라 표준 출력 (STDOUT)에 로그온할 때도 디스크에 기록합니다.

Disk I/O 소모를 방지하려면 두 번째 볼륨을 컨테이너 state 폴더 (예: /run/containerd)에 마운트하고, 워크로드 스토리지용으로 별도의 EBS 볼륨을 사용하고, 불필요한 로컬 로깅을 비활성화해야 합니다.

[eksctl](https://eksctl.io/)을 사용하여 EC2 인스턴스에 두 번째 볼륨을 마운트하려면 다음과 같은 구성의 노드 그룹을 사용할 수 있습니다.

```
managedNodeGroups:
  - name: al2-workers
    amiFamily: AmazonLinux2
    desiredCapacity: 2
    volumeSize: 80
    additionalVolumes:
      - volumeName: '/dev/sdz'
        volumeSize: 100
    preBootstrapCommands:
    - |
      "systemctl stop containerd"
      "mkfs -t ext4 /dev/nvme1n1"
      "rm -rf /var/lib/containerd/*"
      "mount /dev/nvme1n1 /var/lib/containerd/"
      "systemctl start containerd"
```

Terraform을 사용하여 노드 그룹을 프로비저닝하는 경우 [EKS Blueprints for terraform](https://aws-ia.github.io/terraform-aws-eks-blueprints/patterns/stateful/#eks-managed-nodegroup-w-multiple-volumes)의 예를 참조하세요. Karpenter를 사용하여 노드를 프로비저닝하는 경우 노드 사용자 데이터와 함께 [`blockDeviceMappings`](https://karpenter.sh/docs/concepts/nodeclasses/#specblockdevicemappings)를 사용하여 추가 볼륨을 추가할 수 있습니다.

EBS 볼륨을 파드에 직접 탑재하려면 [AWS EBS CSI 드라이버](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)를 사용하고 스토리지 클래스가 있는 볼륨을 사용해야 합니다.

```
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 4Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: public.ecr.aws/docker/library/nginx
    volumeMounts:
    - name: persistent-storage
      mountPath: /data
  volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: ebs-claim
```

## 워크로드에서 EBS 볼륨을 사용하는 경우 EBS 연결 제한이 낮은 인스턴스를 피하세요.

EBS는 워크로드가 영구 스토리지를 확보하는 가장 쉬운 방법 중 하나이지만 확장성 제한도 있습니다. 각 인스턴스 유형에는 [연결할 수 있는 최대 EBS 볼륨](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html) 수가 있습니다. 워크로드는 실행해야 하는 인스턴스 유형을 선언하고 쿠버네티스 taints가 있는 단일 인스턴스의 복제본 수를 제한해야 합니다.

## 디스크에 불필요한 로깅을 비활성화

프로덕션 환경에서 디버그 로깅을 사용하여 애플리케이션을 실행하지 않고 디스크를 자주 읽고 쓰는 로깅을 비활성화하여 불필요한 로컬 로깅을 피하세요. Journald는 로그 버퍼를 메모리에 유지하고 주기적으로 디스크에 플러시하는 로컬 로깅 서비스입니다. Journald는 모든 행을 즉시 디스크에 기록하는 syslog보다 선호됩니다. syslog를 비활성화하면 필요한 총 스토리지 용량도 줄어들고 복잡한 로그 순환 규칙이 필요하지 않습니다. syslog를 비활성화하려면 cloud-init 구성에 다음 코드 조각을 추가하면 됩니다.

```
runcmd:
  - [ systemctl, disable, --now, syslog.service ]
```

## OS 업데이트 속도가 필요할 때 in place 방식으로 인스턴스 패치

!!! Attention
    인스턴스 패치는 필요한 경우에만 수행해야 합니다. Amazon에서는 인프라를 변경할 수 없는 것으로 취급하고 애플리케이션과 동일한 방식으로 하위 환경을 통해 승격되는 업데이트를 철저히 테스트할 것을 권장합니다. 이 섹션은 이것이 불가능할 때 적용됩니다.

컨테이너화된 워크로드를 중단하지 않고 기존 Linux 호스트에 패키지를 설치하는 데 몇 초 밖에 걸리지 않습니다. 인스턴스를 차단(cordoning), 드레이닝(draining) 또는 교체(replacing)하지 않고도 패키지를 설치하고 검증할 수 있습니다.

인스턴스를 교체하려면 먼저 새 AMI를 생성, 검증 및 배포해야 합니다. 인스턴스에는 대체 인스턴스가 생성되어야 하며, 이전 인스턴스는 차단 및 제거되어야 합니다. 그런 다음 새 인스턴스에 워크로드를 생성하고 확인하고 패치가 필요한 모든 인스턴스에 대해 반복해야 합니다. 워크로드를 중단하지 않고 인스턴스를 안전하게 교체하려면 몇 시간, 며칠 또는 몇 주가 걸립니다.

Amazon에서는 자동화된 선언적 시스템에서 구축, 테스트 및 승격되는 불변 인프라를 사용할 것을 권장합니다. 하지만 시스템에 신속하게 패치를 적용해야 하는 경우 시스템을 패치하고 새 AMI가 출시되면 교체해야 합니다. 시스템 패치와 교체 사이의 시간 차이가 크기 때문에 [AWS Systems Manager Patch Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-patch.html)를 사용하는 것이 좋습니다. 필요한 경우 노드 패치를 자동화합니다.

노드 패치를 사용하면 보안 업데이트를 신속하게 출시하고 AMI가 업데이트된 후 정기적인 일정에 따라 인스턴스를 교체할 수 있습니다. [Flatcar Container Linux](https://platcar-linux.org/) 또는 [Bottlerocket OS](https://github.com/bottlerocket-os/bottlerocket)와 같은 읽기 전용 루트 파일 시스템이 있는 운영 체제를 사용하는 경우 해당 운영 체제에서 작동하는 업데이트 연산자를 사용하는 것이 좋습니다. [Flatcar Linux update operator](https://github.com/platcar/platcar-linux-update-operator) 및 [Bottlerocket update operator](https://github.com/bottlerocket-os/bottlerocket-update-operator)는 인스턴스를 재부팅하여 노드를 자동으로 최신 상태로 유지합니다.
