# Running Heterogeneous workloads¶

Kubernetes has support for heterogeneous clusters where you can have a mixture of Linux and Windows nodes in the same cluster. Within that cluster, you can have a mixture of Pods that run on Linux and Pods that run on Windows. You can even run multiple versions of Windows in the same cluster. However, there are several factors (as mentioned below) that will need to be accounted for when making this decision.
쿠버네티스는 동일한 클러스터에 Linux 및 Windows 노드를 혼합하여 사용할 수 있는 이기종(Heterogeneous) 클러스터를 지원합니다. 해당 클러스터 내에는 Linux에서 실행되는 Pod와 Windows에서 실행되는 Pod를 혼합하여 사용할 수 있습니다. 동일한 클러스터에서 여러 버전의 Windows를 실행할 수도 있습니다.하지만 이 결정을 내릴 때 고려해야 할 몇 가지 요소 (아래 설명 참조) 가 있습니다.

# Assigning PODs to Nodes Best practices

Linux 및 Windows 워크로드를 각각의 OS별 노드에 유지하려면 node selector와 taints/tolerations 을 조합하여 사용해야 합니다. 이기종 환경에서 워크로드를 스케줄링하는 주된 목적은 기존 Linux 워크로드와의 호환성이 깨지지 않도록 하는 것입니다.

## Ensuring OS-specific workloads land on the appropriate container host

사용자는 nodeSelector를 사용하여 Windows 컨테이너를 적절한 호스트에서 스케줄링 할 수 있습니다. 현재 모든 쿠버네티스 노드에는 다음과 같은 default labels 이 있습니다:

    kubernetes.io/os = [windows|linux]
    kubernetes.io/arch = [amd64|arm64|...]

Pod specifiction에 ``"kubernetes.io/os": windows`` 와 같은 nodeSelector가 포함되지 않는 경우, Pod는 윈도우 또는 리눅스 어느 호스트에서나 스케줄링 될 수 있습니다. Windows 컨테이너는 Windows에서만 실행할 수 있고 Linux 컨테이너는 Linux에서만 실행할 수 있기 때문에 문제가 될 수 있습니다.

In Enterprise environments, it's not uncommon to have a large number of pre-existing deployments for Linux containers, as well as an ecosystem of off-the-shelf configurations, like Helm charts. In these situations, you may be hesitant to make changes to a deployment's nodeSelectors. **The alternative is to use Taints**.
엔터프라이즈 환경에서는 Linux 컨테이너에 대한 기존 배포가 많을 뿐만 아니라 Helm 차트와 같은 기성 구성 에코시스템(off-the-shelf configurations)을 갖는 것이 일반적입니다. 이러한 상황에서는 deployment의 nodeSelector를 변경하는 것을 주저할 수 있습니다. **대안은 Taint를 사용하는 것**입니다.

예를 들어: `--register-with-taints='os=windows:NoSchedule'`

EKS를 사용하는 경우, eksctl은 clusterConfig를 통해 taint를 적용하는 방법을 제공합니다:

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

모든 Windows 노드에 taint를 추가하는 경우, 스케줄러는 taint를 허용하지 않는 한 해당 노드에서 pod를 스케줄링하지 않습니다. 다음은 Pod manifest의 예시입니다:

```yaml
nodeSelector:
    kubernetes.io/os: windows
tolerations:
    - key: "os"
      operator: "Equal"
      value: "windows"
      effect: "NoSchedule"
```

## Handling multiple Windows build in the same cluster

각 Pod에서 사용하는 Windows container base image 는 노드와 동일한 커널 빌드 버전과 일치해야 합니다. 동일한 클러스터에서 여러 Windows Server 빌드를 사용하려면 추가 노드 label인 nodeSelector를 설정하거나 **windows-build** label을 활용해야 합니다.

쿠버네티스 1.17 버전에서는 **node.kubernetes.io/windows-build** 라는 새로운 label을 자동으로 추가하여 동일한 클러스터에서 여러 윈도우 빌드의 관리를 단순화 합니다. 이전 버전을 실행 중인 경우 이 label을 Windows 노드에 수동으로 추가하는 것이 좋습니다.

This label reflects the Windows major, minor, and build number that need to match for compatibility. Below are values used today for each Windows Server version.
이 label에는 호환성을 위해 일치해야 하는 Windows major, minor, 그리고 build number가 반영되어 있습니다. 다음은 현재 각 Windows Server 버전에 사용되는 값입니다.

중요한 점은 Windows Server가 Long-Term Servicing Channel (LTSC)를 기본 릴리즈(release) 채널로 이동하고 있다는 것입니다. Windows Server Semi-Annual Channel (SAC)는 2022년 8월 9일에 사용 중지되었습니다. Windows Server의 향후 SAC 릴리즈는 없습니다.

| Product Name | Build Number(s) |
| -------- | -------- |
| Server full 2022 LTSC    | 10.0.20348    |
| Server core 2019 LTSC    | 10.0.17763    |

다음 명령을 통해 OS 빌드 버전을 확인할 수 있습니다:

```bash    
kubectl get nodes -o wide
```

KERNEL-VERSION 출력은 Windows OS 빌드 버전을 나타냅니다.

```bash 
NAME                          STATUS   ROLES    AGE   VERSION                INTERNAL-IP   EXTERNAL-IP     OS-IMAGE                         KERNEL-VERSION                  CONTAINER-RUNTIME
ip-10-10-2-235.ec2.internal   Ready    <none>   23m   v1.24.7-eks-fb459a0    10.10.2.235   3.236.30.157    Windows Server 2022 Datacenter   10.0.20348.1607                 containerd://1.6.6
ip-10-10-31-27.ec2.internal   Ready    <none>   23m   v1.24.7-eks-fb459a0    10.10.31.27   44.204.218.24   Windows Server 2019 Datacenter   10.0.17763.4131                 containerd://1.6.6
ip-10-10-7-54.ec2.internal    Ready    <none>   31m   v1.24.11-eks-a59e1f0   10.10.7.54    3.227.8.172     Amazon Linux 2                   5.10.173-154.642.amzn2.x86_64   containerd://1.6.19
```

아래 예제에서는 다양한 Windows 노드 그룹 OS 버전을 실행할 때 올바른 Windows 빌드 버전을 일치시키기 위해 추가 nodeSelector를 pod manifest에 적용합니다.

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

## Simplifying NodeSelector and Toleration in Pod manifests using RuntimeClass

You can also make use of RuntimeClass to simplify the process of using taints and tolerations. This can be accomplished by creating a RuntimeClass object which is used to encapsulate these taints and tolerations.
RuntimeClass를 사용하여 taint와 tolerations을 사용하는 프로세스를 간소화할 수 있습니다. 이러한 taint와 tolerations 을 캡슐화(encapsulate)하는 데 사용되는 RuntimeClass 오브젝트를 만들면 이 작업을 수행할 수 있습니다.

다음 manifest를 통해 RuntimeClass를 생성합니다:

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

RuntimeClass가 생성되면, Pod manifest 의 spec 을 통해 사용합니다.

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

## Managed Node Group Support
고객이 Windows 애플리케이션을 보다 간소화된 방식으로 실행할 수 있도록 AWS에서는 2022년 12월 15일에 [EKS Managed Node Group (MNG) support for Windows containers](https://aws.amazon.com/about-aws/whats-new/2022/12/amazon-eks-automated-provisioning-lifecycle-management-windows-containers/) 지원을 시작 했습니다. [Windows MNGs](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)는 [Linux MNGs](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)와 동일한 워크플로우와 도구를 사용하여 활성화됩니다. Windows Server 2019 및 2022 Family의 Full, Core AMI(Amazon Machine Image)가 지원 됩니다.

Following AMI families are supported for Managed Node Groups(MNG)s.
Managed Node Groups(MNG)에 지원되는 AMI Family는 다음과 같습니다:

| AMI Family |
| ---------   | 
| WINDOWS_CORE_2019_x86_64    | 
| WINDOWS_FULL_2019_x86_64    | 
| WINDOWS_CORE_2022_x86_64    | 
| WINDOWS_FULL_2022_x86_64    | 

## Additional documentations


AWS 공식 문서:
https://docs.aws.amazon.com/eks/latest/userguide/windows-support.html

Pod Networking(CNI)의 작동 방식을 더 잘 이해하려면 다음 링크를 확인하십시오: https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html

EKS 기반 Windows용 Managed Node Group 배포에 관한 AWS Blog:
https://aws.amazon.com/blogs/containers/deploying-amazon-eks-windows-managed-node-groups/