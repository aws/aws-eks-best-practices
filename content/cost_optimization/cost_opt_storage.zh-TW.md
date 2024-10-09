---
日期: 2023-10-31
作者:
  - Chance Lee
---
# 成本優化 - 儲存

## 概覽

在某些情況下,您可能需要運行需要保存短期或長期數據的應用程序。對於這種用例,可以定義並為 Pod 掛載卷,以便其容器可以利用不同的儲存機制。Kubernetes 支持不同類型的 [卷](https://kubernetes.io/docs/concepts/storage/volumes/) 用於臨時和持久儲存。儲存的選擇在很大程度上取決於應用程序的要求。對於每種方法,都有成本影響,下面詳述的做法將有助於您在 EKS 環境中為需要某種形式儲存的工作負載實現成本效率。


## 臨時卷

臨時卷適用於需要臨時本地卷但不需要在重新啟動後保存數據的應用程序。這包括暫存空間、緩存和只讀輸入數據(如配置數據和密鑰)的要求。您可以在 [這裡](https://kubernetes.io/docs/concepts/storage/ephemeral-volumes/) 找到有關 Kubernetes 臨時卷的更多詳細信息。大多數臨時卷(如 emptyDir、configMap、downwardAPI、secret、hostpath)都由本地附加的可寫設備(通常是根磁盤)或 RAM 支持,因此選擇最具成本效益和性能的主機卷很重要。


### 使用 EBS 卷

*我們建議從 [gp3](https://aws.amazon.com/ebs/general-purpose/) 作為主機根卷開始。* 它是亞馬遜 EBS 提供的最新一代通用 SSD 卷,與 gp2 卷相比,每 GB 的價格也較低(最高 20%)。


### 使用 Amazon EC2 實例存儲

[Amazon EC2 實例存儲](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html)為您的 EC2 實例提供臨時塊級儲存。EC2 實例存儲提供的儲存通過物理附加到主機的磁盤來訪問。與 Amazon EBS 不同,您只能在啟動實例時附加實例存儲卷,並且這些卷只在實例生命週期內存在。它們無法分離並重新附加到其他實例。您可以在 [這裡](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html) 了解更多關於 Amazon EC2 實例存儲的信息。*使用實例存儲卷不需要支付額外費用。* 這使它們(實例存儲卷)比具有大型 EBS 卷的一般 EC2 實例 _更具成本效益_。

要在 Kubernetes 中使用本地存儲卷,您應該使用 [Amazon EC2 用戶數據](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-add-user-data.html) 對磁盤進行分區、配置和格式化,以便可以在 pod 規範中將卷掛載為 [HostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath)。或者,您可以利用 [Local Persistent Volume Static Provisioner](https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner) 來簡化本地存儲管理。Local Persistent Volume 靜態供應器允許您通過標準的 Kubernetes PersistentVolumeClaim (PVC) 界面訪問本地實例存儲卷。此外,它將提供包含節點關聯信息的 PersistentVolumes (PVs),以便將 Pod 調度到正確的節點。儘管它使用 Kubernetes PersistentVolumes,但 EC2 實例存儲卷本質上是臨時的。寫入臨時磁盤的數據僅在實例生命週期內可用。實例終止時,數據也會終止。請參考這篇 [博客](https://aws.amazon.com/blogs/containers/eks-persistent-volumes-for-instance-store/) 以獲取更多詳細信息。

請記住,使用 Amazon EC2 實例存儲卷時,總 IOPS 限制與主機共享,並且它將 Pod 綁定到特定主機。在採用 Amazon EC2 實例存儲卷之前,您應該徹底審查您的工作負載要求。


## 持久卷

Kubernetes 通常與運行無狀態應用程序相關聯。但是,在某些情況下,您可能需要運行需要在一個請求到下一個請求之間保存持久數據或信息的微服務。數據庫就是這種用例的常見示例。但是,Pod 及其中的容器或進程都是臨時的。為了在 Pod 生命週期之後保存數據,您可以使用 PV 來定義對特定位置的存儲的訪問,該位置獨立於 Pod。*與 PV 相關的成本在很大程度上取決於所使用的存儲類型以及應用程序如何消耗它。*

[這裡](https://docs.aws.amazon.com/eks/latest/userguide/storage.html) 列出了在 Amazon EKS 上支持 Kubernetes PV 的不同存儲選項。下面介紹的存儲選項包括 Amazon EBS、Amazon EFS、Amazon FSx for Lustre 和 Amazon FSx for NetApp ONTAP。


### Amazon Elastic Block Store (EBS) 卷

Amazon EBS 卷可以作為 Kubernetes PV 使用,以提供塊級存儲卷。這些非常適合依賴隨機讀寫和吞吐量密集型應用程序的數據庫,這些應用程序執行長時間連續的讀寫操作。[Amazon Elastic Block Store Container Storage Interface (CSI) 驅動程序](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html) 允許 Amazon EKS 集群管理用於持久卷的 Amazon EBS 卷的生命週期。Container Storage Interface 能夠並促進 Kubernetes 與存儲系統之間的交互。當 CSI 驅動程序部署到您的 EKS 集群時,您可以通過本機 Kubernetes 存儲資源(如 Persistent Volumes (PVs)、Persistent Volume Claims (PVCs) 和 Storage Classes (SCs))訪問其功能。這個 [鏈接](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/tree/master/examples/kubernetes) 提供了如何使用 Amazon EBS CSI 驅動程序與 Amazon EBS 卷交互的實際示例。


#### 選擇正確的卷

*我們建議使用最新一代塊存儲 (gp3),因為它在價格和性能之間提供了合適的平衡*。它還允許您獨立於卷大小擴展卷 IOPS 和吞吐量,而無需預置額外的塊存儲容量。如果您目前正在使用 gp2 卷,我們強烈建議您遷移到 gp3 卷。這篇 [博客](https://aws.amazon.com/blogs/containers/migrating-amazon-eks-clusters-from-gp2-to-gp3-ebs-volumes/) 解釋了如何在 Amazon EKS 集群上從 *gp2* 遷移到 *gp3*。

當您有需要更高性能且需要比單個 [gp3 卷](https://aws.amazon.com/ebs/general-purpose/) 更大的卷的應用程序時,您應該考慮使用 [io2 block express](https://aws.amazon.com/ebs/provisioned-iops/)。這種存儲非常適合您最大、最密集的 I/O 和關鍵任務部署,例如 SAP HANA 或其他具有低延遲要求的大型數據庫。請記住,實例的 EBS 性能受實例性能限制的約束,因此並非所有實例都支持 io2 block express 卷。您可以在此 [文檔](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/provisioned-iops.html) 中查看支持的實例類型和其他注意事項。

*單個 gp3 卷最多可支持 16,000 最大 IOPS、1,000 MiB/s 最大吞吐量、最大 16TiB。最新一代 Provisioned IOPS SSD 卷提供高達 256,000 IOPS、4,000 MiB/s 吞吐量和 64TiB。*

在這些選項中,您應該最好根據應用程序的需求來調整存儲性能和成本。


#### 監控並隨時間優化

了解您應用程序的基線性能並監控所選卷以檢查其是否滿足您的要求/期望或者是否過度配置(例如,預置的 IOPS 未被完全利用的情況)很重要。

您可以隨著數據的積累逐步增加卷的大小,而不是一開始就分配一個大卷。您可以使用 Amazon Elastic Block Store CSI 驅動程序 (aws-ebs-csi-driver) 中的 [卷調整大小](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/tree/master/examples/kubernetes/resizing) 功能動態調整卷大小。*請記住,您只能增加 EBS 卷的大小。*

要識別和刪除任何未附加的 EBS 卷,您可以使用 [AWS 可信賴顧問的成本優化類別](https://docs.aws.amazon.com/awssupport/latest/user/cost-optimization-checks.html)。此功能可幫助您識別未附加的卷或在一段時間內寫入活動非常低的卷。有一個名為 [Popeye](https://github.com/derailed/popeye) 的雲原生開源、只讀工具,它可以掃描實時 Kubernetes 集群並報告已部署資源和配置中的潛在問題。例如,它可以掃描未使用的 PV 和 PVC,並檢查它們是否已綁定或是否存在任何卷掛載錯誤。

有關監控的深入探討,請參考 [EKS 成本優化可觀察性指南](https://aws.github.io/aws-eks-best-practices/cost_optimization/cost_opt_observability/)。

您可以考慮的另一個選項是 [AWS Compute Optimizer Amazon EBS 卷建議](https://docs.aws.amazon.com/compute-optimizer/latest/ug/view-ebs-recommendations.html)。此工具可自動識別所需的最佳卷配置和正確的性能級別。例如,它可用於基於過去 14 天的最大利用率獲取 EBS 卷的最佳設置,包括預置 IOPS、卷大小和 EBS 卷類型。它還量化了其建議所產生的潛在每月成本節省。您可以查看這篇 [博客](https://aws.amazon.com/blogs/storage/cost-optimizing-amazon-ebs-volumes-using-aws-compute-optimizer/) 以獲取更多詳細信息。


#### 備份保留策略

您可以通過拍攝時間點快照來備份 Amazon EBS 卷上的數據。Amazon EBS CSI 驅動程序支持卷快照。您可以按照 [這裡](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/examples/kubernetes/snapshot/README.md) 概述的步驟學習如何創建快照和恢復 EBS PV。

後續快照是增量備份,這意味著只有自上次快照後在設備上發生更改的塊才會被保存。這最小化了創建快照所需的時間,並通過不複製數據來節省存儲成本。但是,在大規模運營時,如果沒有適當的保留策略,舊 EBS 快照的數量不斷增長會導致意外的成本。如果您直接通過 AWS API 備份 Amazon EBS 卷,您可以利用 [Amazon Data Lifecycle Manager](https://aws.amazon.com/ebs/data-lifecycle-manager/)。它提供了一個自動化、基於策略的生命週期管理解決方案,用於 Amazon Elastic Block Store (EBS) 快照和基於 EBS 的 Amazon Machine Images (AMIs)。該控制台可以更輕鬆地自動化 EBS 快照和 AMI 的創建、保留和刪除。

!!! 注意
    目前無法通過 Amazon EBS CSI 驅動程序使用 Amazon DLM。

在 Kubernetes 環境中,您可以利用一個名為 [Velero](https://velero.io/) 的開源工具來備份您的 EBS 持久卷。您可以在調度作業時設置 TTL 標誌來過期備份。這是 Velero 提供的一個 [指南](https://velero.io/docs/v1.12/how-velero-works/#set-a-backup-to-expire) 示例。


### Amazon Elastic File System (EFS)

[Amazon Elastic File System (EFS)](https://aws.amazon.com/efs/) 是一個無服務器、完全彈性的文件系統,它允許您使用標準文件系統界面和文件系統語義共享文件數據,適用於廣泛的工作負載和應用程序。工作負載和應用程序的示例包括 Wordpress 和 Drupal、開發人員工具如 JIRA 和 Git,以及共享筆記本系統如 Jupyter 以及主目錄。

Amazon EFS 的主要優勢之一是它可以被分散在多個節點和多個可用區域的多個容器掛載。另一個優勢是您只需為使用的存儲付費。EFS 文件系統將自動根據您添加和刪除文件而增長和縮小,從而消除了容量規劃的需求。

要在 Kubernetes 中使用 Amazon EFS,您需要使用 Amazon Elastic File System Container Storage Interface (CSI) 驅動程序 [aws-efs-csi-driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver)。目前,該驅動程序可以動態創建 [訪問點](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html)。但是,Amazon EFS 文件系統必須先被預置,並作為 Kubernetes 存儲類參數的輸入。


#### 選擇正確的 EFS 存儲類

Amazon EFS 提供 [四種存儲類](https://docs.aws.amazon.com/efs/latest/ug/storage-classes.html)。

兩種標準存儲類:

* Amazon EFS Standard
* [Amazon EFS Standard-Infrequent Access](https://aws.amazon.com/blogs/aws/optimize-storage-cost-with-reduced-pricing-for-amazon-efs-infrequent-access/) (EFS Standard-IA)


兩種單區域存儲類:

* [Amazon EFS One Zone](https://aws.amazon.com/blogs/aws/new-lower-cost-one-zone-storage-classes-for-amazon-elastic-file-system/)
* Amazon EFS One Zone-Infrequent Access (EFS One Zone-IA)


Infrequent Access (IA) 存儲類是針對每天不經常訪問的文件進行成本優化的。通過 Amazon EFS 生命週期管理,您可以將在生命週期策略持續時間內未被訪問的文件(7、14、30、60 或 90 天)移動到 IA 存儲類*,這可以將存儲成本分別降低高達 92% 相比 EFS Standard 和 EFS One Zone 存儲類*。

通過 EFS Intelligent-Tiering,生命週期管理可以監控您的文件系統的訪問模式,並自動將文件移動到最佳的存儲類。

!!! 注意
    aws-efs-csi-driver 目前無法控制更改存儲類、生命週期管理或 Intelligent-Tiering。這些應該在 AWS 控制台或通過 EFS API 手動設置。

!!! 注意
    aws-efs-csi-driver 與基於 Window 的容器映像不兼容。

!!! 注意
    當啟用 *vol-metrics-opt-in* (發出卷指標)時,存在已知的內存問題,這是由於 [DiskUsage](https://github.com/kubernetes/kubernetes/blob/ee265c92fec40cd69d1de010b477717e4c142492/pkg/volume/util/fs/fs.go#L66) 函數消耗的內存量與您的文件系統大小成正比。*目前,我們建議在大型文件系統上禁用 `--vol-metrics-opt-in` 選項,以避免消耗太多內存。這裡是 github 問題 [鏈接](https://github.com/kubernetes-sigs/aws-efs-csi-driver/issues/1104) 的更多詳細信息。*


### Amazon FSx for Lustre

Lustre 是一種高性能並行文件系統,通常用於需要高達數百 GB/s 的吞吐量和毫秒級別每個操作延遲的工作負載。它用於機器學習訓練、金融建模、HPC 和視頻處理等場景。[Amazon FSx for Lustre](https://aws.amazon.com/fsx/lustre/) 提供了與 Amazon S3 無縫集成的完全託管共享存儲,具有可擴展性和性能。

您可以使用由 FSx for Lustre 支持的 Kubernetes 持久存儲卷,無論是在 Amazon EKS 還是您在 AWS 上的自管理 Kubernetes 集群。有關更多詳細信息和示例,請參閱 [Amazon EKS 文檔](https://docs.aws.amazon.com/eks/latest/userguide/fsx-csi.html)。

#### 鏈接到 Amazon S3

建議將位於 Amazon S3 上的高持久性長期數據存儲庫與您的 FSx for Lustre 文件系統鏈接。一旦鏈接,大型數據集將根據需要從 Amazon S3 延遲加載到 FSx for Lustre 文件系統。您還可以將分析結果運行回 S3,然後刪除您的 [Lustre] 文件系統。


#### 選擇正確的部署和存儲選項

FSx for Lustre 提供不同的部署選項。第一個選項稱為 *scratch*,它不複製數據,而第二個選項稱為 *persistent*,顧名思義,它會持久化數據。

第一個選項(*scratch*)可用於 *減少臨時較短期數據處理的成本。* 持久部署選項 _旨在用於長期存儲_,它會自動在 AWS 可用區域內複製數據。它還支持 SSD 和 HDD 存儲。

您可以在 FSx for lustre 文件系統的 Kubernetes StorageClass 的參數中配置所需的部署類型。這裡有一個 [鏈接](https://github.com/kubernetes-sigs/aws-fsx-csi-driver/tree/master/examples/kubernetes/dynamic_provisioning#edit-storageclass) 提供了示例模板。

!!! 注意
    對於延遲敏感型工作負載或需要最高 IOPS/吞吐量的工作負載,您應該選擇 SSD 存儲。對於不太關注延遲但需要高吞吐量的工作負載,您應該選擇 HDD 存儲。


#### 啟用數據壓縮

您還可以通過將 "Data Compression Type" 指定為 "LZ4" 來為您的文件系統啟用數據壓縮。啟用後,所有新寫入的文件在寫入磁盤之前將自動在 FSx for Lustre 上壓縮,讀取時將解壓縮。LZ4 數據壓縮算法是無損的,因此可以從壓縮數據中完全重建原始數據。

您可以在 FSx for lustre 文件系統的 Kubernetes StorageClass 的參數中將數據壓縮類型配置為 LZ4。當值設置為 NONE(默認值)時,壓縮將被禁用。這個 [鏈接](https://github.com/kubernetes-sigs/aws-fsx-csi-driver/tree/master/examples/kubernetes/dynamic_provisioning#edit-storageclass) 提供了示例模板。

!!! 注意
    Amazon FSx for Lustre 與基於 Window 的容器映像不兼容。


### Amazon FSx for NetApp ONTAP

[Amazon FSx for NetApp ONTAP](https://aws.amazon.com/fsx/netapp-ontap/) 是一個完全託管的共享存儲,建立在 NetApp 的 ONTAP 文件系統之上。FSx for ONTAP 提供了功能豐富、快速和靈活的共享文件存儲,可廣泛訪問運行在 AWS 或內部部署的 Linux、Windows 和 macOS 計算實例。

Amazon FSx for NetApp ONTAP 支持兩層存儲: *1/主層* 和 *2/容量池層。*

*主層* 是一個基於 SSD 的高性能預置層,用於活躍的、延遲敏感的數據。完全彈性的 *容量池層* 針對不常訪問的數據進行了成本優化,可自動根據數據分層而擴展,並提供幾乎無限的 PB 級容量。您可以在容量池存儲上啟用數據壓縮和重複數據刪除,進一步減少數據消耗的存儲容量。NetApp 的本機基於策略的 FabricPool 功能持續監控數據訪問模式,自動在存儲層之間雙向傳輸數據,以優化性能和成本。

NetApp 的 Astra Trident 提供了動態存儲編排,使用 CSI 驅動程序允許 Amazon EKS 集群管理由 Amazon FSx for NetApp ONTAP 文件系統支持的持久卷 PV 的生命週期。要開始使用,請參閱 Astra Trident 文檔中的 [將 Astra Trident 與 Amazon FSx for NetApp ONTAP 一起使用](https://docs.netapp.com/us-en/trident/trident-use/trident-fsx.html)。


## 其他注意事項

### 最小化容器映像大小

一旦容器部署,容器映像就會作為多層緩存在主機上。通過減小映像的大小,可以減少主機上所需的存儲量。

從一開始就使用精簡的基礎映像,如 [scratch](https://hub.docker.com/_/scratch) 映像或 [distroless](https://github.com/GoogleContainerTools/distroless) 容器映像(只包含您的應用程序及其運行時依賴項),*不僅可以減少存儲成本,還可以帶來其他附帶好處,如減小攻擊面和縮短映像拉取時間。*

您還應該考慮使用開源工具,如 [Slim.ai](https://www.slim.ai/docs/quickstart),它提供了一種簡單、安全的方式來創建最小映像。

多層包、工具、應用程序依賴項和庫很容易使容器映像大小膨脹。通過使用多階段構建,您可以選擇性地從一個階段複製工件到另一個階段,從最終映像中排除所有不必要的內容。您可以在 [這裡](https://docs.docker.com/get-started/09_image_best/) 查看更多映像構建最佳實踐。

另一個需要考慮的是要持久化緩存映像的時間。當使用了一定量的磁盤空間時,您可能需要從映像緩存中清理陳舊的映像。這樣做將有助於確保主機操作有足夠的空間。默認情況下,[kubelet](https://kubernetes.io/docs/reference/generated/kubelet) 每五分鐘對未使用的映像進行一次垃圾收集,每分鐘對未使用的容器進行一次垃圾收集。

*要配置未使用的容器和映像垃圾收集的選項,請使用 [配置文件](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/) 調整 kubelet,並使用 [`KubeletConfiguration`](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/) 資源類型更改與垃圾收集相關的參數。*

您可以在 Kubernetes [文檔](https://kubernetes.io/docs/concepts/architecture/garbage-collection/#containers-images)中了解更多相關信息。
