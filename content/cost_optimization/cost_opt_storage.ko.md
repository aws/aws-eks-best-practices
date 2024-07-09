---
search:
  exclude: true
---


# 비용 최적화 - 스토리지

## 개요

데이터를 단기 또는 장기적으로 보존해야 하는 애플리케이션을 실행해야 하는 시나리오가 있을 수 있습니다. 이러한 사용 사례의 경우, 컨테이너가 다양한 스토리지 메커니즘을 활용할 수 있도록 파드에서 볼륨을 정의하고 마운트할 수 있습니다. 쿠버네티스는 임시 및 영구 스토리지를 위해 다양한 유형의 [볼륨](https://kubernetes.io/docs/concepts/storage/volumes/)을 지원합니다. 스토리지 선택은 주로 애플리케이션 요구 사항에 따라 달라집니다. 각 접근 방식마다 비용에 미치는 영향이 있으며, 아래에 자세히 설명된 사례는 EKS 환경에서 특정 형태의 스토리지가 필요한 워크로드의 비용 효율성을 달성하는 데 도움이 됩니다. 


## 임시(Ephemeral) 볼륨

임시 볼륨은 일시적인 로컬 볼륨이 필요하지만 재시작 후에도 데이터를 유지할 필요가 없는 애플리케이션에 적합합니다. 이러한 예로는 스크래치 공간, 캐싱, 읽기 전용 입력 데이터(예: 구성 데이터 및 암호)에 대한 요구 사항이 포함됩니다. 쿠버네티스 임시 볼륨에 대한 자세한 내용은 [여기](https://kubernetes.io/docs/concepts/storage/ephemeral-volumes/)에서 확인할 수 있다. 대부분의 임시 볼륨 (예: emptyDir, ConfigMap, DownwardAPI, secret, hostpath)은 로컬로 연결된 쓰기 가능 디바이스 (일반적으로 루트 디스크) 또는 RAM으로 백업되므로 가장 비용 효율적이고 성능이 뛰어난 호스트 볼륨을 선택하는 것이 중요합니다. 


### EBS 볼륨 사용

*호스트 루트 볼륨은 [gp3](https://aws.amazon.com/ebs/general-purpose/)로 시작하는 것이 좋습니다.* Amazon EBS에서 제공하는 최신 범용 SSD 볼륨이며 gp2 볼륨에 비해 GB당 가격(최대 20%)도 저렴합니다. 


### Amazon EC2 인스턴스 스토어(Instance Stores) 사용

[Amazon EC2 인스턴스 스토어](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html)는 EC2 인스턴스를 위한 임시 블록 레벨 스토리지를 제공합니다. EC2 인스턴스 스토어가 제공하는 스토리지는 호스트에 물리적으로 연결된 디스크를 통해 액세스할 수 있습니다. Amazon EBS와 달리 인스턴스 스토어 볼륨은 인스턴스가 시작될 때만 연결할 수 있으며, 이러한 볼륨은 인스턴스의 수명 기간 동안에만 존재합니다. 분리한 후 다른 인스턴스에 다시 연결할 수는 없습니다.Amazon EC2 인스턴스 스토어에 대한 자세한 내용은 [여기](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html)에서 확인할 수 있습니다. *인스턴스 스토어 볼륨과 관련된 추가 요금은 없습니다.* 따라서 인스턴스 스토어 볼륨은 EBS 볼륨이 큰 일반 EC2 인스턴스보다 _비용 효율적_이 뛰어납니다. 

쿠버네티스에서 로컬 스토어 볼륨을 사용하려면 [Amazon EC2 사용자 데이터를 사용하여](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-add-user-data.html) 디스크를 파티셔닝, 구성 및 포맷해야 합니다. 그래야 볼륨이 파드 사양에서 [HostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath)로 마운트될 수 있습니다. 또는 [로컬 퍼시스턴트 볼륨 정적 프로비저너(Local Persistent Volume Static Provisioner)](https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner)를 활용하여 로컬 스토리지 관리를 간소화할 수 있습니다. 로컬 퍼시스턴트 볼륨 정적 프로비저너를 사용하면 표준 쿠버네티스 퍼시스턴트 볼륨 클레임(PVC) 인터페이스를 통해 로컬 인스턴스 스토어 볼륨에 액세스할 수 있습니다. 또한 노드 어피니티 정보가 포함된 퍼시스턴트 볼륨 (PV) 을 프로비저닝하여 파드를 올바른 노드에 스케줄링한다.쿠버네티스 퍼시스턴트 볼륨을 사용하긴 하지만 EC2 인스턴스 스토어 볼륨은 사실상 일시적입니다. 임시 디스크에 기록된 데이터는 인스턴스의 수명 기간 동안만 사용할 수 있습니다. 인스턴스가 종료되면 데이터도 종료됩니다. 자세한 내용은 이 [블로그](https://aws.amazon.com/blogs/containers/eks-persistent-volumes-for-instance-store/)를 참조하십시오.

Amazon EC2 인스턴스 스토어 볼륨을 사용할 때는 총 IOPS 한도가 호스트와 공유되며 이는 파드를 특정 호스트에 바인딩한다는 점에 유의하세요. Amazon EC2 인스턴스 스토어 볼륨을 채택하기 전에 워크로드 요구 사항을 철저히 검토해야 합니다.


## 퍼시스턴트 볼륨

쿠버네티스는 일반적으로 스테이트리스 (Stateless) 애플리케이션을 실행하는 것에 적합합니다. 하지만 한 요청부터 다음 요청까지 영구 데이터나 정보를 보존해야 하는 마이크로서비스를 실행해야 하는 시나리오가 있을 수 있습니다. 데이터베이스는 이러한 사용 사례의 일반적인 예입니다. 하지만 파드와 그 안에 있는 컨테이너 또는 프로세스는 사실상 일시적이다. 파드의 수명 이후에도 데이터를 유지하려면 PV를 사용하여 파드와 독립적인 특정 위치의 스토리지에 대한 액세스를 정의할 수 있습니다. *PV와 관련된 비용은 사용 중인 스토리지의 유형과 애플리케이션이 스토리지를 사용하는 방식에 따라 크게 달라집니다.* 

[여기](https://docs.aws.amazon.com/eks/latest/userguide/storage.html)에는 Amazon EKS에서 쿠버네티스 PV를 지원하는 다양한 유형의 스토리지 옵션이 나열되어 있습니다. 아래에서 다루는 스토리지 옵션은 Amazon EBS, Amazon EFS, Amazon FSx for Lustre, Amazon FSx for NetApp ONTAP입니다.


### Amazon Elastic Block Store (EBS) 볼륨

Amazon EBS 볼륨은 쿠버네티스 PV로 사용하여 블록 레벨 스토리지 볼륨을 제공할 수 있습니다. 이는 무작위 읽기 및 쓰기에 의존하는 데이터베이스와 길고 지속적인 읽기 및 쓰기를 수행하는 처리량 집약적인 애플리케이션에 적합합니다. [Amazon EBS 컨테이너 스토리지 인터페이스 (CSI) 드라이버](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)를 사용하면 Amazon EKS 클러스터가 퍼시스턴트 볼륨에 대한 Amazon EBS 볼륨의 수명 주기를 관리할 수 있습니다. 컨테이너 스토리지 인터페이스는 쿠버네티스와 스토리지 시스템 간의 상호 작용을 지원하고 촉진합니다. CSI 드라이버가 EKS 클러스터에 배포되면 퍼시스턴트 볼륨 (PV), 퍼시스턴트 볼륨 클레임 (PVC) 및 스토리지 클래스 (SC) 와 같은 네이티브 쿠버네티스 스토리지 리소스를 통해 해당 기능에 액세스할 수 있습니다. 이 [링크](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/tree/master/examples/kubernetes)는 Amazon EBS CSI 드라이버를 사용하여 Amazon EBS 볼륨과 상호 작용하는 방법에 대한 실제 예를 제공합니다.


#### 적절한 볼륨 선택

*가격과 성능 간의 적절한 균형을 제공하는 최신 블록 스토리지 (gp3)를 사용하는 것이 좋습니다*. 또한 추가 블록 스토리지 용량을 프로비저닝할 필요 없이 볼륨 크기와 독립적으로 볼륨 IOPS와 처리량을 확장할 수 있습니다. 현재 gp2 볼륨을 사용하고 있다면 gp3 볼륨으로 마이그레이션하는 것이 좋습니다. 이 [블로그](https://aws.amazon.com/blogs/containers/migrating-amazon-eks-clusters-from-gp2-to-gp3-ebs-volumes/) 에서는 아마존 EKS 클러스터에서 *gp2*에서 *gp3*로 마이그레이션하는 방법을 설명합니다. 

더 높은 성능이 필요하고 단일 [gp3 볼륨이 지원할 수 있는 용량](https://aws.amazon.com/ebs/general-purpose/)보다 큰 볼륨이 필요한 애플리케이션이 있는 경우 [io2 block express](https://aws.amazon.com/ebs/provisioned-iops/)사용을 고려해야 합니다. 이 유형의 스토리지는 지연 시간이 짧은 기타 대규모 데이터베이스 또는 SAP HANA와 같이 규모가 크고 I/O 집약적이며 미션 크리티컬 배포에 적합합니다. 단, 인스턴스의 EBS 성능은 인스턴스의 성능 제한에 의해 제한되므로 모든 인스턴스가 io2 블록 익스프레스 볼륨을 지원하는 것은 아닙니다. 지원되는 인스턴스 유형 및 기타 고려 사항은 이 [문서](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/provisioned-iops.html)에서 확인할 수 있습니다. 

*단일 gp3 볼륨은 최대 16,000 IOPS, 최대 처리량 1,000MiB/초, 최대 16TiB를 지원할 수 있습니다.최대 256,000 IOPS, 4,000MiB/s, 처리량 및 64TiB를 제공하는 최신 세대의 프로비저닝된 IOPS SSD 볼륨입니다.*

이러한 옵션 중에서 애플리케이션 요구 사항에 맞게 스토리지 성능과 비용을 조정하는 것이 가장 좋습니다.


#### 시간 경과에 따른 모니터링 및 최적화

애플리케이션의 기준 성능을 이해하고 선택한 볼륨에 대해 모니터링하여 요구 사항/기대치를 충족하는지 또는 과다 프로비저닝되었는지 확인하는 것이 중요합니다 (예: 프로비저닝된 IOPS가 완전히 활용되지 않는 시나리오). 

처음부터 큰 볼륨을 할당하는 대신 데이터가 누적되면서 점차 볼륨 크기를 늘릴 수 있습니다. Amazon EBS CSI 드라이버 (aws-ebs-csi-driver) 의 [볼륨 크기 조정](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/tree/master/examples/kubernetes/resizing)기능을 사용하여 볼륨 크기를 동적으로 조정할 수 있습니다. *EBS 볼륨 크기만 늘릴 수 있다는 점에 유의하세요.*

매달려 있는 EBS 볼륨을 식별하고 제거하려면 [AWS Trusted Advisor의 비용 최적화 카테고리](https://docs.aws.amazon.com/awssupport/latest/user/cost-optimization-checks.html)를 사용할 수 있습니다. 이 기능을 사용하면 연결되지 않은 볼륨이나 일정 기간 쓰기 작업이 매우 적은 볼륨을 식별할 수 있습니다. [Popeye](https://github.com/derailed/popeye)라는 클라우드 네이티브 오픈 소스 읽기 전용 도구가 있습니다. 이 도구는 쿠버네티스 클러스터를 스캔하고 배포된 리소스 및 구성과 관련된 잠재적 문제를 보고합니다. 예를 들어, 사용하지 않는 PV와 PVC를 스캔하여 바인딩되었는지 또는 볼륨 마운트 오류가 있는지 확인할 수 있습니다.

모니터링에 대한 자세한 내용은 [EKS 비용 최적화 옵저버빌리티 가이드](https://aws.github.io/aws-eks-best-practices/cost_optimization/cost_opt_observability/)를 참조하십시오. 

고려할 수 있는 또 다른 옵션은 [AWS Compute Optimizer EBS 볼륨 권장 사항](https://docs.aws.amazon.com/compute-optimizer/latest/ug/view-ebs-recommendations.html)입니다. 이 도구는 최적의 볼륨 구성과 필요한 정확한 성능 수준을 자동으로 식별합니다. 예를 들어, 지난 14일 동안의 최대 사용률을 기준으로 프로비저닝된 IOPS, 볼륨 크기 및 EBS 볼륨 유형과 관련된 최적의 설정에 사용할 수 있습니다. 또한 권장 사항을 바탕으로 얻을 수 있는 잠재적인 월별 비용 절감 효과를 수치화합니다. 자세한 내용은 이 [블로그](https://aws.amazon.com/blogs/storage/cost-optimizing-amazon-ebs-volumes-using-aws-compute-optimizer/) 에서 확인할 수 있습니다.


#### 백업 보존 정책

특정 시점 스냅샷을 생성하여 Amazon EBS 볼륨의 데이터를 백업할 수 있습니다.Amazon EBS CSI 드라이버는 볼륨 스냅샷을 지원합니다. [여기](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/examples/kubernetes/snapshot/README.md)에 설명된 단계를 사용하여 스냅샷을 생성하고 EBS PV를 복원하는 방법을 배울 수 있습니다. 

이후 스냅샷은 증분 백업으로 진행됩니다. 즉, 가장 최근 스냅샷 이후에 변경된 디바이스의 블록만 저장됩니다. 이렇게 하면 스냅샷을 만드는 데 필요한 시간이 최소화되고 데이터를 복제하지 않아 스토리지 비용이 절약됩니다. 하지만 적절한 보존 정책 없이 오래된 EBS 스냅샷의 수를 늘리면 대규모 운영 시 예상치 못한 비용이 발생할 수 있습니다. AWS API를 통해 아마존 EBS 볼륨을 직접 백업하는 경우, 아마존 EBS 스냅샷과 EBS 기반 AMI를 위한 자동화된 정책 기반 수명 주기 관리 솔루션을 제공하는 [Amazon Data Lifecycle Manager](https://aws.amazon.com/ebs/data-lifecycle-manager/)(DLM)를 활용할 수 있습니다. 콘솔을 사용하면 EBS 스냅샷과 AMI의 생성, 보존 및 삭제를 더 쉽게 자동화할 수 있습니다. 

!!! note
    현재로서는 Amazon EBS CSI 드라이버를 통해 Amazon DLM을 사용할 수 있는 방법이 없습니다.

쿠버네티스 환경에서는 [Velero](https://velero.io/)라는 오픈 소스 도구를 활용하여 EBS 퍼시스턴트 볼륨을 백업할 수 있습니다. 백업이 만료되도록 작업을 예약할 때 TTL 플래그를 설정할 수 있습니다. 다음은 Velero의 예제는 [이 가이드](https://velero.io/docs/v1.12/how-velero-works/#set-a-backup-to-expire)를 참고합니다. 


### Amazon Elastic File System (EFS)

[Amazon Elastic File System (EFS)](https://aws.amazon.com/efs/) 는 서버리스 방식의 완전 탄력적 파일 시스템으로, 광범위한 워크로드 및 애플리케이션에 대해 표준 파일 시스템 인터페이스 및 파일 시스템 시맨틱스를 사용하여 파일 데이터를 공유할 수 있습니다. 워크로드 및 애플리케이션의 예로는 Wordpress와 Drupal, JIRA와 Git과 같은 개발자 도구, Jupyter와 같은 공유 노트북 시스템, 홈 디렉터리가 있습니다.

Amazon EFS의 주요 이점 중 하나는 여러 노드와 여러 가용 영역에 분산된 여러 컨테이너에 마운트할 수 있다는 것입니다. 또 다른 이점은 사용한 스토리지에 대해서만 비용을 지불한다는 것입니다. EFS 파일 시스템은 파일을 추가하고 제거함에 따라 자동으로 확장 및 축소되므로 용량 계획이 필요 없습니다. 

쿠버네티스에서 Amazon EFS를 사용하려면, Amazon EFS 컨테이너 스토리지 인터페이스 (CSI) 드라이버 인, [aws-efs-csi-driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver)를 사용해야 합니다. 현재 드라이버는 동적으로 [액세스 포인트](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html)를 생성할 수 있습니다. 하지만 Amazon EFS 파일 시스템을 먼저 프로비저닝하고 Kubernetes 스토리지 클래스 파라미터의 입력으로 제공해야 합니다. 


#### 올바른 EFS 스토리지 클래스 선택

Amazon EFS는 [네 가지 스토리지 클래스](https://docs.aws.amazon.com/efs/latest/ug/storage-classes.html)를 제공합니다. 

두 가지 표준 스토리지 클래스:

* Amazon EFS Standard 
* [Amazon EFS Standard-Infrequent Access](https://aws.amazon.com/blogs/aws/optimize-storage-cost-with-reduced-pricing-for-amazon-efs-infrequent-access/) (EFS Standard-IA) 


두 개의 단일-존 스토리지 클래스: 

* [Amazon EFS One Zone](https://aws.amazon.com/blogs/aws/new-lower-cost-one-zone-storage-classes-for-amazon-elastic-file-system/) 
* Amazon EFS One Zone-Infrequent Access (EFS One Zone-IA)


Infrequent Access (IA) 스토리지 클래스는 매일 액세스하지 않는 파일에 맞게 비용 최적화되어 있습니다. Amazon EFS 수명 주기 관리를 사용하면 수명 주기 정책 기간 (7, 14, 30, 60 또는 90일) 동안 액세스하지 않은 파일을 IA 스토리지 클래스*로 이동할 수 있어 EFS Standard 및 EFS One Zone 스토리지 클래스에 비해 각각 최대 92% 까지 스토리지 비용을 절감할 수 있습니다*. 

EFS Intelligent-Tiering을 사용하면 수명 주기 관리가 파일 시스템의 액세스 패턴을 모니터링하고 파일을 가장 최적의 스토리지 클래스로 자동으로 이동합니다. 

!!! note
    aws-efs-csi-driver는 현재 스토리지 클래스 변경, 라이프사이클 관리 또는 Intelligent-Tiering를 제어할 수 없습니다. 이러한 설정은 AWS 콘솔이나 EFS API를 통해 수동으로 설정해야 합니다.

!!! note
    aws-efs-csi-driver는 윈도우 기반 컨테이너 이미지와 호환되지 않습니다.

!!! note
    파일 시스템 크기에 비례하는 메모리 양을 소비하는 [DiskUsage](https://github.com/kubernetes/kubernetes/blob/ee265c92fec40cd69d1de010b477717e4c142492/pkg/volume/util/fs/fs.go#L66) 함수로 인해 *vol-metrics-opt-in* (볼륨 메트릭 출력) 을 활성화하면 알려진 메모리 문제가 발생합니다. *현재는 대용량 파일 시스템에서는* *`--vol-metrics-opt-in` 옵션을 비활성화하여 메모리를 너무 많이 사용하지 않도록 설정하는 것이 좋습니다.자세한 내용은 깃허브 이슈 [링크](https://github.com/kubernetes-sigs/aws-efs-csi-driver/issues/1104) 에서 확인하세요.*


### Amazon FSx for Lustre

Lustre는 최대 수백 GB/s의 처리량과 작업당 밀리초 미만의 지연 시간이 필요한 워크로드에 일반적으로 사용되는 고성능 병렬 파일 시스템입니다. 머신러닝 교육, 금융 모델링, HPC, 비디오 처리와 같은 시나리오에 사용됩니다. [Amazon FSx for Lustre](https://aws.amazon.com/fsx/lustre/)는 Amazon S3와 원활하게 통합되는 확장성과 성능을 갖춘 완전 관리형 공유 스토리지를 제공합니다. 

[FSx for Lustre CSI 드라이버](https://github.com/kubernetes-sigs/aws-fsx-csi-driver)를 사용하여 Amazon EKS 또는 AWS 내 자체 관리형 쿠버네티스 클러스터에서 FSx for Lustre 볼륨을 퍼시스턴트 볼륨으로 사용할 수 있습니다. 자세한 내용과 예제는 [Amazon EKS 설명서](https://docs.aws.amazon.com/eks/latest/userguide/fsx-csi.html)를 참조하십시오. 

#### Amazon S3로 연결

Amazon S3와 같이 내구성이 뛰어난 장기 데이터 리포지토리를 FSx for Lustre 파일 시스템과 연결하는 것이 좋습니다. 일단 연결되면 대규모 데이터 세트가 필요에 따라 Amazon S3에서 FSx for Lustre 파일 시스템으로 레이지 로드(lazy load)됩니다. 분석을 실행하고 결과를 S3로 다시 가져온 다음 [Lustre] 파일 시스템을 삭제할 수도 있습니다. 


#### 적절한 배포 및 스토리지 옵션 선택

FSx for Lustre는 다양한 배포 옵션을 제공합니다.첫 번째 옵션은 *스크래치*로 데이터를 복제하지 않는 반면, 두 번째 옵션은 이름에서 알 수 있듯이 데이터를 유지하는 *지속적*입니다. 

첫 번째 옵션 (*스크래치*)을 사용하면 *일시적인 단기 데이터 처리 비용을 줄일 수 있습니다.* 영구 배포 옵션은 AWS 가용 영역 내에서 데이터를 자동으로 복제하는 _장기 스토리지를 위해 설계되었습니다_. 또한 SSD와 HDD 스토리지를 모두 지원합니다. 

FSx for lustre 파일 시스템의 쿠버네티스 스토리지클래스에 있는 파라미터에서 원하는 배포 유형을 구성할 수 있습니다. 다음은 샘플 템플릿을 제공하는 [링크](https://github.com/kubernetes-sigs/aws-fsx-csi-driver/tree/master/examples/kubernetes/dynamic_provisioning#edit-storageclass)입니다.

!!! note
    지연 시간에 민감한 워크로드 또는 최고 수준의 IOPS/처리량이 필요한 워크로드의 경우 SSD 스토리지를 선택해야 합니다. 지연 시간에 민감하지 않은 처리량 중심 워크로드의 경우 HDD 스토리지를 선택해야 합니다.


#### 데이터 압축 활성화

“LZ4"를 데이터 압축 유형으로 지정하여 파일 시스템에서 데이터 압축을 활성화할 수도 있습니다. 활성화되면 새로 작성된 모든 파일은 디스크에 기록되기 전에 FSx for Lustre에서 자동으로 압축되고 읽을 때 압축이 해제됩니다. LZ4 데이터 압축 알고리즘은 손실이 없으므로 압축된 데이터로 원본 데이터를 완전히 재구성할 수 있습니다. 

lustre 파일 시스템의 쿠버네티스 스토리지클래스용 FSx의 파라미터에서 데이터 압축 유형을 LZ4로 구성할 수 있습니다. 값이 기본값인 NONE으로 설정되면 압축이 비활성화됩니다. 이 [링크](https://github.com/kubernetes-sigs/aws-fsx-csi-driver/tree/master/examples/kubernetes/dynamic_provisioning#edit-storageclass)는 샘플 템플릿을 제공합니다.

!!! note
    Amazon FSx for Lustre는 윈도우 기반 컨테이너 이미지와 호환되지 않습니다.


### Amazon FSx for NetApp ONTAP

[Amazon FSx for NetApp ONTAP](https://aws.amazon.com/fsx/netapp-ontap/)은 NetApp의 ONTAP 파일 시스템을 기반으로 구축된 완전 관리형 공유 스토리지입니다. FSx for ONTAP은 AWS 또는 온프레미스에서 실행되는 리눅스, 윈도우 및 macOS 컴퓨팅 인스턴스에서 광범위하게 액세스할 수 있는 기능이 풍부하고 빠르며 유연한 공유 파일 스토리지를 제공합니다. 

NetApp ONTAP용 Amazon FSx는 *1/기본 계층*과 *2/용량 풀 계층이라는 두 가지 스토리지 계층을 지원합니다.* 

*기본 계층*은 지연 시간에 민감한 활성 데이터를 위한 프로비저닝된 고성능 SSD 기반 계층입니다. 완전히 탄력적인 *용량 풀 계층*은 자주 액세스하지 않는 데이터에 대해 비용 최적화되고, 데이터가 계층화됨에 따라 자동으로 확장되며, 사실상 무제한 페타바이트의 용량을 제공합니다. 용량 풀 스토리지에서 데이터 압축 및 중복 제거를 활성화하여 데이터가 소비하는 스토리지 용량을 더욱 줄일 수 있습니다. NetApp의 기본 정책 기반 FabricPool 기능은 데이터 액세스 패턴을 지속적으로 모니터링하여 스토리지 계층 간에 데이터를 양방향으로 자동 전송하여 성능과 비용을 최적화합니다.

NetApp의 Astra Trident는 CSI 드라이버를 사용한 동적 스토리지 오케스트레이션을 제공합니다. 이를 통해 Amazon EKS 클러스터는 NetApp ONTAP 파일 시스템용 Amazon FSX가 지원하는 퍼시스턴트 볼륨 PV의 수명 주기를 관리할 수 있습니다. 시작하려면 아스트라 트라이던트 설명서의 [NetApp ONTAP용 Amazon FSx와 함께 아스트라 트라이던트 사용](https://docs.netapp.com/us-en/trident/trident-use/trident-fsx.html)을 참조하십시오.


## 기타 고려 사항

### 컨테이너 이미지 크기 최소화

컨테이너가 배포되면 컨테이너 이미지가 호스트에 여러 레이어로 캐시됩니다. 이미지 크기를 줄이면 호스트에 필요한 스토리지 양을 줄일 수 있습니다. 

처음부터 [스크래치](https://hub.docker.com/_/scratch) 이미지 또는 [distroless](https://github.com/GoogleContainerTools/distroless) 컨테이너 이미지 (애플리케이션 및 런타임 종속성만 포함)와 같은 간소화된 기본 이미지를 사용하면 *스토리지 비용을 절감할 수 있을 뿐만 아니라 공격 노출 영역 감소 및 이미지 풀 타임 단축과 같은 기타 부수적인 이점도 줄일 수 있습니다.*

최소한의 이미지를 만들 수 있는 쉽고 안전한 방법을 제공하는 [Slim.ai](https://www.slim.ai/docs/quickstart)와 같은 오픈 소스 도구를 사용하는 것도 고려해 보는 것이 좋습니다.

여러 계층의 패키지, 도구, 애플리케이션 종속성, 라이브러리는 컨테이너 이미지 크기를 쉽게 부풀릴 수 있습니다. 다단계 빌드를 사용하면 최종 이미지에서 필요하지 않은 모든 요소를 제외하고 한 스테이지에서 다른 스테이지로 아티팩트를 선택적으로 복사할 수 있습니다. 더 많은 이미지 구축 모범 사례를 [여기](https://docs.docker.com/get-started/09_image_best/)에서 확인할 수 있습니다. 

고려해야 할 또 다른 사항은 캐시된 이미지를 얼마나 오래 유지할 것인가입니다. 일정량의 디스크를 사용하는 경우 이미지 캐시에서 오래된 이미지를 정리하는 것이 좋습니다. 이렇게 하면 호스트 작업을 위한 충분한 공간을 확보하는 데 도움이 됩니다. 기본적으로 [kubelet](https://kubernetes.io/docs/reference/generated/kubelet)은 미사용 이미지에 대해 5분마다, 미사용 컨테이너에 대해서는 1분마다 가비지 수집을 수행합니다. 

*미사용 컨테이너 및 이미지 가비지 컬렉션에 대한 옵션을 구성하려면 [구성 파일](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/)을 사용하여 kubelet을 조정하고 [`kubeletConfiguration`](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/) 리소스 유형을 사용하여 가비지 컬렉션과 관련된 파라미터를 변경하십시오.* 

이에 대한 자세한 내용은 쿠버네티스 [문서](https://kubernetes.io/docs/concepts/architecture/garbage-collection/#containers-images)에서 확인할 수 있다. 
