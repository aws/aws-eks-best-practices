# VPC 和子網路考量

操作 EKS 叢集除了需要了解 Kubernetes 網路之外，還需要了解 AWS VPC 網路。

我們建議您在開始設計 VPC 或將叢集部署到現有 VPC 之前，先了解 EKS 控制平面通訊機制。

在架構 VPC 和要與 EKS 一起使用的子網路時，請參閱 [叢集 VPC 考量](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html) 和 [Amazon EKS 安全群組考量](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)。

## 概觀

### EKS 叢集架構

EKS 叢集由兩個 VPC 組成：

* 由 AWS 管理的 VPC，用於託管 Kubernetes 控制平面。此 VPC 不會出現在客戶帳戶中。
* 由客戶管理的 VPC，用於託管 Kubernetes 節點。容器會在這裡運行，以及其他由客戶管理的 AWS 基礎架構，例如叢集使用的負載平衡器。此 VPC 會出現在客戶帳戶中。您需要在建立叢集之前先建立客戶管理的 VPC。如果您沒有提供 VPC，eksctl 會建立一個。

客戶 VPC 中的節點需要能夠連接到 AWS VPC 中的受管理 API 伺服器端點。這允許節點向 Kubernetes 控制平面註冊並接收執行應用程式 Pod 的請求。

節點通過 (a) EKS 公用端點或 (b) 由 EKS 管理的跨帳戶 [彈性網路介面](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html) (X-ENI) 連接到 EKS 控制平面。在建立叢集時，您需要指定至少兩個 VPC 子網路。EKS 會在指定的每個子網路中放置一個跨帳戶 ENI (也稱為叢集子網路)。Kubernetes API 伺服器使用這些跨帳戶 ENI 與部署在客戶管理的叢集 VPC 子網路上的節點通訊。

![一般叢集網路插圖，包括負載平衡器、節點和 Pod。](./image.png)

當節點啟動時，會執行 EKS 啟動腳本並安裝 Kubernetes 節點配置檔案。作為啟動過程的一部分，容器執行時間代理程式、kubelet 和 Kubernetes 節點代理程式會啟動。

要註冊節點，Kubelet 會聯繫 Kubernetes 叢集端點。它會透過公用端點 (在 VPC 外部) 或私有端點 (在 VPC 內部) 建立連線。Kubelet 會定期接收 API 指令並提供狀態更新和心跳訊號給端點。

### EKS 控制平面通訊

EKS 有兩種方式控制對 [叢集端點](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html) 的存取。端點存取控制讓您可以選擇端點是否可以從公開網際網路或僅透過您的 VPC 存取。您可以開啟公用端點 (預設值)、私有端點或同時開啟兩者 (公用和私有)。

叢集 API 端點的配置決定了節點與控制平面通訊的路徑。請注意,這些端點設定可以隨時透過 EKS 主控台或 API 進行變更。

#### 公用端點

這是新建立的 Amazon EKS 叢集的預設行為。當只啟用叢集的公用端點時,源自您叢集 VPC 內部 (例如工作節點到控制平面的通訊) 的 Kubernetes API 請求會離開 VPC,但不會離開 Amazon 的網路。為了讓節點能夠連接到控制平面,它們必須具有公用 IP 位址,並且有通往網際網路閘道或 NAT 閘道的路由,以便它們可以使用 NAT 閘道的公用 IP 位址。

#### 公用和私有端點

當同時啟用公用和私有端點時,來自 VPC 內部的 Kubernetes API 請求會透過您 VPC 內的 X-ENI 與控制平面通訊。您的叢集 API 伺服器可從網際網路存取。

#### 私有端點

當只啟用私有端點時,您的 API 伺服器將無法從網際網路公開存取。所有傳送到您叢集 API 伺服器的流量必須來自您叢集的 VPC 或連線的網路。節點會透過您 VPC 內的 X-ENI 與 API 伺服器通訊。請注意,叢集管理工具必須能夠存取私有端點。瞭解 [如何從 Amazon VPC 外部連線到私有 Amazon EKS 叢集端點](https://aws.amazon.com/premiumsupport/knowledge-center/eks-private-cluster-endpoint-vpc/)。

請注意,叢集的 API 伺服器端點會由公用 DNS 伺服器解析為來自 VPC 的私有 IP 位址。過去,只能從 VPC 內部解析端點。

### VPC 配置

Amazon VPC 支援 IPv4 和 IPv6 位址。Amazon EKS 預設支援 IPv4。VPC 必須與之關聯 IPv4 CIDR 區塊。您也可以選擇將多個 IPv4 [無類別域間路由](http://en.wikipedia.org/wiki/CIDR_notation) (CIDR) 區塊和多個 IPv6 CIDR 區塊關聯到您的 VPC。當您建立 VPC 時,必須從 [RFC 1918](http://www.faqs.org/rfcs/rfc1918.html) 中指定的私有 IPv4 位址範圍,為 VPC 指定 IPv4 CIDR 區塊。允許的區塊大小介於 /16 前綴 (65,536 個 IP 位址) 和 /28 前綴 (16 個 IP 位址) 之間。

建立新的 VPC 時,您可以附加單一 IPv6 CIDR 區塊,變更現有 VPC 時最多可附加五個。IPv6 CIDR 區塊大小的前綴長度可以介於 /44 和 /60 之間,而 IPv6 子網路可以介於 /44 和 /64 之間。您可以從 Amazon 維護的 IPv6 位址集區中申請 IPv6 CIDR 區塊。如需更多資訊,請參閱 VPC 使用者指南中的 [VPC CIDR 區塊](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html) 一節。

Amazon EKS 叢集支援 IPv4 和 IPv6。預設情況下,EKS 叢集使用 IPv4 IP。在建立叢集時指定 IPv6 將啟用使用 IPv6 叢集。IPv6 叢集需要雙堆疊 VPC 和子網路。

在建立叢集時,Amazon EKS 建議您至少使用兩個位於不同可用區域的子網路。在叢集建立期間傳遞的子網路稱為叢集子網路。當您建立叢集時,Amazon EKS 會在您指定的子網路中建立多達 4 個跨帳戶 (x-account 或 x-ENI) ENI。x-ENI 始終會部署並用於叢集管理流量,例如日誌傳遞、exec 和 proxy。請參閱 EKS 使用者指南,瞭解完整的 [VPC 和子網路需求](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html#network-requirements-subnets) 詳細資訊。

Kubernetes 工作節點可以在叢集子網路中運行,但不建議這樣做。在 [叢集升級](https://aws.github.io/aws-eks-best-practices/upgrades/#verify-available-ip-addresses) 期間,Amazon EKS 會在叢集子網路中佈建額外的 ENI。當您的叢集擴展時,工作節點和 Pod 可能會耗盡叢集子網路中的可用 IP。因此,為了確保有足夠的可用 IP,您可能需要考慮使用具有 /28 網路遮罩的專用叢集子網路。

Kubernetes 工作節點可以在公用或私有子網路中運行。子網路是公用還是私有,是指該子網路中的流量是否通過 [網際網路閘道](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html) 路由。公用子網路的路由表中有一個條目,可通過網際網路閘道連接到網際網路,但私有子網路則沒有。

源自其他地方並到達您節點的流量稱為 *入站*。源自節點並離開網路的流量稱為 *出站*。在配置了網際網路閘道的子網路中具有公用或彈性 IP 位址 (EIP) 的節點允許來自 VPC 外部的入站流量。私有子網路通常包括 [NAT 閘道](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html),它只允許來自 VPC 內部的入站流量到達節點,同時仍允許來自節點的流量離開 VPC (*出站*)。

在 IPv6 世界中,每個位址都是可路由的網際網路位址。與節點和 Pod 關聯的 IPv6 位址是公用的。通過在 VPC 中實現 [僅出站網際網路閘道 (EIGW)](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html) 來支援私有子網路,允許出站流量但阻止所有入站流量。實現 IPv6 子網路的最佳做法可在 [VPC 使用者指南](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Scenario2.html) 中找到。

### 您可以通過三種不同的方式配置 VPC 和子網路:

#### 僅使用公用子網路

節點和入站資源 (如負載平衡器) 都會在同一個公用子網路中建立。為公用子網路加上標籤 [`kubernetes.io/role/elb`](http://kubernetes.io/role/elb) 以建構面向網際網路的負載平衡器。在此配置中,叢集端點可以配置為公用、私有或兩者 (公用和私有)。

#### 使用私有和公用子網路

節點會在私有子網路上建立,而入站資源則會在公用子網路上實例化。您可以啟用公用、私有或兩者 (公用和私有) 存取叢集端點。根據叢集端點的配置,節點流量將通過 NAT 閘道或 ENI 進入。

#### 僅使用私有子網路

節點和入站資源都會在私有子網路中建立。使用 [`kubernetes.io/role/internal-elb`](http://kubernetes.io/role/internal-elb:1) 子網路標籤來建構內部負載平衡器。存取您的叢集端點將需要 VPN 連線。您必須啟用 [AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/userguide/endpoint-service.html) for EC2 和所有 Amazon ECR 和 S3 儲存庫。只應啟用叢集的私有端點。我們建議您在佈建私有叢集之前先查看 [EKS 私有叢集需求](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html)。

### 跨 VPC 通訊

有許多情況需要多個 VPC 和在這些 VPC 中部署的獨立 EKS 叢集。

您可以使用 [Amazon VPC Lattice](https://aws.amazon.com/vpc/lattice/) 在多個 VPC 和帳戶之間一致且安全地連接服務 (無需由服務如 VPC 對等、AWS PrivateLink 或 AWS Transit Gateway 提供額外連線)。在 [這裡](https://aws.amazon.com/blogs/networking-and-content-delivery/build-secure-multi-account-multi-vpc-connectivity-for-your-applications-with-amazon-vpc-lattice/) 瞭解更多資訊。

![Amazon VPC Lattice, 流量流向](./vpc-lattice.gif)

Amazon VPC Lattice 在 IPv4 和 IPv6 的鏈路本地位址空間中運作,為可能具有重疊 IPv4 位址的服務提供連線。為了提高操作效率,我們強烈建議將 EKS 叢集和節點部署到不重疊的 IP 範圍。如果您的基礎架構包含具有重疊 IP 範圍的 VPC,您需要相應地設計您的網路。我們建議使用 [私有 NAT 閘道](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html#nat-gateway-basics) 或在 [自訂網路](../custom-networking/index.md) 模式下使用 VPC CNI,並結合 [傳輸閘道](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/aws-transit-gateway.html) 來整合 EKS 上的工作負載,以解決重疊 CIDR 的挑戰同時保留可路由的 RFC1918 IP 位址。

![私有 Nat 閘道與自訂網路, 流量流向](./private-nat-gw.gif)

如果您是服務提供者並希望與不同帳戶中的客戶 VPC 共享您的 Kubernetes 服務和入站 (ALB 或 NLB),請考慮使用 [AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html),也稱為端點服務。

### 跨多個帳戶共享 VPC

許多企業採用共享 Amazon VPC 作為簡化網路管理、降低成本並在 AWS 組織中的多個 AWS 帳戶之間改善安全性的一種方式。他們利用 AWS Resource Access Manager (RAM) 安全地與個別 AWS 帳戶、組織單位 (OU) 或整個 AWS 組織共享支援的 [AWS 資源](https://docs.aws.amazon.com/ram/latest/userguide/shareable.html)。

您可以使用 AWS RAM 在來自另一個 AWS 帳戶的共享 VPC 子網路中部署 Amazon EKS 叢集、受管理節點群組和其他支援 AWS 資源 (如負載平衡器、安全群組、端點等)。下圖顯示了一個示例高級架構。這允許中央網路團隊控制網路構造,如 VPC、子網路等,同時允許應用程式或平台團隊在各自的 AWS 帳戶中部署 Amazon EKS 叢集。此情況的完整逐步解說可在 [此 github 儲存庫](https://github.com/aws-samples/eks-shared-subnets) 中找到。

![在跨 AWS 帳戶的 VPC 共享子網路中部署 Amazon EKS。](./eks-shared-subnets.png)

#### 使用共享子網路時的考量事項

* Amazon EKS 叢集和工作節點可以在屬於同一 VPC 的共享子網路中建立。Amazon EKS 不支援跨多個 VPC 建立叢集。

* Amazon EKS 使用 AWS VPC 安全群組 (SG) 來控制 Kubernetes 控制平面與叢集工作節點之間的流量。安全群組也用於控制工作節點與其他 VPC 資源和外部 IP 位址之間的流量。您必須在應用程式/參與者帳戶中建立這些安全群組。請確保您打算用於 Pod 的安全群組也位於參與者帳戶中。您可以在安全群組中配置入站和出站規則,以允許與位於中央 VPC 帳戶的安全群組之間的必要流量。

* 在您的 Amazon EKS 叢集所在的參與者帳戶中建立 IAM 角色和相關聯的政策。這些 IAM 角色和政策對於授予 Amazon EKS 管理的 Kubernetes 叢集以及在 Fargate 上運行的節點和 Pod 所需的必要許可權至關重要。這些許可權使 Amazon EKS 能夠代表您呼叫其他 AWS 服務。

* 您可以遵循以下方法,允許來自 k8s Pod 的跨帳戶存取 AWS 資源 (如 Amazon S3 Bucket、Dynamodb 表等):
    * **資源型政策方法**:如果 AWS 服務支援資源政策,您可以新增適當的資源型政策,允許跨帳戶存取指派給 kubernetes Pod 的 IAM 角色。在此情況下,OIDC 提供者、IAM 角色和許可權政策存在於應用程式帳戶中。要找出支援資源型政策的 AWS 服務,請參閱 [與 IAM 搭配使用的 AWS 服務](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-services-that-work-with-iam.html),並查看 Resource Based 一欄中顯示 Yes 的服務。

    * **OIDC 提供者方法**:IAM 資源 (如 OIDC 提供者、IAM 角色、許可權和信任政策) 將在存在資源的其他參與者 AWS 帳戶中建立。這些角色將被指派給應用程式帳戶中的 Kubernetes Pod,以便它們可以存取跨帳戶資源。請參閱 [Kubernetes 服務帳戶的跨帳戶 IAM 角色](https://aws.amazon.com/blogs/containers/cross-account-iam-roles-for-kubernetes-service-accounts/) 部落格,瞭解此方法的完整逐步解說。

* 您可以在應用程式或中央網路帳戶中部署 Amazon Elastic Loadbalancer (ELB) 資源 (ALB 或 NLB),以路由流量到 k8s Pod。請參閱 [透過跨帳戶負載平衡器公開 Amazon EKS Pod](https://aws.amazon.com/blogs/containers/expose-amazon-eks-pods-through-cross-account-load-balancer/) 逐步解說,瞭解在中央網路帳戶中部署 ELB 資源的詳細說明。此選項提供了更大的靈活性,因為它授予中央網路帳戶對負載平衡器資源的安全性配置完全控制權。

* 使用 Amazon VPC CNI 的 `自訂網路功能` 時,您需要使用中央網路帳戶中列出的可用區域 (AZ) ID 對應來建立每個 `ENIConfig`。這是因為每個 AWS 帳戶中實體 AZ 與 AZ 名稱的對應是隨機的。

### 安全群組

[*安全群組*](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html) 控制允許到達和離開與之關聯的資源的流量。Amazon EKS 使用安全群組來管理 [控制平面和節點](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html) 之間的通訊。當您建立叢集時,Amazon EKS 會建立一個名為 `eks-cluster-sg-my-cluster-uniqueID` 的安全群組。EKS 將這些安全群組與受管理的 ENI 和節點關聯。預設規則允許您的叢集和節點之間的所有流量自由流動,並允許所有出站流量到達任何目的地。

當您建立叢集時,您可以指定自己的安全群組。在指定自己的安全群組時,請參閱 [安全群組建議](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)。

## 建議

### 考慮多可用區域部署

AWS 區域提供多個物理上分離和隔離的可用區域 (AZ),這些可用區域通過低延遲、高吞吐量和高度冗餘的網路相互連接。通過可用區域,您可以設計和操作在可用區域之間自動故障轉移而不中斷的應用程式。Amazon EKS 強烈建議將 EKS 叢集部署到多個可用區域。在建立叢集時,請考慮至少指定兩個可用區域的子網路。

運行在節點上的 Kubelet 會自動將標籤 (如 [`topology.kubernetes.io/region=us-west-2` 和 `topology.kubernetes.io/zone=us-west-2d`](http://topology.kubernetes.io/region=us-west-2,topology.kubernetes.io/zone=us-west-2d)) 添加到節點對象。我們建議結合使用節點標籤和 [Pod 拓撲分佈約束](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) 來控制 Pod 在區域之間的分佈方式。這些提示使 Kubernetes [調度器](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler/) 能夠更好地放置 Pod,以獲得預期的可用性,降低相關故障影響整個工作負載的風險。請參閱 [將節點分配給 Pod](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector),了解節點選擇器和 AZ 分佈約束的示例。

您可以在建立節點時定義子網路或可用區域。如果未配置子網路,節點將放置在叢集子網路中。EKS 對受管理節點群組的支援會自動將節點跨多個可用區域分佈在可用容量上。[Karpenter](https://karpenter.sh/) 將根據工作負載定義的拓撲分佈限制,在指定的 AZ 中相應地擴展節點。

AWS Elastic Load Balancers 由 Kubernetes 叢集的 AWS Load Balancer Controller 管理。它為 Kubernetes 入站資源佈建應用程式負載平衡器 (ALB),為 Kubernetes 類型為 Loadbalancer 的服務佈建網路負載平衡器 (NLB)。Elastic Load Balancer 控制器使用 [標籤](https://aws.amazon.com/premiumsupport/knowledge-center/eks-vpc-subnet-discovery/) 來發現子網路。ELB 控制器需要至少兩個可用區域 (AZ) 才能成功佈建入站資源。請考慮在至少兩個 AZ 中設置子網路,以利用地理冗餘帶來的安全性和可靠性。

### 將節點部署到私有子網路

包含私有和公用子網路的 VPC 是在 EKS 上部署 Kubernetes 工作負載的理想方式。請考慮在兩個不同的可用區域中設置至少兩個公用子網路和兩個私有子網路。公用子網路的相關路由表包含到網際網路閘道的路由。Pod 可以透過 NAT 閘道與網際網路互動。在 IPv6 環境中,私有子網路由 [僅出站網際網路閘道](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html) (EIGW) 支援。

在私有子網路中實例化節點可提供對流量到節點的最大控制,並適用於大多數 Kubernetes 應用程式。入站資源 (如負載平衡器) 會在公用子網路中實例化,並將流量路由到在私有子網路上運行的 Pod。

如果您需要嚴格的安全性和網路隔離,請考慮僅使用私有模式。在此配置中,三個私有子網路會在 AWS 區域的 VPC 中的不同可用區域中部署。部署到子網路的資源無法存取網際網路,網際網路也無法存取子網路中的資源。為了讓您的 Kubernetes 應用程式能夠存取其他 AWS 服務,您必須配置 PrivateLink 介面和/或閘道端點。您可以使用 AWS Load Balancer Controller 設置內部負載平衡器,將流量重新導向到 Pod。私有子網路必須標記為 ([`kubernetes.io/role/internal-elb: 1`](http://kubernetes.io/role/internal-elb)),以便控制器佈建負載平衡器。為了讓節點能夠向叢集註冊,叢集端點必須設置為私有模式。請訪問 [私有叢集指南](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html),瞭解完整的需求和考量事項。

### 考慮為叢集端點設置公用和私有模式

Amazon EKS 提供公用模式、公用和私有模式以及僅私有模式的叢集端點。預設模式是公用模式,但我們建議將叢集端點配置為公用和私有模式。此選項允許來自您叢集 VPC 內部 (例如節點到控制平面的通訊) 的 Kubernetes API 呼叫使用私有 VPC 端點,並且流量保留在您叢集的 VPC 內部。但是,您的叢集 API 伺服器可以從網際網路存取。不過,我們強烈建議限制可以使用公用端點的 CIDR 區塊。[瞭解如何配置公用和私有端點存取,包括限制 CIDR 區塊。](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html#modify-endpoint-access)

當您需要安全性和網路隔離時,我們建議使用僅私有端點。我們建議使用 [EKS 使用者指南](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html#private-access) 中列出的任一選項私下連線到 API 伺服器。

### 謹慎配置安全群組

Amazon EKS 支援使用自訂安全群組。任何自訂安全群組都必須允許節點與 Kubernetes 控制平面之間的通訊。如果您的組織不允許開放通訊,請檢查 [端口需求](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html) 並手動配置規則。

EKS 會將您在建立叢集期間提供的自訂安全群組應用於受管理的介面 (X-ENI)。但它不會立即將它們與節點關聯。在建立節點群組時,強烈建議手動 [關聯自訂安全群組](https://eksctl.io/usage/schema/#nodeGroups-securityGroups)。請考慮啟用 [securityGroupSelectorTerms](https://karpenter.sh/docs/concepts/nodeclasses/#specsecuritygroupselectorterms),以允許 Karpenter 節點範本在自動擴展節點期間發現自訂安全群組。

我們強烈建議建立一個安全群組,以允許所有節點間通訊流量。在啟動過程中,節點需要出站網際網路連線才能存取叢集端點。評估出站存取需求,例如內部部署連線和容器登錄存取,並相應設置規則。在將變更投入生產環境之前,我們強烈建議您在開發環境中仔細檢查連線。

### 在每個可用區域部署 NAT 閘道

如果您在私有子網路 (IPv4 和 IPv6) 中部署節點,請考慮在每個可用區域 (AZ) 中建立一個 NAT 閘道,以確保區域獨立架構並減少跨 AZ 支出。每個 AZ 中的 NAT 閘道都實現了冗餘。

### 使用 Cloud9 存取私有叢集

AWS Cloud9 是一個可以在私有子網路中安全運行的基於網路的 IDE,無需入站存取,使用 AWS Systems Manager。也可以在 Cloud9 實例上禁用出站。[瞭解如何使用 Cloud9 存取私有叢集和子網路。](https://aws.amazon.com/blogs/security/isolating-network-access-to-your-aws-cloud9-environments/)

![AWS Cloud9 主控台連接到無入站存取的 EC2 實例的插圖。](./image-2.jpg)
