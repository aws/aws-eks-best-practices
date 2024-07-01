# Linux 的前綴模式

Amazon VPC CNI 會將網路前綴指派給 [Amazon EC2 網路介面](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-prefix-eni.html)，以增加可用於節點的 IP 位址數量，並增加每個節點的 Pod 密度。您可以設定 Amazon VPC CNI 附加元件的 1.9.0 或更新版本，以指派 IPv4 和 IPv6 CIDR 而非將個別次要 IP 位址指派給網路介面。

前綴模式在 IPv6 叢集上預設為啟用狀態，且為唯一支援的選項。VPC CNI 會將 /80 IPv6 前綴指派給 ENI 上的一個插槽。請參閱本指南的 [IPv6 區段](../ipv6/index.md) 以取得更多資訊。

使用前綴指派模式時，每個執行個體類型的最大彈性網路介面數量保持不變，但您現在可以設定 Amazon VPC CNI 以指派 /28 (16 個 IP 位址) IPv4 位址前綴，而非將個別 IPv4 位址指派給網路介面上的插槽。當 `ENABLE_PREFIX_DELEGATION` 設為 true 時，VPC CNI 會從指派給 ENI 的前綴中，為 Pod 配置一個 IP 位址。請遵循 [EKS 使用者指南](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html) 中提及的指示，啟用前綴 IP 模式。

![illustration of two worker subnets, comparing ENI secondary IPvs to ENIs with delegated prefixes](./image.png)

您可以指派給網路介面的 IP 位址數量上限取決於執行個體類型。您指派給網路介面的每個前綴都算作一個 IP 位址。例如，`c5.large` 執行個體每個網路介面的 IPv4 位址限制為 `10` 個。此執行個體的每個網路介面都有一個主要 IPv4 位址。如果網路介面沒有次要 IPv4 位址，您最多可以將 9 個前綴指派給該網路介面。對於您指派給網路介面的每個額外 IPv4 位址，您可以指派一個較少的前綴給該網路介面。請查看 AWS EC2 文件中有關 [每個執行個體類型的網路介面 IP 位址數量](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI) 和 [將前綴指派給網路介面](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-prefix-eni.html) 的資訊。

在工作節點初始化期間，VPC CNI 會將一個或多個前綴指派給主要 ENI。CNI 會透過維護一個熱池來預先配置一個前綴，以加快 Pod 啟動速度。可以透過設定環境變數來控制要在熱池中保留的前綴數量。

* `WARM_PREFIX_TARGET`，超過目前需求而配置的前綴數量。
* `WARM_IP_TARGET`，超過目前需求而配置的 IP 位址數量。
* `MINIMUM_IP_TARGET`，任何時候都必須可用的最小 IP 位址數量。
* 如果設定了 `WARM_IP_TARGET` 和 `MINIMUM_IP_TARGET`，它們將覆蓋 `WARM_PREFIX_TARGET`。

隨著更多 Pod 排程，將會為現有 ENI 要求額外的前綴。首先，VPC CNI 會嘗試將新的前綴配置給現有 ENI。如果 ENI 已達到容量上限，VPC CNI 會嘗試為節點配置新的 ENI。新的 ENI 將持續連接，直到達到最大 ENI 限制 (由執行個體類型定義)。當新的 ENI 連接時，ipamd 將配置一個或多個前綴，以維持 `WARM_PREFIX_TARGET`、`WARM_IP_TARGET` 和 `MINIMUM_IP_TARGET` 設定。

![flow chart of procedure for assigning IP to pod](./image-2.jpeg)

## 建議

### 使用前綴模式的情況

如果您在工作節點上遇到 Pod 密度問題，請使用前綴模式。為了避免 VPC CNI 錯誤，我們建議在遷移至前綴模式之前，檢查子網路是否有連續的 /28 前綴位址區塊。請參閱 [使用子網路保留以避免子網路碎片化 (IPv4)](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html) 一節，以取得子網路保留的詳細資訊。

為了向下相容，[max-pods](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt) 限制已設定為支援次要 IP 模式。要增加 Pod 密度，請為節點指定 `max-pods` 值和 `--use-max-pods=false` 作為使用者資料。您可以考慮使用 [max-pod-calculator.sh](https://github.com/awslabs/amazon-eks-ami/blob/master/files/max-pods-calculator.sh) 指令碼，計算 EKS 針對特定執行個體類型建議的最大 Pod 數量。請參閱 EKS [使用者指南](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html) 以取得使用者資料範例。

```
./max-pods-calculator.sh --instance-type m5.large --cni-version ``1.9``.0 --cni-prefix-delegation-enabled
```

對於使用 [CNI 自訂網路](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html) 的使用者而言，前綴指派模式尤其相關，因為主要 ENI 不會用於 Pod。使用前綴指派，即使主要 ENI 未用於 Pod，您仍然可以在幾乎所有 Nitro 執行個體類型上連接更多 IP。

### 避免使用前綴模式的情況

如果您的子網路非常碎片化，且沒有足夠可用的 IP 位址來建立 /28 前綴，請避免使用前綴模式。如果產生前綴的子網路碎片化 (高度使用且散佈有次要 IP 位址的子網路)，則前綴連接可能會失敗。您可以透過建立新的子網路並保留前綴空間來避免此問題。

在前綴模式下，工作節點的安全性群組會由 Pod 共用。如果您有安全性需求，需要在共用計算資源上執行具有不同網路安全性需求的應用程式來達到合規性，請考慮使用 [Pod 的安全性群組](../sgpp/index.md)。

### 在相同節點群組中使用類似的執行個體類型

您的節點群組可能包含許多類型的執行個體。如果某個執行個體的最大 Pod 數量較低，該值將套用至節點群組中的所有節點。請考慮在節點群組中使用類似的執行個體類型，以最大化節點使用率。如果您使用 Karpenter 進行自動節點擴展，我們建議在 Provisioner API 的 requirements 部分設定 [node.kubernetes.io/instance-type](https://karpenter.sh/docs/concepts/nodepools/)。

!!! warning
    特定節點群組中所有節點的最大 Pod 數量，由該節點群組中任何單一執行個體類型的*最低*最大 Pod 數量所定義。

### 設定 `WARM_PREFIX_TARGET` 以節省 IPv4 位址

[安裝資訊清單](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/v1.9/aws-k8s-cni.yaml#L158) 中 `WARM_PREFIX_TARGET` 的預設值為 1。在大多數情況下，`WARM_PREFIX_TARGET` 的建議值 1 將提供快速的 Pod 啟動時間和最小化未使用的指派給執行個體的 IP 位址之間的良好平衡。

如果您需要進一步節省每個節點的 IPv4 位址，請使用 `WARM_IP_TARGET` 和 `MINIMUM_IP_TARGET` 設定，這些設定在設定時會覆蓋 `WARM_PREFIX_TARGET`。將 `WARM_IP_TARGET` 設為小於 16 的值，您可以防止 CNI 保留整個多餘的前綴連接。

### 優先配置新的前綴而非連接新的 ENI

配置額外的前綴給現有 ENI 是比建立和連接新的 ENI 給執行個體更快的 EC2 API 操作。使用前綴可提升效能，同時節省 IPv4 位址配置。連接前綴通常在一秒內完成，而連接新的 ENI 則可能需要長達 10 秒。對於大多數使用案例而言，在執行前綴模式時，CNI 只需要每個工作節點一個 ENI。如果您可以承擔 (在最壞的情況下) 每個節點最多 15 個未使用的 IP，我們強烈建議您使用較新的前綴指派網路模式，並實現隨之而來的效能和效率提升。

### 使用子網路保留以避免子網路碎片化 (IPv4)

當 EC2 將 /28 IPv4 前綴配置給 ENI 時，它必須是來自您子網路的連續 IP 位址區塊。如果產生前綴的子網路碎片化 (高度使用且散佈有次要 IP 位址的子網路)，則前綴連接可能會失敗，您將在 VPC CNI 記錄中看到以下錯誤訊息：

```
failed to allocate a private IP/Prefix address: InsufficientCidrBlocks: There are not enough free cidr blocks in the specified subnet to satisfy the request.
```

為了避免碎片化並有足夠的連續空間來建立前綴，您可以使用 [VPC 子網路 CIDR 保留](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html#work-with-subnet-cidr-reservations)來保留子網路內專供前綴使用的 IP 空間。一旦您建立了保留，VPC CNI 外掛程式將呼叫 EC2 API 來指派自動從保留空間配置的前綴。

建議您建立新的子網路、保留前綴空間，並為在該子網路中執行的工作節點啟用前綴指派與 VPC CNI。如果新的子網路僅專用於在您的 EKS 叢集中執行的 Pod，且已啟用 VPC CNI 前綴指派，則您可以跳過前綴保留步驟。

### 避免降級 VPC CNI

前綴模式適用於 VPC CNI 1.9.0 版和更新版本。一旦啟用前綴模式並將前綴指派給 ENI，就必須避免將 Amazon VPC CNI 附加元件降級至低於 1.9.0 的版本。如果您決定降級 VPC CNI，必須刪除並重新建立節點。

### 在過渡至前綴委派期間取代所有節點

我們強烈建議您建立新的節點群組來增加可用的 IP 位址數量，而非滾動取代現有的工作節點。Cordon 和 drain 所有現有節點，以安全地逐出所有現有的 Pod。為了防止服務中斷，我們建議您在生產叢集上為關鍵工作負載實作 [Pod 中斷預算](https://kubernetes.io/docs/tasks/run-application/configure-pdb)。新節點上的 Pod 將從指派給 ENI 的前綴獲得 IP。確認 Pod 正在執行後，您可以刪除舊節點和節點群組。如果您使用受管理的節點群組，請遵循這裡提及的步驟來安全地 [刪除節點群組](https://docs.aws.amazon.com/eks/latest/userguide/delete-managed-node-group.html)。