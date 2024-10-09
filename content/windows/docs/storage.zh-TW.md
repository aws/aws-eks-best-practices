# 持久性儲存選項

## 什麼是內建 (in-tree) 與外部 (out-of-tree) 儲存體插件?

在引入容器儲存介面 (Container Storage Interface, CSI) 之前,所有的儲存體插件都是內建的,這意味著它們是與 Kubernetes 核心二進位檔案一起建置、連結、編譯和發佈的,並擴充了 Kubernetes 核心 API。這意味著要將新的儲存系統加入 Kubernetes (一個儲存體插件) 就需要將程式碼合併到 Kubernetes 核心程式碼庫中。

外部儲存體插件是獨立於 Kubernetes 程式碼庫開發的,並作為擴充功能部署 (安裝) 在 Kubernetes 叢集上。這使廠商能夠獨立於 Kubernetes 發佈週期來更新驅動程式。這在很大程度上是因為 Kubernetes 已經建立了一個儲存介面或 CSI,為廠商提供了一種標準的方式來與 k8s 介接。

您可以在 https://docs.aws.amazon.com/eks/latest/userguide/storage.html 查看更多關於 Amazon Elastic Kubernetes Services (EKS) 儲存類別和 CSI 驅動程式的資訊。

## Windows 的內建儲存體插件
Kubernetes 儲存體使需要資料持久性的應用程式能夠部署在 Kubernetes 上。持久性儲存體的管理包括佈建/解佈建/調整儲存體大小、將儲存體連接/分離到/從 Kubernetes 節點,以及將儲存體掛載/卸載到/從 Pod 中的個別容器。實作這些特定儲存體後端或協定的儲存體管理動作的程式碼,是以 Kubernetes 儲存體插件的形式發佈 **(內建儲存體插件)**。在 Amazon Elastic Kubernetes Services (EKS) 上,以下類別的 Kubernetes 儲存體插件在 Windows 上受支援:

*內建儲存體插件:* [awsElasticBlockStore](https://kubernetes.io/docs/concepts/storage/volumes/#awselasticblockstore)

為了在 Windows 節點上使用內建儲存體插件,有必要建立額外的 StorageClass 來使用 NTFS 作為 fsType。在 EKS 上,預設的 StorageClass 使用 ext4 作為預設的 fsType。

StorageClass 為管理員提供了一種描述他們所提供的「儲存類別」的方式。不同的類別可能對應到服務品質層級、備份政策或由叢集管理員決定的任意政策。Kubernetes 對於什麼樣的類別並不固步自封。在其他儲存系統中,這個概念有時被稱為「配置檔」。

您可以透過執行以下命令來檢查:

```bash
kubectl describe storageclass gp2
```

輸出:

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

要建立支援 **NTFS** 的新 StorageClass,請使用以下資訊清單:

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

透過執行以下命令來建立 StorageClass:

```bash 
kubectl apply -f NTFSStorageClass.yaml
```

下一步是建立 Persistent Volume Claim (PVC)。

Persistent Volume (PV) 是由管理員或透過 PVC 動態佈建的叢集中的一塊儲存空間。它是叢集中的一種資源,就像節點是叢集資源一樣。這個 API 物件捕捉了儲存實作的詳細資料,無論是 NFS、iSCSI 或特定於雲端供應商的儲存系統。

Persistent Volume Claim (PVC) 是使用者對儲存空間的請求。Claim 可以請求特定大小和存取模式 (例如,它們可以掛載為 ReadWriteOnce、ReadOnlyMany 或 ReadWriteMany)。

使用者對於不同的使用案例需要具有不同屬性 (如效能) 的 Persistent Volume。叢集管理員需要能夠提供各種不同的 Persistent Volume,不僅僅是大小和存取模式不同,而且不會將使用者暴露在實作這些儲存體的細節中。為了滿足這些需求,就有了 StorageClass 資源。

在下面的範例中,PVC 已在 windows 命名空間中建立。

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

透過執行以下命令來建立 PVC:

```bash 
kubectl apply -f persistent-volume-claim.yaml
```

以下資訊清單建立了一個 Windows Pod,將 VolumeMount 設置為 `C:\Data`,並使用 PVC 作為連接到 `C:\Data` 的儲存體。

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

透過 PowerShell 存取 Windows Pod 來測試結果:

```bash 
kubectl exec -it podname powershell -n windows
```

在 Windows Pod 內部,執行: `ls`

輸出:

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

**data 目錄**是由 EBS 儲存體提供的。

## Windows 的外部儲存體插件
與 CSI 插件相關的程式碼以外部腳本和二進位檔的形式發佈,通常作為容器映像檔分發,並使用標準的 Kubernetes 結構 (如 DaemonSet 和 StatefulSet) 進行部署。CSI 插件處理 Kubernetes 中的各種儲存體管理動作。CSI 插件通常由節點插件 (以 DaemonSet 的形式在每個節點上運行) 和控制器插件組成。

CSI 節點插件 (尤其是那些與作為區塊裝置或透過共享檔案系統公開的持久性儲存體相關的插件) 需要執行各種特權操作,如掃描磁碟裝置、掛載檔案系統等。這些操作因主機作業系統而異。對於 Linux 工作節點,容器化的 CSI 節點插件通常作為特權容器部署。對於 Windows 工作節點,容器化 CSI 節點插件的特權操作是透過 [csi-proxy](https://github.com/kubernetes-csi/csi-proxy) 支援的,這是一個由社群管理的獨立二進位檔,需要預先安裝在每個 Windows 節點上。

[Amazon EKS 優化的 Windows AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html) 從 2022 年 4 月開始包含 CSI-proxy。客戶可以在 Windows 節點上使用 [SMB CSI 驅動程式](https://github.com/kubernetes-csi/csi-driver-smb) 來存取 [Amazon FSx for Windows File Server](https://aws.amazon.com/fsx/windows/)、[Amazon FSx for NetApp ONTAP SMB 共享](https://aws.amazon.com/fsx/netapp-ontap/) 和/或 [AWS Storage Gateway - File Gateway](https://aws.amazon.com/storagegateway/file/)。

以下 [部落格文章](https://aws.amazon.com/blogs/modernizing-with-aws/using-smb-csi-driver-on-amazon-eks-windows-nodes/) 有關於如何設置 SMB CSI 驅動程式來使用 Amazon FSx for Windows File Server 作為 Windows Pod 的持久性儲存體的實作細節。

## Amazon FSx for Windows File Server
一個選項是透過 SMB 的一個功能 [SMB 全域對應](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/persistent-storage)來使用 Amazon FSx for Windows File Server,該功能使得在主機上掛載 SMB 共享,然後將該共享上的目錄傳遞到容器中成為可能。容器不需要配置特定的伺服器、共享、使用者名稱或密碼 - 這些都在主機上處理。容器的工作方式就像它有本地儲存一樣。

> SMB 全域對應對於 orchestrator 是透明的,並且是透過 HostPath 掛載的,這 **可能會帶來安全性問題**。

在下面的範例中,路徑 `G:\Directory\app-state` 是 Windows 節點上的 SMB 共享。

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

以下 [部落格文章](https://aws.amazon.com/blogs/containers/using-amazon-fsx-for-windows-file-server-on-eks-windows-containers/) 有關於如何設置 Amazon FSx for Windows File Server 作為 Windows Pod 的持久性儲存體的實作細節。