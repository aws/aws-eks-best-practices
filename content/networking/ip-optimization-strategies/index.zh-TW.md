# 優化 IP 地址利用率

由於應用程式現代化,容器化環境的規模正在迅速增長。這意味著部署了越來越多的工作節點和 Pod。

[Amazon VPC CNI](../vpc-cni/) 插件會從 VPC 的 CIDR(s) 為每個 Pod 分配一個 IP 地址。這種方法可以使用諸如 VPC Flow Logs 和其他監控解決方案等工具完全查看 Pod 地址。根據您的工作負載類型,這可能會導致大量 IP 地址被 Pod 消耗。

在設計您的 AWS 網路架構時,重要的是要在 VPC 和節點級別優化 Amazon EKS IP 消耗。這將有助於您減輕 IP 耗盡問題,並提高每個節點的 Pod 密度。

在本節中,我們將討論可以幫助您實現這些目標的技術。

## 優化節點級 IP 消耗

[前綴委派](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html)是 Amazon Virtual Private Cloud (Amazon VPC) 的一項功能,允許您將 IPv4 或 IPv6 前綴分配給您的 Amazon Elastic Compute Cloud (Amazon EC2) 實例。它增加了每個網路介面 (ENI) 的 IP 地址數量,從而提高了每個節點的 Pod 密度並提高了計算效率。自定義網路也支持前綴委派。

有關詳細資訊,請參閱 [Linux 節點的前綴委派](../prefix-mode/index_linux/)和 [Windows 節點的前綴委派](../prefix-mode/index_windows/)部分。

## 緩解 IP 耗盡

為了防止您的集群消耗所有可用的 IP 地址,我們強烈建議您在規劃 VPC 和子網時考慮未來的增長。

採用 [IPv6](../ipv6/) 是從一開始就避免這些問題的好方法。但是,對於那些可擴展性需求超出了最初規劃且無法採用 IPv6 的組織,改善 VPC 設計是應對 IP 地址耗盡的建議做法。Amazon EKS 客戶最常用的技術是向 VPC 添加不可路由的次要 CIDR,並配置 VPC CNI 在為 Pod 分配 IP 地址時使用這個額外的 IP 空間。這通常被稱為 [自定義網路](../custom-networking/)。

我們將介紹您可以使用哪些 Amazon VPC CNI 變數來優化分配給節點的熱池 IP。在本節結尾,我們將介紹一些其他架構模式,這些模式不是 Amazon EKS 的內在特性,但可以幫助緩解 IP 耗盡。

### 使用 IPv6 (推薦)

採用 IPv6 是解決 RFC1918 限制的最簡單方法;我們強烈建議您在選擇網路架構時首先考慮採用 IPv6。IPv6 提供了顯著更大的總 IP 地址空間,集群管理員可以專注於遷移和擴展應用程序,而不必花費精力來解決 IPv4 限制。

Amazon EKS 集群支持 IPv4 和 IPv6。默認情況下,EKS 集群使用 IPv4 地址空間。在集群創建時指定基於 IPv6 的地址空間將啟用 IPv6 的使用。在 IPv6 EKS 集群中,Pod 和服務將獲得 IPv6 地址,同時**保持遺留 IPv4 端點能夠連接到在 IPv6 集群上運行的服務,反之亦然**。集群內的所有 Pod 到 Pod 通信始終通過 IPv6 進行。在 VPC (/56) 內,IPv6 子網的 IPv6 CIDR 塊大小固定為 /64。這提供了大約 18 萬億 (2^64) 個 IPv6 地址,允許您在 EKS 上擴展部署。

有關詳細資訊,請參閱 [運行 IPv6 EKS 集群](../ipv6/)部分,體驗實踐請參閱 [了解 Amazon EKS 上的 IPv6](https://catalog.workshops.aws/ipv6-on-aws/en-US/lab-6) 部分的 [Get hands-on with IPv6 workshop](https://catalog.workshops.aws/ipv6-on-aws/en-US)。

![EKS 集群在 IPv6 模式下,流量流向](./ipv6.gif)

### 優化 IPv4 集群中的 IP 消耗

本節專門針對運行遺留應用程序和/或尚未準備好遷移到 IPv6 的客戶。雖然我們鼓勵所有組織盡快遷移到 IPv6,但我們也認識到,有些組織可能仍需要尋找其他方法來擴展其使用 IPv4 的容器工作負載。因此,我們還將向您介紹優化 Amazon EKS 集群中 IPv4 (RFC1918) 地址空間消耗的架構模式。

#### 為增長做規劃

作為防止 IP 耗盡的第一道防線,我們強烈建議您在規劃 IPv4 VPC 和子網時考慮未來的增長,以防止您的集群消耗所有可用的 IP 地址。如果子網沒有足夠的可用 IP 地址,您將無法創建新的 Pod 或節點。

在構建 VPC 和子網之前,建議您從所需的工作負載規模反向推導。例如,當使用 [eksctl](https://eksctl.io/) (一個用於在 EKS 上創建和管理集群的簡單 CLI 工具) 創建集群時,默認情況下會創建 /19 子網。/19 的子網掩碼對於大多數工作負載類型來說是合適的,允許分配超過 8000 個地址。

!!! attention
    在為 VPC 和子網設置大小時,除了 Pod 和節點之外,還可能有許多其他元素(如負載均衡器、RDS 數據庫和其他 VPC 內服務)會消耗 IP 地址。
此外,Amazon EKS 最多可以創建 4 個彈性網路接口 (X-ENI),這是允許與控制平面通信所需的(更多信息請參閱[這裡](../subnets/))。在集群升級期間,Amazon EKS 會創建新的 X-ENI 並在升級成功時刪除舊的 X-ENI。因此,我們建議與 EKS 集群關聯的子網至少使用 /28 (16 個 IP 地址)的子網掩碼。

您可以使用 [EKS 子網計算器範例](../subnet-calc/subnet-calc.xlsx)電子表格來規劃您的網路。該電子表格根據工作負載和 VPC ENI 配置計算 IP 使用情況。將 IP 使用情況與 IPv4 子網進行比較,以確定配置和子網大小是否足以滿足您的工作負載。請記住,如果您的 VPC 中的子網用盡了可用 IP 地址,我們建議您[使用 VPC 的原始 CIDR 塊創建新的子網](https://docs.aws.amazon.com/vpc/latest/userguide/working-with-subnets.html#create-subnets)。請注意,[Amazon EKS 現在允許修改集群子網和安全組](https://aws.amazon.com/about-aws/whats-new/2023/10/amazon-eks-modification-cluster-subnets-security/)。

#### 擴展 IP 空間

如果您即將耗盡 RFC1918 IP 空間,您可以使用 [自定義網路](../custom-networking/)模式,通過在專用的額外子網內調度 Pod 來節省可路由 IP。
雖然自定義網路將接受 VPC 範圍內的任何有效次要 CIDR 範圍,但我們建議您使用 CG-NAT 空間 (即 `100.64.0.0/10` 或 `198.19.0.0/16`) 中的 CIDR (/16),因為這些範圍不太可能在企業環境中使用,而不是 RFC1918 範圍。

有關詳細資訊,請參閱專用 [自定義網路](../custom-networking/)部分。

![自定義網路,流量流向](./custom-networking.gif)

#### 優化熱池 IP

使用默認配置時,VPC CNI 會在熱池中保留整個 ENI (及其關聯的 IP)。這可能會消耗大量 IP,尤其是在較大的實例類型上。

如果您的集群子網中可用的 IP 地址數量有限,請仔細檢查這些 VPC CNI 配置環境變數:

* `WARM_IP_TARGET`
* `MINIMUM_IP_TARGET`
* `WARM_ENI_TARGET`

您可以將 `MINIMUM_IP_TARGET` 的值配置為與您預期在節點上運行的 Pod 數量相匹配。這樣可以確保在創建 Pod 時,CNI 可以從熱池分配 IP 地址,而無需調用 EC2 API。

請注意,如果將 `WARM_IP_TARGET` 的值設置得太低,將會導致對 EC2 API 的額外調用,這可能會導致請求被節流。對於大型集群,請與 `MINIMUM_IP_TARGET` 一起使用,以避免請求被節流。

要配置這些選項,您可以下載 `aws-k8s-cni.yaml` 清單並設置環境變數。在撰寫本文時,最新版本位於[這裡](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/master/aws-k8s-cni.yaml)。請檢查配置值的版本是否與已安裝的 VPC CNI 版本匹配。

!!! Warning
    當您更新 CNI 時,這些設置將被重置為默認值。在更新之前,請備份 CNI。在更新成功後,請檢查配置設置以確定是否需要重新應用它們。

您可以在不中斷現有應用程序的情況下動態調整 CNI 參數,但您應該選擇能夠支持您的可擴展性需求的值。例如,如果您正在處理批處理工作負載,我們建議將默認的 `WARM_ENI_TARGET` 更新為與 Pod 規模需求相匹配。將 `WARM_ENI_TARGET` 設置為較高的值可以始終保持運行大型批處理工作負載所需的熱 IP 池,從而避免數據處理延遲。

!!! warning
    改善您的 VPC 設計是應對 IP 地址耗盡的建議做法。請考慮諸如 IPv6 和次要 CIDR 之類的解決方案。調整這些值以最小化熱 IP 的數量應僅作為在排除其他選項後的臨時解決方案。錯誤配置這些值可能會干擾集群操作。

    **在對生產系統進行任何更改之前**,請務必查看[此頁面](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/eni-and-ip-target.md)上的注意事項。

#### 監控 IP 地址庫存

除了上述解決方案外,還很重要能夠查看 IP 利用率。您可以使用 [CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html) 監控子網的 IP 地址庫存。一些可用的指標包括:

* 集群可以支持的最大 ENI 數量
* 已分配的 ENI 數量
* 當前分配給 Pod 的 IP 地址數量
* 可用的總 IP 地址數量和最大數量

您還可以設置 [CloudWatch 警報](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html),以在子網即將用盡 IP 地址時獲得通知。請訪問 EKS 用戶指南以獲取 [CNI 指標助手](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html)的安裝說明

!!! warning
    請確保將 VPC CNI 的 `DISABLE_METRICS` 變數設置為 false。

#### 進一步考慮

還有一些其他不是 Amazon EKS 內在的架構模式可以幫助解決 IP 耗盡問題。例如,您可以[優化跨 VPC 的通信](../subnets/#communication-across-vpcs)或[在多個帳戶之間共享 VPC](../subnets/#sharing-vpc-across-multiple-accounts),以限制 IPv4 地址分配。

在這裡了解更多有關這些模式的信息:

* [設計超大規模 Amazon VPC 網路](https://aws.amazon.com/blogs/networking-and-content-delivery/designing-hyperscale-amazon-vpc-networks/)
* [使用 Amazon VPC Lattice 構建安全的多帳戶多 VPC 連接](https://aws.amazon.com/blogs/networking-and-content-delivery/build-secure-multi-account-multi-vpc-connectivity-for-your-applications-with-amazon-vpc-lattice/)