---
search:
  exclude: true
---


# 윈도우 서버 및 컨테이너 패치

윈도우 서버 패치 작업은 윈도우 관리자를 위한 표준 관리 작업입니다. Amazon System Manager - Patch Manager, WSUS, System Center Configuration Manager 등과 같은 다양한 도구를 사용하여 이 작업을 수행할 수 있습니다. 하지만 Amazon EKS 클러스터의 윈도우 노드를 일반 윈도우 서버로 취급해서는 안 됩니다. 이들은 변경할 수 없는 서버로 취급되어야 합니다. 간단히 말해, 기존 노드를 업데이트하지 말고 시작 템플릿에 새로 업데이트된 AMI를 기반으로 새 노드를 시작하기만 하면 됩니다.

[EC2 Image Builder](https://aws.amazon.com/image-builder/)를 사용하여 레시피를 생성하고 구성 요소를 추가하여 AMI 빌드를 자동화할 수 있습니다.

다음 예제는 **구성 요소**를 보여줍니다. 구성 요소는 AWS에서 구축한 기존 구성 요소(Amazon-managed)일 수도 있고 사용자가 생성한 구성 요소(Owned by me)일 수도 있습니다. Amazon에서 관리하는 **update-windows**라는 구성 요소에 주목하십시오. 이렇게 하면 EC2 Image Builder 파이프라인을 통해 AMI를 생성하기 전에 윈도우 서버가 업데이트됩니다.

![](./images/associated-components.png)

EC2 Image Builder를 사용하면 Amazon 제공 퍼블릭 AMI를 기반으로 AMI를 구축하고 비즈니스 요구 사항에 맞게 커스터마이징할 수 있습니다. 그런 다음 해당 AMI를 EKS 노드 그룹에서 생성한 Auto Scaling 그룹의 시작 템플릿(Launch Template)에 연결 할 수 있습니다. 이 작업이 완료되면 기존 윈도우 노드를 종료할 수 있으며 새로 업데이트된 AMI를 기반으로 새 윈도우 노드가 시작됩니다.

## 윈도우 이미지 푸싱(Pushing)와 풀링(Pulling)
Amazon은 2개의 캐시된 윈도우 컨테이너 이미지를 포함하는 EKS 최적화 AMI를 제공합니다.
  
    mcr.microsoft.com/windows/servercore
    mcr.microsoft.com/windows/nanoserver

![](./images/images.png)

캐시된 이미지는 main OS 업데이트에 따라 업데이트 됩니다. Microsoft가 윈도우 컨테이너 베이스 이미지에 직접적인 영향을 미치는 새로운 윈도우 업데이트를 출시하면 해당 업데이트는 main OS에서 일반적인 윈도우 업데이트(ordinary Windows Update)로 시작 됩니다. 환경을 최신 상태로 유지하면 노드 및 컨테이너 수준에서 보다 안전한 환경이 제공됩니다.

윈도우 컨테이너 이미지의 크기는 푸시/풀 수행에 영향을 미치므로 컨테이너 시작 시간(conatiner startup time)이 느려질 수 있습니다. [윈도우 컨테이너 이미지 캐싱](https://aws.amazon.com/blogs/containers/speeding-up-windows-container-launch-times-with-ec2-image-builder-and-image-cache-strategy/)에 방식으로 컨테이너 이미지를 캐싱하면 컨테이너 시작 대신 AMI 빌드 생성시 비용이 많이 드는 I/O 작업(파일 추출)이 발생할 수 있습니다. 따라서 필요한 모든 이미지 레이어가 AMI에서 추출되어 바로 사용할 수 있게 되므로 윈도우 컨테이너가 시작되고 트래픽 수신을 시작할 수 있는 시간이 단축됩니다. 푸시 작업 중에는 이미지를 구성하는 레이어만 저장소에 업로드됩니다.

다음 예제에서는 Amazon ECR에서 **fluentd-windows-sac2004** 이미지의 크기가 **390.18MB**에 불과하다는 것을 보여줍니다. 푸시 작업 중에 발생한 업로드 양입니다.

다음 예제에서는 Amazon ECR 리포지토리에 푸시된 [fluentd Windows ltsc](https://github.com/fluent/fluentd-docker-image/blob/master/v1.14/windows-ltsc2019/Dockerfile) 이미지를 보여줍니다. ECR에 저장되는 레이어의 크기는 **533.05MB**입니다.

![](./images/ecr-image.png)

 아래 `docker image ls` 출력에서는 fluentd v1.14-windows-ltsc2019-1의 크기가 디스크에서 **6.96GB**이지만, 해당 양의 데이터를 다운로드하고 추출했다는 의미는 아닙니다.

실제로 풀 수행시에는 **compressed 533.05MB**만 다운로드되어 추출됩니다.

```bash
REPOSITORY                                                              TAG                        IMAGE ID       CREATED         SIZE
111122223333.dkr.ecr.us-east-1.amazonaws.com/fluentd-windows-coreltsc   latest                     721afca2c725   7 weeks ago     6.96GB
fluent/fluentd                                                          v1.14-windows-ltsc2019-1   721afca2c725   7 weeks ago     6.96GB
amazonaws.com/eks/pause-windows                                         latest                     6392f69ae6e7   10 months ago   255MB
```

size 컬럼에 이미지의 전체 크기로 6.96GB가 표시됩니다. 이에 대한 상세한 내역입니다:

* Windows Server Core 2019 LTSC Base image = 5.74GB
* Fluentd Uncompressed Base Image = 6.96GB
* Difference on disk = 1.2GB
* Fluentd [compressed final image ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-info.html) = 533.05MB

기본 이미지가 로컬 디스크에 이미 있으므로 디스크의 총 용량은 1.2GB가 추가됩니다. 다음에 size 컬럼에 GB 용량이 표시되더라도 너무 걱정할 필요 없습니다. 이미 70% 이상이 캐시된 컨테이너 이미지로 디스크에 저장되어 있을 것입니다.

## 참고 자료
[EC2 Image builder 및 이미지 캐시 전략으로 윈도우 컨테이너 시작 시간 단축](https://aws.amazon.com/blogs/containers/speeding-up-windows-container-launch-times-with-ec2-image-builder-and-image-cache-strategy/)



