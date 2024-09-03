---
search:
  exclude: true
---


# 영구 스토리지 옵션

## In-tree와 Out-of-tree 볼륨 플러그인

컨테이너 스토리지 인터페이스(CSI)가 도입되기 전에는 모든 볼륨 플러그인이 in-tree 였습니다. 즉, 코어 쿠버네티스 바이너리와 함께 빌드, 연결, 컴파일 및 제공되고 핵심 쿠버네티스 API를 확장했습니다. 이는 쿠버네티스에 새로운 스토리지 시스템(볼륨 플러그인)을 추가하려면 핵심 코어 쿠버네티스 코드 저장소에 대한 코드를 확인해야 하는 것을 의미했습니다.

Out-of-tree 볼륨 플러그인은 쿠버네티스 코드 베이스와 독립적으로 개발되며 쿠버네티스 클러스터에 확장으로 배포(및 설치) 됩니다. 이를 통해 벤더는 쿠버네티스 릴리스 주기와 별도로 드라이버를 업데이트 할 수 있습니다. 이는 쿠버네티스가 벤더에 k8s와 인터페이스하는 표준 방법을 제공하는 스토리지 인터페이스 혹은 CSI를 만들었기 때문에 가능합니다.

Amazon Elastic Kubernetes Services (EKS) 스토리지 클래스 및 CSI 드라이버에 대한 자세한 내용을 [AWS 문서](https://docs.aws.amazon.com/eks/latest/userguide/storage.html)에서 확인할 수 있습니다.

## 윈도우용 In-tree 볼륨 플러그인
쿠버네티스 볼륨을 사용하면 데이터 지속성 요구 사항이 있는 애플리케이션을 쿠버네티스에 배포할 수 있습니다. 퍼시스턴트 볼륨 관리는 볼륨 프로비저닝/프로비저닝 해제/크기 조정, 쿠버네티스 노드에 볼륨 연결/분리, 파드의 개별 컨테이너에 볼륨 마운트/마운트 해제로 구성됩니다. 특정 스토리지 백엔드 또는 프로토콜에 대해 이런 볼륨 관리 작업을 구현하기 위한 코드는 쿠버네티스 볼륨 플러그인 **(In-tree 볼륨 플러그인)** 형식으로 제공됩니다. Amazon EKS에서는 윈도우에서 다음과 같은 클래스의 쿠버네티스 볼륨 플러그인이 지원됩니다:

*In-tree 볼륨 플러그인:* [awsElasticBlockStore](https://kubernetes.io/docs/concepts/storage/volumes/#awselasticblockstore)

윈도우 노드에서 In-tree 볼륨 플러그인을 사용하기 위해서는 NTFS를 fsType 으로 사용하기 위한 추가 StorageClass를 생성해야 합니다. EKS에서 기본 StorageClass는 ext4를 기본 fsType으로 사용합니다.

StorageClass는 관리자가 제공하는 스토리지의 "클래스"를 설명하는 방법을 제공합니다. 다양한 클래스는 QoS 수준, 백업 정책 또는 클러스터 관리자가 결정한 임의 정책에 매핑될 수 있습니다. 쿠버네티스는 클래스가 무엇을 나타내는지에 대해 의견이 없습니다. 이 개념은 다른 스토리지 시스템에서는 "프로파일" 이라고 부르기도 합니다.

다음 명령을 실행하여 확인할 수 있습니다:

```bash
kubectl describe storageclass gp2
```

출력:

```bash
Name:            gp2
IsDefaultClass:  Yes
Annotations:     kubectl.kubernetes.io/last-applied-configuration={"apiVersion":"storage.k8s.io/v1","kind":"StorageClas
","metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"},"name":"gp2"},"parameters":{"fsType"
"ext4","type":"gp2"},"provisioner":"kubernetes.io/aws-ebs","volumeBindingMode":"WaitForFirstConsumer"}
,storageclass.kubernetes.io/is-default-class=true
Provisioner:           kubernetes.io/aws-ebs
Parameters:            fsType=ext4,type=gp2
AllowVolumeExpansion:  <unset>
MountOptions:          <none>
ReclaimPolicy:         Delete
VolumeBindingMode:     WaitForFirstConsumer
Events:                <none>
```

**NTFS**를 지원하는 새 StorageClass를 생성하려면 다음 매니페스트를 사용하십시오:

```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: gp2-windows
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
  fsType: ntfs
volumeBindingMode: WaitForFirstConsumer
```

다음 명령을 실행하여 StorageClass를 생성합니다:

```bash 
kubectl apply -f NTFSStorageClass.yaml
```

다음 단계는 퍼시스턴트 볼륨 클레임(PVC)을 생성하는 것입니다.

퍼시스턴트 볼륨(PV)은 관리자가 프로비저닝했거나 PVC를 사용하여 동적으로 프로비저닝된 클러스터의 스토리지입니다. 노드가 클러스터 리소스인 것처럼 클러스터의 리소스입니다. 이 API 객체는 NFS, iSCSI 또는 클라우드 공급자별 스토리지 시스템 등 스토리지 구현의 세부 정보를 캡처합니다.

PVC는 사용자의 스토리지 요청입니다. 클레임은 특정 크기 및 액세스 모드를 요청할 수 있습니다(예: ReadWriteOnce, ReadOnlyMany 또는 ReadWriteMan로 마운트될 수 있음).

사용자에게는 다양한 유즈케이스를 위해 성능과 같은 다양한 속성을 가진 PV가 필요합니다. 클러스터 관리자는 사용자에게 해당 볼륨이 구현되는 방법에 대한 세부 정보를 노출시키지 않고도 크기 및 액세스 모드보다 더 다양한 방식으로 PV를 제공할 수 있어야 합니다. 이런 요구 사항을 충족하기 위해 StorageClass 리소스가 있습니다. 

아래 예제에서 윈도우 네임스페이스 내에 PVC가 생성되었습니다.

```yaml 
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-windows-pv-claim
  namespace: windows
spec: 
  accessModes:
    - ReadWriteOnce
  storageClassName: gp2-windows
  resources: 
    requests:
      storage: 1Gi
```

다음 명령을 실행하여 PVC를 만듭니다:

```bash 
kubectl apply -f persistent-volume-claim.yaml
```

다음 매니페스트에서는 윈도우 파드를 생성하고 VolumeMount를 `C:\Data`로 설정하고 PVC를 `C:\Data`에 연결된 스토리지로 사용합니다.

```yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: windows-server-ltsc2019
  namespace: windows
spec:
  selector:
    matchLabels:
      app: windows-server-ltsc2019
      tier: backend
      track: stable
  replicas: 1
  template:
    metadata:
      labels:
        app: windows-server-ltsc2019
        tier: backend
        track: stable
    spec:
      containers:
      - name: windows-server-ltsc2019
        image: mcr.microsoft.com/windows/servercore:ltsc2019
        ports:
        - name: http
          containerPort: 80
        imagePullPolicy: IfNotPresent
        volumeMounts:
        - mountPath: "C:\\data"
          name: test-volume
      volumes:
        - name: test-volume
          persistentVolumeClaim:
            claimName: ebs-windows-pv-claim
      nodeSelector:
        kubernetes.io/os: windows
        node.kubernetes.io/windows-build: '10.0.17763'
```

PowerShell을 통해 윈도우 파드에 액세스하여 결과를 테스트합니다:

```bash 
kubectl exec -it podname powershell -n windows
```

윈도우 파드 내에서 `ls`를 수행합니다:

출력:

```bash 
PS C:\> ls


    Directory: C:\


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----          3/8/2021   1:54 PM                data
d-----          3/8/2021   3:37 PM                inetpub
d-r---          1/9/2021   7:26 AM                Program Files
d-----          1/9/2021   7:18 AM                Program Files (x86)
d-r---          1/9/2021   7:28 AM                Users
d-----          3/8/2021   3:36 PM                var
d-----          3/8/2021   3:36 PM                Windows
-a----         12/7/2019   4:20 AM           5510 License.txt
```

**data directory** 는 EBS 볼륨에 의해 제공됩니다.

## 윈도우 Out-of-tree
CSI 플러그인과 연결된 코드는 일반적으로 컨테이너 이미지로 배포되고 데몬셋(DaemonSet) 및 스테이트풀셋(StatefulSet)과 같은 표준 쿠버네티스 구성을 사용하여 배포되는 out-of-tree 스크립트 및 바이너리로 제공됩니다. CSI 플러그인은 쿠버네티스에서 광범위한 볼륨 관리 작업을 처리합니다. CSI 플러그인은 일반적으로 노드 플러그인(각 노드에서 데몬셋으로 실행됨)과 컨트롤러 플러그인으로 구성됩니다.

CSI 노드 플러그인 (특히 블록 장치 또는 공유 파일 시스템을 통해 노출되는 퍼시스턴트 볼륨과 관련된 플러그인)은 디스크 장치 스캔, 파일 시스템 탑재 등과 같은 다양한 권한 작업을 수행해야 합니다. 이런 작업은 호스트 운영 체제마다 다릅니다. 리눅스 워커 노드의 경우 컨테이너화된 CSI 노드 플러그인은 일반적으로 권한 있는 컨테이너로 배포됩니다. 윈도우 워커 노드의 경우 각 윈도우 노드에 사전 설치해야 하는 커뮤니티 관리 독립 실행형 바이너리인 [csi-proxy](https://github.com/kubernetes-csi/csi-proxy) 를 사용하여 컨테이너화된 CSI 노드 플러그인에 대한 권한 있는 작업이 지원됩니다. 

[Amazon EKS 최적화 윈도우 AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html)에서는 2022년 4월부터 CSI-proxy가 포함됩니다. 고객은 윈도우 노드의 [SMB CSI 드라이버](https://github.com/kubernetes-csi/csi-driver-smb)를 사용하여 [Amazon FSx for Windows File Server](https://aws.amazon.com/fsx/windows/), [Amazon FSx for NetApp ONTAP SMB Shares](https://aws.amazon.com/fsx/netapp-ontap/), 및/또는 [AWS Storage Gateway – File Gateway](https://aws.amazon.com/storagegateway/file/)에 액세스 할 수 있습니다.

다음 [블로그](https://aws.amazon.com/blogs/modernizing-with-aws/using-smb-csi-driver-on-amazon-eks-windows-nodes/)에서는 Amazon FSx for Windows File Server를 위도우 파드용 영구 스토리지로 사용하도록 SMB CSI 드라이버를 설정하는 방법에 대한 세부 정보가 나와 있습니다.

## Amazon FSx for Windows File Server
한 가지 옵션은 [SMB Global Mapping](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/persistent-storage)이라는 SMB 기능을 통해 Windows 파일 서버용 Amazon FSx를 사용하는 것입니다. 이 기능을 사용하면 호스트에 SMB 공유를 마운트한 다음 해당 공유의 디렉터리를 컨테이너로 전달할 수 있습니다. 컨테이너를 특정 서버, 공유, 사용자 이름 또는 암호로 구성할 필요가 없습니다. 대신 호스트에서 모두 처리됩니다. 컨테이너는 로컬 스토리지가 있는 것처럼 작동합니다.

> SMB Global Mapping은 오케스트레이터에게 투명하게 전달되며 HostPath를 통해 마운트되므로 **보안 문제가 발생할 수 있습니다**.

아래 예제에서, `G:\Directory\app-state` 경로는 윈도우 노드의 SMB 공유입니다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-fsx
spec:
  containers:
  - name: test-fsx
    image: mcr.microsoft.com/windows/servercore:ltsc2019
    command:
      - powershell.exe
      - -command
      - "Add-WindowsFeature Web-Server; Invoke-WebRequest -UseBasicParsing -Uri 'https://dotnetbinaries.blob.core.windows.net/servicemonitor/2.0.1.6/ServiceMonitor.exe' -OutFile 'C:\\ServiceMonitor.exe'; echo '<html><body><br/><br/><marquee><H1>Hello EKS!!!<H1><marquee></body><html>' > C:\\inetpub\\wwwroot\\default.html; C:\\ServiceMonitor.exe 'w3svc'; "
    volumeMounts:
      - mountPath: C:\dotnetapp\app-state
        name: test-mount
  volumes:
    - name: test-mount
      hostPath: 
        path: G:\Directory\app-state
        type: Directory
  nodeSelector:
      beta.kubernetes.io/os: windows
      beta.kubernetes.io/arch: amd64
```

다음 [블로그](https://aws.amazon.com/blogs/containers/using-amazon-fsx-for-windows-file-server-on-eks-windows-containers/) 에서는 Amazon FSx for Windows File Server를 윈도우 파드용 영구 스토리지로 설정하는 방법에 대한 세부 정보가 나와 있습니다.
