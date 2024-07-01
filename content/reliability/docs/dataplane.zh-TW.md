# EKS 資料平面

為了運行高可用性和高彈性的應用程式,您需要一個高可用性和高彈性的資料平面。彈性資料平面可確保 Kubernetes 能夠自動擴展和修復您的應用程式。高彈性的資料平面包含兩個或更多工作節點,可以隨著工作負載的增加而擴展和縮減,並能自動從故障中恢復。

在 EKS 中,您可以選擇 [EC2 實例](https://docs.aws.amazon.com/eks/latest/userguide/worker.html)或 [Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)作為工作節點。如果您選擇 EC2 實例,您可以自行管理工作節點或使用 [EKS 受管節點群組](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)。您可以在一個集群中混合使用受管理、自行管理的工作節點和 Fargate。

EKS on Fargate 提供了最簡單的方式來實現高彈性資料平面。Fargate 在一個隔離的計算環境中運行每個 Pod。在 Fargate 上運行的每個 Pod 都會獲得自己的工作節點。Fargate 會自動根據 Kubernetes 擴展 Pod 來擴展資料平面。您可以使用 [horizontal pod autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html) 來擴展資料平面和您的工作負載。

擴展 EC2 工作節點的首選方式是使用 [Kubernetes Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md)、[EC2 Auto Scaling groups](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) 或社區項目如 [Atlassian's Escalator](https://github.com/atlassian/escalator)。

## 建議

### 使用 EC2 Auto Scaling 群組來創建工作節點

使用 EC2 Auto Scaling 群組而不是創建單個 EC2 實例並將其加入集群來創建工作節點是最佳實踐。Auto Scaling 群組會自動替換任何終止或失敗的節點,確保集群始終有足夠的容量來運行您的工作負載。

### 使用 Kubernetes Cluster Autoscaler 來擴展節點

當由於集群資源不足而無法運行 Pod 時,Cluster Autoscaler 會調整資料平面的大小,而添加另一個工作節點將有助於解決這個問題。儘管 Cluster Autoscaler 是一個反應式的過程,但它會等到 Pod 由於集群容量不足而處於 *Pending* 狀態時才會觸發。當發生這種情況時,它會向集群添加 EC2 實例。每當集群資源不足時,新的副本或新的 Pod 將無法可用(*處於 Pending 狀態*),直到添加了工作節點。如果資料平面無法快速擴展以滿足工作負載的需求,這種延遲可能會影響您應用程式的可靠性。如果一個工作節點持續處於低利用率狀態,並且它上面的所有 Pod 都可以在其他工作節點上調度,Cluster Autoscaler 將終止該節點。

### 為 Cluster Autoscaler 配置過度配置

Cluster Autoscaler 在集群中已經有 Pod 處於 *Pending* 狀態時才會觸發資料平面的擴展。因此,在您的應用程式需要更多副本和實際獲得更多副本之間可能會有延遲。解決這種可能延遲的一種方法是添加比所需更多的副本,即為應用程式膨脹副本數量。

Cluster Autoscaler 推薦的另一種模式是使用 [*pause* Pod 和優先級抢占功能](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-can-i-configure-overprovisioning-with-cluster-autoscaler)。*pause Pod* 運行一個 [pause 容器](https://github.com/kubernetes/kubernetes/tree/master/build/pause),顧名思義,它什麼也不做,只是作為集群中其他 Pod 可以使用的計算容量的佔位符。由於它以 *非常低的優先級* 運行,當另一個 Pod 需要被創建但集群沒有可用容量時,pause Pod 就會被從節點上驅逐。Kubernetes 調度器注意到 pause Pod 的驅逐,並試圖重新調度它。但由於集群正在滿負荷運行,pause Pod 仍然處於 *Pending* 狀態,於是 Cluster Autoscaler 會對此做出反應,添加節點。

有一個 Helm chart 可用於安裝 [cluster overprovisioner](https://github.com/helm/charts/tree/master/stable/cluster-overprovisioner)。

### 使用 Cluster Autoscaler 和多個 Auto Scaling 群組

運行 Cluster Autoscaler 時啟用 `--node-group-auto-discovery` 標誌。這樣做將允許 Cluster Autoscaler 找到包含特定定義標籤的所有自動擴展群組,並防止需要在清單中定義和維護每個自動擴展群組。

### 使用 Cluster Autoscaler 和本地存儲

默認情況下,Cluster Autoscaler 不會縮減部署了帶有本地存儲的 Pod 的節點。將 `--skip-nodes-with-local-storage` 標誌設置為 false 以允許 Cluster Autoscaler 縮減這些節點。

### 將工作節點和工作負載分散到多個可用區

通過在多個可用區運行工作節點和 Pod,您可以保護工作負載免受單個可用區故障的影響。您可以使用創建節點所在的子網來控制工作節點創建在哪個可用區。

如果您使用的是 Kubernetes 1.18 或更高版本,跨可用區分散 Pod 的推薦方法是使用 [Pod 的拓撲擴散約束](https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/#spread-constraints-for-pods)。

下面的部署將儘可能跨可用區分散 Pod,如果不可能,也允許這些 Pod 運行:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          whenUnsatisfiable: ScheduleAnyway
          topologyKey: topology.kubernetes.io/zone
          labelSelector:
            matchLabels:
              app: web-server
      containers:
      - name: web-app
        image: nginx
        resources:
          requests:
            cpu: 1
```

!!! 注意
    `kube-scheduler` 只通過存在的節點上的標籤來感知拓撲域。如果上面的部署被部署到只有單個可用區的集群中,所有的 Pod 將被調度到那些節點上,因為 `kube-scheduler` 不知道其他可用區。為了使這種拓撲擴散約束按預期工作,必須在所有可用區都已經存在節點。這個問題將在 Kubernetes 1.24 中通過添加 `MinDomainsInPodToplogySpread` [特性閘](https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/#api)得到解決,該特性允許指定 `minDomains` 屬性來通知調度器有多少個可用域。

!!! 警告
    將 `whenUnsatisfiable` 設置為 `DoNotSchedule` 將導致如果無法滿足拓撲擴散約束,Pod 將無法被調度。只有在您寧願 Pod 不運行而不違反拓撲擴散約束時才應該這樣設置。

在較舊版本的 Kubernetes 上,您可以使用 Pod 反親和性規則來跨多個可用區調度 Pod。下面的清單通知 Kubernetes 調度器 *優先* 在不同的可用區調度 Pod。

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
  labels:
    app: web-server
spec:
  replicas: 4
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-server
              topologyKey: failure-domain.beta.kubernetes.io/zone
            weight: 100
      containers:
      - name: web-app
        image: nginx
```

!!! 警告
    不要要求 Pod 必須被調度到不同的可用區,否則部署中的 Pod 數量永遠不會超過可用區的數量。

### 在使用 EBS 卷時確保每個可用區都有容量

如果您使用 [Amazon EBS 來提供持久卷](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html),那麼您需要確保 Pod 和相關的 EBS 卷位於同一個可用區。在撰寫本文時,EBS 卷只能在單個可用區內使用。Pod 無法訪問位於不同可用區的 EBS 支持的持久卷。Kubernetes [調度器知道工作節點](https://kubernetes.io/docs/reference/kubernetes-api/labels-annotations-taints/#topologykubernetesiozone)所在的可用區。Kubernetes 將始終在與卷所在的相同可用區調度需要 EBS 卷的 Pod。但是,如果卷所在的可用區沒有可用的工作節點,則無法調度該 Pod。

為每個可用區創建一個 Auto Scaling 群組,並確保集群始終有足夠的容量來在與 Pod 所需的 EBS 卷相同的可用區調度 Pod。此外,您應該為 Cluster Autoscaler 啟用 `--balance-similar-node-groups` 功能。

如果您運行的應用程式使用 EBS 卷但沒有高可用性要求,則可以將該應用程式的部署限制在單個可用區。在 EKS 中,工作節點會自動添加 `failure-domain.beta.kubernetes.io/zone` 標籤,其中包含可用區的名稱。您可以通過運行 `kubectl get nodes --show-labels` 來查看附加到節點的標籤。有關內置節點標籤的更多信息,請參閱[這裡](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#built-in-node-labels)。您可以使用節點選擇器在特定可用區調度 Pod。

在下面的示例中,Pod 只會被調度在 `us-west-2c` 可用區:

```
apiVersion: v1
kind: Pod
metadata:
  name: single-az-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: failure-domain.beta.kubernetes.io/zone
            operator: In
            values:
            - us-west-2c
  containers:
  - name: single-az-container
    image: kubernetes/pause
```

持久卷(由 EBS 支持)也會自動標記為所在可用區的名稱;您可以通過運行 `kubectl get pv -L topology.ebs.csi.aws.com/zone` 來查看您的持久卷所屬的可用區。當創建一個 Pod 並聲明一個卷時,Kubernetes 將在與該卷相同的可用區調度該 Pod。

考慮以下情況;您有一個 EKS 集群,其中有一個節點群組。該節點群組有三個工作節點分散在三個可用區。您有一個使用 EBS 支持的持久卷的應用程式。當您創建這個應用程式和相應的卷時,它的 Pod 會被創建在這三個可用區中的第一個。然後,運行這個 Pod 的工作節點變得不健康並隨後無法使用。Cluster Autoscaler 將用一個新的工作節點替換不健康的節點;但是,由於自動擴展群組跨越三個可用區,新的工作節點可能會在第二個或第三個可用區啟動,而不是按需求在第一個可用區啟動。由於受可用區約束的 EBS 卷只存在於第一個可用區,但在該可用區沒有可用的工作節點,因此無法調度該 Pod。因此,您應該在每個可用區創建一個節點群組,以便始終有足夠的容量來運行無法在其他可用區調度的 Pod。

或者,[EFS](https://github.com/kubernetes-sigs/aws-efs-csi-driver) 可以簡化在運行需要持久存儲的應用程式時的集群自動擴展。客戶端可以從該區域的所有可用區同時訪問 EFS 文件系統。即使使用 EFS 支持的持久卷的 Pod 被終止並在不同的可用區重新調度,它也能夠掛載該卷。

### 運行 node-problem-detector

工作節點的故障可能會影響您應用程式的可用性。[node-problem-detector](https://github.com/kubernetes/node-problem-detector) 是一個 Kubernetes 插件,您可以在集群中安裝它來檢測工作節點問題。您可以使用 [npd 的補救系統](https://github.com/kubernetes/node-problem-detector#remedy-systems)自動排空和終止該節點。

### 為系統和 Kubernetes 守護進程保留資源

通過[為操作系統和 Kubernetes 守護進程保留計算容量](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/),您可以提高工作節點的穩定性。Pod - 特別是那些沒有聲明 `limits` 的 Pod - 可能會耗盡系統資源,導致節點處於操作系統進程和 Kubernetes 守護進程(如 `kubelet`、容器運行時等)與 Pod 競爭系統資源的情況。您可以使用 `kubelet` 標誌 `--system-reserved` 和 `--kube-reserved` 分別為系統進程(`udev`、`sshd` 等)和 Kubernetes 守護進程保留資源。

如果您使用 [EKS 優化的 Linux AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html),則默認情況下會為系統和 Kubernetes 守護進程保留 CPU、內存和存儲。當基於此 AMI 的工作節點啟動時,EC2 用戶數據被配置為觸發 [`bootstrap.sh` 腳本](https://github.com/awslabs/amazon-eks-ami/blob/master/files/bootstrap.sh)。該腳本根據 EC2 實例上的 CPU 內核數和總內存計算 CPU 和內存保留量。計算出的值將被寫入位於 `/etc/kubernetes/kubelet/kubelet-config.json` 的 `KubeletConfiguration` 文件。

如果您在節點上運行自定義守護進程,並且默認保留的系統資源不足,您可能需要增加系統資源保留量。

`eksctl` 提供了最簡單的方式來自定義[系統和 Kubernetes 守護進程的資源保留](https://eksctl.io/usage/customizing-the-kubelet/)。

### 實施 QoS

對於關鍵應用程式,請考慮為 Pod 中的容器定義 `requests`=`limits`。這將確保該容器不會在另一個 Pod 請求資源時被殺死。

為所有容器實施 CPU 和內存限制是最佳實踐,因為它可以防止容器無意中消耗系統資源,從而影響共存進程的可用性。

### 為所有工作負載配置和調整資源請求/限制

對於調整工作負載的資源請求和限制,可以應用一些通用指導原則:

- 不要為 CPU 指定資源限制。在沒有限制的情況下,請求充當了容器獲得 [相對 CPU 時間](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#how-pods-with-resource-limits-are-run) 的權重。這允許您的工作負載使用全部 CPU,而不會受到人為限制或飢餓的影響。

- 對於非 CPU 資源,配置 `requests`=`limits` 可以提供最可預測的行為。如果 `requests`!=`limits`,容器的 [QOS](https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/#qos-classes) 也會從 Guaranteed 降低到 Burstable,從而更容易在 [節點壓力](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/) 事件中被驅逐。

- 對於非 CPU 資源,不要指定一個遠大於請求的限制。限制相對於請求配置得越大,節點就越有可能被過度使用,導致工作負載中斷的可能性越高。

- 正確調整請求尤其重要,當使用像 [Karpenter](https://aws.github.io/aws-eks-best-practices/karpenter/) 或 [Cluster AutoScaler](https://aws.github.io/aws-eks-best-practices/cluster-autoscaling/) 這樣的節點自動擴展解決方案時。這些工具會根據您的工作負載請求來確定要配置的節點數量和大小。如果您的請求太小而限制較大,您可能會發現您的工作負載被驅逐或由於內存不足而被殺死,因為它們被緊密地打包在一個節點上。

確定資源請求可能很困難,但像 [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) 這樣的工具可以通過在運行時觀察容器資源使用情況來幫助您 "正確調整" 請求大小。其他可能有用的確定請求大小的工具包括:

- [Goldilocks](https://github.com/FairwindsOps/goldilocks)
- [Parca](https://www.parca.dev/)
- [Prodfiler](https://prodfiler.com/)
- [rsg](https://mhausenblas.info/right-size-guide/)

### 為命名空間配置資源配額

命名空間旨在用於跨多個團隊或項目的多用戶環境中使用。它們為名稱提供了一個範圍,是在多個團隊、項目、工作負載之間劃分集群資源的一種方式。您可以限制命名空間中的總體資源消耗。[`ResourceQuota`](https://kubernetes.io/docs/concepts/policy/resource-quotas/) 對象可以按類型限制可以在命名空間中創建的對象的數量,以及該項目中的資源可以消耗的總計算資源量。您可以限制給定命名空間中可以請求的總存儲和/或計算(CPU 和內存)資源量。

> 如果為命名空間啟用了計算資源(如 CPU 和內存)的資源配額,則必須為該命名空間中的每個容器指定請求或限制。

請考慮為每個命名空間配置配額。請考慮使用 `LimitRanges` 自動將預配置的限制應用於命名空間中的容器。

### 限制命名空間內容器的資源使用

資源配額有助於限制命名空間可以使用的資源量。[`LimitRange` 對象](https://kubernetes.io/docs/concepts/policy/limit-range/)可以幫助您實施容器可以請求的最小和最大資源。使用 `LimitRange` 您可以為容器設置默認的請求和限制,如果在您的組織中設置計算資源限制不是標準做法,這將很有幫助。顧名思義,`LimitRange` 可以在命名空間中強制每個 Pod 或容器的最小和最大計算資源使用,以及強制每個 PersistentVolumeClaim 的最小和最大存儲請求。

請考慮將 `LimitRange` 與 `ResourceQuota` 一起使用,以在容器和命名空間級別強制執行限制。設置這些限制將確保容器或命名空間不會侵佔集群中其他租戶使用的資源。

## CoreDNS

CoreDNS 在 Kubernetes 中履行名稱解析和服務發現功能。它默認安裝在 EKS 集群上。為了互操作性,CoreDNS 的 Kubernetes Service 仍然命名為 [kube-dns](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/)。CoreDNS Pod 作為一個 Deployment 運行在 `kube-system` 命名空間中,在 EKS 中,默認情況下它運行兩個副本,並聲明了請求和限制。DNS 查詢被發送到運行在 `kube-system` 命名空間中的 `kube-dns` Service。

## 建議

### 監控 CoreDNS 指標

CoreDNS 內置支持 [Prometheus](https://github.com/coredns/coredns/tree/master/plugin/metrics)。您應該特別考慮監控 CoreDNS 延遲(`coredns_dns_request_duration_seconds_sum`,在 [1.7.0](https://github.com/coredns/coredns/blob/master/notes/coredns-1.7.0.md) 之前的版本中,該指標被稱為 `core_dns_response_rcode_count_total`)、錯誤(`coredns_dns_responses_total`, NXDOMAIN, SERVFAIL, FormErr)和 CoreDNS Pod 的內存消耗。

為了故障排查目的,您可以使用 kubectl 查看 CoreDNS 日誌:

```shell
for p in $(kubectl get pods -n kube-system -l k8s-app=kube-dns -o jsonpath='{.items[*].metadata.name}'); do kubectl logs $p -n kube-system; done
```

### 使用 NodeLocal DNSCache

您可以通過運行 [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) 來提高集群 DNS 性能。該功能在集群節點上作為 DaemonSet 運行 DNS 緩存代理。所有 Pod 都使用運行在節點上的 DNS 緩存代理進行名稱解析,而不是使用 `kube-dns` Service。

### 為 CoreDNS 配置 cluster-proportional-scaler

提高集群 DNS 性能的另一種方法是根據集群中的節點數和 CPU 內核數自動水平擴展 CoreDNS Deployment。[Horizontal cluster-proportional-autoscaler](https://github.com/kubernetes-sigs/cluster-proportional-autoscaler/blob/master/README.md) 是一個容器,它根據可調度資料平面的大小來調整 Deployment 的副本數。

節點和節點中 CPU 內核的總和是您可以根據它們來擴展 CoreDNS 的兩個指標。您可以同時使用這兩個指標。如果您使用較大的節點,CoreDNS 的擴展將基於 CPU 內核數。而如果您使用較小的節點,CoreDNS 副本的數量將取決於資料平面中的 CPU 內核數。比例自動擴展器配置如下所示:

```
linear: '{"coresPerReplica":256,"min":1,"nodesPerReplica":16}'
```

### 為節點組選擇 AMI

EKS 為每個支持的 Kubernetes 版本在每個區域提供優化的 EC2 AMI,客戶可以使用這些 AMI 來創建自行管理和受管理的節點組。當發現任何 CVE 或 bug 時,EKS 會將這些 AMI 標記為已棄用。因此,建議在選擇節點組的 AMI 時不要使用已棄用的 AMI。

可以使用 Ec2 describe-images api 和以下命令過濾掉已棄用的 AMI:

```
aws ec2 describe-images --image-id ami-0d551c4f633e7679c --no-include-deprecated
```

您也可以通過驗證 describe-image 輸出是否包含 DeprecationTime 作為一個字段來識別已棄用的 AMI。例如:

```
aws ec2 describe-images --image-id ami-xxx --no-include-deprecated
{
    "Images": [
        {
            "Architecture": "x86_64",
            "CreationDate": "2022-07-13T15:54:06.000Z",
            "ImageId": "ami-xxx",
            "ImageLocation": "123456789012/eks_xxx",
            "ImageType": "machine",
            "Public": false,
            "OwnerId": "123456789012",
            "PlatformDetails": "Linux/UNIX",
            "UsageOperation": "RunInstances",
            "State": "available",
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "DeleteOnTermination": true,
                        "SnapshotId": "snap-0993a2fc4bbf4f7f4",
                        "VolumeSize": 20,
                        "VolumeType": "gp2",
                        "Encrypted": false
                    }
                }
            ],
            "Description": "EKS Kubernetes Worker AMI with AmazonLinux2 image, (k8s: 1.19.15, docker: 20.10.13-2.amzn2, containerd: 1.4.13-3.amzn2)",
            "EnaSupport": true,
            "Hypervisor": "xen",
            "Name": "aws_eks_optimized_xxx",
            "RootDeviceName": "/dev/xvda",
            "RootDeviceType": "ebs",
            "SriovNetSupport": "simple",
            "VirtualizationType": "hvm",
            "DeprecationTime": "2023-02-09T19:41:00.000Z"
        }
    ]
}
```