---
search:
  exclude: true
---


# Amazon EKS 최적화 윈도우 AMI 관리
윈도우 Amazon EKS 최적화 AMI는 윈도우 서버 2019와 윈도우 서버 2022를 기반으로 구축되었습니다. 아마존 EKS 윈도우 노드의 기본 이미지 역할을 하도록 구성되어 있습니다. 해당 AMI는 Amazon EKS 노드의 기본 이미지로 사용하도록 구성되어 있습니다. 기본적으로 AMI에는 다음 구성 요소가 포함됩니다:
- [kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)
- [kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/)
- [AWS IAM Authenticator for Kubernetes](https://github.com/kubernetes-sigs/aws-iam-authenticator)
- [csi-proxy](https://github.com/kubernetes-csi/csi-proxy)
- [containerd](https://containerd.io/)

AWS Systems Manager Parameter Store API를 쿼리하여 Amazon EKS 최적화 AMI용 아마존 머신 이미지 (AMI) ID를 프로그래밍 방식으로 검색할 수 있습니다. 이 파라미터를 사용하면 Amazon EKS 최적화 AMI ID를 수동으로 찾아볼 필요가 없습니다. Systems Manager Parameter Store API에 대한 자세한 내용은 [GetParameter](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_GetParameter.html)를 참조하십시오. Amazon EKS 최적화 AMI 메타데이터를 검색하려면 사용자 계정에 `SSM:GetParameter` IAM 권한이 있어야 합니다.

다음 예제는 윈도우 서버 2019 LTSC 코어용 최신 아마존 EKS 최적화 AMI의 AMI ID를 검색합니다. AMI 이름에 나열된 버전 번호는 준비된 해당 쿠버네티스 빌드와 관련이 있습니다.

```bash    
aws ssm get-parameter --name /aws/service/ami-windows-latest/Windows_Server-2019-English-Core-EKS_Optimized-1.21/image_id --region us-east-1 --query "Parameter.Value" --output text
```

출력 예:

```
ami-09770b3eec4552d4e
```

## Amazon EKS 최적화 자체적인 윈도우 AMI 관리

프로덕션 환경을 향한 필수 단계는 Amazon EKS 클러스터 전체에서 동일한 Amazon EKS 최적화 윈도우 AMI 및 kubelet 버전을 유지 관리하는 것입니다. 

Amazon EKS 클러스터 전체에서 동일한 버전을 사용하면 문제 해결 시간이 단축되고 클러스터 일관성이 향상됩니다.[Amazon EC2 Image Builder](https://aws.amazon.com/image-builder/)를 사용하면 Amazon EKS 클러스터에서 사용할 사용자 지정 Amazon EKS 최적화 윈도우 AMI를 생성하고 유지 관리할 수 있습니다.

Amazon EC2 Image Builder를 사용하여 윈도우 서버 버전, AWS 윈도우 서버 AMI 출시일 및/또는 OS 빌드 버전 중에서 선택할 수 있습니다. 구성 요소 빌드 단계에서는 기존 EKS 최적화 윈도우 아티팩트와 kubelet 버전 중에서 선택할 수 있습니다. 자세한 내용은 [이 문서](https://docs.aws.amazon.com/eks/latest/userguide/eks-custom-ami-windows.html)에서 확인 가능합니다.

![](./images/build-components.png)

**참고:** 기본 이미지를 선택하기 전에 [윈도우 서버 버전 및 라이선스](licensing.ko.md) 섹션에서 릴리스 채널 업데이트와 관련된 중요한 세부 정보를 참조하십시오.

## 사용자 지정 EKS 최적화 AMI를 위한 더 빠른 시작 구성 ##

사용자 지정 Windows Amazon EKS 최적화 AMI를 사용하는 경우 빠른 실행 기능을 활성화하여 Windows 워커 노드를 최대 65% 더 빠르게 시작할 수 있습니다.이 기능은 _Sysprep specialize_, _Windows Out of Box Experience (OOBE)_ 단계를 수행하고 필요한 재부팅이 이미 완료된 사전 프로비저닝된 스냅샷 세트를 유지 관리합니다. 이 스냅샷은 이후 실행 시 사용되므로 노드를 확장하거나 교체하는 데 걸리는 시간을 줄일 수 있습니다. Fast Launch는 EC2 콘솔 또는 AWS CLI를 통해 *소유한* AMI에 대해서만 활성화할 수 있으며 유지되는 스냅샷 수는 구성할 수 있습니다. 

**NOTE:** 빠른 실행은 Amazon에서 제공하는 기본 EKS 최적화 AMI와 호환되지 않습니다. 활성화하기 전에 위와 같이 사용자 지정 AMI를 생성하십시오. 

자세한 내용은 다음을 참조하십시오. [AWS 윈도우 AMI - 더 빠른 시작을 위한 AMI 구성](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/windows-ami-version-history.html#win-ami-config-fast-launch)

## 사용자 지정 AMI에 윈도우 베이스 레이어 캐싱

윈도우 컨테이너 이미지는 리눅스 이미지보다 큽니다.컨테이너화된.NET Framework 기반 애플리케이션을 실행하는 경우 평균 이미지 크기는 약 8.24GB입니다.파드 스케줄링 중에는 파드가 Running 상태에 도달하기 전에 컨테이너 이미지를 완전히 가져와서 디스크에서 추출해야 합니다.

이 프로세스 동안 컨테이너 런타임 (containerd) 은 디스크의 전체 컨테이너 이미지를 가져와 추출합니다.pull 작업은 병렬 프로세스입니다. 즉, 컨테이너 런타임은 컨테이너 이미지 레이어를 병렬로 가져옵니다.반면 추출 작업은 순차적 프로세스로 진행되며 I/O가 많이 소요됩니다.이로 인해 컨테이너 이미지가 완전히 추출되어 컨테이너 런타임 (containerd) 에서 사용할 준비가 되기까지 8분 이상 걸릴 수 있으며, 그 결과 파드 시작 시간이 몇 분 정도 걸릴 수 있습니다.

**Windows Server 및 컨테이너 패치** 항목에서 언급한 것처럼 EKS로 사용자 지정 AMI를 구축할 수 있는 옵션이 있습니다. AMI를 준비하는 동안 EC2 이미지 빌더 구성 요소를 추가하여 필요한 Windows 컨테이너 이미지를 모두 로컬로 가져온 다음 AMI를 생성할 수 있습니다. 이 전략을 사용하면 파드가 **Running** 상태에 도달하는 시간을 크게 줄일 수 있습니다. 

Amazon EC2 이미지 빌더에서 [컴퍼넌트](https://docs.aws.amazon.com/imagebuilder/latest/userguide/manage-components.html)를 생성하여 필요한 이미지를 다운로드하고 이미지 레시피에 첨부하십시오. 다음 예제는 ECR 저장소에서 특정 이미지를 가져옵니다. 

```
name: ContainerdPull
description: This component pulls the necessary containers images for a cache strategy.
schemaVersion: 1.0

phases:
  - name: build
    steps:
      - name: containerdpull
        action: ExecutePowerShell
        inputs:
          commands:
            - Set-ExecutionPolicy Unrestricted -Force
            - (Get-ECRLoginCommand).Password | docker login --username AWS --password-stdin 111000111000.dkr.ecr.us-east-1.amazonaws.com
            - ctr image pull mcr.microsoft.com/dotnet/framework/aspnet:latest
            - ctr image pull 111000111000.dkr.ecr.us-east-1.amazonaws.com/myappcontainerimage:latest
```

다음 구성 요소가 예상대로 작동하는지 확인하려면 EC2 Image builder (EC2InstanceProfileForImageBuilder)에서 사용하는 IAM 역할에 연결된 정책이 있는지 확인하십시오:

![](./images/permissions-policies.png)

## 관련 블로그 ##
다음 블로그에서는 사용자 지정 Amazon EKS Windows AMI를 위한 캐싱 전략을 구현하는 방법을 단계별로 확인할 수 있습니다:

[EC2 이미지 빌더 및 이미지 캐시 전략을 통한 윈도우 컨테이너 시작 시간 단축](https://aws.amazon.com/blogs/containers/speeding-up-windows-container-launch-times-with-ec2-image-builder-and-image-cache-strategy/)
