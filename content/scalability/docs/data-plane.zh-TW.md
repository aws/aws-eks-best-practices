# Kubernetes 資料平面

Kubernetes 資料平面包括 EC2 實例、負載平衡器、儲存空間和其他由 Kubernetes 控制平面使用的 API。為了組織目的，我們將 [叢集服務](./cluster-services.md) 分組在單獨的頁面中，而負載平衡器擴展能力可在 [工作負載部分](./workloads.md) 中找到。本節將重點放在擴展計算資源上。

選擇 EC2 實例類型可能是客戶面臨的最困難決策之一，因為在具有多個工作負載的叢集中，沒有一種適合所有情況的解決方案。以下是一些提示，可幫助您避免在擴展計算時遇到常見的陷阱。

## 自動節點自動擴展

我們建議您使用可減少工作量並與 Kubernetes 深度整合的節點自動擴展功能。[受管理節點群組](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 和 [Karpenter](https://karpenter.sh/) 適用於大規模叢集。

受管理節點群組將為您提供 Amazon EC2 Auto Scaling 群組的靈活性，並增加了受管理升級和配置的優點。它可以與 [Kubernetes 叢集自動擴展器](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) 一起擴展，是具有各種計算需求的叢集的常見選擇。

Karpenter 是由 AWS 創建的開源、工作負載本地節點自動擴展器。它根據工作負載對資源 (例如 GPU) 和污點和容忍度 (例如區域分佈) 的要求來擴展叢集中的節點，而無需管理節點群組。節點是直接從 EC2 創建的，這避免了預設節點群組配額 (每個群組 450 個節點) 並提供了更大的實例選擇靈活性和較少的操作開銷。我們建議客戶盡可能使用 Karpenter。

## 使用多種不同的 EC2 實例類型

每個 AWS 區域都有每種實例類型的可用實例數量有限。如果您創建了僅使用一種實例類型的叢集，並將節點數量擴展超過該區域的容量，您將收到沒有可用實例的錯誤。為了避免這種情況，您不應任意限制叢集中可以使用的實例類型。

Karpenter 預設會使用廣泛的相容實例類型，並將根據待處理工作負載的要求、可用性和成本在佈建時挑選實例。您可以透過 [NodePools](https://karpenter.sh/docs/concepts/nodepools/#instance-types) 中的 `karpenter.k8s.aws/instance-category` 鍵來擴大所使用的實例類型列表。

Kubernetes 叢集自動擴展器要求節點群組的大小相似，以便可以一致地進行擴展。您應根據 CPU 和記憶體大小創建多個群組，並獨立擴展它們。使用 [ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector) 來識別適合您的節點群組的相似大小實例。

```
ec2-instance-selector --service eks --vcpus-min 8 --memory-min 16
a1.2xlarge
a1.4xlarge
a1.metal
c4.4xlarge
c4.8xlarge
c5.12xlarge
c5.18xlarge
c5.24xlarge
c5.2xlarge
c5.4xlarge
c5.9xlarge
c5.metal
```

## 偏好較大的節點以減少 API 伺服器負載

在決定要使用哪些實例類型時，較少的大型節點將對 Kubernetes 控制平面的負載較小，因為運行的 kubelet 和 DaemonSet 較少。但是，大型節點可能無法像較小的節點那樣充分利用。節點大小應根據您的工作負載可用性和擴展需求進行評估。

具有三個 u-24tb1.metal 實例 (24 TB 記憶體和 448 核心) 的叢集有 3 個 kubelet，並且預設情況下每個節點最多可運行 110 個 Pod。如果您的 Pod 每個使用 4 個核心，那麼這可能是預期的 (4 核心 x 110 = 每個節點 440 核心)。對於 3 節點叢集，如果發生一個實例故障，您處理實例事故的能力會很低，因為 1/3 的叢集可能會受到影響。您應在工作負載中指定節點要求和 Pod 分佈，以便 Kubernetes 調度程序可以正確地放置工作負載。

工作負載應定義它們所需的資源和通過污點、容忍度和 [PodTopologySpread](https://kubernetes.io/blog/2020/05/introducing-podtopologyspread/) 所需的可用性。它們應偏好可充分利用並滿足可用性目標的最大節點，以減少控制平面負載、降低操作成本並節省成本。

如果有可用資源，Kubernetes 調度程序將自動嘗試跨可用區域和主機分佈工作負載。如果沒有可用容量，Kubernetes 叢集自動擴展器將嘗試在每個可用區域中平均添加節點。Karpenter 將嘗試盡可能快速且便宜地添加節點，除非工作負載指定了其他要求。

要強制工作負載使用調度程序分佈並在可用區域中創建新節點，您應使用 topologySpreadConstraints:

```
spec:
  topologySpreadConstraints:
    - maxSkew: 3
      topologyKey: "topology.kubernetes.io/zone"
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          dev: my-deployment
    - maxSkew: 2
      topologyKey: "kubernetes.io/hostname"
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          dev: my-deployment
```

## 使用相似大小的節點以獲得一致的工作負載性能

工作負載應定義它們需要在哪種大小的節點上運行，以允許一致的性能和可預測的擴展。請求 500m CPU 的工作負載在具有 4 核心的實例上與在具有 16 核心的實例上的性能會有所不同。避免使用 T 系列等可突發 CPU 的實例類型。

為了確保您的工作負載獲得一致的性能，工作負載可以使用 [支持的 Karpenter 標籤](https://karpenter.sh/docs/concepts/scheduling/#labels) 來鎖定特定的實例大小。

```
kind: deployment
...
spec:
  template:
    spec:
    containers:
    nodeSelector:
      karpenter.k8s.aws/instance-size: 8xlarge
```

在使用 Kubernetes 叢集自動擴展器的叢集中調度工作負載時，應將節點選擇器與基於標籤匹配的節點群組相匹配。

```
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: eks.amazonaws.com/nodegroup
            operator: In
            values:
            - 8-core-node-group    # 匹配您的節點群組名稱
```

## 有效使用計算資源

計算資源包括 EC2 實例和可用區域。有效使用計算資源將提高可擴展性、可用性、性能，並降低總體成本。在具有多個應用程序的自動擴展環境中，很難預測有效資源使用情況。[Karpenter](https://karpenter.sh/) 是根據工作負載需求按需佈建實例以最大化利用率和靈活性而創建的。

Karpenter 允許工作負載聲明它需要哪種類型的計算資源，而無需先創建節點群組或為特定節點配置標籤污點。有關更多信息，請參閱 [Karpenter 最佳實踐](https://aws.github.io/aws-eks-best-practices/karpenter/)。考慮在您的 Karpenter 佈建器中啟用 [consolidation](https://aws.github.io/aws-eks-best-practices/karpenter/#configure-requestslimits-for-all-non-cpu-resources-when-using-consolidation)，以替換利用率低下的節點。

## 自動更新 Amazon Machine Image (AMI)

保持工作節點組件的最新狀態將確保您擁有最新的安全補丁和與 Kubernetes API 兼容的功能。更新 kubelet 是 Kubernetes 功能最重要的組件，但自動化操作系統、內核和本地安裝的應用程序補丁將在擴展時減少維護。

建議您對節點映像使用最新的 [Amazon EKS 優化的 Amazon Linux 2](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) 或 [Amazon EKS 優化的 Bottlerocket AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami-bottlerocket.html)。Karpenter 將自動使用 [最新可用的 AMI](https://karpenter.sh/docs/concepts/nodepools/#instance-types) 在叢集中佈建新節點。受管理節點群組將在 [節點群組更新](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html) 期間更新 AMI，但不會在節點佈建時更新 AMI ID。

對於受管理節點群組，當新的 AMI 可用時，您需要使用新的 AMI ID 更新 Auto Scaling 群組 (ASG) 啟動模板。AMI 次要版本 (例如從 1.23.5 到 1.24.3) 將在 EKS 控制台和 API 中作為 [節點群組的升級](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html) 提供。補丁版本 (例如從 1.23.5 到 1.23.6) 將不會作為節點群組的升級提供。如果您希望保持節點群組與 AMI 補丁版本的最新狀態，您需要創建新的啟動模板版本，並讓節點群組使用新的 AMI 版本替換實例。

您可以從 [此頁面](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) 或使用 AWS CLI 找到最新可用的 AMI。

```
aws ssm get-parameter \
  --name /aws/service/eks/optimized-ami/1.24/amazon-linux-2/recommended/image_id \
  --query "Parameter.Value" \
  --output text
```
## 為容器使用多個 EBS 卷

EBS 卷根據卷的類型 (例如 gp3) 和磁盤大小具有輸入/輸出 (I/O) 配額。如果您的應用程序與主機共用單個 EBS 根卷，則可能會耗盡整個主機的磁盤配額，從而導致其他應用程序等待可用容量。如果應用程序將文件寫入其覆蓋分區、從主機掛載本地卷以及在它們記錄到標準輸出 (STDOUT) 時 (取決於所使用的記錄代理程序)，它們就會寫入磁盤。

為了避免磁盤 I/O 耗盡，您應為容器狀態資料夾 (例如 /run/containerd) 掛載第二個卷、為工作負載儲存使用單獨的 EBS 卷，並禁用不必要的本地記錄。

要使用 [eksctl](https://eksctl.io/) 為您的 EC2 實例掛載第二個卷，您可以使用具有以下配置的節點群組:

```
managedNodeGroups:
  - name: al2-workers
    amiFamily: AmazonLinux2
    desiredCapacity: 2
    volumeSize: 80
    additionalVolumes:
      - volumeName: '/dev/sdz'
        volumeSize: 100
    preBootstrapCommands:
    - |
      "systemctl stop containerd"
      "mkfs -t ext4 /dev/nvme1n1"
      "rm -rf /var/lib/containerd/*"
      "mount /dev/nvme1n1 /var/lib/containerd/"
      "systemctl start containerd"
```

如果您使用 terraform 來佈建節點群組，請參閱 [EKS Blueprints for terraform](https://aws-ia.github.io/terraform-aws-eks-blueprints/patterns/stateful/#eks-managed-nodegroup-w-multiple-volumes) 中的示例。如果您使用 Karpenter 來佈建節點，您可以使用 [`blockDeviceMappings`](https://karpenter.sh/docs/concepts/nodeclasses/#specblockdevicemappings) 和節點用戶數據來添加額外的卷。

要直接將 EBS 卷掛載到您的 Pod，您應使用 [AWS EBS CSI 驅動程序](https://github.com/kubernetes-sigs/aws-ebs-csi-driver) 並使用儲存類別消耗卷。

```
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 4Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: public.ecr.aws/docker/library/nginx
    volumeMounts:
    - name: persistent-storage
      mountPath: /data
  volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: ebs-claim
```

## 如果工作負載使用 EBS 卷，請避免使用 EBS 附加限制低的實例

EBS 是工作負載獲得持久存儲的最簡單方式之一，但它也有可擴展性限制。每種實例類型都有可附加的 [EBS 卷的最大數量](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html)。工作負載需要聲明它們應該在哪些實例類型上運行，並使用 Kubernetes 污點限制單個實例上的副本數量。

## 禁用不必要的磁盤記錄

避免不必要的本地記錄，在生產環境中不要運行應用程序的調試記錄，並禁用頻繁讀寫磁盤的記錄。Journald 是本地記錄服務，它在記憶體中保留日誌緩衝區並定期刷新到磁盤。Journald 優於 syslog，後者會立即將每一行記錄到磁盤。禁用 syslog 還可降低您需要的總存儲量，並避免需要複雜的日誌輪換規則。要禁用 syslog，您可以將以下片段添加到您的 cloud-init 配置中:

```
runcmd:
  - [ systemctl, disable, --now, syslog.service ]
```

## 當需要操作系統更新速度時就地修補實例

!!! 注意
    只有在必要時才應就地修補實例。Amazon 建議將基礎設施視為不可變的，並徹底測試以與應用程序相同的方式通過較低環境升級的更新。本節適用於無法執行此操作的情況。

在現有 Linux 主機上安裝軟件包只需幾秒鐘，而不會中斷容器化工作負載。可以安裝並驗證軟件包而無需排空、清空或替換實例。

要替換實例，您首先需要創建、驗證和分發新的 AMI。需要為實例創建替換實例，並排空和清空舊實例。然後需要在新實例上創建工作負載、驗證並重複所有需要修補的實例。在不中斷工作負載的情況下安全地替換實例需要數小時、數天或數週。

Amazon 建議使用可從自動化、聲明式系統構建、測試和升級的不可變基礎設施，但如果您需要快速修補系統，則需要就地修補系統並在新的 AMI 可用時替換它們。由於修補系統和替換系統之間的時間差異很大，我們建議在需要時使用 [AWS Systems Manager Patch Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-patch.html) 來自動修補節點。

修補節點將允許您快速推出安全更新，並在您的 AMI 更新後定期替換實例。如果您使用具有只讀根文件系統的操作系統 (如 [Flatcar Container Linux](https://flatcar-linux.org/) 或 [Bottlerocket OS](https://github.com/bottlerocket-os/bottlerocket))，我們建議使用與這些操作系統配合使用的更新操作員。[Flatcar Linux 更新操作員](https://github.com/flatcar/flatcar-linux-update-operator) 和 [Bottlerocket 更新操作員](https://github.com/bottlerocket-os/bottlerocket-update-operator) 將自動重新啟動實例以保持節點的最新狀態。