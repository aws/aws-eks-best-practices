---
search:
  exclude: true
---


# Karpenter 모범 사례

## Karpenter

Karpenter는 unschedulable 파드에 대응하여 새 노드를 자동으로 프로비저닝하는 오픈 소스 클러스터 오토스케일러입니다. Karpenter는 pending 상태의 파드의 전체 리소스 요구 사항을 평가하고 이를 실행하기 위한 최적의 인스턴스 유형을 선택합니다. 데몬셋이 아닌 파드가 없는 인스턴스를 자동으로 확장하거나 종료하여 낭비를 줄입니다. 또한 파드를 능동적으로 이동하고 노드를 삭제하거나 더 저렴한 인스턴스 유형으로 교체하여 클러스터 비용을 절감하는 통합 기능도 지원합니다.

**Karpenter를 사용해야 하는 이유**

Karpenter가 출시되기 전에 쿠버네티스 사용자는 주로 [Amazon EC2 Auto Scaling 그룹](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html)과 [쿠버네티스 Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)(CA)를 사용하여 클러스터의 컴퓨팅 용량을 동적으로 조정했습니다. Karpenter를 사용하면 유연성과 다양성을 달성하기 위해 수십 개의 노드 그룹을 만들 필요가 없습니다. 게다가 Karpenter는 (CA처럼) 쿠버네티스 버전과 밀접하게 연결되어 있지 않기 때문에 AWS와 쿠버네티스 API 사이를 오갈 필요가 없습니다.

Karpenter는 단일 시스템 내 인스턴스 오케스트레이션 기능을 통합적으로 수행하며 더 간단하고 안정적이며 보다 클러스터를 잘 파악합니다. Karpenter는 다음과 같은 간소화된 방법을 제공하여 클러스터 오토스케일러가 제시하는 몇 가지 문제를 해결하도록 설계되었습니다.

* 워크로드 요구 사항에 따라 노드를 프로비저닝합니다.
* 유연한 워크로드 프로비저너 옵션을 사용하여 인스턴스 유형별로 다양한 노드 구성을 생성합니다. Karpenter를 사용하면 많은 특정 사용자 지정 노드 그룹을 관리하는 대신 유연한 단일 프로비저너로 다양한 워크로드 용량을 관리할 수 있습니다.
* 노드를 빠르게 시작하고 파드를 스케줄링하여 대규모 파드 스케줄링을 개선합니다.

Karpenter 사용에 대한 정보 및 설명서를 보려면 [karpenter.sh](https://karpenter.sh/) 사이트를 방문하세요.

## 권장 사항

모범 사례는 Karpenter, 프로비저너(provisioner), 파드 스케줄링 섹션으로 구분됩니다.

## Karpenter 모범 사례

다음 모범 사례는 Karpenter 자체와 관련된 주제를 다룹니다.

### 변화하는 용량 요구가 있는 워크로드에는 Karpenter를 사용하세요

Karpenter는 [Auto Scaling 그룹](https://aws.amazon.com/blogs/containers/amazon-eks-cluster-multi-zone-auto-scaling-groups/)(ASG) 및 [관리형 노드 그룹](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)(MNG)보다 쿠버네티스 네이티브 API에 더 가까운 스케일링 관리를 제공합니다. ASG 및 MNG는 EC2 CPU 부하와 같은 AWS 레벨 메트릭을 기반으로 스케일링이 트리거되는 AWS 네이티브 추상화입니다. [Cluster Autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html#cluster-autoscaler)는 쿠버네티스 추상화를 AWS 추상화로 연결하지만, 이로 인해 특정 가용영역에 대한 스케줄링과 같은 유연성이 다소 떨어집니다.

Karpenter는 일부 유연성을 쿠버네티스에 직접 적용하기 위해 AWS 추상화 계층을 제거합니다. Karpenter는 수요가 급증하는 시기에 직면하거나 다양한 컴퓨팅 요구 사항이 있는 워크로드가 있는 클러스터에 가장 적합합니다.MNG와 ASG는 정적이고 일관성이 높은 워크로드를 실행하는 클러스터에 적합합니다. 요구 사항에 따라 동적으로 관리되는 노드와 정적으로 관리되는 노드를 혼합하여 사용할 수 있습니다.

### 다음과 같은 경우에는 다른 Auto Scaling 프로젝트를 고려합니다.

Karpenter에서 아직 개발 중인 기능이 필요합니다. Karpenter는 비교적 새로운 프로젝트이므로 아직 Karpenter에 포함되지 않은 기능이 필요한 경우 당분간 다른 오토스케일링 프로젝트를 고려해 보세요.

### EKS Fargate 또는 노드 그룹에 속한 워커 노드에서 Karpenter 컨트롤러를 실행합니다.

Karpenter는 [헬름 차트](https://karpenter.sh/docs/getting-started/)를 사용하여 설치됩니다. 이 헬름 차트는 Karpenter 컨트롤러와 웹훅 파드를 디플로이먼트로 설치하는데, 이 디플로이먼트를 실행해야 컨트롤러를 사용하여 클러스터를 확장할 수 있습니다. 최소 하나 이상의 워커 노드가 있는 소규모 노드 그룹을 하나 이상 사용하는 것이 좋습니다. 대안으로, 'karpenter' 네임스페이스에 대한 Fargate 프로파일을 생성하여 EKS Fargate에서 이런 파드를 실행할 수 있습니다. 이렇게 하면 이 네임스페이스에 배포된 모든 파드가 EKS Fargate에서 실행됩니다. Karpenter가 관리하는 노드에서는 Karpenter를 실행하지 마십시오.

### Karpenter에서 사용자 지정 시작 템플릿(launch template)을 사용하지 마십시오.

Karpenter는 사용자 지정 시작 템플릿을 사용하지 말 것을 강력히 권장합니다. 사용자 지정 시작 템플릿을 사용하면 멀티 아키텍처 지원, 노드 자동 업그레이드 기능 및 보안그룹 검색이 불가능합니다. 시작 템플릿을 사용하면 Karpenter 프로비저너 내에서 특정 필드가 중복되고 Karpenter는 다른 필드(예: 서브넷 및 인스턴스 유형)를 무시하기 때문에 혼동이 발생할 수도 있습니다.

사용자 지정 사용자 데이터(EC2 User Data)를 사용하거나 AWS 노드 템플릿에서 사용자 지정 AMI를 직접 지정하면 시작 템플릿 사용을 피할 수 있는 경우가 많습니다. 이 작업을 수행하는 방법에 대한 자세한 내용은 [노드 템플릿](https://karpenter.sh/docs/concepts/node-templates)에서 확인할 수 있습니다.


### 워크로드에 맞지 않는 인스턴스 유형은 제외합니다.

특정 인스턴스 유형이 클러스터에서 실행되는 워크로드에 필요하지 않은 경우, [node.kubernetes.io/instance-type](http://node.kubernetes.io/instance-type) 키에서 해당 인스턴스 유형을 제외하는 것이 좋습니다.

다음 예제는 큰 Graviton 인스턴스의 프로비저닝을 방지하는 방법을 보여줍니다.

```yaml
- key: node.kubernetes.io/instance-type
    operator: NotIn
    values:
      'm6g.16xlarge'
      'm6gd.16xlarge'
      'r6g.16xlarge'
      'r6gd.16xlarge'
      'c6g.16xlarge'
```

### 스팟 사용 시 인터럽트 핸들링 활성화

Karpenter는 [설정](https://karpenter.sh/docs/concepts/settings/#configmap)에서 `aws.interruptionQueue` 값을 통해 [네이티브 인터럽트 처리](https://karpenter.sh/docs/concepts/deprovisioning/#interruption)를 지원합니다. 인터럽트 핸들링은 다음과 같이 워크로드에 장애를 일으킬 수 있는 향후 비자발적 인터럽트 이벤트를 감시합니다.

* 스팟 인터럽트 경고
* 예정된 변경 상태 이벤트 (유지 관리 이벤트)
* 인스턴스 종료 이벤트
* 인스턴스 중지 이벤트

Karpenter는 노드에서 이런 이벤트 중 하나가 발생할 것을 감지하면 중단 이벤트가 발생하기 전에 노드를 자동으로 차단(cordon), 드레인 및 종료하여 중단 전에 워크로드를 정리할 수 있는 최대 시간을 제공합니다. [해당 글](https://karpenter.sh/docs/faq/#interruption-handling)에서 설명한 것처럼 AWS Node Termination Handler를 Karpenter와 함께 사용하는 것은 권장되지 않습니다.

종료 전 2분이 소요되는 체크포인트 또는 기타 형태의 정상적인 드레인이 필요한 파드는 해당 클러스터에서 Karpenter 중단 처리가 가능해야 합니다.

### **아웃바운드 인터넷 액세스가 없는 Amazon EKS 프라이빗 클러스터**

인터넷 연결 경로 없이 VPC에 EKS 클러스터를 프로비저닝할 때는 EKS 설명서에 나와 있는 프라이빗 클러스터 [요구 사항](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html#private-cluster-requirements)에 따라 환경을 구성했는지 확인해야 합니다. 또한 VPC에 STS VPC 지역 엔드포인트를 생성했는지 확인해야 합니다. 그렇지 않은 경우 아래와 비슷한 오류가 표시됩니다.

```console
ERROR controller.controller.metrics Reconciler error {"commit": "5047f3c", "reconciler group": "karpenter.sh", "reconciler kind": "Provisioner", "name": "default", "namespace": "", "error": "fetching instance types using ec2.DescribeInstanceTypes, WebIdentityErr: failed to retrieve credentials\ncaused by: RequestError: send request failed\ncaused by: Post \"https://sts.<region>.amazonaws.com/\": dial tcp x.x.x.x:443: i/o timeout"}
```

Karpenter 컨트롤러는 서비스 어카운트용 IAM 역할(IRSA)을 사용하기 때문에 프라이빗 클러스터에서는 이런 변경이 필요합니다. IRSA로 구성된 파드는 AWS 보안 토큰 서비스 (AWS STS) API를 호출하여 자격 증명을 획득합니다. 아웃바운드 인터넷 액세스가 없는 경우 ***VPC안에서 AWS STS VPC 엔드포인트***를 생성하여 사용해야 합니다.

또한 프라이빗 클러스터를 사용하려면 ***SSM용VPC 엔드포인트***를 생성해야 합니다. Karpenter는 새 노드를 프로비저닝하려고 할 때 시작 템플릿 구성과 SSM 파라미터를 쿼리합니다. VPC에 SSM VPC 엔드포인트가 없는 경우 다음과 같은 오류가 발생합니다.

```console
INFO    controller.provisioning Waiting for unschedulable pods  {"commit": "5047f3c", "provisioner": "default"}
INFO    controller.provisioning Batched 3 pods in 1.000572709s  {"commit": "5047f3c", "provisioner": "default"}
INFO    controller.provisioning Computed packing of 1 node(s) for 3 pod(s) with instance type option(s) [c4.xlarge c6i.xlarge c5.xlarge c5d.xlarge c5a.xlarge c5n.xlarge m6i.xlarge m4.xlarge m6a.xlarge m5ad.xlarge m5d.xlarge t3.xlarge m5a.xlarge t3a.xlarge m5.xlarge r4.xlarge r3.xlarge r5ad.xlarge r6i.xlarge r5a.xlarge]        {"commit": "5047f3c", "provisioner": "default"}
ERROR   controller.provisioning Could not launch node, launching instances, getting launch template configs, getting launch templates, getting ssm parameter, RequestError: send request failed
caused by: Post "https://ssm.<region>.amazonaws.com/": dial tcp x.x.x.x:443: i/o timeout  {"commit": "5047f3c", "provisioner": "default"}
```

***[가격 목록 쿼리 API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-pelong.html)를 위한 VPC 엔드포인트*** 는 없습니다.
결과적으로 가격 데이터는 시간이 지남에 따라 부실해질 것입니다. 
Karpenter는 바이너리에 온디맨드 가격 책정 데이터를 포함하여 이 문제를 해결하지만 Karpenter가 업그레이드될 때만 해당 데이터를 업데이트합니다.
가격 데이터 요청이 실패하면 다음과 같은 오류 메시지가 표시됩니다.

```console
ERROR   controller.aws.pricing  updating on-demand pricing, RequestError: send request failed
caused by: Post "https://api.pricing.us-east-1.amazonaws.com/": dial tcp 52.94.231.236:443: i/o timeout; RequestError: send request failed
caused by: Post "https://api.pricing.us-east-1.amazonaws.com/": dial tcp 52.94.231.236:443: i/o timeout, using existing pricing data from 2022-08-17T00:19:52Z  {"commit": "4b5f953"}
```

요약하자면 완전한 프라이빗 EKS 클러스터에서 Karpenter를 사용하려면 다음과 같은 VPC 엔드포인트를 생성해야 합니다.

```console
com.amazonaws.<region>.ec2
com.amazonaws.<region>.ecr.api
com.amazonaws.<region>.ecr.dkr
com.amazonaws.<region>.s3 – For pulling container images
com.amazonaws.<region>.sts – For IAM roles for service accounts
com.amazonaws.<region>.ssm - If using Karpenter
```

!!! note
    Karpenter (컨트롤러 및 웹훅 배포) 컨테이너 이미지는 Amazon ECR 전용 또는 VPC 내부에서 액세스할 수 있는 다른 사설 레지스트리에 있거나 복사되어야 합니다.그 이유는 Karpenter 컨트롤러와 웹훅 파드가 현재 퍼블릭 ECR 이미지를 사용하고 있기 때문입니다. VPC 내에서 또는 VPC와 피어링된 네트워크에서 이런 이미지를 사용할 수 없는 경우, 쿠버네티스가 ECR Public에서 이런 이미지를 가져오려고 할 때 이미지 가져오기 오류가 발생합니다.

자세한 내용은 [이슈 988](https://github.com/aws/karpenter/issues/988) 및 [이슈 1157](https://github.com/aws/karpenter/issues/1157) 을 참조하십시오.

## 프로비져너 생성

다음 모범 사례는 프로비져너 생성과 관련된 주제를 다룹니다.

### 다음과 같은 경우 프로비져너를 여러 개 만들 수 있습니다.

여러 팀이 클러스터를 공유하고 서로 다른 워커 노드에서 워크로드를 실행해야 하거나 OS 또는 인스턴스 유형 요구 사항이 다른 경우 여러 프로비저너를 생성하세요. 예를 들어 한 팀은 Bottlerocket을 사용하고 다른 팀은 Amazon Linux를 사용하려고 할 수 있습니다. 마찬가지로 한 팀은 다른 팀에는 필요하지 않은 값비싼 GPU 하드웨어를 사용할 수 있습니다. 프로비저닝 도구를 여러 개 사용하면 각 팀에서 가장 적합한 자산을 사용할 수 있습니다.

### 상호 배타적이거나 가중치가 부여되는 프로비저닝 도구 만들기

일관된 스케줄링 동작을 제공하려면 상호 배타적이거나 가중치가 부여되는 프로비저너를 만드는 것이 좋습니다. 일치하지 않고 여러 프로비져너가 일치하는 경우 Karpenter는 사용할 프로비져너를 임의로 선택하여 예상치 못한 결과를 초래합니다. 여러 프로비져너를 만들 때 유용한 예는 다음과 같습니다.

GPU를 사용하여 프로비저닝 도구를 만들고 이런 (비용이 많이 드는) 노드에서만 특수 워크로드를 실행하도록 허용:

```yaml
# Provisioner for GPU Instances with Taints
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: gpu
spec:
  requirements:
  - key: node.kubernetes.io/instance-type
    operator: In
    values:
    - p3.8xlarge
    - p3.16xlarge
  taints:
  - effect: NoSchedule
    key: nvidia.com/gpu
    value: "true"
  ttlSecondsAfterEmpty: 60
```

태인트(Taint)를 위한 톨러레이션(Toleration)을 갖고 있는 디플로이먼트: 

```yaml
# Deployment of GPU Workload will have tolerations defined
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inflate-gpu
spec:
  ...
    spec:
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
```

다른 팀을 위한 일반 디플로이먼트의 경우 프로비저너 사양에 NodeAffinify가 포함될 수 있습니다. 그러면 디플로이먼트는 노드 셀렉터 용어를 사용하여 `billing-team` 과 일치시킬 수 있습니다.

```yaml
# Provisioner for regular EC2 instances
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: generalcompute
spec:
  labels:
    billing-team: my-team
  requirements:
  - key: node.kubernetes.io/instance-type
    operator: In
    values:
    - m5.large
    - m5.xlarge
    - m5.2xlarge
    - c5.large
    - c5.xlarge
    - c5a.large
    - c5a.xlarge
    - r5.large
    - r5.xlarge
```

노드 어피니티를 사용하는 디플로이먼트:

```yaml
# Deployment will have spec.affinity.nodeAffinity defined
kind: Deployment
metadata:
  name: workload-my-team
spec:
  replicas: 200
  ...
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                - key: "billing-team"
                  operator: "In"
                  values: ["my-team"]
```

### 타이머(TTL)를 사용하여 클러스터에서 노드를 자동으로 삭제합니다.

프로비저닝된 노드의 타이머를 사용하여 워크로드 파드가 없거나 만료 시간에 도달한 노드를 삭제할 시기를 설정할 수 있습니다. 노드 만료를 업그레이드 수단으로 사용하여 노드를 폐기하고 업데이트된 버전으로 교체할 수 있습니다. **`ttlSecondsUntilExpired`** 및 **`ttlSecondsAfterEmpty`**를 사용하여 노드를 프로비저닝 해제하는 방법에 대한 자세한 내용은 Karpenter 설명서의 [Karpenter 노드 디프로비저닝 방법](https://karpenter.sh/docs/concepts/deprovisioning)을 참조하십시오.

### 특히 스팟을 사용할 때는 Karpenter가 프로비저닝할 수 있는 인스턴스 유형을 지나치게 제한하지 마십시오.

스팟을 사용할 때 Karpenter는 [가격 및 용량 최적화](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-fleet-allocation-strategy.html) 할당 전략을 사용하여 EC2 인스턴스를 프로비저닝합니다. 이 전략은 EC2가 시작 중인 인스턴스 수만큼 가장 깊은 풀의 인스턴스를 프로비저닝하고 중단 위험이 가장 적은 인스턴스 수에 맞게 인스턴스를 프로비저닝하도록 지시합니다. 그런 다음 EC2 플릿은 이런 풀 중 가장 저렴한 가격의 스팟 인스턴스를 요청합니다. Karpenter에 사용할 수 있는 인스턴스 유형이 많을수록 EC2는 스팟 인스턴스의 런타임을 더 잘 최적화할 수 있습니다. 기본적으로 Karpenter는 클러스터가 배포된 지역 및 가용영역에서 EC2가 제공하는 모든 인스턴스 유형을 사용합니다. Karpenter는 보류 중인 파드를 기반으로 모든 인스턴스 유형 세트 중에서 지능적으로 선택하여 파드가 적절한 크기와 장비를 갖춘 인스턴스로 스케줄링되도록 합니다. 예를 들어, 파드에 GPU가 필요하지 않은 경우 Karpenter는 GPU를 지원하는 EC2 인스턴스 유형으로 파드를 예약하지 않습니다. 어떤 인스턴스 유형을 사용해야 할지 확실하지 않은 경우 Amazon [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector)를 실행하여 컴퓨팅 요구 사항에 맞는 인스턴스 유형 목록을 생성할 수 있습니다. 예를 들어 CLI는 메모리 vCPU,아키텍처 및 지역을 입력 파라미터로 사용하고 이런 제약 조건을 충족하는 EC2 인스턴스 목록을 제공합니다.

```console
$ ec2-instance-selector --memory 4 --vcpus 2 --cpu-architecture x86_64 -r ap-southeast-1
c5.large
c5a.large
c5ad.large
c5d.large
c6i.large
t2.medium
t3.medium
t3a.medium
```

스팟 인스턴스를 사용할 때 Karpenter에 너무 많은 제약을 두어서는 안 됩니다. 그렇게 하면 애플리케이션의 가용성에 영향을 미칠 수 있기 때문입니다. 예를 들어 특정 유형의 모든 인스턴스가 회수되고 이를 대체할 적절한 대안이 없다고 가정해 보겠습니다. 구성된 인스턴스 유형의 스팟 용량이 보충될 때까지 파드는 보류 상태로 유지됩니다. 스팟 풀은 AZ마다 다르기 때문에 여러 가용영역에 인스턴스를 분산하여 용량 부족 오류가 발생할 위험을 줄일 수 있습니다. 하지만 일반적인 모범 사례는 Karpenter가 스팟을 사용할 때 다양한 인스턴스 유형 세트를 사용할 수 있도록 하는 것입니다.

## 스케줄링 파드

다음 모범 사례는 노드 프로비저닝을 위해 Karpenter를 사용하여 클러스터에 파드를 배포하는 것과 관련이 있습니다.

### 고가용성을 위한 EKS 모범 사례를 따르십시오.

고가용성 애플리케이션을 실행해야 하는 경우 일반적인 EKS 모범 사례 [권장 사항](https://aws.github.io/aws-eks-best-practices/reliability/docs/application/#recommendations)을 따르십시오. 여러 노드와 영역에 파드를 분산하는 방법에 대한 자세한 내용은 Karpenter 설명서의 [토폴로지 확산](https://karpenter.sh/docs/concepts/scheduling/#topology-spread)을 참조하십시오. 파드를 제거하거나 삭제하려는 시도가 있는 경우 [중단 예산(Disruption Budgets)](https://karpenter.sh/docs/troubleshooting/#disruption-budgets)을 사용하여 유지 관리가 필요한 최소 가용 파드를 설정하세요.

### 계층화된 제약 조건을 사용하여 클라우드 공급자가 제공하는 컴퓨팅 기능을 제한하십시오.

Karpenter의 계층형 제약 조건 모델을 사용하면 복잡한 프로비저너 및 파드 배포 제약 조건 세트를 생성하여 파드 스케줄링에 가장 적합한 조건을 얻을 수 있습니다. 파드 사양이 요청할 수 있는 제약 조건의 예는 다음과 같습니다.

* 특정 애플리케이션만 사용할 수 있는 가용영역에서 실행해야 합니다. 예를 들어 특정 가용영역에 있는 EC2 인스턴스에서 실행되는 다른 애플리케이션과 통신해야 하는 파드가 있다고 가정해 보겠습니다. VPC의 AZ 간 트래픽을 줄이는 것이 목표라면 EC2 인스턴스가 위치한 AZ에 파드를 같은 위치에 배치하는 것이 좋습니다. 이런 종류의 타겟팅은 대개 노드 셀렉터를 사용하여 수행됩니다. [노드 셀렉터](https://karpenter.sh/docs/concepts/scheduling/#selecting-nodes)에 대한 추가 정보는 쿠버네티스 설명서를 참조하십시오.
* 특정 종류의 프로세서 또는 기타 하드웨어가 필요합니다. GPU에서 파드를 실행해야 하는 팟스펙 예제는 Karpenter 문서의 [액셀러레이터](https://karpenter.sh/docs/concepts/scheduling/#acceleratorsgpu-resources)섹션을 참조하십시오.

### 결제 경보를 생성하여 컴퓨팅 지출을 모니터링하세요

클러스터를 자동으로 확장하도록 구성할 때는 지출이 임계값을 초과했을 때 경고하는 청구 알람를 생성하고 Karpenter 구성에 리소스 제한을 추가해야 합니다. Karpenter로 리소스 제한을 설정하는 것은 Karpenter 프로비저너가 인스턴스화할 수 있는 컴퓨팅 리소스의 최대량을 나타낸다는 점에서 AWS Autoscaling 그룹의 최대 용량을 설정하는 것과 비슷합니다.

!!! note
    전체 클러스터에 대해 글로벌 제한을 설정할 수는 없습니다. 한도는 특정 프로비저너에 적용됩니다.

아래 스니펫은 Karpenter에게 최대 1000개의 CPU 코어와 1000Gi의 메모리만 프로비저닝하도록 지시합니다. Karpenter는 한도에 도달하거나 초과할 때만 용량 추가를 중단합니다. 한도를 초과하면 Karpenter 컨트롤러는 '1001의 메모리 리소스 사용량이 한도 1000을 초과합니다' 또는 이와 비슷한 모양의 메시지를 컨트롤러 로그에 기록합니다. 컨테이너 로그를 CloudWatch 로그로 라우팅하는 경우 [지표 필터](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html)를 생성하여 로그에서 특정 패턴이나 용어를 찾은 다음 [CloudWatch 알람](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)을 생성하여 구성된 지표 임계값을 위반했을 때 경고를 보낼 수 있습니다.

Karpenter에서 제한을 사용하는 자세한 내용은 Karpenter 설명서의 [리소스 제한 설정](https://karpenter.sh/docs/concepts/provisioners/#speclimitsresources)을 참조하십시오.

```yaml
spec:
  limits:
    resources:
      cpu: 1000
      memory: 1000Gi
```

Karpenter가 프로비저닝할 수 있는 인스턴스 유형을 제한하거나 제한하지 않는 경우 Karpenter는 필요에 따라 클러스터에 컴퓨팅 파워를 계속 추가합니다. Karpenter를 이런 방식으로 구성하면 클러스터를 자유롭게 확장할 수 있지만 비용에도 상당한 영향을 미칠 수 있습니다. 이런 이유로 결제 경보를 구성하는 것이 좋습니다. 청구 경보를 사용하면 계정에서 계산된 예상 요금이 정의된 임계값을 초과할 경우 알림을 받고 사전에 알림을 받을 수 있습니다. 자세한 내용은 [예상 요금을 사전에 모니터링하기 위한 Amazon CloudWatch 청구 경보 설정](https://aws.amazon.com/blogs/mt/setting-up-an-amazon-cloudwatch-billing-alarm-to-proactively-monitor-estimated-charges/)을 참조하십시오.

기계 학습을 사용하여 비용과 사용량을 지속적으로 모니터링하여 비정상적인 지출을 감지하는 AWS 비용 관리 기능인 비용 예외 탐지를 활성화할 수도 있습니다. 자세한 내용은 [AWS 비용 이상 탐지 시작](https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html) 가이드에서 확인할 수 있습니다. AWS Budgets에서 예산을 편성한 경우, 특정 임계값 위반 시 알림을 받도록 조치를 구성할 수도 있습니다. 예산 활동을 통해 이메일을 보내거나, SNS 주제에 메시지를 게시하거나, Slack과 같은 챗봇에 메시지를 보낼 수 있습니다. 자세한 내용은 [AWS 예산 작업 구성](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)을 참조하십시오.

### 제거 금지(do-not-evict) 어노테이션 사용하여 Karpenter가 노드 프로비저닝을 취소하지 못하도록 하세요.

Karpenter가 프로비저닝한 노드에서 중요한 애플리케이션(예: *장기 실행* 배치 작업 또는 스테이트풀 애플리케이션)을 실행 중이고 노드의 TTL이 만료되었으면* 인스턴스가 종료되면 애플리케이션이 중단됩니다. 파드에 `karpenter.sh/do-not-evict` 어노테이션을 추가하면 파드가 종료되거나 `do-not-evict` 어노테이션이 제거될 때까지 Karpenter가 노드를 보존하도록 지시하는 것입니다. 자세한 내용은 [디프로비저닝](https://karpenter.sh/docs/concepts/deprovisioning/#disabling-deprovisioning) 설명서를 참조하십시오.

노드에 데몬셋이 아닌 파드가 작업과 관련된 파드만 남아 있는 경우, Karpenter는 작업 상태가 성공 또는 실패인 한 해당 노드를 대상으로 지정하고 종료할 수 있습니다.

### 통합(Consolidation)을 사용할 때 CPU가 아닌 모든 리소스에 대해 요청=제한(requests=limits)을 구성합니다.

일반적으로 파드 리소스 요청과 노드의 할당 가능한 리소스 양을 비교하여 통합 및 스케줄링을 수행합니다. 리소스 제한은 고려되지 않습니다. 예를 들어 메모리 한도가 메모리 요청량보다 큰 파드는 요청을 초과할 수 있습니다. 동일한 노드의 여러 파드가 동시에 버스트되면 메모리 부족(OOM) 상태로 인해 일부 파드가 종료될 수 있습니다.통합은 요청만 고려하여 파드를 노드에 패킹하는 방식으로 작동하기 때문에 이런 일이 발생할 가능성을 높일 수 있다.

### LimitRanges 를 사용하여 리소스 요청 및 제한에 대한 기본값을 구성합니다.

쿠버네티스는 기본 요청이나 제한을 설정하지 않기 때문에 컨테이너는 기본 호스트, CPU 및 메모리의 리소스 사용량을 제한하지 않습니다. 쿠버네티스 스케줄러는 파드의 총 요청(파드 컨테이너의 총 요청 또는 파드 Init 컨테이너의 총 리소스 중 더 높은 요청)을 검토하여 파드를 스케줄링할 워커 노드를 결정합니다. 마찬가지로 Karpenter는 파드의 요청을 고려하여 프로비저닝하는 인스턴스 유형을 결정합니다. 일부 파드에서 리소스 요청을 지정하지 않는 경우 제한 범위를 사용하여 네임스페이스에 적절한 기본값을 적용할 수 있습니다.

[네임스페이스에 대한 기본 메모리 요청 및 제한 구성](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/)을 참조하십시오.

### 정확한 리소스 요청을 모든 워크로드에 적용

Karpenter는 워크로드 요구 사항에 대한 정보가 정확할 때 워크로드에 가장 적합한 노드를 시작할 수 있습니다.이는 Karpenter의 통합 기능을 사용하는 경우 특히 중요합니다.

[모든 워크로드에 대한 리소스 요청/제한 구성 및 크기 조정](https://aws.github.io/aws-eks-best-practices/reliability/docs/dataplane/#configure-and-size-resource-requestslimits-for-all-workloads)을 참조하십시오.

## 추가 리소스
* [Karpenter/Spot Workshop](https://ec2spotworkshops.com/karpenter.html)
* [Karpenter Node Provisioner](https://youtu.be/_FXRIKWJWUk)
* [TGIK Karpenter](https://youtu.be/zXqrNJaTCrU)
* [Karpenter vs. Cluster Autoscaler](https://youtu.be/3QsVRHVdOnM)
* [Groupless Autoscaling with Karpenter](https://www.youtube.com/watch?v=43g8uPohTgc)