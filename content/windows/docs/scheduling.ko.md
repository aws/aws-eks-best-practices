---
search:
  exclude: true
---


# 이기종 워크로드 실행¶

쿠버네티스는 동일한 클러스터에 리눅스 및 윈도우 노드를 혼합하여 사용할 수 있는 이기종(Heterogeneous) 클러스터를 지원합니다. 해당 클러스터 내에는 리눅스에서 실행되는 파드와 윈도우에서 실행되는 파드를 혼합하여 사용할 수 있습니다. 동일한 클러스터에서 여러 버전의 윈도우를 실행할 수도 있습니다. 하지만 이 결정을 내릴 때 고려해야 할 몇 가지 요소(아래 설명 참조)가 있습니다.

# 노드 내 파드 할당 모범 사례

리눅스 및 윈도우 워크로드를 각각의 OS별 노드에 유지하려면 노드 셀렉터(NodeSelector)와 테인트(Taint)/톨러레이션(Toleration)을 조합하여 사용해야 합니다. 이기종 환경에서 워크로드를 스케줄링하는 주된 목적은 기존 리눅스 워크로드와의 호환성이 깨지지 않도록 하는 것입니다.

## 특정 OS 워크로드가 적절한 컨테이너 노드에서 실행 보장

사용자는 노드셀렉터를 사용하여 윈도우 컨테이너를 적절한 호스트에서 스케줄링 할 수 있습니다. 현재 모든 쿠버네티스 노드에는 다음과 같은 default labels 이 있습니다:

    kubernetes.io/os = [windows|linux]
    kubernetes.io/arch = [amd64|arm64|...]

파드 스펙에 ``"kubernetes.io/os": windows`` 와 같은 노드셀렉터가 포함되지 않는 경우, 파드는 윈도우 또는 리눅스 어느 호스트에서나 스케줄링 될 수 있습니다. 윈도우 컨테이너는 윈도우에서만 실행할 수 있고 리눅스 컨테이너는 리눅스에서만 실행할 수 있기 때문에 문제가 될 수 있습니다.

엔터프라이즈 환경에서는 리눅스 컨테이너에 대한 기존 배포가 많을 뿐만 아니라 헬름 차트와 같은 기성 구성 에코시스템(off-the-shelf configurations)을 갖는 것이 일반적입니다. 이런 상황에서는 디플로이먼트의 노드셀렉터를 변경하는 것을 주저할 수 있습니다. **대안은 테인트를 사용하는 것**입니다.

예를 들어: `--register-with-taints='os=windows:NoSchedule'`

EKS를 사용하는 경우, eksctl은 clusterConfig를 통해 테인트를 적용하는 방법을 제공합니다:

```yaml
NodeGroups:
  - name: windows-ng
    amiFamily: WindowsServer2022FullContainer
    ...
    labels:
      nodeclass: windows2022
    taints:
      os: "windows:NoSchedule"
```

모든 윈도우 노드에 테인트를 추가하는 경우, 스케줄러는 테인트를 허용하지 않는 한 해당 노드에서 파드를 스케줄링하지 않습니다. 다음은 파드 매니페스트의 예시입니다:

```yaml
nodeSelector:
    kubernetes.io/os: windows
tolerations:
    - key: "os"
      operator: "Equal"
      value: "windows"
      effect: "NoSchedule"
```

## 동일한 클러스터에서 여러 윈도우 빌드 처리

각 파드에서 사용하는 윈도우 컨테이너 베이스 이미지는 노드와 동일한 커널 빌드 버전과 일치해야 합니다. 동일한 클러스터에서 여러 윈도우 Server 빌드를 사용하려면 추가 노드 레이블인 노드셀렉터를 설정하거나 **windows-build** 레이블을 활용해야 합니다.

쿠버네티스 1.17 버전에서는 **node.kubernetes.io/windows-build** 라는 새로운 레이블을 자동으로 추가하여 동일한 클러스터에서 여러 윈도우 빌드의 관리를 단순화 합니다. 이전 버전을 실행 중인 경우 이 레이블을 윈도우 노드에 수동으로 추가하는 것이 좋습니다.

이 레이블에는 호환성을 위해 일치해야 하는 윈도우 메이저, 마이너, 그리고 빌드 번호가 반영되어 있습니다. 다음은 현재 각 윈도우 서버 버전에 사용되는 값입니다.

중요한 점은 윈도우 서버가 장기 서비스 채널(LTSC)를 기본 릴리스 채널로 이동하고 있다는 것입니다. 윈도우 서버 반기 채널(SAC)은 2022년 8월 9일에 사용 중지되었습니다. 윈도우 서버의 향후 SAC 릴리스는 없습니다.


| Product Name | Build Number(s) |
| -------- | -------- |
| Server full 2022 LTSC    | 10.0.20348    |
| Server core 2019 LTSC    | 10.0.17763    |

다음 명령을 통해 OS 빌드 버전을 확인할 수 있습니다:

```bash    
kubectl get nodes -o wide
```

KERNEL-VERSION 출력은 윈도우 OS 빌드 버전을 나타냅니다.

```bash 
NAME                          STATUS   ROLES    AGE   VERSION                INTERNAL-IP   EXTERNAL-IP     OS-IMAGE                         KERNEL-VERSION                  CONTAINER-RUNTIME
ip-10-10-2-235.ec2.internal   Ready    <none>   23m   v1.24.7-eks-fb459a0    10.10.2.235   3.236.30.157    Windows Server 2022 Datacenter   10.0.20348.1607                 containerd://1.6.6
ip-10-10-31-27.ec2.internal   Ready    <none>   23m   v1.24.7-eks-fb459a0    10.10.31.27   44.204.218.24   Windows Server 2019 Datacenter   10.0.17763.4131                 containerd://1.6.6
ip-10-10-7-54.ec2.internal    Ready    <none>   31m   v1.24.11-eks-a59e1f0   10.10.7.54    3.227.8.172     Amazon Linux 2                   5.10.173-154.642.amzn2.x86_64   containerd://1.6.19
```

아래 예제에서는 다양한 윈도우 노드 그룹 OS 버전을 실행할 때 올바른 윈도우 빌드 버전을 일치시키기 위해 추가 노드셀렉터를 파드 스펙에 적용합니다.

```yaml
nodeSelector:
    kubernetes.io/os: windows
    node.kubernetes.io/windows-build: '10.0.20348'
tolerations:
    - key: "os"
    operator: "Equal"
    value: "windows"
    effect: "NoSchedule"
```

## RuntimeClass를 사용하여 파드 매니페스트의 노드셀렉터와 톨러레이션 단순화

RuntimeClass를 사용하여 테인트와 톨러레이션을 사용하는 프로세스를 간소화할 수 있습니다. 이런 테인트와 톨러레이션을 캡슐화하는 RuntimeClass 오브젝트를 만들어 이 작업을 수행할 수 있습니다.

다음 매니페스트를 통해 RuntimeClass를 생성합니다:

```yaml
apiVersion: node.k8s.io/v1beta1
kind: RuntimeClass
metadata:
  name: windows-2022
handler: 'docker'
scheduling:
  nodeSelector:
    kubernetes.io/os: 'windows'
    kubernetes.io/arch: 'amd64'
    node.kubernetes.io/windows-build: '10.0.20348'
  tolerations:
  - effect: NoSchedule
    key: os
    operator: Equal
    value: "windows"
```

RuntimeClass가 생성되면, 파드 매니페스트의 스펙을 통해 사용합니다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iis-2022
  labels:
    app: iis-2022
spec:
  replicas: 1
  template:
    metadata:
      name: iis-2022
      labels:
        app: iis-2022
    spec:
      runtimeClassName: windows-2022
      containers:
      - name: iis
```

## 관리형 노드 그룹 지원
고객이 윈도우 애플리케이션을 보다 간소화된 방식으로 실행할 수 있도록 AWS에서는 2022년 12월 15일에 [윈도우 컨테이너에 대한 EKS 관리형 노드 그룹 (MNG) 지원](https://aws.amazon.com/about-aws/whats-new/2022/12/amazon-eks-automated-provisioning-lifecycle-management-windows-containers/)을 시작 했습니다. [윈도우 관리형 노드 그룹](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)은 [리눅스 관리형 노드 그룹](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)과 동일한 워크플로우와 도구를 사용하여 활성화됩니다. 윈도우 서버 2019 및 2022 패밀리의 Full, Core AMI(Amazon Machine Image)가 지원 됩니다.

관리형 노드 그룹(MNG)에 지원되는 AMI 패밀리는 다음과 같습니다:

| AMI Family |
| ---------   | 
| WINDOWS_CORE_2019_x86_64    | 
| WINDOWS_FULL_2019_x86_64    | 
| WINDOWS_CORE_2022_x86_64    | 
| WINDOWS_FULL_2022_x86_64    | 

## 추가 문서


AWS 공식 문서:
https://docs.aws.amazon.com/eks/latest/userguide/windows-support.html

파드 네트워킹(CNI)의 작동 방식을 더 잘 이해하려면 다음 링크를 확인하십시오: https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html

EKS 기반 윈도우용 관리형 노드 그룹 배포에 관한 AWS 블로그:
https://aws.amazon.com/blogs/containers/deploying-amazon-eks-windows-managed-node-groups/