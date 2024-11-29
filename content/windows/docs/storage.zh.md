# 持久存储选项

## 什么是内置与外置卷插件？

在引入容器存储接口(CSI)之前，所有卷插件都是内置的，这意味着它们是与Kubernetes核心二进制文件一起构建、链接、编译和发布的，并扩展了Kubernetes核心API。这意味着向Kubernetes添加新的存储系统(卷插件)需要将代码合并到Kubernetes核心代码库中。

外置卷插件独立于Kubernetes代码库开发，并作为扩展部署(安装)在Kubernetes集群上。这使供应商能够独立于Kubernetes发布周期单独更新驱动程序。这在很大程度上是因为Kubernetes创建了一个存储接口或CSI，为供应商提供了一种与k8s接口的标准方式。

您可以在https://docs.aws.amazon.com/eks/latest/userguide/storage.html上查看有关Amazon Elastic Kubernetes Services (EKS)存储类和CSI驱动程序的更多信息。

## Windows的内置卷插件
Kubernetes卷使需要数据持久性的应用程序能够部署在Kubernetes上。持久卷的管理包括卷的配置/取消配置/调整大小、将卷附加/分离到/从Kubernetes节点，以及将卷挂载/卸载到/从pod中的单个容器。实现特定存储后端或协议的这些卷管理操作的代码以Kubernetes卷插件的形式发布**(内置卷插件)**。在Amazon Elastic Kubernetes Services (EKS)上，支持以下类别的Kubernetes卷插件在Windows上运行：

*内置卷插件：* [awsElasticBlockStore](https://kubernetes.io/docs/concepts/storage/volumes/#awselasticblockstore)

为了在Windows节点上使用内置卷插件，有必要创建一个额外的StorageClass来使用NTFS作为fsType。在EKS上，默认的StorageClass使用ext4作为默认的fsType。

StorageClass为管理员提供了一种描述他们提供的"存储类"的方式。不同的类可能映射到服务质量级别、备份策略或由集群管理员确定的任意策略。Kubernetes对类代表什么没有任何意见。这个概念在其他存储系统中有时被称为"配置文件"。

您可以通过运行以下命令来检查它：

```bash
kubectl describe storageclass gp2
```

输出：

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

要创建支持**NTFS**的新StorageClass，请使用以下清单：

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

通过运行以下命令创建StorageClass：

```bash 
kubectl apply -f NTFSStorageClass.yaml
```

下一步是创建持久卷声明(PVC)。

持久卷(PV)是由管理员预先配置或使用PVC动态配置的集群中的一块存储。它是集群中的一种资源，就像节点是集群资源一样。此API对象捕获了存储实现的细节，无论是NFS、iSCSI还是特定于云提供商的存储系统。

持久卷声明(PVC)是用户对存储的请求。声明可以请求特定大小和访问模式(例如，它们可以以ReadWriteOnce、ReadOnlyMany或ReadWriteMany模式挂载)。

用户需要具有不同属性(如性能)的持久卷来满足不同的用例需求。集群管理员需要能够提供各种不同于仅大小和访问模式的持久卷，而无需向用户公开这些卷的实现细节。为了满足这些需求，就有了StorageClass资源。

在下面的示例中，PVC是在windows命名空间中创建的。

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

通过运行以下命令创建PVC：

```bash 
kubectl apply -f persistent-volume-claim.yaml
```

以下清单创建了一个Windows Pod，将卷挂载设置为`C:\Data`,并使用PVC作为附加到`C:\Data`的存储。

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

通过PowerShell访问Windows pod来测试结果：

```bash 
kubectl exec -it podname powershell -n windows
```

在Windows Pod内，运行： `ls`

输出：

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

**data目录**由EBS卷提供。

## Windows的外置插件
与CSI插件相关的代码作为外置脚本和二进制文件发布，通常以容器镜像的形式分发，并使用标准的Kubernetes构造(如DaemonSet和StatefulSet)进行部署。CSI插件处理Kubernetes中的各种卷管理操作。CSI插件通常由节点插件(作为DaemonSet在每个节点上运行)和控制器插件组成。

CSI节点插件(尤其是那些与作为块设备或通过共享文件系统暴露的持久卷相关的插件)需要执行各种特权操作，如扫描磁盘设备、挂载文件系统等。这些操作因主机操作系统而异。对于Linux工作节点，容器化的CSI节点插件通常作为特权容器部署。对于Windows工作节点，容器化CSI节点插件的特权操作使用[csi-proxy](https://github.com/kubernetes-csi/csi-proxy)支持，这是一个由社区管理的独立二进制文件，需要预先安装在每个Windows节点上。

[Amazon EKS优化的Windows AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html)从2022年4月开始包含CSI代理。客户可以在Windows节点上使用[SMB CSI驱动程序](https://github.com/kubernetes-csi/csi-driver-smb)来访问[Amazon FSx for Windows File Server](https://aws.amazon.com/fsx/windows/)、[Amazon FSx for NetApp ONTAP SMB共享](https://aws.amazon.com/fsx/netapp-ontap/)和/或[AWS Storage Gateway - File Gateway](https://aws.amazon.com/storagegateway/file/)。

以下[博客](https://aws.amazon.com/blogs/modernizing-with-aws/using-smb-csi-driver-on-amazon-eks-windows-nodes/)详细介绍了如何设置SMB CSI驱动程序以使用Amazon FSx for Windows File Server作为Windows Pod的持久存储。

## Amazon FSx for Windows File Server
一种选择是通过SMB的一个名为[SMB全局映射](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/persistent-storage)的功能使用Amazon FSx for Windows File Server，该功能使得可以在主机上挂载SMB共享，然后将该共享上的目录传递到容器中。容器不需要配置特定的服务器、共享、用户名或密码 - 这一切都在主机上处理。容器的工作方式就像它有本地存储一样。

> SMB全局映射对编排器是透明的，并且通过HostPath挂载，这**可能会带来安全隐患**。

在下面的示例中，路径`G:\Directory\app-state`是Windows节点上的SMB共享。

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

以下[博客](https://aws.amazon.com/blogs/containers/using-amazon-fsx-for-windows-file-server-on-eks-windows-containers/)详细介绍了如何设置Amazon FSx for Windows File Server作为Windows Pod的持久存储。