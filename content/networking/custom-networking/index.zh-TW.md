# 自訂網路

預設情況下，Amazon VPC CNI 會從主要子網路為 Pod 指派 IP 位址。主要子網路是主要 ENI 所連接的子網路 CIDR，通常是節點/主機的子網路。

如果子網路 CIDR 太小，CNI 可能無法獲取足夠的次要 IP 位址來指派給您的 Pod。這是 EKS IPv4 叢集的常見挑戰。

自訂網路是解決這個問題的一種解決方案。

自訂網路透過從次要 VPC 位址空間 (CIDR) 指派節點和 Pod IP 來解決 IP 耗盡問題。自訂網路支援 ENIConfig 自訂資源。ENIConfig 包括一個替代子網路 CIDR 範圍 (從次要 VPC CIDR 中分割)，以及 Pod 將屬於的安全性群組。啟用自訂網路時，VPC CNI 會在 ENIConfig 中定義的子網路中建立次要 ENI。CNI 會從 ENIConfig CRD 中定義的 CIDR 範圍為 Pod 指派 IP 位址。

由於主要 ENI 不會被自訂網路使用，因此您可以在節點上執行的 Pod 數量最大值會較低。主機網路 Pod 會繼續使用指派給主要 ENI 的 IP 位址。此外，主要 ENI 用於處理來源網路轉譯並路由 Pod 流量到節點外部。

## 範例設定

雖然自訂網路會接受次要 CIDR 範圍的有效 VPC 範圍，但我們建議您使用來自 CG-NAT 空間的 CIDR (/16)，即 100.64.0.0/10 或 198.19.0.0/16，因為這些在公司環境中不太可能被使用，而不是其他 RFC1918 範圍。有關您可以與 VPC 一起使用的允許和限制 CIDR 區塊關聯的其他資訊，請參閱 VPC 文件中 VPC 和子網路大小調整一節的 [IPv4 CIDR 區塊關聯限制](https://docs.aws.amazon.com/vpc/latest/userguide/configure-your-vpc.html#add-cidr-block-restrictions)。

如下圖所示，工作節點的主要彈性網路介面 ([ENI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html)) 仍使用主要 VPC CIDR 範圍 (在這種情況下為 10.0.0.0/16)，但次要 ENI 使用次要 VPC CIDR 範圍 (在這種情況下為 100.64.0.0/16)。現在，為了讓 Pod 使用 100.64.0.0/16 CIDR 範圍，您必須設定 CNI 外掛程式以使用自訂網路。您可以按照 [這裡](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html) 記載的步驟操作。

![illustration of pods on secondary subnet](./image.png)

如果您想讓 CNI 使用自訂網路，請設定 `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG` 環境變數為 `true`。

```
kubectl set env daemonset aws-node -n kube-system AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true
```


當 `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true` 時，CNI 將從 `ENIConfig` 中定義的子網路指派 Pod IP 位址。`ENIConfig` 自訂資源用於定義將安排 Pod 的子網路。

```
apiVersion : crd.k8s.amazonaws.com/v1alpha1
kind : ENIConfig
metadata:
  name: us-west-2a
spec: 
  securityGroups:
    - sg-0dff111a1d11c1c11
  subnet: subnet-011b111c1f11fdf11
```

在建立 `ENIconfig` 自訂資源後，您需要建立新的工作節點並清空現有節點。現有的工作節點和 Pod 將不受影響。


## 建議

### 何時使用自訂網路

如果您正在處理 IPv4 耗盡且暫時無法使用 IPv6，我們建議您考慮使用自訂網路。Amazon EKS 對 [RFC6598](https://datatracker.ietf.org/doc/html/rfc6598) 空間的支援使您能夠擺脫 [RFC1918](https://datatracker.ietf.org/doc/html/rfc1918) 位址耗盡的挑戰，並擴展 Pod。請考慮使用自訂網路與前綴委派來增加節點上的 Pod 密度。

如果您有在不同網路上以不同安全性群組需求執行 Pod 的安全性需求，您可能會考慮使用自訂網路。啟用自訂網路後，Pod 會使用 ENIConfig 中定義的不同子網路或安全性群組，而不是節點主要網路介面。

自訂網路確實是部署多個 EKS 叢集和應用程式以連接內部部署資料中心服務的理想選擇。您可以增加 EKS 在 VPC 中可存取的私有位址 (RFC1918) 數量，用於諸如 Amazon Elastic Load Balancing 和 NAT-GW 等服務，同時在多個叢集中使用不可路由的 CG-NAT 空間來供您的 Pod 使用。使用 [transit gateway](https://aws.amazon.com/transit-gateway/) 和共用服務 VPC (包括跨多個可用區域的 NAT 閘道以實現高可用性) 的自訂網路，可讓您提供可擴展且可預測的流量流。這篇 [部落格文章](https://aws.amazon.com/blogs/containers/eks-vpc-routable-ip-address-conservation/) 描述了一種架構模式，這是將 EKS Pod 連接到資料中心網路的最推薦方式之一。

### 何時避免使用自訂網路

#### 準備實施 IPv6

自訂網路可以緩解 IP 耗盡問題，但需要額外的操作開銷。如果您目前正在部署雙堆疊 (IPv4/IPv6) VPC 或您的計劃包括 IPv6 支援，我們建議您實施 IPv6 叢集。您可以設定 IPv6 EKS 叢集並遷移您的應用程式。在 IPv6 EKS 叢集中，Kubernetes 和 Pod 都會獲得 IPv6 位址，並可以與 IPv4 和 IPv6 端點進行通訊。請查看 [執行 IPv6 EKS 叢集](../ipv6/index.md) 的最佳實務。

#### 耗盡 CG-NAT 空間

此外，如果您目前正在使用來自 CG-NAT 空間的 CIDR 或無法將次要 CIDR 與您的叢集 VPC 連結，您可能需要探索其他選項，例如使用替代 CNI。我們強烈建議您獲得商業支援或擁有偵錯和提交修補程式給開源 CNI 外掛程式專案的內部知識。請參閱 [替代 CNI 外掛程式](https://docs.aws.amazon.com/eks/latest/userguide/alternate-cni-plugins.html) 使用者指南以取得更多詳細資訊。

#### 使用私有 NAT 閘道

Amazon VPC 現在提供 [私有 NAT 閘道](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html) 功能。Amazon 的私有 NAT 閘道可讓私有子網路中的執行個體連接到具有重疊 CIDR 的其他 VPC 和內部部署網路。請考慮使用這篇 [部落格文章](https://aws.amazon.com/blogs/containers/addressing-ipv4-address-exhaustion-in-amazon-eks-clusters-using-private-nat-gateways/) 中所描述的方法來使用私有 NAT 閘道，以解決由於重疊 CIDR 而導致的 EKS 工作負載通訊問題，這是我們客戶表達的一個重大疑慮。自訂網路本身無法解決重疊 CIDR 的困難，而且會增加配置挑戰。

此部落格文章實作中使用的網路架構遵循 Amazon VPC 文件中 [啟用重疊網路之間的通訊](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html#private-nat-overlapping-networks) 下的建議。如本部落格文章所示，您可以將私有 NAT 閘道的使用與 RFC6598 位址結合，以管理客戶的私有 IP 耗盡問題。EKS 叢集、工作節點會部署在不可路由的 100.64.0.0/16 VPC 次要 CIDR 範圍，而私有 NAT 閘道、NAT 閘道則部署在可路由的 RFC1918 CIDR 範圍。該部落格解釋了如何使用 transit gateway 連接 VPC 以促進跨具有重疊不可路由 CIDR 範圍的 VPC 的通訊。對於 VPC 中不可路由位址範圍內的 EKS 資源需要與其他沒有重疊位址範圍的 VPC 通訊的使用案例，客戶有選擇使用 VPC 對等來互連這些 VPC 的選項。這種方法可能提供潛在的成本節省，因為所有在可用區域內透過 VPC 對等連線傳輸的資料現在都是免費的。

![illustration of network traffic using private NAT gateway](./image-3.png)

#### 節點和 Pod 的獨特網路

如果您需要將節點和 Pod 隔離到特定網路以滿足安全性需求，我們建議您將節點和 Pod 部署到來自較大次要 CIDR 區塊 (例如 100.64.0.0/8) 的子網路。在您的 VPC 中安裝新的 CIDR 後，您可以使用次要 CIDR 部署另一個節點群組，並清空原始節點以自動將 Pod 重新部署到新的工作節點。有關如何實施的更多資訊，請參閱這篇 [部落格](https://aws.amazon.com/blogs/containers/optimize-ip-addresses-usage-by-pods-in-your-amazon-eks-cluster/) 文章。

下圖所示的設定並未使用自訂網路。相反地，Kubernetes 工作節點會部署在您 VPC 的次要 VPC CIDR 範圍 (例如 100.64.0.0/10) 的子網路上。您可以讓 EKS 叢集保持運行 (控制平面將保留在原始子網路/s 上)，但節點和 Pod 將被移至次要子網路/s。這是另一種雖然不太常見但可以緩解 VPC 中 IP 耗盡風險的方法。我們建議在重新部署 Pod 到新的工作節點之前清空舊的節點。

![illustration of worker nodes on secondary subnet](./image-2.png)

### 使用可用區域標籤自動化配置

您可以讓 Kubernetes 自動套用對應於工作節點可用區域 (AZ) 的 ENIConfig。

Kubernetes 會自動將標籤 [`topology.kubernetes.io/zone`](http://topology.kubernetes.io/zone) 新增至您的工作節點。當您每個可用區域只有一個次要子網路 (替代 CIDR) 時，Amazon EKS 建議將可用區域用作您的 ENI 配置名稱。請注意，標籤 `failure-domain.beta.kubernetes.io/zone` 已被棄用，並由標籤 `topology.kubernetes.io/zone` 取代。

1. 將 `name` 欄位設定為您 VPC 的可用區域。
2. 使用此命令啟用自動配置：

```
kubectl set env daemonset aws-node -n kube-system AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true
```

如果您每個可用區域有多個次要子網路，您需要建立特定的 `ENI_CONFIG_LABEL_DEF`。您可以考慮將 `ENI_CONFIG_LABEL_DEF` 設定為 [`k8s.amazonaws.com/eniConfig`](http://k8s.amazonaws.com/eniConfig)，並使用自訂 eniConfig 名稱 (例如 [`k8s.amazonaws.com/eniConfig=us-west-2a-subnet-1`](http://k8s.amazonaws.com/eniConfig=us-west-2a-subnet-1) 和 [`k8s.amazonaws.com/eniConfig=us-west-2a-subnet-2`](http://k8s.amazonaws.com/eniConfig=us-west-2a-subnet-2)) 標記節點。

### 在配置次要網路時取代 Pod

啟用自訂網路不會修改現有節點。自訂網路是一個破壞性動作。我們建議在啟用自訂網路後，不要對您叢集中的所有工作節點進行滾動更換，而是使用 [EKS 入門指南](https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html) 中的 AWS CloudFormation 範本，並在工作節點佈建之前，使用自訂資源呼叫 Lambda 函數來更新 `aws-node` Daemonset 的環境變數以啟用自訂網路。

如果您在切換到自訂 CNI 網路功能之前有任何節點在您的叢集中執行 Pod，您應該隔離並 [清空節點](https://aws.amazon.com/premiumsupport/knowledge-center/eks-worker-node-actions/) 以優雅地關閉 Pod 並終止節點。只有與 ENIConfig 標籤或註釋相符的新節點才會使用自訂網路，因此在這些新節點上排程的 Pod 才能從次要 CIDR 獲得 IP 位址。

### 計算每個節點的最大 Pod 數量

由於節點的主要 ENI 不再用於指派 Pod IP 位址，因此您可以在給定的 EC2 執行個體類型上執行的 Pod 數量會減少。您可以使用自訂網路與前綴指派來解決此限制。使用前綴指派時，每個次要 IP 會在次要 ENI 上替換為 /28 前綴。

考慮使用自訂網路的 m5.large 執行個體的最大 Pod 數量。

不使用前綴指派時可以執行的最大 Pod 數量為 29

* ((3 ENIs - 1) * (10 次要 IP 每個 ENI - 1)) + 2 = 20

啟用前綴附加會將 Pod 數量增加到 290。

* (((3 ENIs - 1) * ((10 次要 IP 每個 ENI - 1) * 16)) + 2 = 290

但是，我們建議將 max-pods 設定為 110 而不是 290，因為該執行個體的虛擬 CPU 數量相當小。對於較大的執行個體，EKS 建議將 max pods 值設定為 250。在使用較小執行個體類型 (例如 m5.large) 時，您可能會在耗盡 IP 位址之前先耗盡執行個體的 CPU 和記憶體資源。

!!! info
    當 CNI 前綴將 /28 前綴分配給 ENI 時，它必須是 IP 位址的連續區塊。如果生成前綴的子網路高度分散，則前綴附加可能會失敗。您可以透過為叢集建立新的專用 VPC 或為前綴附加保留一組專用子網路 CIDR 來減輕這種情況的發生。請造訪 [子網路 CIDR 保留](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html) 以取得這個主題的更多資訊。

### 識別現有的 CG-NAT 空間使用情況

自訂網路可以緩解 IP 耗盡問題，但無法解決所有挑戰。如果您已經在使用 CG-NAT 空間供您的叢集使用，或根本無法將次要 CIDR 與您的叢集 VPC 關聯，我們建議您探索其他選項，例如使用替代 CNI 或移至 IPv6 叢集。
