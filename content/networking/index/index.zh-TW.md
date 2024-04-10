# Amazon EKS 網路最佳實踐指南

了解 Kubernetes 網路對於有效運作您的叢集和應用程式至關重要。Pod 網路(也稱為叢集網路)是 Kubernetes 網路的核心。Kubernetes 支援 [Container Network Interface](https://github.com/containernetworking/cni) (CNI) 插件來實作叢集網路。

Amazon EKS 正式支援 [Amazon Virtual Private Cloud (VPC)](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) CNI 插件來實作 Kubernetes Pod 網路。VPC CNI 提供與 AWS VPC 的原生整合,並以底層模式運作。在底層模式中,Pod 和主機位於相同的網路層,並共用網路命名空間。從叢集和 VPC 的觀點來看,Pod 的 IP 位址是一致的。

本指南介紹 [Amazon VPC Container Network Interface](https://github.com/aws/amazon-vpc-cni-k8s) [(VPC CNI)](https://github.com/aws/amazon-vpc-cni-k8s) 在 Kubernetes 叢集網路的背景下。VPC CNI 是 EKS 支援的預設網路插件,因此是本指南的重點。VPC CNI 可高度配置以支援不同的使用案例。本指南進一步包含專門針對不同 VPC CNI 使用案例、操作模式、子元件的章節,以及建議。

Amazon EKS 執行上游 Kubernetes,並通過 Kubernetes 一致性認證。雖然您可以使用替代 CNI 插件,但本指南不提供管理替代 CNI 的建議。請查看 [EKS 替代 CNI](https://docs.aws.amazon.com/eks/latest/userguide/alternate-cni-plugins.html) 文件,以獲取合作夥伴清單和有效管理替代 CNI 的資源。

## Kubernetes 網路模型

Kubernetes 對叢集網路設定以下要求:

* 在同一個節點上排程的 Pod 必須能夠在不使用 NAT (網路位址轉譯) 的情況下與其他 Pod 通訊。
* 在特定節點上運行的所有系統守護程序 (例如背景程序 [kubelet](https://kubernetes.io/docs/concepts/overview/components/)) 都可以與在同一節點上運行的 Pod 通訊。
* 使用 [主機網路](https://docs.docker.com/network/host/) 的 Pod 必須能夠在不使用 NAT 的情況下與所有其他節點上的所有其他 Pod 聯繫。

請參閱 [Kubernetes 網路模型](https://kubernetes.io/docs/concepts/services-networking/#the-kubernetes-network-model) 以了解 Kubernetes 對於相容網路實作的期望。下圖說明了 Pod 網路命名空間與主機網路命名空間之間的關係。

![主機網路和 2 個 Pod 網路命名空間的插圖](image.png)

## Container Networking Interface (CNI)

Kubernetes 支援 CNI 規範和插件來實作 Kubernetes 網路模型。CNI 由一個 [規範](https://github.com/containernetworking/cni/blob/main/SPEC.md) (目前版本為 1.0.0) 和用於編寫插件的程式庫組成,以配置容器中的網路介面,以及一些支援的插件。CNI 僅關注容器的網路連線,以及在刪除容器時移除已分配的資源。

通過傳遞 `--network-plugin=cni` 命令列選項來啟用 CNI 插件。kubelet 從 `--cni-conf-dir` (預設為 /etc/cni/net.d) 讀取檔案,並使用該檔案中的 CNI 配置來設定每個 Pod 的網路。CNI 配置檔案必須符合 CNI 規範 (最低版本 v0.4.0),並且配置中引用的任何所需 CNI 插件都必須存在於 `--cni-bin-dir` 目錄中 (預設為 /opt/cni/bin)。如果目錄中有多個 CNI 配置檔案,*kubelet 會使用按名稱字典順序排列的第一個配置檔案*。

## Amazon Virtual Private Cloud (VPC) CNI

AWS 提供的 VPC CNI 是 EKS 叢集的預設網路附加元件。在佈建 EKS 叢集時,會預設安裝 VPC CNI 附加元件。VPC CNI 在 Kubernetes 工作節點上執行。VPC CNI 附加元件包含 CNI 二進位檔和 IP 位址管理 (ipamd) 插件。CNI 會從 VPC 網路為 Pod 指派一個 IP 位址。ipamd 會為每個 Kubernetes 節點管理 AWS Elastic Networking Interfaces (ENIs),並維護暖池 IP。VPC CNI 提供配置選項,可預先分配 ENI 和 IP 位址,以加快 Pod 啟動時間。請參閱 [Amazon VPC CNI](../vpc-cni/index.md) 以獲取建議的插件管理最佳實踐。

Amazon EKS 建議您在建立叢集時至少指定兩個可用區域中的子網路。Amazon VPC CNI 會從節點子網路為 Pod 分配 IP 位址。我們強烈建議您檢查子網路中可用的 IP 位址。在部署 EKS 叢集之前,請考慮 [VPC 和子網路](../subnets/index.md) 建議。

Amazon VPC CNI 會從附加到節點主要 ENI 的子網路分配一個暖池 ENI 和次要 IP 位址。這種 VPC CNI 的模式稱為 "[次要 IP 模式](../vpc-cni/index.md)"。Pod 數量 (Pod 密度) 由實例類型定義的 ENI 數量和每個 ENI 的 IP 位址數量 (限制) 決定。次要模式是預設模式,適用於較小的叢集和較小的實例類型。如果您遇到 Pod 密度挑戰,請考慮使用 [前綴模式](../prefix-mode/index_linux.md)。您也可以透過為 ENI 指派前綴來增加節點上可用於 Pod 的 IP 位址。

Amazon VPC CNI 與 AWS VPC 原生整合,允許使用者將現有的 AWS VPC 網路和安全性最佳實踐應用於建置 Kubernetes 叢集。這包括能夠使用 VPC 流量日誌、VPC 路由政策和安全群組來隔離網路流量。預設情況下,Amazon VPC CNI 會將與節點主要 ENI 關聯的安全群組應用於 Pod。當您想為 Pod 指派不同的網路規則時,請考慮啟用 [Pod 的安全群組](../sgpp/index.md)。

預設情況下,VPC CNI 會從指派給節點主要 ENI 的子網路為 Pod 分配 IP 位址。在運行數千個工作負載的大型叢集時,常常會遇到 IPv4 位址不足的情況。AWS VPC 允許您透過 [指派次要 CIDR](https://docs.aws.amazon.com/vpc/latest/userguide/configure-your-vpc.html#add-cidr-block-restrictions) 來擴展可用的 IP,以解決 IPv4 CIDR 區塊耗盡的問題。AWS VPC CNI 允許您為 Pod 使用不同的子網路 CIDR 範圍。這個 VPC CNI 功能稱為 [自訂網路](../custom-networking/index.md)。您可以考慮使用自訂網路來搭配 EKS 使用 100.64.0.0/10 和 198.19.0.0/16 CIDR (CG-NAT)。這有效地允許您建立一個環境,Pod 不再消耗您 VPC 中的任何 RFC1918 IP 位址。

自訂網路是解決 IPv4 位址耗盡問題的一種選擇,但需要操作開銷。我們建議使用 IPv6 叢集而非自訂網路來解決此問題。具體而言,如果您已完全耗盡 VPC 的所有可用 IPv4 位址空間,我們建議遷移至 [IPv6 叢集](../ipv6/index.md)。請評估您組織支援 IPv6 的計劃,並考慮投資 IPv6 是否可能具有更長期的價值。

EKS 對 IPv6 的支援著重於解決由有限的 IPv4 位址空間導致的 IP 耗盡問題。為了回應客戶遇到的 IPv4 耗盡問題,EKS 優先考慮 IPv6 單堆疊 Pod 而非雙堆疊 Pod。也就是說,Pod 可能能夠存取 IPv4 資源,但不會從 VPC CIDR 範圍獲得 IPv4 位址。VPC CNI 會從 AWS 管理的 VPC IPv6 CIDR 區塊為 Pod 分配 IPv6 位址。

## 子網路計算機

本專案包含一份 [子網路計算機 Excel 文件](../subnet-calc/subnet-calc.xlsx)。此計算機文件模擬在不同的 ENI 配置選項 (例如 `WARM_IP_TARGET` 和 `WARM_ENI_TARGET`) 下,特定工作負載的 IP 位址消耗。該文件包含兩個工作表,第一個用於暖 ENI 模式,第二個用於暖 IP 模式。請查看 [VPC CNI 指南](../vpc-cni/index.md) 以獲取有關這些模式的更多資訊。

輸入:
- 子網路 CIDR 大小
- 暖 ENI 目標 *或* 暖 IP 目標
- 實例清單
    - 類型、數量,以及每個實例排程的工作負載 Pod 數量

輸出:
- 托管的總 Pod 數量
- 消耗的子網路 IP 數量
- 剩餘的子網路 IP 數量
- 實例級詳細資訊
    - 每個實例的暖 IP/ENI 數量
    - 每個實例的活動 IP/ENI 數量