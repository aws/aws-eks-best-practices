---
日期: 2023-09-22
作者:
  - Lukonde Mwila
---
# 成本優化 - 網路

為了實現彈性和容錯能力,架構高可用性 (HA) 系統是最佳實踐。在實踐中,這意味著將您的工作負載和底層基礎架構分散到特定 AWS 區域中的多個可用區域 (AZ)。確保這些特性存在於您的 Amazon EKS 環境中,將提高整體系統的可靠性。與此同時,您的 EKS 環境可能還包含各種構造 (即 VPC)、組件 (即 ELB) 和集成 (即 ECR 和其他容器註冊表)。

高可用性系統和其他特定用例組件的組合可能會在數據傳輸和處理方面發揮重大作用。這反過來又會影響數據傳輸和處理產生的成本。

下面詳述的做法將幫助您設計和優化 EKS 環境,以實現不同領域和用例的成本效益。


## Pod 到 Pod 通信

根據您的設置,Pod 之間的網路通信和數據傳輸可能會對運行 Amazon EKS 工作負載的總體成本產生重大影響。本節將介紹不同的概念和方法,以減少與 Pod 間通信相關的成本,同時考慮高可用性 (HA) 架構、應用程序性能和彈性。

### 限制流量到可用區域

頻繁的出口跨區流量 (在 AZ 之間分佈的流量) 可能會對您的網路相關成本產生重大影響。以下是控制 EKS 集群中 Pod 之間跨區流量量的一些策略。

_如果您想獲得 Pod 之間跨區流量的詳細可見性 (例如以字節為單位的數據傳輸量),請[參考此文章](https://aws.amazon.com/blogs/containers/getting-visibility-into-your-amazon-eks-cross-az-pod-to-pod-network-bytes/)。_

**使用拓撲感知路由 (前稱為拓撲感知提示)**

![Topology aware routing](../images/topo_aware_routing.png)

使用拓撲感知路由時,重要的是要理解服務、EndpointSlices 和 `kube-proxy` 在路由流量時是如何協同工作的。如上圖所示,服務是接收目的地為您的 Pod 的流量的穩定網路抽象層。創建服務時,將創建多個 EndpointSlices。每個 EndpointSlice 都有一個包含 Pod 地址子集的端點列表,以及它們運行的節點和任何其他拓撲信息。`kube-proxy` 是在集群的每個節點上運行的 daemonset,也扮演內部路由的角色,但它是根據從創建的 EndpointSlices 中消費的信息進行路由的。

當[*拓撲感知路由*](https://kubernetes.io/docs/concepts/services-networking/topology-aware-routing/)在 Kubernetes 服務上啟用和實現時,EndpointSlice 控制器將根據集群分散的不同區域按比例分配端點。對於這些端點中的每一個,EndpointSlice 控制器還將設置一個區域 _hint_。_hint_ 描述了端點應該為哪個區域提供流量服務。然後 `kube-proxy` 將根據應用的 _hint_ 將流量從一個區域路由到一個端點。

下圖顯示了如何組織 EndpointSlices 及其 hints,以便 `kube-proxy` 可以根據流量的區域起點知道它們應該去哪個目的地。如果沒有 hints,就沒有這樣的分配或組織,流量將被代理到不同的區域目的地,而不管它來自哪裡。

![Endpoint Slice](../images/endpoint_slice.png)

在某些情況下,EndpointSlice 控制器可能會為不同區域應用一個 _hint_,這意味著該端點可能最終會為來自不同區域的流量提供服務。這樣做的原因是為了嘗試在不同區域之間保持均勻的流量分佈。

以下是啟用 _拓撲感知路由_ 的服務代碼片段。

```yaml hl_lines="6-7"
apiVersion: v1
kind: Service
metadata:
  name: orders-service
  namespace: ecommerce
    annotations:
      service.kubernetes.io/topology-mode: Auto
spec:
  selector:
    app: orders
  type: ClusterIP
  ports:
  - protocol: TCP
    port: 3003
    targetPort: 3003
```

下面的截圖顯示了 EndpointSlice 控制器成功為在 AZ `eu-west-1a` 中運行的 Pod 副本的端點應用了一個 hint。

![Slice shell](../images/slice_shell.png)

!!! note
    需要注意的是,拓撲感知路由仍處於 **beta** 階段。此外,當工作負載廣泛且均勻地分佈在集群拓撲中時,此功能更可預測。因此,強烈建議將其與增加應用程序可用性的調度約束 (如 [pod 拓撲分佈約束](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)) 結合使用。

**使用自動擴展器: 將節點佈建到特定 AZ**

_我們強烈建議_ 在多個 AZ 中運行您的工作負載,以提高可靠性。這可以提高應用程序的可靠性,特別是在某個 AZ 出現問題的情況下。如果您願意為了減少網路相關成本而犧牲可靠性,您可以將節點限制在單個 AZ 中。

要在同一 AZ 中運行所有 Pod,可以在同一 AZ 中佈建工作節點,或者在同一 AZ 中運行的工作節點上調度 Pod。要在單個 AZ 中佈建節點,請使用 [Cluster Autoscaler (CA)](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) 定義一個節點組,其子網路屬於同一 AZ。對於 [Karpenter,](https://karpenter.sh/) 使用 "[_topology.kubernetes.io/zone"_](http://topology.kubernetes.io/zone%E2%80%9D) 並指定您希望創建工作節點的 AZ。例如,下面的 Karpenter 佈建器片段將在 us-west-2a AZ 中佈建節點。

**Karpenter**

```yaml hl_lines="5-9"
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
name: single-az
spec:
  requirements:
  - key: "topology.kubernetes.io/zone"
    operator: In
    values: ["us-west-2a"]
```

**Cluster Autoscaler (CA)**

```yaml hl_lines="7-8"
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: my-ca-cluster
  region: us-east-1
  version: "1.21"
availabilityZones:
- us-east-1a
managedNodeGroups:
- name: managed-nodes
  labels:
    role: managed-nodes
  instanceType: t3.medium
  minSize: 1
  maxSize: 10
  desiredCapacity: 1
...
```

**使用 Pod 分配和節點親和性**

或者,如果您有在多個 AZ 中運行的工作節點,每個節點都將具有標籤 _[topology.kubernetes.io/zone](http://topology.kubernetes.io/zone%E2%80%9D)_,其值為其 AZ (例如 us-west-2a 或 us-west-2b)。您可以使用 `nodeSelector` 或 `nodeAffinity` 將 Pod 調度到單個 AZ 中的節點。例如,以下清單文件將在 AZ us-west-2a 中運行的節點上調度 Pod。

```yaml hl_lines="7-9"
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    env: test
spec:
  nodeSelector:
    topology.kubernetes.io/zone: us-west-2a
  containers:
  - name: nginx
    image: nginx 
    imagePullPolicy: IfNotPresent
```

### 限制流量到節點

在某些情況下,僅限制區域級別的流量是不夠的。除了降低成本外,您可能還需要降低某些頻繁相互通信的應用程序之間的網路延遲。為了實現最佳網路性能和降低成本,您需要一種限制流量到特定節點的方式。例如,微服務 A 應該始終與節點 1 上的微服務 B 通信,即使在高可用性 (HA) 設置中也是如此。如果微服務 A 在節點 1 上與微服務 B 在節點 2 上通信,可能會對這種性能要求較高的應用程序產生負面影響,特別是如果節點 2 位於不同的 AZ。

**使用服務內部流量策略**

為了限制 Pod 網路流量到節點,您可以使用 _[服務內部流量策略](https://kubernetes.io/docs/concepts/services-networking/service-traffic-policy/)_。默認情況下,發送到工作負載服務的流量將在不同生成的端點之間隨機分佈。因此,在 HA 架構中,這意味著來自微服務 A 的流量可能會進入任何給定節點上任何微服務 B 的副本。但是,如果將服務的內部流量策略設置為 `Local`,則流量將限制在流量發起節點上的端點。此策略規定了專用節點本地端點。根據這一含義,該工作負載的網路流量相關成本將低於全集群分佈的情況。此外,延遲也會降低,從而提高應用程序的性能。

!!! note
    需要注意的是,此功能無法與 Kubernetes 中的拓撲感知路由結合使用。

![Local internal traffic](../images/local_traffic.png)

以下是為服務設置 _內部流量策略_ 的代碼片段。


```yaml hl_lines="14"
apiVersion: v1
kind: Service
metadata:
  name: orders-service
  namespace: ecommerce
spec:
  selector:
    app: orders
  type: ClusterIP
  ports:
  - protocol: TCP
    port: 3003
    targetPort: 3003
  internalTrafficPolicy: Local
```

為了避免應用程序由於流量丟棄而出現意外行為,您應該考慮以下方法:

* 為每個通信的 Pod 運行足夠的副本
* 使用 [拓撲分佈約束](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) 實現 Pod 的相對均勻分佈
* 對於通信 Pod 的共置,使用 [pod 親和性規則](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#inter-pod-affinity-and-anti-affinity)

在此示例中,您有 2 個微服務 A 的副本和 3 個微服務 B 的副本。如果微服務 A 的副本分佈在節點 1 和 2 上,而微服務 B 的所有 3 個副本都在節點 3 上,那麼它們就無法通信,因為 `Local` 內部流量策略。當沒有可用的節點本地端點時,流量將被丟棄。

![node-local_no_peer](../images/no_node_local_1.png)

如果微服務 B 在節點 1 和 2 上有 2 個副本,那麼 `graphql` 和 `orders` 之間將有通信。但是您仍然會有一個孤立的微服務 B 副本,沒有任何對等副本可以與之通信。

![node-local_with_peer](../images/no_node_local_2.png)

!!! note
    在某些情況下,上圖所示的孤立副本可能不會引起關注,如果它仍然有用途 (例如為外部傳入流量提供服務)。

**使用服務內部流量策略與拓撲分佈約束**

將 _內部流量策略_ 與 _拓撲分佈約束_ 結合使用可以確保您為通信的微服務在不同節點上擁有正確數量的副本。


```yaml hl_lines="16-22"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: express-test
spec:
  replicas: 6
  selector:
    matchLabels:
      app: express-test
  template:
    metadata:
      labels:
        app: express-test
        tier: backend
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: "topology.kubernetes.io/zone"
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: express-test
```

**使用服務內部流量策略與 Pod 親和性規則**

另一種方法是在使用服務內部流量策略時利用 Pod 親和性規則。通過 Pod 親和性,您可以影響調度器將某些頻繁通信的 Pod 共置。通過對某些 Pod 應用嚴格的調度約束 (`requiredDuringSchedulingIgnoredDuringExecution`),當調度器將 Pod 放置在節點上時,這將為 Pod 共置提供更好的結果。

```yaml hl_lines="11-20"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphql
  namespace: ecommerce
  labels:
    app.kubernetes.io/version: "0.1.6"
    ...
    spec:
      serviceAccountName: graphql-service-account
      affinity:
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - orders
            topologyKey: "kubernetes.io/hostname"
```

## 負載均衡器到 Pod 通信

EKS 工作負載通常由負載均衡器前置,該負載均衡器將流量分佈到 EKS 集群中的相關 Pod。您的架構可能包括內部和/或外部負載均衡器。根據您的架構和網路流量配置,負載均衡器與 Pod 之間的通信可能會對數據傳輸費用產生重大影響。

您可以使用 [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller) 自動管理 ELB 資源 (ALB 和 NLB) 的創建。在這種設置中產生的數據傳輸費用將取決於網路流量的路徑。AWS Load Balancer Controller 支持兩種網路流量模式,_instance mode_ 和 _ip mode_。

使用 _instance mode_ 時,將在集群中的每個節點上打開一個 NodePort。然後,負載均衡器將在節點之間均勻代理流量。如果節點上正在運行目標 Pod,則不會產生數據傳輸成本。但是,如果目標 Pod 位於不同的節點並且在與接收流量的 NodePort 不同的 AZ 中,則將有一個額外的網路跳躍從 kube-proxy 到目標 Pod。在這種情況下,將產生跨 AZ 數據傳輸費用。由於流量在節點之間均勻分佈,很可能會產生與從 kube-proxy 到相關目標 Pod 的跨區網路跳躍相關的額外數據傳輸費用。

下圖描繪了從負載均衡器到 NodePort 的流量網路路徑,以及從 `kube-proxy` 到位於不同 AZ 中的單獨節點上的目標 Pod 的網路路徑。這是 _instance mode_ 設置的一個示例。

![LB to Pod](../images/lb_2_pod.png)

使用 _ip mode_ 時,網路流量直接從負載均衡器代理到目標 Pod。因此,此方法不涉及數據傳輸費用。

!!! tip
    建議將您的負載均衡器設置為 _ip 流量模式_,以減少數據傳輸費用。對於此設置,還需要確保您的負載均衡器部署在 VPC 中的所有子網中。

下圖描繪了網路 _ip mode_ 中從負載均衡器到 Pod 的流量網路路徑。

![IP mode](../images/ip_mode.png)

## 從容器註冊表傳輸數據

### Amazon ECR

數據傳輸到 Amazon ECR 私有註冊表是免費的。_同區域內的數據傳輸不收費_,但是傳輸到互聯網和跨區域的數據傳輸將按互聯網數據傳輸費率在兩端收費。

您應該利用 ECR 內置的 [image replication feature](https://docs.aws.amazon.com/AmazonECR/latest/userguide/replication.html) 將相關容器映像複製到與您的工作負載相同的區域。這樣,複製將被收取一次費用,而所有相同區域 (內部區域) 的映像拉取都將免費。

您可以進一步減少與從 ECR 拉取映像 (數據傳輸出) 相關的數據傳輸成本,方法是 _使用 [Interface VPC Endpoints](https://docs.aws.amazon.com/whitepapers/latest/aws-privatelink/what-are-vpc-endpoints.html) 連接到同區域的 ECR 存儲庫_。連接到 ECR 的公共 AWS 端點 (通過 NAT 網關和互聯網網關) 的替代方法將產生更高的數據處理和傳輸成本。下一節將詳細介紹降低工作負載與 AWS 服務之間數據傳輸成本的方法。

如果您運行的工作負載具有特別大的映像,您可以構建自己的自定義 Amazon Machine Images (AMI),其中預先緩存了容器映像。這可以減少從容器註冊表到 EKS 工作節點的初始映像拉取時間和潛在數據傳輸成本。


## 傳輸到互聯網和 AWS 服務

將 Kubernetes 工作負載與其他 AWS 服務或第三方工具和平台通過互聯網集成是一種常見做法。用於路由流量到相關目的地的底層網路基礎架構可能會影響數據傳輸過程中產生的成本。

### 使用 NAT 網關

NAT 網關是執行網路地址轉換 (NAT) 的網路組件。下圖描繪了 EKS 集群中的 Pod 與其他 AWS 服務 (Amazon ECR、DynamoDB 和 S3) 以及第三方平台通信。在此示例中,Pod 運行在單獨 AZ 的私有子網中。為了發送和接收來自互聯網的流量,NAT 網關部署在一個 AZ 的公共子網中,允許具有私有 IP 地址的任何資源共享單個公共 IP 地址來訪問互聯網。這個 NAT 網關反過來與互聯網網關組件通信,允許數據包被發送到最終目的地。

![NAT Gateway](../images/nat_gw.png)

在使用 NAT 網關進行此類用例時,_您可以通過在每個 AZ 部署一個 NAT 網關來最小化數據傳輸成本_。這樣,路由到互聯網的流量將通過同一 AZ 中的 NAT 網關,避免了跨 AZ 數據傳輸。但是,即使您可以節省跨 AZ 數據傳輸的成本,這種設置的含義是您的架構中將產生額外的 NAT 網關成本。

下圖描繪了這種推薦方法。

![Recommended approach](../images/recommended_approach.png)

### 使用 VPC 端點

為了進一步降低此類架構的成本,_您應該使用 [VPC Endpoints](https://docs.aws.amazon.com/whitepapers/latest/aws-privatelink/what-are-vpc-endpoints.html) 在您的工作負載與 AWS 服務之間建立連接_。VPC 端點允許您從 VPC 內部訪問 AWS 服務,而無需數據/網路數據包穿越互聯網。所有流量都保留在 AWS 網路內部。有兩種類型的 VPC 端點: Interface VPC Endpoints ([由許多 AWS 服務支持](https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-privatelink-support.html)) 和 Gateway VPC Endpoints (僅由 S3 和 DynamoDB 支持)。

**Gateway VPC Endpoints**

_與 Gateway VPC Endpoints 無關的每小時或數據傳輸費用_。使用 Gateway VPC Endpoints 時,需要注意的是,它們無法跨 VPC 邊界擴展。它們不能在 VPC 對等、VPN 網路或通過 Direct Connect 中使用。

**Interface VPC Endpoint**

VPC 端點有 [每小時費用](https://aws.amazon.com/privatelink/pricing/),並且根據 AWS 服務的不同,可能還會有通過底層 ENI 進行數據處理的額外費用。要減少與 Interface VPC Endpoints 相關的跨 AZ 數據傳輸成本,您可以在每個 AZ 中創建一個 VPC 端點。您可以在同一 VPC 中創建多個指向同一 AWS 服務的 VPC 端點。

下圖顯示了 Pod 通過 VPC 端點與 AWS 服務通信。

![VPC Endpoints](../images/vpc_endpoints.png)

## VPC 之間的數據傳輸

在某些情況下,您可能在不同的 VPC 中 (位於同一 AWS 區域內) 有需要相互通信的工作負載。這可以通過允許流量穿越附加到各自 VPC 的互聯網網關來實現。可以通過在公共子網中部署基礎架構組件 (如 EC2 實例、NAT 網關或 NAT 實例) 來啟用此類通信。但是,包含這些組件的設置將產生處理/傳輸進出 VPC 的數據的費用。如果從單獨的 VPC 發出和接收的流量跨越 AZ,則還將產生額外的數據傳輸費用。下圖描繪了一個使用 NAT 網關和互聯網網關在不同 VPC 中的工作負載之間建立通信的設置。

![Between VPCs](../images/between_vpcs.png)

### VPC 對等連接

為了降低此類用例的成本,您可以使用 [VPC Peering](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html)。使用 VPC 對等連接,在同一 AZ 內保留的網路流量不會產生數據傳輸費用。如果流量跨越 AZ,將產生費用。儘管如此,VPC 對等方法是在同一 AWS 區域內工作負載之間進行成本效益通信的推薦方法。但是,需要注意的是,VPC 對等主要有效於 1:1 VPC 連接,因為它不允許傳遞網路。

下圖是工作負載通過 VPC 對等連接進行通信的高級表示。

![Peering](../images/peering.png)

### 傳遞網路連接

如上一節所指出的,VPC 對等連接不允許傳遞網路連接。如果您想連接 3 個或更多具有傳遞網路要求的 VPC,那麼您應該使用 [Transit Gateway](https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html) (TGW)。這將使您能夠克服 VPC 對等的限制或在多個 VPC 之間進行多個 VPC 對等連接帶來的任何操作開銷。您需要按小時付費,並為發送到 TGW 的數據付費。_通過 TGW 流動的跨 AZ 流量不會產生目的地費用。_

下圖顯示了在同一 AWS 區域內的不同 VPC 之間的工作負載之間的跨 AZ 流量通過 TGW 流動。

![Transitive](../images/transititive.png)

## 使用服務網格

服務網格提供了強大的網路功能,可用於減少 EKS 集群環境中的網路相關成本。但是,如果您採用服務網格,您應該仔細考慮它將為您的環境帶來的操作任務和複雜性。

### 限制流量到可用區域

**使用 Istio 的區域加權分佈**

Istio 允許您在路由發生後對流量應用網路策略。這是通過 [Destination Rules](https://istio.io/latest/docs/reference/config/networking/destination-rule/) 如 [locality weighted distribution](https://istio.io/latest/docs/tasks/traffic-management/locality-load-balancing/distribute/) 來實現的。使用此功能,您可以根據流量的來源控制可以進入某個目的地的流量權重 (以百分比表示)。此流量的來源可以是外部 (或公共) 負載均衡器或集群內的 Pod。當所有 Pod 端點都可用時,區域將根據加權輪詢負載均衡算法進行選擇。如果某些端點不健康或不可用,則 [區域權重將自動調整](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/locality_weight.html) 以反映可用端點的變化。

!!! note
    在實施區域加權分佈之前,您應該首先了解您的網路流量模式以及目的地規則策略可能對您的應用程序行為產生的影響。因此,重要的是要有分佈式跟踪機制,例如 [AWS X-Ray](https://aws.amazon.com/xray/) 或 [Jaeger](https://www.jaegertracing.io/)。

上述 Istio 目的地規則也可以應用於管理從負載均衡器到 EKS 集群中的 Pod 的流量。可以將區域加權分佈規則應用於從高可用負載均衡器 (特別是 Ingress Gateway) 接收流量的服務。這些規則允許您根據其區域來源 (在本例中為負載均衡器) 控制流量流向何處的比例。如果配置正確,與負載均衡器均勻或隨機分佈流量到不同 AZ 中的 Pod 副本相比,將產生較少的出口跨區流量。

下面是 Istio 中 Destination Rule 資源的代碼塊示例。如下所示,此資源為來自 `eu-west-1` 區域中 3 個不同 AZ 的傳入流量指定了加權配置。這些配置聲明,來自給定 AZ 的大部分傳入流量 (在本例中為 70%) 應該被代理到與其發源 AZ 相同的目的地。

```yaml hl_lines="7-11"
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: express-test-dr
spec:
  host: express-test.default.svc.cluster.local
  trafficPolicy:
    loadBalancer:                        
      localityLbSetting:
        distribute:
        - from: eu-west-1/eu-west-1a/    
          to:
            "eu-west-1/eu-west-1a/*": 70 
            "eu-west-1/eu-west-1b/*": 20
            "eu-west-1/eu-west-1c/*": 10
        - from: eu-west-1/eu-west-1b/*    
          to:
            "eu-west-1/eu-west-1a/*": 20 
            "eu-west-1/eu-west-1b/*": 70
            "eu-west-1/eu-west-1c/*": 10
        - from: eu-west-1/eu-west-1c/*    
          to:
            "eu-west-1/eu-west-1a/*": 20 
            "eu-west-1/eu-west-1b/*": 10
            "eu-west-1/eu-west-1c/*": 70**
    connectionPool:
      http:
        http2MaxRequests: 10
        maxRequestsPerConnection: 10
    outlierDetection:
      consecutiveGatewayErrors: 1
      interval: 1m
      baseEjectionTime: 30s
```

!!! note
    可以分佈到目的地的最小權重為 1%。這樣做的原因是為了在主要目的地的端點不健康或不可用時維護故障轉移區域和區域。

下圖描繪了一種情況,其中在 _eu-west-1_ 區域有一個高可用負載均衡器,並應用了區域加權分佈。對於此圖,目的地規則策略配置為將來自 _eu-west-1a_ 的 60% 流量發送到同一 AZ 中的 Pod,而將來自 _eu-west-1a_ 的 40% 流量發送到 eu-west-1b 中的 Pod。

![Istio Traffic Control](../images/istio-traffic-control.png)

### 限制流量到可用區域和節點

**使用 Istio 的服務內部流量策略**

為了減少與 _外部_ 傳入流量和 Pod 之間 _內部_ 流量相關的網路成本,您可以結合 Istio 的目的地規則和 Kubernetes 服務 _內部流量策略_。將 Istio 目的地規則與服務內部流量策略相結合的方式在很大程度上取決於以下三個因素:

* 微服務的角色
* 微服務之間的網路流量模式
* 微服務應如何部署在 Kubernetes 集群拓撲中

下圖顯示了在嵌套請求的情況下網路流量的流向,以及上述策略如何控制流量。

![External and Internal traffic policy](../images/external-and-internal-traffic-policy.png)

1. 最終用戶向 **APP A** 發出請求,後者又向 **APP C** 發出嵌套請求。此請求首先發送到高可用負載均衡器,該負載均衡器在 AZ 1 和 AZ 2 中都有實例,如上圖所示。
2. 外部傳入請求隨後由 Istio Virtual Service 路由到正確的目的地。
3. 請求路由後,Istio 目的地規則根據流量來源 (AZ 1 或 AZ 2) 控制流量流向各個 AZ 的比例。
4. 流量然後進入 **APP A** 的服務,並被代理到各個 Pod 端點。如圖所示,80% 的傳入流量被發送到 AZ 1 中的 Pod 端點,20% 的傳入流量被發送到 AZ 2。
5. **APP A** 隨後向 **APP C** 發出內部請求。**APP C** 的服務啟用了內部流量策略 (`internalTrafficPolicy``: Local`)。
6. 來自 **APP A** (在 *NODE 1* 上) 到 **APP C** 的內部請求成功,因為有可用的節點本地端點用於 **APP C**。
7. 來自 **APP A** (在 *NODE 3* 上) 到 **APP C** 的內部請求失敗,因為沒有可用的 _節點本地端點_ 用於 **APP C**。如圖所示,APP C 在 NODE 3 上沒有副本。****

下面的截圖來自此方法的實時示例。第一組截圖演示了對 `graphql` 的成功外部請求以及從 `graphql` 到位於節點 `ip-10-0-0-151.af-south-1.compute.internal` 上的共置 `orders` 副本的成功嵌套請求。

![Before](../images/before.png)
![Before results](../images/before-results.png)

使用 Istio,您可以驗證和導出代理感知的任何 [upstream clusters](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/intro/terminology) 和端點的統計信息。這可以幫助提供網路流量的圖像以及工作負載服務之間的分佈份額。繼續使用相同的示例,可以使用以下命令獲取 `graphql` 代理感知的 `orders` 端點:


```bash
kubectl exec -it deploy/graphql -n ecommerce -c istio-proxy -- curl localhost:15000/clusters | grep orders 
```

```bash
...
orders-service.ecommerce.svc.cluster.local::10.0.1.33:3003::**rq_error::0**
orders-service.ecommerce.svc.cluster.local::10.0.1.33:3003::**rq_success::119**
orders-service.ecommerce.svc.cluster.local::10.0.1.33:3003::**rq_timeout::0**
orders-service.ecommerce.svc.cluster.local::10.0.1.33:3003::**rq_total::119**
orders-service.ecommerce.svc.cluster.local::10.0.1.33:3003::**health_flags::healthy**
orders-service.ecommerce.svc.cluster.local::10.0.1.33:3003::**region::af-south-1**
orders-service.ecommerce.svc.cluster.local::10.0.1.33:3003::**zone::af-south-1b**
...
```

在這種情況下,`graphql` 代理只知道與它共享節點的 `orders` 副本的端點。如果您從 orders 服務中刪除 `internalTrafficPolicy: Local` 設置,然後重新運行類似上面的命令,則結果將返回分佈在不同節點上的所有副本的端點。此外,通過檢查各個端點的 `rq_total`,您會注意到網路分佈的份額相對均勻。因此,如果端點與運行在不同 AZ 中的上游服務相關聯,則這種跨區域的網路分佈將導致更高的成本。

如上一節所述,您可以通過利用 pod 親和性來共置頻繁通信的 Pod。

```yaml hl_lines="11-20"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphql
  namespace: ecommerce
  labels:
    app.kubernetes.io/version: "0.1.6"
    ...
    spec:
      serviceAccountName: graphql-service-account
      affinity:
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - orders
            topologyKey: "kubernetes.io/hostname"
```

當 `graphql` 和 `orders` 副本不在同一節點 (`ip-10-0-0-151.af-south-1.compute.internal`) 上時,第一個對 `graphql` 的請求成功,如 Postman 截圖中的 `200 response code` 所示,而第二個從 `graphql` 到 `orders` 的嵌套請求失敗,返回 `503 response code`。

![After](../images/after.png)
![After results](../images/after-results.png)

## 其他資源

* [Addressing latency and data transfer costs on EKS using Istio](https://aws.amazon.com/blogs/containers/addressing-latency-and-data-transfer-costs-on-eks-using-istio/)
* [Exploring the effect of Topology Aware Hints on network traffic in Amazon Elastic Kubernetes Service](https://aws.amazon.com/blogs/containers/exploring-the-effect-of-topology-aware-hints-on-network-traffic-in-amazon-elastic-kubernetes-service/)
* [Getting visibility into your Amazon EKS Cross-AZ pod to pod network bytes](https://aws.amazon.com/blogs/containers/getting-visibility-into-your-amazon-eks-cross-az-pod-to-pod-network-bytes/)
* [Optimize AZ Traffic with Istio](https://youtu.be/EkpdKVm9kQY)
* [Optimize AZ Traffic with Topology Aware Routing](https://youtu.be/KFgE_lNVfz4)
* [Optimize Kubernetes Cost & Performance with Service Internal Traffic Policy](https://youtu.be/-uiF_zixEro)
* [Optimize Kubernetes Cost & Performance with Istio and Service Internal Traffic Policy](https://youtu.be/edSgEe7Rihc)
* [Overview of Data Transfer Costs for Common Architectures](https://aws.amazon.com/blogs/architecture/overview-of-data-transfer-costs-for-common-architectures/) 
* [Understanding data transfer costs for AWS container services](https://aws.amazon.com/blogs/containers/understanding-data-transfer-costs-for-aws-container-services/)
