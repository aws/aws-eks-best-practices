# 網路安全

網路安全有幾個方面。第一個涉及應用規則來限制網路流量在服務之間的流動。第二個涉及在傳輸過程中對流量進行加密。在 EKS 上實現這些安全措施的機制有多種,但通常包括以下項目:

## 流量控制

- 網路策略
- 安全組

## 網路加密

- 服務網格
- 容器網路介面 (CNIs)
- Ingress 控制器和負載平衡器
- Nitro 實例
- ACM 私有 CA 與 cert-manager

## 網路策略

在 Kubernetes 集群中,所有 Pod 之間的通信默認是允許的。儘管這種靈活性可能有助於促進實驗,但它並不被認為是安全的。Kubernetes 網路策略為您提供了一種限制 Pod 之間網路流量(通常稱為東西向流量)以及 Pod 和外部服務之間網路流量的機制。Kubernetes 網路策略在 OSI 模型的第 3 層和第 4 層運作。網路策略使用 pod、命名空間選擇器和標籤來識別源和目標 pod,但也可以包括 IP 地址、端口號、協議或這些的組合。網路策略可以應用於 pod 的入站或出站連接,通常稱為入站和出站規則。

通過 Amazon VPC CNI 插件的原生網路策略支持,您可以實現網路策略來保護 kubernetes 集群中的網路流量。這與上游 Kubernetes 網路策略 API 集成,確保與 Kubernetes 標準的兼容性和一致性。您可以使用上游 API 支持的不同[識別符](https://kubernetes.io/docs/concepts/services-networking/network-policies/)來定義策略。默認情況下,所有入站和出站流量都允許進入 pod。當指定了 policyType Ingress 的網路策略時,唯一允許進入 pod 的連接是來自 pod 所在節點的連接以及入站規則允許的連接。出站規則也是如此。如果定義了多個規則,則在做出決策時會考慮所有規則的聯合。因此,評估順序不會影響策略結果。

!!! 注意
    當您首次配置 EKS 集群時,VPC CNI 網路策略功能默認是不啟用的。請確保您部署了支持的 VPC CNI 插件版本,並將 vpc-cni 插件的 `ENABLE_NETWORK_POLICY` 標誌設置為 `true` 以啟用此功能。請參閱 [Amazon EKS 用戶指南](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html)以獲取詳細說明。

## 建議

### 開始使用網路策略 - 遵循最小特權原則

#### 創建默認拒絕策略

與 RBAC 策略一樣,建議在網路策略中遵循最小特權訪問原則。首先創建一個拒絕所有策略,該策略限制命名空間內的所有入站和出站流量。

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

![default-deny](./images/default-deny.jpg)

!!! 提示
    上圖是由 [Tufin](https://orca.tufin.io/netpol/) 的網路策略查看器創建的。

#### 創建一個規則以允許 DNS 查詢

一旦您設置了默認的全部拒絕規則,您就可以開始層層添加其他規則,例如允許 pod 查詢 CoreDNS 進行名稱解析的規則。

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-access
  namespace: default
spec:
  podSelector:
    matchLabels: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

![allow-dns-access](./images/allow-dns-access.jpg)

#### 逐步添加規則以選擇性地允許命名空間/pod 之間的流量

了解應用程序要求,並根據需要創建細粒度的入站和出站規則。下面的示例展示了如何將端口 80 上的入站流量限制為從 `client-one` 到 `app-one`。這有助於最小化攻擊面,並降低未經授權訪問的風險。

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-app-one
  namespace: default
spec:
  podSelector:
    matchLabels:
      k8s-app: app-one
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          k8s-app: client-one
    ports:
    - protocol: TCP
      port: 80
```

![allow-ingress-app-one](./images/allow-ingress-app-one.png)

### 監控網路策略執行

- **使用網路策略編輯器**
  - [網路策略編輯器](https://networkpolicy.io/)有助於可視化、安全評分和從網路流量日誌自動生成
  - 以交互式方式構建網路策略
- **審計日誌**
  - 定期審查您的 EKS 集群的審計日誌
  - 審計日誌提供了有關在集群上執行的操作的大量信息,包括對網路策略的更改
  - 使用此信息跟蹤網路策略隨時間的變化,並檢測任何未經授權或意外的變化
- **自動化測試**
  - 通過創建一個模擬生產環境的測試環境來實現自動化測試,並定期部署試圖違反您的網路策略的工作負載。
- **監控指標**
  - 配置您的可觀察性代理程序,從 VPC CNI 節點代理程序中刮取 Prometheus 指標,這允許監控代理程序健康狀況和 sdk 錯誤。
- **定期審計網路策略**
  - 定期審計您的網路策略,以確保它們符合您當前的應用程序要求。隨著您的應用程序的發展,審計為您提供了機會來刪除冗餘的入站、出站規則,並確保您的應用程序沒有過多的權限。
- **使用開放策略代理 (OPA) 確保網路策略的存在**
  - 使用如下所示的 OPA 策略,確保在上線應用程序 pod 之前網路策略始終存在。如果沒有相應的網路策略,此策略將拒絕帶有標籤 `k8s-app: sample-app` 的 k8s pod 的上線。

```javascript
package kubernetes.admission
import data.kubernetes.networkpolicies

deny[msg] {
    input.request.kind.kind == "Pod"
    pod_label_value := {v["k8s-app"] | v := input.request.object.metadata.labels}
    contains_label(pod_label_value, "sample-app")
    np_label_value := {v["k8s-app"] | v := networkpolicies[_].spec.podSelector.matchLabels}
    not contains_label(np_label_value, "sample-app")
    msg:= sprintf("The Pod %v could not be created because it is missing an associated Network Policy.", [input.request.object.metadata.name])
}
contains_label(arr, val) {
    arr[_] == val
}
```

### 故障排除

#### 監控 vpc-network-policy-controller、node-agent 日誌

啟用 EKS 控制平面控制器管理器日誌,以診斷網路策略功能。您可以將控制平面日誌流式傳輸到 CloudWatch 日誌組,並使用 [CloudWatch 日誌洞見](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)執行高級查詢。從日誌中,您可以查看哪些 pod 端點對象被解析為網路策略、策略的協調狀態,以及調試策略是否按預期工作。

此外,Amazon VPC CNI 允許您啟用從 EKS 工作節點收集和導出策略執行日誌到 [Amazon Cloudwatch](https://aws.amazon.com/cloudwatch/)。啟用後,您可以利用 [CloudWatch 容器洞見](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html)來提供與網路策略相關的使用情況洞見。

Amazon VPC CNI 還附帶了一個 SDK,提供了與節點上的 eBPF 程序交互的接口。當 `aws-node` 部署到節點上時,SDK 就會安裝。您可以在節點上的 `/opt/cni/bin` 目錄下找到已安裝的 SDK 二進制文件。在啟動時,SDK 支持基本功能,如檢查 eBPF 程序和映射。

```shell
sudo /opt/cni/bin/aws-eks-na-cli ebpf progs
```

#### 記錄網路流量元數據

[AWS VPC 流量日誌](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html)捕獲有關通過 VPC 的流量的元數據,例如源和目標 IP 地址和端口以及接受/丟棄的數據包。可以分析此信息,查看 VPC 內部資源(包括 Pod)之間的可疑或異常活動。但是,由於 pod 的 IP 地址在替換時經常會更改,因此流量日誌本身可能不夠。Calico Enterprise 通過 pod 標籤和其他元數據擴展了流量日誌,使得更容易解析 pod 之間的流量流。

## 安全組

EKS 使用 [AWS VPC 安全組](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html) (SGs) 來控制 Kubernetes 控制平面和集群的工作節點之間的流量。安全組也用於控制工作節點與其他 VPC 資源和外部 IP 地址之間的流量。當您配置 EKS 集群(使用 Kubernetes 版本 1.14-eks.3 或更高版本)時,將為您自動創建一個集群安全組。此安全組允許 EKS 控制平面和來自托管節點組的節點之間的無阻礙通信。為簡單起見,建議您將集群 SG 添加到所有節點組,包括非托管節點組。

在 Kubernetes 版本 1.14 和 EKS 版本 eks.3 之前,EKS 控制平面和節點組配置了單獨的安全組。EKS 控制平面和節點組安全組的最小和建議規則可以在 [https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html) 上找到。_控制平面安全組_的最小規則允許從工作節點 SG 進行端口 443 的入站流量。這條規則允許 kubelets 與 Kubernetes API 服務器通信。它還包括端口 10250 的出站流量到工作節點 SG;10250 是 kubelets 監聽的端口。同樣,_節點組_的最小規則允許從控制平面 SG 進行端口 10250 的入站流量,並允許端口 443 的出站流量到控制平面 SG。最後還有一條規則允許節點組內部的無阻礙通信。

如果您需要控制在集群內運行的服務與集群外運行的服務(如 RDS 數據庫)之間的通信,請考慮[為 pod 配置安全組](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html)。使用安全組為 pod,您可以將一個**現有的**安全組分配給一組 pod。

!!! 警告
    如果您引用了在創建 pod 之前不存在的安全組,則 pod 將不會被調度。

您可以通過創建 `SecurityGroupPolicy` 對象並指定 `PodSelector` 或 `ServiceAccountSelector` 來控制將哪些 pod 分配給安全組。將選擇器設置為 `{}` 將把 `SecurityGroupPolicy` 中引用的 SG 分配給命名空間中的所有 pod 或命名空間中的所有服務帳戶。在實現安全組為 pod 之前,請確保您已熟悉所有[注意事項](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html#security-groups-pods-considerations)。

!!! 重要
    如果您使用 SG 為 pod,您**必須**創建規則允許從集群安全組(kubelet)進行端口 53 的出站流量。同樣,您**必須**更新集群安全組以接受來自 pod 安全組的端口 53 入站流量。

!!! 重要
    [安全組的限制](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html#vpc-limits-security-groups)在使用安全組為 pod 時仍然適用,因此請謹慎使用。

!!! 重要
    您**必須**為 pod 配置的所有探針創建入站流量規則。

!!! 重要
    安全組為 pod 依賴於一個稱為 [ENI 綁定](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/container-instance-eni.html)的功能,該功能是為了增加 EC2 實例的 ENI 密度而創建的。當一個 pod 被分配給一個 SG 時,VPC 控制器會將節點組中的一個分支 ENI 與該 pod 關聯。如果在調度 pod 時,節點組中沒有足夠的分支 ENI,則 pod 將保持掛起狀態。實例可以支持的分支 ENI 數量因實例類型/系列而異。有關進一步詳細信息,請參閱 [https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html#supported-instance-types](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html#supported-instance-types)。

儘管安全組為 pod 提供了一種 AWS 原生的方式來控制集群內外的網路流量,而無需策略守護程序的開銷,但也有其他選擇。例如,Cilium 策略引擎允許您在網路策略中引用 DNS 名稱。Calico Enterprise 包括一個將網路策略映射到 AWS 安全組的選項。如果您已實現了像 Istio 這樣的服務網格,您可以使用出口網關來限制對特定完全限定域或 IP 地址的網路出口。有關此選項的更多信息,請閱讀關於 [Istio 中的出口流量控制](https://istio.io/blog/2019/egress-traffic-control-in-istio-part-1/)的三部分系列文章。

## 何時使用網路策略與安全組為 pod?

### 何時使用 Kubernetes 網路策略

- **控制 pod 到 pod 的流量**
  - 適合控制集群內部 pod 之間的網路流量(東西向流量)
- **在 IP 地址或端口級別(OSI 第 3 層或第 4 層)控制流量**

### 何時使用 AWS 安全組為 pod (SGP)

- **利用現有的 AWS 配置**
  - 如果您已經有一組複雜的 EC2 安全組來管理對 AWS 服務的訪問,並且您正在將應用程序從 EC2 實例遷移到 EKS,SGP 可以是一個非常好的選擇,允許您重用安全組資源並將其應用於您的 pod。
- **控制對 AWS 服務的訪問**
  - 如果您在 EKS 集群中運行的應用程序需要與其他 AWS 服務(如 RDS 數據庫)通信,請使用 SGP 作為控制從 pod 到 AWS 服務的流量的有效機制。
- **隔離 Pod 和節點流量**
  - 如果您想完全分離 pod 流量和其餘節點流量,請在 `POD_SECURITY_GROUP_ENFORCING_MODE=strict` 模式下使用 SGP。

### 使用 `安全組為 pod` 和 `網路策略` 的最佳實踐

- **分層安全**
  - 結合使用 SGP 和 kubernetes 網路策略,實現分層安全方法
  - 使用 SGP 限制對集群外部 AWS 服務的網路級訪問,而 kubernetes 網路策略可以限制集群內部 pod 之間的網路流量
- **最小特權原則**
  - 只允許 pod 或命名空間之間必要的流量
- **對應用程序進行網段劃分**
  - 盡可能對網路策略進行應用程序分段,以減少應用程序受損時的影響範圍
- **保持策略簡單明了**
  - Kubernetes 網路策略可能非常細粒度和複雜,最好保持它們盡可能簡單,以減少錯誤配置的風險並簡化管理開銷
- **減少攻擊面**
  - 通過限制應用程序的暴露來最小化攻擊面

!!! 注意
    安全組為 pod 提供了兩種執行模式:`strict` 和 `standard`。當在 EKS 集群中同時使用網路策略和安全組為 pod 功能時,您必須使用 `standard` 模式。

在網路安全方面,分層方法通常是最有效的解決方案。結合使用 kubernetes 網路策略和 SGP 可以為您在 EKS 中運行的應用程序提供穩健的深度防禦策略。

## 服務網格策略執行或 Kubernetes 網路策略

`服務網格`是一個專用的基礎設施層,您可以將其添加到應用程序中。它允許您透明地添加觀察能力、流量管理和安全性等功能,而無需將它們添加到您自己的代碼中。

服務網格在 OSI 模型的第 7 層(應用層)強制執行策略,而 kubernetes 網路策略在第 3 層(網路層)和第 4 層(傳輸層)運作。在這個領域有許多產品,如 AWS AppMesh、Istio、Linkerd 等。

### 何時使用服務網格進行策略執行

- 已經投資服務網格
- 需要更高級的功能,如流量管理、可觀察性和安全性
  - 流量控制、負載平衡、斷路器、速率限制、超時等
  - 對您的服務性能的詳細洞見(延遲、錯誤率、每秒請求數、請求量等)
  - 您想要實現和利用服務網格的安全功能,如 mTLS

### 選擇 Kubernetes 網路策略用於簡單的用例

- 限制哪些 pod 可以相互通信
- 網路策略需要的資源比服務網格少,因此適合簡單的用例或規模較小的集群,在這些情況下,運行和管理服務網格的開銷可能是不合理的

!!! 提示
    網路策略和服務網格也可以一起使用。使用網路策略為您的 pod 提供基線安全性和隔離,然後使用服務網格添加流量管理、可觀察性和安全性等其他功能。

## 第三方網路策略引擎

當您有高級策略需求時,如全局網路策略、支持基於 DNS 主機名的規則、第 7 層規則、基於服務帳戶的規則以及明確的拒絕/日誌操作等,請考慮第三方網路策略引擎。[Calico](https://docs.projectcalico.org/introduction/) 是來自 [Tigera](https://tigera.io) 的開源策略引擎,可以很好地與 EKS 配合使用。除了實現 Kubernetes 網路策略的全套功能外,Calico 還支持擴展的網路策略,提供了更豐富的功能集,包括對第 7 層規則(如 HTTP)的支持,當與 Istio 集成時。Calico 策略可以在命名空間、Pod、服務帳戶或全局範圍內定義。當策略範圍為服務帳戶時,它會將一組入站/出站規則與該服務帳戶關聯。在適當的 RBAC 規則下,您可以防止團隊覆蓋這些規則,從而允許 IT 安全專業人員安全地委派命名空間管理。Isovalent 公司(Cilium 的維護者)也擴展了網路策略,包括對第 7 層規則(如 HTTP)的部分支持。Cilium 還支持 DNS 主機名,這對於限制 Kubernetes 服務/Pod 與 VPC 內外的資源之間的流量很有用。相比之下,Calico Enterprise 包括一個功能,可以將 Kubernetes 網路策略映射到 AWS 安全組,以及 DNS 主機名。

您可以在 [https://github.com/ahmetb/kubernetes-network-policy-recipes](https://github.com/ahmetb/kubernetes-network-policy-recipes) 找到常見 Kubernetes 網路策略的列表。Calico 的類似規則集可以在 [https://docs.projectcalico.org/security/calico-network-policy](https://docs.projectcalico.org/security/calico-network-policy) 上找到。

### 遷移到 Amazon VPC CNI 網路策略引擎

為了保持一致性並避免 pod 通信行為出現意外,建議在您的集群中僅部署一個網路策略引擎。如果您想從 3P 遷移到 VPC CNI 網路策略引擎,我們建議在啟用 VPC CNI 網路策略支持之前,將您現有的 3P NetworkPolicy CRD 轉換為 Kubernetes NetworkPolicy 資源。並在生產環境中應用之前,在單獨的測試集群中測試轉換後的策略。這樣可以讓您識別並解決 pod 通信行為中任何潛在的問題或不一致。

#### 遷移工具

為了協助您的遷移過程,我們開發了一個名為 [K8s 網路策略遷移器](https://github.com/awslabs/k8s-network-policy-migrator)的工具,它可以將您現有的 Calico/Cilium 網路策略 CRD 轉換為 Kubernetes 原生網路策略。轉換後,您可以直接在運行 VPC CNI 網路策略控制器的新集群上測試轉換後的網路策略。該工具旨在幫助您簡化遷移過程,並確保平滑過渡。

!!! 重要
    遷移工具只會轉換與原生 kubernetes 網路策略 api 兼容的 3P 策略。如果您正在使用 3P 插件提供的高級網路策略功能,遷移工具將跳過並報告它們。

請注意,目前 AWS VPC CNI 網路策略工程團隊不支持遷移工具,它是以最大努力的基礎提供給客戶的。我們鼓勵您利用這個工具來促進您的遷移過程。如果您在使用工具時遇到任何問題或錯誤,我們誠懇地要求您在 [GitHub 上創建一個問題](https://github.com/awslabs/k8s-network-policy-migrator/issues)。您的反饋對我們來說是非常寶貴的,將有助於我們不斷改進我們的服務。

### 其他資源

- [Kubernetes 與 Tigera: 網路策略、安全性和審計](https://youtu.be/lEY2WnRHYpg)
- [Calico Enterprise](https://www.tigera.io/tigera-products/calico-enterprise/)
- [Cilium](https://cilium.readthedocs.io/en/stable/intro/)
- [NetworkPolicy 編輯器](https://cilium.io/blog/2021/02/10/network-policy-editor) Cilium 提供的交互式策略編輯器
- [Inspektor Gadget advise network-policy gadget](https://www.inspektor-gadget.io/docs/latest/gadgets/advise/network-policy/) 根據網路流量分析建議網路策略

## 傳輸中的加密

需要符合 PCI、HIPAA 或其他法規的應用程序可能需要在傳輸過程中加密數據。如今,TLS 是加密線路上流量的事實標準。TLS 與其前身 SSL 一樣,通過加密協議在網路上提供安全通信。TLS 使用對稱加密,其中加密數據的密鑰是根據會話開始時協商的共享密鑰生成的。以下是在 Kubernetes 環境中加密數據的一些方式。

### Nitro 實例

在以下 Nitro 實例類型(如 C5n、G4、I3en、M5dn、M5n、P3dn、R5dn 和 R5n)之間交換的流量默認情況下會自動加密。當存在中間跳躍(如過境網關或負載平衡器)時,流量不會被加密。有關傳輸中的加密以及支持默認網路加密的完整實例類型列表的更多詳細信息,請參閱[傳輸中的加密](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/data-protection.html#encryption-transit)。

### 容器網路介面 (CNIs)

[WeaveNet](https://www.weave.works/oss/net/) 可以配置為使用 NaCl 加密自動加密所有 sleeve 流量,並使用 IPsec ESP 加密快速數據路徑流量。

### 服務網格

傳輸中的加密也可以通過服務網格(如 App Mesh、Linkerd v2 和 Istio)來實現。AppMesh 支持使用 X.509 證書或 Envoy 的密鑰發現服務(SDS)的 [mTLS](https://docs.aws.amazon.com/app-mesh/latest/userguide/mutual-tls.html)。Linkerd 和 Istio 都支持 mTLS。

[aws-app-mesh-examples](https://github.com/aws/aws-app-mesh-examples) GitHub 存儲庫提供了使用 X.509 證書和 SPIRE 作為 SDS 提供者配置 Envoy 容器 mTLS 的演練:

- [使用 X.509 證書配置 mTLS](https://github.com/aws/aws-app-mesh-examples/tree/main/walkthroughs/howto-k8s-mtls-file-based)
- [使用 SPIRE (SDS) 配置 TLS](https://github.com/aws/aws-app-mesh-examples/tree/main/walkthroughs/howto-k8s-mtls-sds-based)

App Mesh 還支持使用 [AWS 證書管理器](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html) (ACM) 發布的私有證書或存儲在虛擬節點本地文件系統上的證書的 [TLS 加密](https://docs.aws.amazon.com/app-mesh/latest/userguide/virtual-node-tls.html)。

[aws-app-mesh-examples](https://github.com/aws/aws-app-mesh-examples) GitHub 存儲庫提供了使用由 ACM 發布的證書和打包在您的 Envoy 容器中的證書配置 TLS 的演練:

- [使用文件提供的 TLS 證書配置 TLS](https://github.com/aws/aws-app-mesh-examples/tree/master/walkthroughs/howto-tls-file-provided)
- [使用 AWS 證書管理器配置 TLS](https://github.com/aws/aws-app-mesh-examples/tree/master/walkthroughs/tls-with-acm)

### Ingress 控制器和負載平衡器

Ingress 控制器是一種智能路由來自集群外部的 HTTP/S 流量到集群內部運行的服務的方式。通常,這些 Ingress 前面是一個第 4 層負載平衡器,如經典負載平衡器或網路負載平衡器 (NLB)。加密流量可以在網路中的不同位置終止,例如在負載平衡器、Ingress 資源或 Pod 上。您終止 SSL 連接的方式和位置將最終由您組織的網路安全策略決定。例如,如果您有一個要求端到端加密的策略,您將不得不在 Pod 上解密流量。這將給您的 Pod 增加額外的負擔,因為它將不得不花費週期建立初始握手。總的來說,SSL/TLS 處理是非常耗費 CPU 的。因此,如果您有靈活性,請嘗試在 Ingress 或負載平衡器上執行 SSL 卸載。

#### 使用 AWS 彈性負載平衡器進行加密

[AWS 應用程序負載平衡器](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) (ALB) 和 [網路負載平衡器](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html) (NLB) 都支持傳輸加密 (SSL 和 TLS)。ALB 的 `alb.ingress.kubernetes.io/certificate-arn` 註釋允許您指定要添加到 ALB 的證書。如果省略了註釋,控制器將嘗試通過使用主機字段匹配可用的 [AWS 證書管理器 (ACM)](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html) 證書來向需要它的監聽器添加證書。從 EKS v1.15 開始,您可以使用如下所示的 `service.beta.kubernetes.io/aws-load-balancer-ssl-cert` 註釋與 NLB 一起使用。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: demo-app
  namespace: default
  labels:
    app: demo-app
  annotations:
     service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
     service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "<certificate ARN>"
     service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
     service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "http"
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 80
    protocol: TCP
  selector:
    app: demo-app
---
kind: Deployment
apiVersion: apps/v1
metadata:
  name: nginx
  namespace: default
  labels:
    app: demo-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demo-app
  template:
    metadata:
      labels:
        app: demo-app
    spec:
      containers:
        - name: nginx
          image: nginx
          ports:
            - containerPort: 443
              protocol: TCP
            - containerPort: 80
              protocol: TCP
```

以下是有關 SSL/TLS 終止的其他示例。

- [使用 Contour 和 Let's Encrypt 以 GitOps 方式保護 EKS Ingress](https://aws.amazon.com/blogs/containers/securing-eks-ingress-contour-lets-encrypt-gitops/)
- [如何使用 ACM 終止 Amazon EKS 工作負載上的 HTTPS 流量?](https://aws.amazon.com/premiumsupport/knowledge-center/terminate-https-traffic-eks-acm/)

!!! 注意
    一些 Ingress,如 AWS LB 控制器,使用註釋而不是作為 Ingress 規範的一部分來實現 SSL/TLS。

### ACM 私有 CA 與 cert-manager

您可以使用 ACM 私有證書頒發機構 (CA) 和 [cert-manager](https://cert-manager.io/)（一個流行的 Kubernetes 插件,用於分發、續期和吊銷證書）來啟用 TLS 和 mTLS,以保護您在 EKS 中的應用程序工作負載,包括 Ingress、Pod 和 Pod 之間。ACM 私有 CA 是一個高度可用、安全的托管 CA,無需管理自己的 CA 的前期和維護成本。如果您正在使用默認的 Kubernetes 證書頒發機構,那麼您有機會通過 ACM 私有 CA 來提高安全性並滿足合規性要求。ACM 私有 CA 在 FIPS 140-2 第 3 級硬件安全模塊(非常安全)中保護私鑰,而默認 CA 將密鑰編碼存儲在內存中(不太安全)。集中式 CA 還可以為 Kubernetes 環境內外的私有證書提供更好的控制和可審計性。

#### 用於工作負載之間相互 TLS 的短期 CA 模式

在 EKS 中使用 ACM 私有 CA 進行 mTLS 時,建議您使用短期證書和_短期 CA 模式_。雖然在通用 CA 模式下也可以發出短期證書,但對於需要頻繁發出新證書的用例,使用短期 CA 模式的成本效益更高(比通用模式便宜約 75%)。此外,您應該嘗試將私有證書的有效期與 EKS 集群中的 pod 生命週期保持一致。[在這裡了解有關 ACM 私有 CA 及其優勢的更多信息](https://aws.amazon.com/certificate-manager/private-certificate-authority/)。

#### ACM 設置說明

首先按照 [ACM 私有 CA 技術文檔](https://docs.aws.amazon.com/acm-pca/latest/userguide/create-CA.html)中提供的步驟創建一個私有 CA。創建了私有 CA 後,使用[常規安裝說明](https://cert-manager.io/docs/installation/)安裝 cert-manager。安裝 cert-manager 後,按照 [GitHub 上的設置說明](https://github.com/cert-manager/aws-privateca-issuer#setup)安裝私有 CA Kubernetes cert-manager 插件。該插件允許 cert-manager 從 ACM 私有 CA 請求私有證書。

現在您有了一個私有 CA 和一個安裝了 cert-manager 和插件的 EKS 集群,是時候設置權限並創建發行者了。更新 EKS 節點角色的 IAM 權限,以允許訪問 ACM 私有 CA。將 `<CA_ARN>` 替換為您的私有 CA 的值:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "awspcaissuer",
            "Action": [
                "acm-pca:DescribeCertificateAuthority",
                "acm-pca:GetCertificate",
                "acm-pca:IssueCertificate"
            ],
            "Effect": "Allow",
            "Resource": "<CA_ARN>"
        }
    ]
}
```

也可以使用 [IAM 角色服務帳戶, 或 IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)。請參閱下面的附加資源部分以獲取完整示例。

通過創建一個名為 cluster-issuer.yaml 的自定義資源定義文件,在 Amazon EKS 中創建一個發行者,其中包含以下文本,並用您的私有 CA 的 `<CA_ARN>` 和 `<Region>` 信息替換相應部分。

```yaml
apiVersion: awspca.cert-manager.io/v1beta1
kind: AWSPCAClusterIssuer
metadata:
          name: demo-test-root-ca
spec:
          arn: <CA_ARN>
          region: <Region>
```

部署您創建的發行者。

```bash
kubectl apply -f cluster-issuer.yaml
```

您的 EKS 集群現在已配置為從私有 CA 請求證書。您現在可以使用 cert-manager 的 `Certificate` 資源來發出證書,只需將 `issuerRef` 字段的值更改為您上面創建的私有 CA 發行者即可。有關如何指定和請求證書資源的更多詳細信息,請查看 cert-manager 的[證書資源指南](https://cert-manager.io/docs/usage/certificate/)。[在這裡查看示例](https://github.com/cert-manager/aws-privateca-issuer/tree/main/config/samples/)。

### ACM 私有 CA 與 Istio 和 cert-manager

如果您在 EKS 集群中運行 Istio,您可以禁用 Istio 控制平面(特別是 `istiod`)充當根證書頒發機構 (CA) 的功能,並將 ACM 私有 CA 配置為工作負載之間 mTLS 的根 CA。如果您採用這種方法,請考慮在 ACM 私有 CA 中使用_短期 CA 模式_。請參閱[上一節](#short-lived-ca-mode-for-mutual-tls-between-workloads)和這篇[博客文章](https://aws.amazon.com/blogs/security/how-to-use-aws-private-certificate-authority-short-lived-certificate-mode)以了解更多詳情。

#### Istio 中證書簽名的工作方式(默認)

Kubernetes 中的工作負載使用服務帳戶進行識別。如果您沒有指定服務帳戶,Kubernetes 將自動為您的工作負載分配一個。此外,服務帳戶會自動掛載一個相關的令牌。該令牌用於服務帳戶的工作負載向 Kubernetes API 進行身份驗證。服務帳戶可能足以作為 Kubernetes 的身份,但 Istio 有自己的身份管理系統和 CA。當工作負載與其 envoy 側車代理一起啟動時,它需要從 Istio 獲得一個分配的身份,以便被視為可信任並被允許與網格中的其他服務通信。

為了從 Istio 獲得這個身份,`istio-agent` 會向 Istio 控制平面發送一個稱為證書簽名請求 (或 CSR) 的請求。此 CSR 包含服務帳戶令牌,以便可以在處理之前驗證工作負載的身份。此驗證過程由 `istiod` 處理,它同時充當註冊機構 (或 RA) 和 CA。RA 充當守門人,確保只有經過驗證的 CSR 才能通過並到達 CA。一旦 CSR 被驗證,它將被轉發到 CA,CA 隨後將發出一個包含 [SPIFFE](https://spiffe.io/) 身份的證書,其中包含服務帳戶。該證書被稱為 SPIFFE 可驗證身份文檔 (或 SVID)。SVID 被分配給請求服務,用於識別目的和加密服務之間傳輸中的流量。

![Istio 證書簽名請求的默認流程](./images/default-istio-csr-flow.png)

#### Istio 與 ACM 私有 CA 的證書簽名工作方式

您可以使用一個名為 Istio 證書簽名請求代理 ([istio-csr](https://cert-manager.io/docs/projects/istio-csr/)) 的 cert-manager 插件將 Istio 與 ACM 私有 CA 集成。該代理允許使用 cert manager 發行者(在本例中是 ACM 私有 CA)來保護 Istio 工作負載和控制平面組件。_istio-csr_ 代理公開了與 _istiod_ 在默認配置中提供的相同的服務,用於驗證傳入的 CSR。不同的是,在驗證之後,它會將請求轉換為 cert manager 支持的資源(即與外部 CA 發行者的集成)。

每當有來自工作負載的 CSR 時,它將被轉發到 _istio-csr_,_istio-csr_ 將從 ACM 私有 CA 請求證書。_istio-csr_ 與 ACM 私有 CA 之間的通信由 [AWS 私有 CA 發行者插件](https://github.com/cert-manager/aws-privateca-issuer)啟用。cert manager 使用此插件從 ACM 私有 CA 請求 TLS 證書。發行者插件將與 ACM 私有 CA 服務通信,為工作負載請求一個簽名證書。一旦證書被簽名,它將被返回給 _istio-csr_,_istio-csr_ 將讀取簽名請求,並將其返回給發起 CSR 的工作負載。

![使用 istio-csr 的 Istio 證書簽名請求流程](./images/istio-csr-with-acm-private-ca.png)

#### Istio 與私有 CA 設置說明

1. 首先按照[本節](#acm-private-ca-with-cert-manager)中的設置說明完成以下步驟:
2. 創建一個私有 CA
3. 安裝 cert-manager
4. 安裝發行者插件
5. 設置權限並創建一個發行者。該發行者代表 CA,用於簽署 `istiod` 和網格工作負載證書。它將與 ACM 私有 CA 通信。
6. 創建一個 `istio-system` 命名空間。這是將部署 `istiod 證書`和其他 Istio 資源的地方。
7. 安裝配置為使用 AWS 私有 CA 發行者插件的 Istio CSR。您可以保留工作負載的證書簽名請求,以驗證它們是否獲得批准和簽名 (`preserveCertificateRequests=true`)。

    ```bash
    helm install -n cert-manager cert-manager-istio-csr jetstack/cert-manager-istio-csr \
    --set "app.certmanager.issuer.group=awspca.cert-manager.io" \
    --set "app.certmanager.issuer.kind=AWSPCAClusterIssuer" \
    --set "app.certmanager.issuer.name=<the-name-of-the-issuer-you-created>" \
    --set "app.certmanager.preserveCertificateRequests=true" \
    --set "app.server.maxCertificateDuration=48h" \
    --set "app.tls.certificateDuration=24h" \
    --set "app.tls.istiodCertificateDuration=24h" \
    --set "app.tls.rootCAFile=/var/run/secrets/istio-csr/ca.pem" \
    --set "volumeMounts[0].name=root-ca" \
    --set "volumeMounts[0].mountPath=/var/run/secrets/istio-csr" \
    --set "volumes[0].name=root-ca" \
    --set "volumes[0].secret.secretName=istio-root-ca"
    ```

8. 使用自定義配置安裝 Istio,以將 `cert-manager istio-csr` 替換為網格的證書提供者,而不是 `istiod`。此過程可以使用 [Istio Operator](https://tetrate.io/blog/what-is-istio-operator/) 進行。

    ```yaml
    apiVersion: install.istio.io/v1alpha1
    kind: IstioOperator
    metadata:
      name: istio
      namespace: istio-system
    spec:
      profile: "demo"
      hub: gcr.io/istio-release
      values:
      global:
        # 將證書提供者更改為 cert-manager istio 代理
        caAddress: cert-manager-istio-csr.cert-manager.svc:443
      components:
        pilot:
          k8s:
            env:
              # 禁用 istiod CA 服務器功能
            - name: ENABLE_CA_SERVER
              value: "false"
            overlays:
            - apiVersion: apps/v1
              kind: Deployment
              name: istiod
              patches:

                # 從 Secret 掛載掛載 istiod 服務和 webhook 證書
              - path: spec.template.spec.containers.[name:discovery].args[7]
                value: "--tlsCertFile=/etc/cert-manager/tls/tls.crt"
              - path: spec.template.spec.containers.[name:discovery].args[8]
                value: "--tlsKeyFile=/etc/cert-manager/tls/tls.key"
              - path: spec.template.spec.containers.[name:discovery].args[9]
                value: "--caCertFile=/etc/cert-manager/ca/root-cert.pem"

              - path: spec.template.spec.containers.[name:discovery].volumeMounts[6]
                value:
                  name: cert-manager
                  mountPath: "/etc/cert-manager/tls"
                  readOnly: true
              - path: spec.template.spec.containers.[name:discovery].volumeMounts[7]
                value:
                  name: ca-root-cert
                  mountPath: "/etc/cert-manager/ca"
                  readOnly: true

              - path: spec.template.spec.volumes[6]
                value:
                  name: cert-manager
                  secret:
                    secretName: istiod-tls
              - path: spec.template.spec.volumes[7]
                value:
                  name: ca-root-cert
                  configMap:
                    defaultMode: 420
                    name: istio-ca-root-cert
    ```

9. 部署您創建的自定義資源。

    ```bash
    istioctl operator init
    kubectl apply -f istio-custom-config.yaml
    ```

10. 現在您可以在 EKS 集群中部署一個工作負載到網格,並[強制執行 mTLS](https://istio.io/latest/docs/reference/config/security/peer_authentication/)。

![Istio 證書簽名請求](./images/istio-csr-requests.png)

## 工具和資源

- [Amazon EKS 安全沉浸式研討會 - 網路安全](https://catalog.workshops.aws/eks-security-immersionday/en-US/6-network-security)
- [如何在 EKS 中實現 cert-manager 和 ACM 私有 CA 插件以啟用 TLS](https://aws.amazon.com/blogs/security/tls-enabled-kubernetes-clusters-with-acm-private-ca-and-amazon-eks-2/)。
- [使用新的 AWS 負載平衡器控制器和 ACM 私有 CA 在 Amazon EKS 上設置端到端 TLS 加密](https://aws.amazon.com/blogs/containers/setting-up-end-to-end-tls-encryption-on-amazon-eks-with-the-new-aws-load-balancer-controller/)。
- [私有 CA Kubernetes cert-manager 插件在 GitHub 上](https://github.com/cert-manager/aws-privateca-issuer)。
- [私有 CA Kubernetes cert-manager 插件用戶指南](https://docs.aws.amazon.com/acm-pca/latest/userguide/PcaKubernetes.html)。
- [如何使用 AWS 私有證書頒發機構短期證書模式](https://aws.amazon.com/blogs/security/how-to-use-aws-private-certificate-authority-short-lived-certificate-mode)
- [在 Kubernetes 中驗證服務網格 TLS,使用 ksniff 和 Wireshark](https://itnext.io/verifying-service-mesh-tls-in-kubernetes-using-ksniff-and-wireshark-2e993b26bf95)
- [ksniff](https://github.com/eldadru/ksniff)
- [egress-operator](https://github.com/monzo/egress-operator) 一個操作員和 DNS 插件,用於控制從集群出口的流量,無需協議檢查
- [NeuVector by SUSE](https://www.suse.com/neuvector/) 開源、零信任容器安全平台,提供策略網路規則、數據丟失防護 (DLP)、Web 應用程序防火牆 (WAF) 和網路威脅簽名。
