# 運行 IPv6 EKS 集群

<iframe width="560" height="315" src="https://www.youtube.com/embed/zdXpTT0bZXo" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

EKS 在 IPv6 模式下解決了大規模 EKS 集群中常見的 IPv4 耗盡問題。EKS 對 IPv6 的支持著重於解決 IPv4 耗盡問題,這源於 IPv4 地址空間的有限大小。這是許多客戶提出的一個重大問題,與 Kubernetes 的 "[IPv4/IPv6 雙堆疊](https://kubernetes.io/docs/concepts/services-networking/dual-stack/)"功能不同。
EKS/IPv6 還將提供使用 IPv6 CIDR 互連網路邊界的靈活性,從而最小化遭受 CIDR 重疊的機會,因此解決了雙重問題(集群內、跨集群)。
在以 IPv6 模式 (--ip-family ipv6) 部署 EKS 集群時,此操作是不可逆的。簡單來說,EKS IPv6 支持將在整個集群生命週期內啟用。

在 IPv6 EKS 集群中,Pod 和服務將收到 IPv6 地址,同時保持與舊版 IPv4 端點的兼容性。這包括外部 IPv4 端點訪問集群內服務的能力,以及 Pod 訪問外部 IPv4 端點的能力。

Amazon EKS IPv6 支持利用了 VPC 原生的 IPv6 功能。每個 VPC 都分配了一個 IPv4 地址前綴(CIDR 塊大小可以從 /16 到 /28)和來自 Amazon 的 GUA (全球單播地址)的唯一 /56 IPv6 地址前綴(固定);您可以為 VPC 中的每個子網分配一個 /64 地址前綴。路由表、網路存取控制清單、對等連接和 DNS 解析等 IPv4 功能在啟用了 IPv6 的 VPC 中的工作方式與之前相同。然後,VPC 被稱為雙堆疊 VPC,接著是雙堆疊子網,以下圖表示支持 EKS/IPv6 集群的 IPV4 和 IPv6 VPC 基礎模式:

![Dual Stack VPC, mandatory foundation for EKS cluster in IPv6 mode](./eks-ipv6-foundation.png)

在 IPv6 世界中,每個地址都是可路由的網際網路地址。預設情況下,VPC 從公共 GUA 範圍分配 IPv6 CIDR。VPC 不支持從 RFC 4193 定義的 [Unique Local Address (ULA)](https://en.wikipedia.org/wiki/Unique_local_address) 範圍 (fd00::/8 或 fc00::/8) 分配私有 IPv6 地址,即使您想要分配您自己擁有的 IPv6 CIDR。從私有子網路出口到互聯網是通過在 VPC 中實現僅出口互聯網閘道 (EIGW) 來支持的,允許出站流量而阻止所有入站流量。
以下圖表示在 EKS/IPv6 集群內 Pod IPv6 互聯網出口流量:

![Dual Stack VPC, EKS Cluster in IPv6 Mode, Pods in private subnets egressing to Internet IPv6 endpoints](./eks-egress-ipv6.png)

在 [VPC 使用者指南](https://docs.aws.amazon.com/whitepapers/latest/ipv6-on-aws/IPv6-on-AWS.html)中可以找到實施 IPv6 子網路的最佳實踐。

在 IPv6 EKS 集群中,節點和 Pod 收到公共 IPv6 地址。EKS 根據唯一本地 IPv6 單播地址 (ULA) 為服務分配 IPv6 地址。IPv6 集群的 ULA 服務 CIDR 在集群創建階段自動分配,無法指定,與 IPv4 不同。以下圖表示 EKS/IPv6 集群控制平面和數據平面基礎架構模式:

![Dual Stack VPC, EKS Cluster in IPv6 Mode, control plane ULA, data plane IPv6 GUA for EC2 & Pods](./eks-cluster-ipv6-foundation.png)

## 概述

EKS/IPv6 僅支持前綴模式 (VPC-CNI 插件 ENI IP 分配模式)。瞭解更多關於 [前綴模式](https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/index_linux/)。
> 前綴分配僅適用於基於 Nitro 的 EC2 實例,因此 EKS/IPv6 僅支持在數據平面使用基於 Nitro 的 EC2 實例的集群。

簡單來說,每個工作節點的 /80 IPv6 前綴將產生約 10^14 個 IPv6 地址,限制因素將不再是 IP,而是 Pod 密度(資源方面)。

IPv6 前綴分配僅在 EKS 工作節點啟動時發生。
這種行為有助於緩解高 Pod 損耗 EKS/IPv4 集群中由於 VPC CNI 插件 (ipamd) 產生的節流 API 調用而導致 Pod 調度延遲的情況,這些 API 調用旨在及時分配私有 IPv4 地址。它還被認為可以使 VPC-CNI 插件高級旋鈕調優 [WARM_IP/ENI*、MINIMUM_IP*](https://github.com/aws/amazon-vpc-cni-k8s#warm_ip_target) 變得不必要。

以下圖放大顯示了 IPv6 工作節點彈性網路介面 (ENI):

![illustration of worker subnet, including primary ENI with multiple IPv6 Addresses](./image-2.png)

每個 EKS 工作節點都分配了 IPv4 和 IPv6 地址,以及相應的 DNS 條目。對於給定的工作節點,僅從雙堆疊子網中消耗一個 IPv4 地址。EKS 對 IPv6 的支持使您能夠通過高度固定的僅出口 IPv4 模型與 IPv4 端點(AWS、內部部署、互聯網)通信。EKS 實現了一個主機本地 CNI 插件,次於 VPC CNI 插件,用於為 Pod 分配和配置 IPv4 地址。CNI 插件從 169.254.172.0/22 範圍為 Pod 配置一個特定於主機的不可路由 IPv4 地址。分配給 Pod 的 IPv4 地址在工作節點內是唯一的,並且不會在工作節點之外宣告。169.254.172.0/22 提供了多達 1024 個唯一的 IPv4 地址,可以支持大型實例類型。

以下圖表示 IPv6 Pod 連接到集群邊界外的 IPv4 端點(非互聯網)的流程:

![EKS/IPv6, IPv4 egress-only flow](./eks-ipv4-snat-cni.png)

在上圖中,Pod 將執行端點的 DNS 查找,並在收到 IPv4 "A" 響應時,Pod 的僅節點唯一 IPv4 地址將通過源網路地址轉換 (SNAT) 轉換為連接到 EC2 工作節點的主網路介面的私有 IPv4 (VPC) 地址。

EKS/IPv6 Pod 還需要使用公共 IPv4 地址通過互聯網連接到 IPv4 端點,存在類似的流程。
以下圖表示 IPv6 Pod 連接到集群邊界外的 IPv4 端點(可路由到互聯網)的流程:

![EKS/IPv6, IPv4 Internet egress-only flow](./eks-ipv4-snat-cni-internet.png)

在上圖中,Pod 將執行端點的 DNS 查找,並在收到 IPv4 "A" 響應時,Pod 的僅節點唯一 IPv4 地址將通過源網路地址轉換 (SNAT) 轉換為連接到 EC2 工作節點的主網路介面的私有 IPv4 (VPC) 地址。然後,Pod IPv4 地址(源 IPv4: EC2 主 IP)將路由到 IPv4 NAT 網關,在那裡 EC2 主 IP 將轉換(SNAT)為有效的可路由到互聯網的 IPv4 公共 IP 地址(NAT 網關分配的公共 IP)。

任何跨節點的 Pod 到 Pod 通信都使用 IPv6 地址。VPC CNI 配置 iptables 來處理 IPv6,同時阻止任何 IPv4 連接。

Kubernetes 服務將僅從唯一 [本地 IPv6 單播地址 (ULA)](https://datatracker.ietf.org/doc/html/rfc4193) 收到 IPv6 地址(ClusterIP)。IPv6 集群的 ULA 服務 CIDR 在 EKS 集群創建階段自動分配,無法修改。以下圖表示 Pod 到 Kubernetes 服務的流程:

![EKS/IPv6, IPv6 Pod to IPv6 k8s service (ClusterIP ULA) flow](./Pod-to-service-ipv6.png)

服務通過 AWS 負載平衡器暴露到互聯網。負載平衡器收到公共 IPv4 和 IPv6 地址,又稱為雙堆疊負載平衡器。對於訪問 IPv6 集群 kubernetes 服務的 IPv4 客戶端,負載平衡器執行 IPv4 到 IPv6 的轉換。

Amazon EKS 建議在私有子網路中運行工作節點和 Pod。您可以在公共子網路中創建公共負載平衡器,該負載平衡器將流量負載平衡到在私有子網路中運行的 Pod 上的節點。
以下圖表示互聯網 IPv4 用戶訪問 EKS/IPv6 Ingress 服務:

![Internet IPv4 user to EKS/IPv6 Ingress service](./ipv4-internet-to-eks-ipv6.png)

> 注意:上述模式需要部署 [最新版本](https://kubernetes-sigs.github.io/aws-load-balancer-controller) 的 AWS 負載平衡器控制器

### EKS 控制平面 <-> 數據平面通信

EKS 將以雙堆疊模式(IPv4/IPv6)在跨帳戶中提供彈性網路介面(X-ENI)。Kubernetes 節點組件(如 kubelet 和 kube-proxy)配置為支持雙堆疊。kubelet 和 kube-proxy 在 hostNetwork 模式下運行,並綁定到連接到節點的主網路介面的 IPv4 和 IPv6 地址。Kubernetes api-server 通過 X-ENI 與 Pod 和節點組件通信是基於 IPv6 的。Pod 通過 X-ENI 與 api-server 通信,Pod 到 api-server 的通信始終使用 IPv6 模式。

![illustration of cluster including X-ENIs](./image-5.png)

## 建議

### 維護對 IPv4 EKS API 的訪問

EKS API 只能通過 IPv4 訪問。這也包括集群 API 端點。您將無法從僅 IPv6 網路訪問集群端點和 API。需要您的網路支持 (1) 促進 IPv6 和 IPv4 主機之間通信的 NAT64/DNS64 等 IPv6 過渡機制,以及 (2) 支持 IPv4 端點轉換的 DNS 服務。

### 根據計算資源進行調度

單個 IPv6 前綴就足以在單個節點上運行許多 Pod。這也有效地消除了 ENI 和 IP 對節點上最大 Pod 數量的限制。儘管 IPv6 消除了對最大 Pod 的直接依賴,但在使用較小實例類型(如 m5.large)的前綴附件時,您可能會先耗盡實例的 CPU 和內存資源,而不是 IP 地址。如果使用自行管理的節點組或具有自定義 AMI ID 的受管節點組,則必須手動設置 EKS 建議的最大 Pod 值。

您可以使用以下公式來確定可以在 IPv6 EKS 集群的節點上部署的最大 Pod 數量。

* ((實例類型的網路介面數量(每個網路介面的前綴數-1)* 16) + 2

* ((3 個 ENI)*((每個 ENI 10 個次要 IP-1)* 16)) + 2 = 460 (實際)

受管節點組會自動為您計算最大 Pod 數量。避免更改 EKS 建議的最大 Pod 數量值,以免由於資源限制而導致 Pod 調度失敗。

### 評估現有自定義網路的目的

如果目前啟用了 [自定義網路](https://aws.github.io/aws-eks-best-practices/networking/custom-networking/),Amazon EKS 建議您重新評估在 IPv6 下對它的需求。如果您選擇使用自定義網路來解決 IPv4 耗盡問題,那在 IPv6 下就不再需要了。如果您正在利用自定義網路來滿足安全性要求,例如為節點和 Pod 提供單獨的網路,我們鼓勵您提交 [EKS 路線圖請求](https://github.com/aws/containers-roadmap/issues)。

### EKS/IPv6 集群中的 Fargate Pod

EKS 支持在 Fargate 上運行的 Pod 使用 IPv6。在 Fargate 上運行的 Pod 將消耗來自 VPC CIDR 範圍(IPv4 和 IPv6)的 IPv6 和 VPC 可路由私有 IPv4 地址。簡單來說,您的 EKS/Fargate Pod 集群範圍內的密度將受到可用 IPv4 和 IPv6 地址的限制。建議您為雙堆疊子網路/VPC CIDR 規劃未來增長。如果底層子網路沒有可用的 IPv4 地址,則無法調度新的 Fargate Pod,無論有多少可用的 IPv6 地址。

### 部署 AWS 負載平衡器控制器 (LBC)

**上游內建的 Kubernetes 服務控制器不支持 IPv6**。我們建議使用 [最新版本](https://kubernetes-sigs.github.io/aws-load-balancer-controller) 的 AWS 負載平衡器控制器附加元件。LBC 只有在消耗了相應的 kubernetes service/ingress 定義時,並且該定義帶有註解 `"alb.ingress.kubernetes.io/ip-address-type: dualstack"` 和 `"alb.ingress.kubernetes.io/target-type: ip"`時,才會部署雙堆疊 NLB 或雙堆疊 ALB。

AWS 網路負載平衡器不支持雙堆疊 UDP 協議地址類型。如果您對低延遲、實時流媒體、在線遊戲和 IoT 有強烈要求,我們建議運行 IPv4 集群。要瞭解如何管理 UDP 服務的健康檢查,請參閱 ["如何將 UDP 流量路由到 Kubernetes"](https://aws.amazon.com/blogs/containers/how-to-route-udp-traffic-into-kubernetes/)。
